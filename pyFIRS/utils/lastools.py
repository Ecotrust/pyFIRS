import os
import subprocess
import platform
from .formatters import listlike, format_lastools_kws

# Pythonic wrappers for LAStools command line tools
def get_bounds(lasinfo):
    '''Parses the minimum and maximum X, Y, and Z values from LASinfo output.

    This is a helper function used by the pitfree function.

    Parameters
    ----------
    lasinfo: string
        result produced by executing the lasinfo command line tool on a lidar
        data file

    Returns
    -------
    bounds: tuple
        a 6-tuple containing (xmin, ymin, zmin, xmax, ymax, zmax)
    '''
    min_start = lasinfo.index('min x y z:')
    min_stop = lasinfo.index('\r\n', min_start)
    min_line = lasinfo[min_start: min_stop]
    min_vals = min_line.split(':')[1].strip().split(' ')
    mins = (float(min_vals[0]), float(min_vals[1]), float(min_vals[2]))

    max_start = lasinfo.index('max x y z:', min_stop)
    max_stop = lasinfo.index('\r\n', max_start)
    max_line = lasinfo[max_start: max_stop]
    max_vals = max_line.split(':')[1].strip().split(' ')
    maxs = (float(max_vals[0]), float(max_vals[1]), float(max_vals[2]))
    return mins + maxs

