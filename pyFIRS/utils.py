import os
import subprocess
import glob
import geopandas as gpd
import rasterio
import numpy as np
from tqdm.autonotebook import tqdm
import time
import ipyparallel as ipp


class PipelineError(RuntimeError):
    def __init__(self, message):
        self.message = message

def listlike(arg):
    '''Checks whether an argument is list-like, returns boolean'''
    return not hasattr(arg, "strip") and (hasattr(arg, "__getitem__") or
            hasattr(arg, "__iter__"))

def timefmt(seconds):
    '''Formats a time given in seconds in human-readable format.'''
    m, s = divmod(seconds, 60)
    h, m = divmod(m, 60)
    return '{:.0f} hrs, {:.0f} min, {:.1f} sec'.format(h,m,s)

def run_speed(res):
    '''Reports time spent processing jobs using ipyparallel.

    Parameters (required)
    ----------
    res: an ipyparallel AsyncResult object
        Produced, for example, when you map a function to a list of inputs,
        as in `res = view.map_async(my_func, inputs)`
    '''
    print('Human time spent:', timefmt(res.wall_time))
    print('Computer time spent:', timefmt(res.serial_time))
    print('Parallel speedup:', '{:.2f}x'.format(res.serial_time/res.wall_time))
    print('Human time per job:', '{:.2f} sec'.format(res.wall_time/res.progress))
    print('Computer time per job:', '{:.2f} sec'.format(res.serial_time/res.progress))

def pbar(res):
    '''Creates a progress bar using TQDM.

    Parameters
    ----------
    res: AsyncResult object
        result from mapping a function to a view using `ipyparallel`, for
        example, from `res = view.map_async(my_func, inputs)`
    '''
    jobs_done = res.progress
    with tqdm(total=len(res), initial=jobs_done, desc='Progress', unit='tile') as pbar:
        while not res.ready():
            new_progress = res.progress - jobs_done
            jobs_done += new_progress
            pbar.update(new_progress)
            time.sleep(0.5)
        # once jobs are completed (i.e., res.ready() returns True)
        # update the progress bar one last time
        pbar.update(len(res)-jobs_done)

def clean_dir(dir_to_clean, file_extensions):
    '''Deletes files with specified extension(s) from a directory.

    This function is intended to help cleanup outputs from command line
    tools that we do not want to keep. Files to be deleted will be
    identified using a wildcard with that file extension in dir_to_clean.

    Parameters
    ----------
    dir_to_clean: string, path
        path to directory to delete files from
    file_extension: string or list-like of strings
        file extensions that will be used for identifying files to remove,
        such as ['.tfw', '.kml'].
    '''
    if listlike(file_extensions):
        for ext in file_extensions:
            to_rem = glob.glob(os.path.join(dir_to_clean, '*{}'.format(ext)))
            for file in to_rem:
                os.remove(file)
            print("Removed {:,d} files with extension {}.".format(len(to_rem),ext))
    elif type(file_extension) == str:
        to_rem = glob.glob(os.path.join(dir_to_clean, '*{}'.format(ext)))
        for file in to_rem:
            os.remove(file)
        print("Removed {:,d} files with extension {}.".format(len(to_rem),ext))
    else:
        raise(TypeError, 'file_extensions needs to be a string or list-like of strings.')

