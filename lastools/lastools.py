# LAStools wrappers

class useLAStools(object):
    """A class for executing LAStools functions as methods"""
    os = __import__('os')
    subprocess = __import__('subprocess')

    def __init__(self,src):
        """Initialize with a path to the LAStools executables"""
        self.src = src

    def test_run(self, input):
        print(str(input))

    def run(self, cmd, *args, **kwargs):
        """A helper function to execute a LAStools command using subprocess"""
        args = ['-{}'.format(arg) for arg in args]
        kws = [('-{} '.format(key), value) for (key, value) in kwargs.items()]
        #print(kws)
        cmd = self.os.path.join(self.src, cmd)
        #print([cmd, *args, *kws])
        proc = self.subprocess.run([cmd, *args, *kws],
                            stderr = self.subprocess.PIPE,
                            stdout = self.subprocess.PIPE)
        if proc.returncode != 0:
            # the first two lines of stderr may be boilerplate
            # print the error message from third line and below
            print(proc.stderr.decode())

    def lasview(self, *args, **kwargs):
        """A simple OpenGL-based viewer for LIDAR in LAS/LAZ/ASCII format
        that can also edit or delete points as well as compute/display
        a TIN computed from (a selection of) the points.

        For more details, see:
        http://www.cs.unc.edu/~isenburg/laszip/download/lasview_README.txt
        """
        cmd = 'lasview'
        self.run(cmd, *args, **kwargs)

    def lasinfo(self, *args, **kwargs):
        """Reports the contents of the header and a short summary of the
        points. Warns when there is a difference between the header
        information and the point content.

        For more details, see:
        http://www.cs.unc.edu/~isenburg/laszip/download/lasinfo_README.txt
        """
        cmd = 'lasinfo'
        self.run(cmd, *args, **kwargs)

    def lasground(self, *args, **kwargs):
        """This is a tool for bare-earth extraction: it classifies LIDAR
        points into ground points (class = 2) and non-ground points
        (class = 1). This tools works very well in natural environments
        such as mountains, forests, fields, hills, or other terrain
        with few man-made objects.

        For more details, see:
        http://www.cs.unc.edu/~isenburg/laszip/download/lasground_README.txt
        """
        cmd = 'lasground'
        self.run(cmd, *args, **kwargs)

    def lasclassify(self, *args, **kwargs):
        """This tool classifies buildings and high vegetation (i.e. trees)
        in LAS/LAZ files. This tool requires that the bare-earth points
        have already been identified (e.g. with lasground) and that the
        elevation of each point above the ground was already computed
        with lasheight (which stores this height in the 'user data' field
        of each point).

        For more details, see:
        http://www.cs.unc.edu/~isenburg/laszip/download/lasclassify_README.txt
        """
        cmd = 'lasclassify'
        self.run(cmd, *args, **kwargs)

    def las2dem(self, *args, **kwargs):
        """This tool reads LIDAR points from the LAS/LAZ format (or some
        ASCII format), triangulates them temporarily into a TIN, and
        then rasters the TIN onto a DEM.

        For more details, see:
        http://www.cs.unc.edu/~isenburg/laszip/download/las2dem_README.txt
        """
        cmd = 'las2dem'
        self.run(cmd, *args, **kwargs)

    def las2iso(self, *args, **kwargs):
        """reads LIDAR in LAS/LAZ/ASCII format and extracts isocontours by
        constructing and interpolating a temporary TIN. It is possible
        to triangulate only certain points such as only first returns
        (-first_only) or only last returns (-last_only). One can also
        only triangulate points that have a particular classification.
        For example, the option '-keep_class 2 3' will triangulate only
        the points of classification 2 or 3.

        For more details, see:
        http://www.cs.unc.edu/~isenburg/laszip/download/las2iso_README.txt
        """
        cmd = 'las2iso'
        self.run(cmd, *args, **kwargs)

    def lascolor(self, *args, **kwargs):
        """This tool colors LiDAR points based on imagery that is usually
        an ortho-photo. The tool computes into which pixel a LAS point
        is falling and then sets the RGB values accordingly. Currently
        only the TIF format is supported. The world coordinates need
        to be either in GeoTIFF tags or in an accompanying *.tfw file.

        For more details, see:
        http://www.cs.unc.edu/~isenburg/laszip/download/lascolor_README.txt
        """
        cmd = 'lascolor'
        self.run(cmd, *args, **kwargs)

    def lasgrid(*args, **kwargs):
        """This tool reads LIDAR from LAS/LAZ/ASCII and grids them onto
        a raster. The most important parameter '-step n' specifies the
        n x n area that of LiDAR points that are gridded on one raster
        (or pixel). The output is either in BIL, ASC, IMG, TIF, PNG,
        JPG, XYZ, CSV, or DTM format. The tool can raster '-elevation'
        or '-intensity' of each point and can compute the '-lowest' or
        the '-highest', the '-average', or the standard deviation
        '-stddev', as well as the '-range'.

        For more details, see:
        http://www.cs.unc.edu/~isenburg/laszip/download/lasgrid_README.txt
        """
        cmd = 'lasgrid'
        self.run(cmd, *args, **kwargs)

    def lasoverlap(self, *args, **kwargs):
        """This tool reads LIDAR points from LAS/LAZ/ASCII/BIN/SHP and
        checks the flight line overlap and / or the vertical and
        horizontal alignment.

        For more details, see:
        http://www.cs.unc.edu/~isenburg/laszip/download/lasoverlap_README.txt
        """
        cmd = 'lasoverlap'
        self.run(cmd, *args, **kwargs)

    def lasoverage(self, *args, **kwargs):
        """This tool reads LIDAR point in the LAS/LAZ/ASCII/BIN format
        of an airborne collect and finds the "overage" points that
        get covered by more than a single flightline. It either marks
        these overage points or removes them from the output files.
        The tool requires that the files either have the flightline
        information stored for each point in the point source ID field
        (e.g. for tiles containing overlapping flightlines) or that
        there are multiple files where each corresponds to a flight
        line ('-files_are_flightlines'). It is also required that the
        scan angle field of each point is populated.

        If the point source ID field of a LAS tile is not properly
        populated (but there are GPS time stamps) and each point has
        a scan angle, then you can use the '-recover_flightlines'
        flag that reconstructs the missing flightline information
        from gaps in the GPS time.

        For more details, see:
        http://www.cs.unc.edu/~isenburg/laszip/download/lasoverage_README.txt
        """
        cmd = 'lasoverage'
        self.run(cmd, *args, **kwargs)

    def lasboundary(self, *args, **kwargs):
        """reads LIDAR from LAS/LAZ/ASCII format and computes a boundary
        polygon for the points. By default this is a *concave hull*
        of the points which is - by default - always a single polygon
        where "islands of points" are connected by edges that are
        traversed in each direction once.

        For more details, see:
        http://www.cs.unc.edu/~isenburg/laszip/download/lasboundary_README.txt
        """
        cmd = 'lasboundary'
        self.run(cmd, *args, **kwargs)

    def lasclip(self, *args, **kwargs):
        """takes as input a LAS/LAZ/TXT file and a SHP/TXT file with one
        or many polygons (e.g. building footprints), clips away all the
        points that fall outside all polygons (or inside some polygons),
        and stores the surviving points to the output LAS/LAZ/TXT file.

        For more details, see:
        http://www.cs.unc.edu/~isenburg/laszip/download/lasclip_README.txt
        """
        cmd = 'lasclip'
        self.run(cmd, *args, **kwargs)

    def lasheight(self, *args, **kwargs):
        """This tool computes the height of each LAS point above the
        ground. This assumes that grounds points have already been
        classified (classification == 2) so they can be identified
        and used to construct a ground TIN. The ground points can
        also be in an separate file '-ground_points ground.las' or
        '-ground_points dtm.csv -parse ssxyz'.

        For more details, see:
        http://www.cs.unc.edu/~isenburg/laszip/download/lasheight_README.txt
        """
        cmd = 'lasheight'
        self.run(cmd, *args, **kwargs)

    def lastrack(self, *args, **kwargs):
        """This tool takes one (or many) LAS or LAZ files together with
        a trajectory file that must have matching GPS time stamps. It
        then computes the height of each point above this trajectory
        plus a constant offset. This '-offset -1.93' parameter allows
        to subtract the elevation of the GPS unit above the ground for
        a mobile survey by lowering (or raising) the trajectory to be
        at the level of the road surface.

        Is is important that both - the files with the LiDAR points
        the files with the trajectory points - do not only have the
        same GPS time stamps but are also in the same projection.

        For more details, see:
        http://www.cs.unc.edu/~isenburg/laszip/download/lastrack_README.txt
        """
        cmd = 'lastrack'
        self.run(cmd, *args, **kwargs)

    def lascanopy(*args, **kwargs):
        """This tool reads LiDAR from LAS/LAZ/BIN/SHP/QFIT/ASCII, computes
        popular forestry metrics, and grids them onto a raster. A very
        important parameter is '-step n' that specifies the n x n area
        of LiDAR points that are gridded on one raster (or pixel). The
        default of step is 20. The output can be either in BIL, ASC, IMG,
        TIF, XYZ, FLT, or DTM format. New is raster output in CSV format
        where you can request the '-centroids' to be added. In order to
        shift the raster grid that the points are binned into away from
        the default alignment of (0/0) to (5/15) use '-grid_ll 5 15'.

        For more details, see:
        http://www.cs.unc.edu/~isenburg/laszip/download/lascanopy_README.txt
        """
        cmd = 'lascanopy'
        self.run(cmd, *args, **kwargs)

    def lasthin(self, *args, **kwargs):
        """A fast LIDAR thinning algorithm for LAS/LAZ/ASCII. It places
        a uniform grid over the points and within each grid cell keeps
        only the point with the lowest (or '-highest' or '-random') Z
        coordinate. When keeping '-random' points you can in addition
        specify a '-seed 232' for the random generator. You can also
        keep the point that is closest to the center of each cell with
        the option '-central'.

        For more details, see:
        http://www.cs.unc.edu/~isenburg/laszip/download/lasthin_README.txt
        """
        cmd = 'lasthin'
        self.run(cmd, *args, **kwargs)

    def lassort(self, *args, **kwargs):
        """sorts the points of a LAS file into z-order arranged cells of
        a square quad tree and saves them into LAS or LAZ format. This
        is useful to bucket together returns from different swaths or
        to merge first and last returns that were stored in separate
        files.

        For more details, see:
        http://www.cs.unc.edu/~isenburg/laszip/download/lassort_README.txt
        """
        cmd = 'lassort'
        self.run(cmd, *args, **kwargs)

    def lasduplicate(*args, **kwargs):
        """Removes all duplicate points from a LAS/LAZ/ASCII file. In the
        default mode those are xy-duplicate points that have identical
        x and y coordinates. The first point survives, all subsequent
        duplicates are removed. It is also possible to keep the lowest
        points amongst all xy-duplicates via '-lowest_z'.

        For more details, see:
        http://www.cs.unc.edu/~isenburg/laszip/download/lassort_README.txt
        """
        cmd = 'lasduplicate'
        self.run(cmd, *args, **kwargs)

    def lascontrol(self, *args, **kwargs):
        """This tool computes the height of the LIDAR at certain x and y
        control points locations and reports the height difference in
        respect to the control points' elevation.

        The tool reads LIDAR in LAS/LAZ/ASCII format, triangulates the
        relevant points into a TIN. For classified data sets containing
        a mix of ground and vegetation/building points it is imperative
        to specified the points against which the reference measurements
        are to be taken (i.e. usually '-keep_class 2').

        The tool collects for each ground control point all LiDAR points
        that fall into a 3 by 3 grid of cells surrounding the control
        point. By default the size of each of the nine grid cells is 5
        meter by 5 meter so that the total patch surrounding the control
        point that needs to be covered by LiDAR for that control point
        to get evaluated is 15 meter by 15 meter. This can be changed
        with the '-step 2' parameter which would shrink each of the nine
        cells to 2 meter by 2 meter.

        For more details, see:
        http://www.cs.unc.edu/~isenburg/laszip/download/lascontrol_README.txt
        """
        cmd = 'lascontrol'
        self.run(cmd, *args, **kwargs)

    def lastile(self, *args, **kwargs):
        """tiles a potentially very large amount of LAS points from one
        or many files into square non-overlapping tiles of a specified
        size and save them into LAS or LAZ format.

        For more details, see:
        http://www.cs.unc.edu/~isenburg/laszip/download/lastile_README.txt
        """
        cmd = 'lastile'
        self.run(cmd, *args, **kwargs)

    def lassplit(self, *args, **kwargs):
        """splits the input file(s) into several output files based on
        various parameters. By default lassplit split a combined LAS
        file into its original, individual flight lines by splitting
        based on the point source ID of the points.

        For more details, see:
        http://www.cs.unc.edu/~isenburg/laszip/download/lassplit_README.txt
        """
        cmd = 'lassplit'
        self.run(cmd, *args, **kwargs)

    def txt2las(self, *args, **kwargs):
        """Converts LIDAR data from a standard ASCII format into the more
        efficient binary LAS/LAZ/BIN representations. You can request
        a particular point type with '-set_point_type 6'.

        Reads also directy from *.gz, *.zip, *.rar, and *.7z files if
        the corresponding gzip.exe, unzip.exe, unrar.exe, and 7z.exe
        are in the same folder.

        Allows adding a VLR to the header with projection information.

        If your input text file is PTS or PTX format you can preserve
        the extra header information of these files. Simply add the
        appropriate '-ipts' or '-iptx' switch to the command line which
        will store this in a VLR. You can later reconstruct the PTS or
        PTX files with 'las2las' or 'las2txt' by adding the corresponding
        '-opts' or '-optx' option to the command line.

        Also allows adding additional attributes to LAS/LAZ files using
        the "Extra Bytes" concept with '-add_attribute'.

        For more details, see:
        http://www.cs.unc.edu/~isenburg/laszip/download/txt2las_README.txt
        """
        cmd = 'txt2las'
        self.run(cmd, *args, **kwargs)
