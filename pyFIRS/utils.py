import os
import subprocess
import glob
import json
import xml.etree.ElementTree as ET
from xml.etree.ElementTree import ParseError

import geopandas as gpd
import rasterio
import numpy as np
from shapely.geometry import Polygon


class PipelineError(RuntimeError):
    def __init__(self, message):
        self.message = message


def listlike(arg):
    '''Checks whether an argument is list-like, returns boolean'''
    return not hasattr(arg, "strip") and (hasattr(arg, "__getitem__")
                                          or hasattr(arg, "__iter__"))


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
            print("Removed {:,d} files with extension {}.".format(
                len(to_rem), ext))
    elif type(file_extension) == str:
        to_rem = glob.glob(os.path.join(dir_to_clean, '*{}'.format(ext)))
        for file in to_rem:
            os.remove(file)
        print("Removed {:,d} files with extension {}.".format(
            len(to_rem), ext))
    else:
        raise (TypeError,
               'file_extensions needs to be a string or list-like of strings.')


def clean_buffer_polys(poly_shp,
                       tile_shp,
                       odir,
                       simp_tol=None,
                       simp_topol=None):
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


def clip_tile_from_shp(in_raster, in_shp, odir, buffer=0):
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
    buffer: numeric
        additional buffer to add to total bounding box of shapefile when
        clipping the raster

    Returns
    -------
    proc_clip: CompletedProcess
        The result of executing subprocess.run using the rio clip command.
    '''
    basename = os.path.basename(in_raster)
    # read the shapefile using geopandas and calculate its bounds
    gdf = gpd.read_file(in_shp)
    tile_bnds = ' '.join(str(x) for x in gdf.buffer(buffer).total_bounds)

    # create the output directory if it doesn't already exist
    os.makedirs(odir, exist_ok=True)
    outfile = os.path.join(odir, basename)
    # clip the raster
    proc_clip = subprocess.run(
        ['rio', 'clip', in_raster, outfile, '--bounds', tile_bnds],
        stderr=subprocess.PIPE,
        stdout=subprocess.PIPE)
    return proc_clip


def convert_project(infile, outfile, crs):
    '''Converts a raster to another format and specifies its projection.

    Uses rasterio command line tool executed using subprocess. The file
    generated will have the same name and be in the same folder as the input
    file.

    Parameters
    ----------
    infile: string, path to file
        input raster to be converted
    outfile: string, path to file
        output raster to be generated
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
    # convert the file to the new format
    proc_convert = subprocess.run(['rio', 'convert', infile, outfile],
                                  stderr=subprocess.PIPE,
                                  stdout=subprocess.PIPE)
    # add the projection info
    proc_project = subprocess.run(['rio', 'edit-info', '--crs', crs, outfile],
                                  stderr=subprocess.PIPE,
                                  stdout=subprocess.PIPE)
    return proc_convert, proc_project


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
                variable = root.find('report').find('details').find(
                    result).find('variable').text
                note = root.find('report').find('details').find(result).find(
                    'note').text
                if result == 'fail':
                    failed += 1
                    failed_messages.append('{} -> {} | {} : {}'.format(
                        tile_id, result, variable, note))
                elif result == 'warning':
                    warnings += 1
                    warning_messages.append('{} -> {} | {} : {}'.format(
                        tile_id, result, variable, note))
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
            for invalid_file in glob.glob(
                    os.path.join(xml_dir, tile_id + '*')):
                basename = os.path.basename(invalid_file)
                os.rename(invalid_file, os.path.join(invalid_dir, basename))

            num_invalid += 1
    print('Moved files for {} invalid tiles to {}'.format(
        num_invalid, invalid_dir))


def get_bbox_as_poly(infile, epsg=None):
    """Uses PDAL's info tool to extract the bounding box of a file as a
    shapely Polygon. If an EPSG code is provided, a GeoDataFrame is returned.

    Parameters
    ----------
    infile : str, path to file
        path to input file that PDAL can read
    epsg : int
        EPSG code defining the coordinate reference system. Optional.

    Returns
    -------
    bbox_poly : Polygon or GeoDataFrame
        By default (no EPSG is provided), a shapely Polygon with the bounding
        box as its coordinates is returned. If an EPSG code is specified,
        bbox_poly is returned as a GeoPandas GeoDataFrame.

    """
    result = subprocess.run(['pdal', 'info', infile],
                             stderr = subprocess.PIPE,
                             stdout = subprocess.PIPE)

    json_result = json.loads(result.stdout.decode())

    coords = json_result['stats']['bbox']['native']['boundary']['coordinates']
    geometry = Polygon(*coords)

    if epsg:
        bbox_poly = gpd.GeoDataFrame(geometry=[geometry],
                                     crs={'init': 'epsg:{}'.format(epsg)})
    else:
        bbox_poly = Polygon(*coords)

    return bbox_poly