def clean_buffer_polys(poly_shp, tile_shp, odir, simp_tol=None, simp_topol=None):
    """Removes polygons within the buffer zone of a tile.

    This function removes polygons from a shapefile that fall in the buffered
    area of point cloud tile. When building footprints or tree crowns (for
    example) are delineated from a point cloud, a buffer around the tile is
    generally be used to avoid edge effects. This tool computes the centroid of
    each polygon and determines whether it falls within the bounds of the
    unbuffered tile. It outputs a new shapefile containing only those polygons
    whose centroids fall within the unbuffered tile.

    The polygons may be simplified using optional arguments simp_tol and
    simp_topol to reduce the number of points that define their boundaries.

    Parameters
    ----------
    polygons_shp: string, path to shapefile (required)
        A shapefile containing the polygons delineated within a buffered tile.
    tile_shp: string, path to shapefile (required)
        A shapefile containing the bounds of the tile WITHOUT buffers
    odir: string, path to directory (required)
        Path to the output directory for the new shapefile
    simp_tol = numeric,
        Tolerance level for simplification. All points within a simplified
        geometry will be no more than simp_tol from the original.
    simp_topol = boolean (optional)
        Whether or not to preserve topology of polygons. If False, a quicker
        algorithm will be used, but may produce self-intersecting or otherwise
        invalid geometries.
    """
    fname = os.path.basename(poly_shp)
    outfile = os.path.join(odir, fname)
    os.makedirs(odir, exist_ok=True)

    tile_boundary = gpd.read_file(tile_shp)
    polys = gpd.read_file(poly_shp)

    # boolean indicator of whether each polygon falls within tile boundary
    clean_polys_ix = polys.centroid.within(tile_boundary.loc[0].geometry)
    # retrieve the polygons within the boundary
    clean_polys = polys[clean_polys_ix]

    if simp_tol:
        clean_polys = clean_polys.simplify(simp_tol, simp_topol)

    if len(clean_polys) > 0:
        clean_polys.to_file(outfile)

def clip_tile_from_shp(in_raster, in_shp, odir):
    '''Clips a raster image to the bounding box of a shapefile.

    The input raster will be clipped using a rasterio command line tool. The
    output raster will have the same name and file type as the input raster, and
    will be written to the output directory, odir. The process is executed using
    subprocess.run().

    Parameters
    ----------
    in_raster: string, path to file
        raster image to be clipped
    in_shp: string, path to file
        shapefile from which bounding box is calculated to clip the raster
    odir: string, path
        output directory where clipped raster will be stored

    Returns
    -------
    proc_clip: CompletedProcess
        The result of executing subprocess.run using the rio clip command.
    '''
    basename = os.path.basename(in_raster)
    # read the shapefile using geopandas and calculate its bounds
    gdf = gpd.read_file(in_shp)
    tile_bnds = ' '.join(str(x) for x in gdf.total_bounds)

    # create the output directory if it doesn't already exist
    os.makedirs(odir, exist_ok=True)
    outfile = os.path.join(odir, basename)
    # clip the raster
    proc_clip = subprocess.run(['rio', 'clip', in_raster, outfile, '--bounds', tile_bnds],
                               stderr=subprocess.PIPE, stdout=subprocess.PIPE)
    return proc_clip

def convert_project(infile, to_fmt, crs):
    '''Converts a raster to another format and specifies its projection.

    Uses rasterio command line tool executed using subprocess. The file
    generated will have the same name and be in the same folder as the input
    file.

    Parameters
    ----------
    infile: string, path to file
        input raster to be converted
    to_fmt: string
        extension indicating file format to convert to (e.g., '.tif')
    crs: string
        specification of coordinate reference system to use following rasterio
        command line tool (RIO) formatting (e.g., 'EPSG:3857')

    Returns
    -------
    proc_convert: CompletedProcess
        result of executing subprocess.run using rio convert
    proc_project: CompletedProcess
        result of executing subprocess.run using rio edit-info
    '''
    outdir, basename = os.path.split(infile)
    fname = basename.split('.')[0]
    outfile = os.path.join(outdir, fname+to_fmt)

    # convert the file to the new format
    proc_convert = subprocess.run(['rio', 'convert', infile, outfile],
                                  stderr=subprocess.PIPE,
                                  stdout=subprocess.PIPE)
    # add the projection info
    proc_project = subprocess.run(['rio', 'edit-info', '--crs', crs, outfile],
                                  stderr=subprocess.PIPE,
                                  stdout=subprocess.PIPE)
    return proc_convert, proc_project