class useLAStools(object):
    "A class for executing LAStools functions as methods"

    def __init__(self,src='C:/lastools/bin'):
        "Initialize with a path to the LAStools executables"
        self.src = src
        self.system = platform.system()

    def test_run(self, input):
        print(str(input))

    def run(self, cmd, **kwargs):
        """Executes a LAStools command line tool.

        Formats kwargs provided in Pythonic format into the format expected
        by LAStools command line tools and executes the command line tool using
        the subprocess module.

        Parameters
        ----------
        cmd: string
            name of LAStools commandline tool

        Returns
        -------
        CompletedProcess, a class from the subprocess module that includes
        attributes such as args, stdout, stderr, and returncode.
        """
        kws = [('-{} '.format(key), format_lastools_kws(value)) for (key, value) in kwargs.items()]

        # check to see if echo has been requested
        if ('-echo ','') in kws:
            echo = True
            kws.remove(('-echo ', ''))
        else:
            echo = False

        cmd = os.path.join(self.src, cmd)

        if self.system == 'Linux':
            # if we're on a linux system, execute the commands using WINE
            # (this requires WINE to be installed)
            proc = subprocess.run(['wine', cmd, *kws],
                                       stderr = subprocess.PIPE,
                                       stdout = subprocess.PIPE)
        else:
            proc = subprocess.run([cmd, *kws],
                                       stderr = subprocess.PIPE,
                                       stdout = subprocess.PIPE)
        if echo:
            print(proc.stdout.decode())
            print(proc.stderr.decode())

        return proc

    def pitfree(self, lasfile, resolution=0.33333, splat_radius=0.1,
                max_TIN_edge=1.0, cleanup=True):
        '''Creates a pit-free Canopy Height Model from a lidar point cloud.

        This function chains together several LAStools command line tools to
        produce a pit-free Canopy Height Model (CHM) from a raw lidar point
        cloud. A working subdirectory is created in the same folder where the
        input lidar data file is located to hold intermediate files from the
        process, which will be deleted (by default) upon completion of the CHM.
        A GeoTiff of the CHM is output to the same folder as the inputfile named
        {inputfile}_chm_pitfree.tif

        This method was first described by:

            Khosravipour, A. et al. (2014) "Generating Pit-free Canopy Height
            Models from Airborne Lidar."" Photogrammetric Engineering & Remote
            Sensing 80(9): 863–872.

        The method was elaborated by co-author/LAStools developer Martin
        Isenburg in a blog post, "Rasterizing Perfect Canopy Height Models from
        LiDAR". The default values used here are drawn from this blog post:
        https://rapidlasso.com/2014/11/04/rasterizing-perfect-canopy-height-models-from-lidar/

        Parameters
        ----------
        lasfile: string, path to file (required)
            Lidar point cloud input file to process.
        resolution: numeric (optional)
            Size of grid cells for Canopy Height Model, in same units as lidar
            data. Used in the `step` argument of las2dem. Default is 0.33333.
        splat_radius: numeric (optional)
            Distance by which lidar points will be replicated in each of eight
            directions, which used in the `subcircle` argument of lasthin.
            Default is 0.1.
        max_TIN_edge: numeric (optional)
            Maximum length of edges for points to remain connected in TIN
            created by las2dem. Used in the `kill` argument of las2dem. Default
            is 1.0.
        cleanup: boolean (optional)
            Whether or not to remove the temporary working directory and
            intermediate files produced. Defaults to True.
        '''
        path_to_file = os.path.abspath(lasfile)
        path, file = os.path.split(path_to_file)
        basename = file.split('.')[0]

        # make a temporary working directory
        tmpdir = os.path.join(path, 'tmp_{}'.format(basename))
        os.mkdir(tmpdir)

        # run lasheight to normalize point cloud
        suffix = '_normalized'
        outfile = os.path.join(tmpdir, basename + suffix + '.laz')
        self.lasheight(i=path_to_las, o=outfile, replace_z=True)

        # get the minimum and maximum normalized heights
        # we'll use these later for creating layered canopy height models
        proc = self.lasinfo(i=outfile)
        lasinfo = proc.stderr.decode()
        _, _, zmin, _, _, zmax = get_bounds(lasinfo)

        # create DEM of ground for minimum value of pitfree CHM
        infile = os.path.join(tmpdir, basename + suffix + '.laz') # *_height.laz
        suffix = '_chm_ground'
        outfile = os.path.join(tmpdir, basename + suffix + '.bil')
        self.las2dem(i=infile, o=outfile, drop_z_above=0.1,
                    step=resolution) # resolution of ground model

        # "splat" and thin the lidar point cloud to get highest points using a
        # finer resolution than our final CHM will be
        suffix = '_temp'
        outfile = os.path.join(tmpdir, basename + suffix + '.laz')
        self.lasthin(i=infile, o=outfile, highest=True,
                    subcircle=splat_radius,
                    step=resolution/2.0)

        # generate CHM layers above ground, above 2m, and then in 5m increments
        # up to zmax... las2dem first makes a TIN and then rasterizes to grid
        hts = [0,2] + [x for x in range(5,int(zmax),5)]
        infile = os.path.join(tmpdir, basename + suffix + '.laz')
        # loop through the layers
        for ht in hts:
            suffix = '_chm{0:03d}'.format(ht)
            outfile = os.path.join(tmpdir, basename + suffix + '.bil')
            self.las2dem(i=infile, o=outfile,
                        drop_z_below=ht, # specify layer height from ground
                        kill=max_TIN_edge, # trim edges in TIN > max_TIN_edge
                        step=resolution) # resolution of layer DEM

        # merge the CHM layers into a GeoTiff
        infiles = os.path.join(tmpdir,'*.bil')
        suffix = '_chm_pitfree'
        outfile = os.path.join(path, basename + suffix + '.tif')
        self.lasgrid(i=infiles, merged=True, o=outfile, highest=True,
                    step=resolution) # resolution of pit-free CHM

        if cleanup:
            shutil.rmtree(tmpdir)

    def lasview(self, **kwargs):
        "http://www.cs.unc.edu/~isenburg/laszip/download/lasview_README.txt"
        cmd = 'lasview'
        return self.run(cmd, **kwargs)

    def lasinfo(self, **kwargs):
        "http://www.cs.unc.edu/~isenburg/laszip/download/lasinfo_README.txt"
        cmd = 'lasinfo'
        return self.run(cmd, **kwargs)

    def lasground(self, **kwargs):
        "http://www.cs.unc.edu/~isenburg/laszip/download/lasground_README.txt"
        cmd = 'lasground'
        return self.run(cmd, **kwargs)

    def lasclassify(self, **kwargs):
        "http://www.cs.unc.edu/~isenburg/laszip/download/lasclassify_README.txt"
        cmd = 'lasclassify'
        return self.run(cmd, **kwargs)

    def las2dem(self, **kwargs):
        "http://www.cs.unc.edu/~isenburg/laszip/download/las2dem_README.txt"
        cmd = 'las2dem'
        return self.run(cmd, **kwargs)

    def las2iso(self, **kwargs):
        "http://www.cs.unc.edu/~isenburg/laszip/download/las2iso_README.txt"
        cmd = 'las2iso'
        return self.run(cmd, **kwargs)

    def lascolor(self, **kwargs):
        "http://www.cs.unc.edu/~isenburg/laszip/download/lascolor_README.txt"
        cmd = 'lascolor'
        return self.run(cmd, **kwargs)

    def lasgrid(self, **kwargs):
        "http://www.cs.unc.edu/~isenburg/laszip/download/lasgrid_README.txt"
        cmd = 'lasgrid'
        return self.run(cmd, **kwargs)

    def lasoverlap(self, **kwargs):
        "http://www.cs.unc.edu/~isenburg/laszip/download/lasoverlap_README.txt"
        cmd = 'lasoverlap'
        return self.run(cmd, **kwargs)

    def lasoverage(self, **kwargs):
        "http://www.cs.unc.edu/~isenburg/laszip/download/lasoverage_README.txt"
        cmd = 'lasoverage'
        return self.run(cmd, **kwargs)

    def lasboundary(self, **kwargs):
        "http://www.cs.unc.edu/~isenburg/laszip/download/lasboundary_README.txt"
        cmd = 'lasboundary'
        return self.run(cmd, **kwargs)

    def lasclip(self, **kwargs):
        "http://www.cs.unc.edu/~isenburg/laszip/download/lasclip_README.txt"
        cmd = 'lasclip'
        return self.run(cmd, **kwargs)

    def lasheight(self, **kwargs):
        "http://www.cs.unc.edu/~isenburg/laszip/download/lasheight_README.txt"
        cmd = 'lasheight'
        return self.run(cmd, **kwargs)

    def lastrack(self, **kwargs):
        "http://www.cs.unc.edu/~isenburg/laszip/download/lastrack_README.txt"
        cmd = 'lastrack'
        return self.run(cmd, **kwargs)

    def lascanopy(self, **kwargs):
        "http://www.cs.unc.edu/~isenburg/laszip/download/lascanopy_README.txt"
        cmd = 'lascanopy'
        return self.run(cmd, **kwargs)

    def lasthin(self, **kwargs):
        "http://www.cs.unc.edu/~isenburg/laszip/download/lasthin_README.txt"
        cmd = 'lasthin'
        return self.run(cmd, **kwargs)

    def lassort(self, **kwargs):
        "http://www.cs.unc.edu/~isenburg/laszip/download/lassort_README.txt"
        cmd = 'lassort'
        return self.run(cmd, **kwargs)

    def lasduplicate(self, **kwargs):
        "http://www.cs.unc.edu/~isenburg/laszip/download/lassort_README.txt"
        cmd = 'lasduplicate'
        return self.run(cmd, **kwargs)

    def lascontrol(self, **kwargs):
        "http://www.cs.unc.edu/~isenburg/laszip/download/lascontrol_README.txt"
        cmd = 'lascontrol'
        return self.run(cmd, **kwargs)

    def lastile(self, **kwargs):
        "http://www.cs.unc.edu/~isenburg/laszip/download/lastile_README.txt"
        cmd = 'lastile'
        return self.run(cmd, **kwargs)

    def lassplit(self, **kwargs):
        "http://www.cs.unc.edu/~isenburg/laszip/download/lassplit_README.txt"
        cmd = 'lassplit'
        return self.run(cmd, **kwargs)

    def txt2las(self, **kwargs):
        "http://www.cs.unc.edu/~isenburg/laszip/download/txt2las_README.txt"
        cmd = 'txt2las'
        return self.run(cmd, **kwargs)

    def blast2dem(self, **kwargs):
        "http://www.cs.unc.edu/~isenburg/laszip/download/blast2dem_README.txt"
        cmd = 'blast2dem'
        return self.run(cmd, **kwargs)

    def blast2iso(self, **kwargs):
        "http://www.cs.unc.edu/~isenburg/laszip/download/blast2iso_README.txt"
        cmd = 'blast2iso'
        return self.run(cmd, **kwargs)

    def las2las(self, **kwargs):
        "http://www.cs.unc.edu/~isenburg/laszip/download/las2las_README.txt"
        cmd = 'las2las'
        return self.run(cmd, **kwargs)

    def las2shp(self, **kwargs):
        "http://www.cs.unc.edu/~isenburg/laszip/download/las2shp_README.txt"
        cmd = 'las2shp'
        return self.run(cmd, **kwargs)

    def las2tin(self, **kwargs):
        "http://www.cs.unc.edu/~isenburg/laszip/download/las2tin_README.txt"
        cmd = 'las2shp'
        return self.run(cmd, **kwargs)

    def lasvoxel(self, **kwargs):
        "http://www.cs.unc.edu/~isenburg/laszip/download/lasvoxel_README.txt"
        cmd = 'lasvoxel'
        return self.run(cmd, **kwargs)

    def lasreturn(self, **kwargs):
        "http://www.cs.unc.edu/~isenburg/laszip/download/lasreturn_README.txt"
        cmd = 'lasreturn'
        return self.run(cmd, **kwargs)

    def laszip(self, **kwargs):
        "http://www.cs.unc.edu/~isenburg/laszip/download/laszip_README.txt"
        cmd = 'laszip'
        return self.run(cmd, **kwargs)

    def lasindex(self, **kwargs):
        "http://www.cs.unc.edu/~isenburg/laszip/download/lasindex_README.txt"
        cmd = 'lasindex'
        return self.run(cmd, **kwargs)