def fname(path):
    """returns the filename as basename split from extension.

    Parameters
    -----------
    path : str, path to file
        filepath from which filename will be sliced


    Returns
    --------
    filename : str
        name of file, split from extension
    """
    filename = os.path.basename(path).split('.')[0]
    return filename


def annulus(inner_radius, outer_radius, dtype=np.uint8):
    """Generates a flat, donut-shaped (annular) structuring element.

    A pixel is within the neighborhood if the euclidean distance between
    it and the origin falls between the inner and outer radii (inclusive).

    Parameters
    ----------
    inner_radius : int
        The inner radius of the annular structuring element
    outer_radius : int
        The outer radius of the annular structuring element
    dtype : data-type
        The data type of the structuring element

    Returns
    -------
    selem : ndarray
        The structuring element where elements of the neighborhood are 1
        and 0 otherwise
    """
    L = np.arange(-outer_radius, outer_radius + 1)
    X, Y = np.meshgrid(L, L)
    selem = np.array(((X ** 2 + Y ** 2) <= outer_radius ** 2) *
                     ((X ** 2 + Y ** 2) >= inner_radius ** 2),
                    dtype=dtype)
    return selem


def inspect_failures(failed_dir):
    """Prints error messages reported for tiles that failed in the lidar
    processing pipeline.

    Parameters
    ----------
    failed_dir : string, path to directory
         path to directory containing text files indicating any tiles which
         failed processing
    """
    failed = glob.glob(os.path.join(failed_dir, '*.txt'))

    for filename in failed:
        with open(filename) as f:
            print([line for line in f.readlines() if line.rstrip() != ''])
        print('----------------------')


def processing_summary(all_tiles, already_finished, processing_tiles, finished_dir, failed_dir):
    """Prints a summary indicating progress of a lidar processing pipeline.

    Parameters
    ----------
    all_tiles : list-like
        all tiles within a lidar acquisition
    already_finished : list-like
        tiles which were successfully processed in a previous execution of the
        processing pipeline
    processing_tiles : list-like
        tiles which are being processed during the currently executing pipeline
    finished_dir : string, path to directory
        path to directory containing text files indicating any tiles which have
        finished processing
    failed_dir : string, path to directory
        path to directory containing text files indicating any tiles which
        failed processing
    """

    failed = glob.glob(os.path.join(failed_dir, '*.txt'))
    finished = glob.glob(os.path.join(finished_dir, '*.txt'))

    summary = '''
    Processing Summary
    -------------------
    {:>5,d} tiles in acquisition
    {:>5,d} tiles previously finished in acquisition

    {:>5,d} tiles being processed in this run
    {:>5,d} tiles from this run finished

    {:>5,d} tiles failed
    '''.format(len(all_tiles),
               len(already_finished),
               len(processing_tiles),
               len(finished) - (len(all_tiles) - len(processing_tiles)),
               len(failed))

    total_percent_unfinished = int(70 * (1-len(finished)/len(all_tiles)))
    total_percent_finished = int(70 * len(finished)/len(all_tiles))
    total_percent_failed = int(70 * len(failed)/len(all_tiles))

    this_run_unfinished = int(70 - 70*(len(finished) - (len(all_tiles) - \
    len(processing_tiles))) / len(processing_tiles))
    this_run_finished = int(70*(len(finished) - (len(all_tiles) - \
    len(processing_tiles))) / len(processing_tiles))

    progress_bars = '|' + '=' * this_run_finished + ' '* this_run_unfinished +\
     '!' * total_percent_failed + '|  {:.1%} this run\n'.format((len(finished)\
      - (len(all_tiles) - len(processing_tiles))) / len(processing_tiles)) + \
    '|' + '=' * total_percent_finished + ' ' * total_percent_unfinished + '!' \
    * total_percent_failed + '|  {:.1%} total'.format(len(finished) / \
    len(all_tiles))

    print(summary)
    print(progress_bars)