def setup_cluster():
    '''Sets up framework for executing parallel jobs using ipyparallel.

    This function imports pyFIRS and other relevant packages to the workers in
    the cluster.

    This assumes a cluster has already been started. You can start a cluster
    from the command line (or using jupyter notebook magics) using:
    `> ipcluster start -n {num_cores}`
    replacing {num_cores} with the number of separate processes you want to have
    running. Alternatively, if you are using `ipyparallel` version >= 4.0 and
    are using a Jupyter Notebook, you should find a tab when you first launch
    jupyter where you can start/stop IPython clusters.

    Returns
    -------
    rc: Client
        ipyparallel Client
    dv: DirectView
        ipyparallel DirectView object
    v: LoadBalancedView
        ipyparallel LoadBalancedVIew object
    '''
    rc = ipp.Client()
    dv = rc[:] # direct view of the workers
    v = rc.load_balanced_view() # load-balanced view of the workers

    # import the relevant packages to all the workers
    with dv.sync_imports():
        import subprocess
        import os
        from pyFIRS.wrappers import lastools
        from pyFIRS.wrappers import fusion
        import rasterio
        from pyFIRS.utils import clip_tile_from_shp, convert_project

    print('Viewing {} workers in the cluster.'.format(len(rc.ids)))
    return rc, dv, v

def validation_summary(xml_dir, verbose=False):
    '''
    Generates a summary of validation results for a directory of lidar files

    Parameters
    ----------
    xml_dir : string, path to directory
        directory containing xml files produced by LASvalidate
    verbose : boolean
        whether or not to include the messages describing why any files
        produced warning or failed validation.

    Returns
    -------
    summary_report : a printed report
    '''
    xmls = glob.glob(os.path.join(xml_dir, '*.xml'))
    passed = 0
    warnings = 0
    failed = 0
    parse_errors = 0
    warning_messages = []
    failed_messages = []

    for validation_report in xmls:
        try:
            tile_id = os.path.basename(validation_report).split('.')[0]
            tree = ET.parse(validation_report)
            root = tree.getroot()
            result = root.find('report').find('summary').text.strip()
            if result == 'pass':
                passed += 1
            else:
                variable = root.find('report').find('details').find(result).find('variable').text
                note = root.find('report').find('details').find(result).find('note').text
                if result == 'fail':
                    failed += 1
                    failed_messages.append('{} -> {} | {} : {}'.format(tile_id, result, variable, note))
                elif result == 'warning':
                    warnings +=1
                    warning_messages.append('{} -> {} | {} : {}'.format(tile_id, result, variable, note))
        except ParseError:
            parse_errors += 1

    summary = '''LASvalidate Summary
====================
Passed: {:,d}
Failed: {:,d}
Warnings: {:,d}
ParseErrors: {:,d}
'''.format(passed, failed, warnings, parse_errors)

    details = '''Details
========
{}
{}
'''.format('\n'.join(failed_messages), '\n'.join(warning_messages))

    print(summary)
    if verbose:
        print(details)


def move_invalid_tiles(xml_dir, dest_dir):
    '''Moves lidar data that fail validation checks into a new directory

    Parameters
    ----------
    xml_dir : string, path to directory
        where the xml reports produced by LASvalidate can be found
    dest_dir : str, path to directory
        where you would like the point cloud and associated files to be moved

    Returns
    -------
    A printed statement about how many tiles were moved.
    '''

    xmls = glob.glob(os.path.join(xml_dir, '*.xml'))
    invalid_dir = dest_dir

    num_invalid = 0

    for validation_report in xmls:
        tile_id = os.path.basename(validation_report).split('.')[0]
        tree = ET.parse(validation_report)
        root = tree.getroot()
        result = root.find('report').find('summary').text.strip()

        if result == 'fail':
            # move the lidar file to a different folder
            os.makedirs(invalid_dir, exist_ok=True)
            for invalid_file in glob.glob(os.path.join(raw, tile_id + '*')):
                basename = os.path.basename(invalid_file)
                os.rename(invalid_file, os.path.join(invalid_dir, basename))

            num_invalid += 1
    print('Moved files for {} invalid tiles to {}'.format(num_invalid, invalid_dir))
