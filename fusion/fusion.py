# Wrappers for subprocess calls for FUSION command line tools
import warnings

# helpder functions for formatting command line arguments
def listlike(arg):
    '''Checks whether an argument is list-like, returns boolean'''
    return (not hasattr(arg, "strip") and hasattr(arg, "__getitem__") or
            hasattr(arg, "__iter__"))

def format_kws(arg):
    '''Formats keyword arguments for FUSION command line usage'''
     if isinstance(arg, bool):
         return ''
     elif listlike(arg):
         return ':'+",".join(str(x) for x in arg)
     else:
         return ':' + str(arg)

def format_args(arg):
    '''Formats positional arguments for FUSION command line usage'''
     if listlike(arg):
         return " ".join(str(x) for x in arg)
     else:
         str(arg)

# wrappers for FUSION command line tools
class useFUSION(object):
    "A class for executing FUSION functions as methods"
    os = __import__('os')
    subprocess = __import__('subprocess')

    def __init__(self,src):  "Initialize with a path to the FUSION executables"
        self.src = src

    def run(self, cmd, **kwargs, *params):
        "Formats and executes a FUSION command line call using subprocess"
        # prepend the path to FUSION tools to the user-specified command
        cmd = self.os.path.join(self.src, cmd)
        # format kwargs as FUSION 'switches'
        switches = ['/{}{}'.format(key, format_kws(value)) for (key, value)
                    in kwargs.items() if value]
        # format the required parameters for each function as strings
        params = [format_args(param) for param in params]

        # execute the command using subprocess, capturing stderr and stdout
        # output can be silenced using the 'quiet' arg in a FUSION command
        proc = self.subprocess.run([cmd, *switches, *params],
                                   stderr = self.subprocess.PIPE,
                                   stdout = self.subprocess.PIPE)
        print(proc.stdout.decode())
        print(proc.stderr.decode())

    def ascii2dtm(self, surfacefile, xyunits, zunits, coordsys, zone,
                  horizdatum, vertdatum, gridfile, **kwargs):
        """Converts raster data stored in ESRI ASCII raster format into a PLANS
        format data file.

        Data in the input ASCII raster file can represent a surface or raster
        data. ASCII2DTM converts areas containing NODATA values into areas with
        negative elevation values in the output data file.

        Parameters (required)
        ----------
        surfacefile: string
            Name for output canopy surface file (stored in PLANS DTM format
            with .dtm extension).
        xyunits: string
            Units for LIDAR data XY
                'M' for meters
                'F' for feet.
        zunits: string
            Units for LIDAR data elevations:
                'M' for meters
                'F' for feet
        coordsys: int
            Coordinate system for the canopy model:
                0 for unknown
                1 for UTM
                2 for state plane
        zone: int
            Coordinate system zone for the canopy model (0 for unknown).
        horizdatum: int
            Horizontal datum for the canopy model:
                0 for unknown
                1 for NAD27
                2 for NAD83
        vertdatum: int
            Vertical datum for the canopy model:
                0 for unknown
                1 for NGVD29
                2 for NAVD88
                3 for GRS80
        Gridfile: string
            Name of the ESRI ASCII raster file containing surface data.

        **Kwargs (optional)
        ------
        multiplier: numeric
            Multiply all data values in the input surface by the constant.
        offset: numeric
            Add the constant to all data values in the input surface. The
            constant can be negative.
        nan: boolean
            Use more robust (but slower) logic when reading values from the
            input file to correctly parse NAN values (not a number).
        ------
        additional boolean kwargs available for most FUSION commands include:
        quiet, verbose, newlog, version, locale, nolazsipdll
        ------
        """
        cmd = 'ascii2dtm'
        params = [surfacefile, xyunits, zunits, coordsys, zone, horizdatum,
                  vertdatum, gridfile]
        self.run(cmd, **kwargs, *params)


    def asciiimport(self, ParamFile, InputFile, OutputFile=None, **kwargs):
        """ASCIIImport allows you to use the configuration files that describe
        the format of ASCII data files to convert data into FUSION’s LDA format.
        The configuration files are created using FUSION’s Tools... Data
        conversion... Import generic ASCII LIDAR data... menu option. This
        option allows you to interactively develop the format specifications
        needed to convert and ASCII data file into LDA format.

        Parameters
        ----------
        ParamFile: string, path to file (required)
            Name of the format definition parameter file (created in FUSION's
            Tools... Data conversion... Import generic ASCII LIDAR data... menu
            option.
        InputFile: string, path to file (required)
            Name of the ASCII input file containing LIDAR data.
        OutputFile: string, path to file (optional)
            Name for the output LDA or LAS file (extension will be provided
            depending on the format produced). If OutputFile is omitted, the
            output file is named using the name of the input file and the
            extension appropriate for the format (.lda for LDA, .las for LAS).

        **Kwargs (optional), aka "Switches" in FUSION
        --------
        LAS: boolean
            Output file is stored in LAS version 1.0 format.
        -------
        additional boolean kwargs available for most FUSION commands include:
        quiet, verbose, newlog, version, locale, nolazsipdll

        Progress information for the conversion is displayed when the /verbose
        switch is used.
        -------
        """
        cmd = 'asciiimport'
        params = [ParamFile, InputFile, OutputFile]
        self.run(cmd, **kwargs, *params)

    def canopymaxima(self, inputfile outputfile, **kwargs):
        """Uses a canopy height model to identify local maxima using a
        variable-size evaluation window.

        The window size is based on the canopy height. For some forest types,
        this tool can identify individual trees. However, it does not work in
        all forest types and it can only identify dominant and codominant trees
        in the upper canopy. The local maxima algorithm in CanopyMaxima is
        similar to that reported in Popescu et al. (2002) and Popescu and Wynn
        (2004) and implemented in the TreeVAW software (Kini and Popescu, 2004).

        Parameters (required)
        ----------
        inputfile: string, path to file
            Name for the input canopy height model file.
        outputfile: string, path to file
            Name for the output CSV file containing the maxima.

        **Kwargs (optional), aka "Switches" in FUSION
        --------
        ground: string, path to file
            Use the specified surface model(s) to represent the ground surface.
            File may be wildcard or text list file (extension .txt).
        threshold: numeric
            Limit analysis to areas above a height of # units (default: 10.0).
        wse: 4- or 6-tuple or list-like (A,B,C,D) or (A,B,C,D,E,F)
            Constant and coefficients for the variable window size equation used
            to compute the window size given the canopy surface height window:
            width = A + B*ht + C*ht^2 + D*ht^3 + E*ht^4 + F*ht^5
            Defaults values are for metric units:
            A = 2.51503, B = 0, C = 0.00901, D = 0, E = 0, F = 0.
            Use A = 8.251, B = 0, C = 0.00274, D = E = F = 0 when using
            imperial units.
        mult: numeric
            Window size multiplier (default: 1.0).
        res: numeric
            Resolution multiplier for intermediate grids (default: 2.0). A value
            of 2 results in intermediate grids with twice the number of rows and
            columns
        outxy: 4-tuple or list-like (minx,miny,maxx,maxy)
            Restrict output of tree located outside of the extent defined by
            (minx,miny) and (maxx,maxy). Tree on the left and bottom edges will
            be output, those on the top and right edges will not.
        crad: boolean
            Output 16 individual crown radii for each tree. Radii start at 3
            o'clock and are in counter-clockwise order at 22.5 degree intervals.
        shape: boolean
            Create shapefile outputs for the canopy maxima points and the
            perimeter of the area associated with each maxima.
        img8: boolean
            Create an 8-bit image showing local maxima and minima (use when 24
            bit image fails due to large canopy model).
        img24: boolean
            Create an 24-bit image showing local maxima and minima.
        new: boolean
            Create a new output file (erase output file if one exists).
        summary: boolean
            Produce a summary file containing tree height summary statistics.
        projection: string, path to file
            Associate the specified projection file with shapefile and raster
            data products.
        -------
        additional boolean kwargs available for most FUSION commands include:
        quiet, verbose, newlog, version, locale, nolazsipdll
        -------
        """
        cmd = 'canopymaxima'
        params = [inputfile outputfile]
        self.run(cmd, **kwargs, *params)

    def canopymodel(self, surfacefile, cellsize, xyunits, zunits, coordsys,
                    zone, horizdatum, vertdatum, datafiles, **kwargs):
        """Creates a canopy surface model using a LIDAR point cloud.

        By default, the algorithm used by CanopyModel assigns the elevation of
        the highest return within each grid cell to the grid cell center.
        CanopyModel provides for smoothing of the generated surface using a
        median or a mean filter or both. Specialized logic, activated using the
        /peaks switch, preserves local maxima in the surface while smoothing to
        force the surface to adhere to the tops of trees. CanopyModel provides
        options to compute a texture metric (coefficient of variation of surface
        values within an n by n window), slope, or aspect for the canopy model
        and output them as the final surface. When used with a bare-earth model,
        CanopyModel subtracts the ground elevations from the return elevations
        to produce a canopy height model. Output from CanopyModel is a PLANS
        format DTM file that uses floating point elevation values and contains
        coordinate projection information.

        Parameters (required)
        ----------
        surfacefile: string
            Name for output canopy surface file (stored in PLANS DTM format
            with .dtm extension).
        xyunits: string
            Units for LIDAR data XY:
                'M' for meters
                'F' for feet.
        zunits: string
            Units for LIDAR data elevations:
                'M' for meters
                'F' for feet
        coordsys: int
            Coordinate system for the canopy model:
                0 for unknown
                1 for UTM
                2 for state plane
        zone: int
            Coordinate system zone for the canopy model (0 for unknown).
        horizdatum: int
            Horizontal datum for the canopy model:
                0 for unknown
                1 for NAD27
                2 for NAD83
        vertdatum: int
            Vertical datum for the canopy model:
                0 for unknown
                1 for NGVD29
                2 for NAVD88
                3 for GRS80
        datafiles: string or list-like of strings of paths to file(s)
            LIDAR data file (LDA, LAS, ASCII LIDARDAT formats)...may be wildcard
            or name of text file listing the data files. If wildcard or text
            file is used, no other datafiles will be recognized.

        **Kwargs (optional)
        --------
        median: int
            Apply median filter to model using # by # neighbor window.
        mean: int
            Apply mean filter to model using # by # neighbor window.
        texture: int
            Calculate the surface texture metric using # by # neighbor window.
        slope: boolean
            Calculate surface slope for the final surface.
        aspect: boolean
            Calculate surface aspect for the final surface.
        outlier: 2-tuple or list-like -- (low, high)
            Omit points with elevations below low and above high if used with a
            bare-earth surface this option will omit points with heights below
            low or above high.
        multiplier: numeric
            Multiply the output values by the constant (#).
        return: string or int
            Specifies the returns to be included in the sample (can include
            A,1,2,3,4,5,6,7,8,9,F,L,O) Options are specified without commas
            (e.g. return=123) For LAS files only: F indicates first and only
            returns, L indicates last of many returns.
        class: string or list-like
            Used with LAS format files only. Specifies that only points with
            classification values listed are to be used when creating the canopy
            surface. If defined as a string, classification values should be
            separated by a comma e.g. (2,3,4,5) and can range from 0 to 31.
            If the first character of string is “~”, all classes except those
            listed will be used.
        ground: string or path to file
            Use the specified bare-earth surface model(s) to normalize the LIDAR
            data. The file specifier can be a single file name, a “wildcard”
            specifier, or the name of a text file containing a list of model
            files (must have “.txt” extension). In operation, CanopyModel will
            determine which models are needed by examining the extents of the
            input point data.
        ascii: boolean
            Write the output surface in ASCII raster format in addition to
            writing the surface in DTM format.
        grid: string, 4-tuple or list-like (X,Y,W,H)
            Force the origin of the output grid to be (X,Y) instead of computing
            an origin from the data extents and force the grid to be W units
            wide and H units high...W and H will be rounded up to a multiple of
            cellsize. If defined as a string, use format 'X,Y,W,H'
        gridxy: string, 4-tuple or list-like (X1,Y1,X2,Y2)
            Force the origin of the output grid (lower left corner) to be
            (X1,Y1) instead of computing an origin from the data extents and
            force the upper right corner to be (X2, Y2). X2 and Y2 will be
            rounded up to a multiple of cellsize. If defined as a string, use
            format 'X1,Y1,X2,Y2'.
        align: string, path to file
            Force alignment of the output grid to use the origin (lower left
            corner), width and height of the specified dtmfile. Behavior is the
            same as /gridxy except the X1,Y1,X2,Y2 parameters are read from the
            dtmfile.
        extent: string, path to file
            Force the origin and extent of the output grid to match the lower
            left corner and extent of the specified PLANS format DTM file but
            adjust the origin to be an even multiple of the cell size and the
            width and height to be multiples of the cell size.
        rasterorigin: boolean
            Offset the origin and adjust the extent of the surface so raster
            data products created using the surface will align with the extent
            specified with the /grid or /gridxy options. /rasterorigin is only
            used in conjunction with the /grid or /gridxy option.
        surface: boolean
            Use the bare-earth surface model in conjunction with values
            specified in /outlier to omit points based on their height above the
            ground surface but create a surface that is not normalized relative
            to the bare-earth surface (the surface uses the point elevations).
        peaks: boolean
            Preserve localized peaks in the final surface. Only useful with
            /median or /smooth.
        pointcount: boolean
            Output the number of data points in each cell in addition to the
            canopy surface/height values. Counts are output in .DTM format. If
            there are no points for a cell, the elevation/height value for the
            cell is set to 999.0.
        nofill: boolean
            Don’t fill holes in the surface model. In general, holes result from
            a lack of data within a cell. The default behavior is to fill holes
            in the interior of the surface model.
        --------
        additional boolean kwargs available for most FUSION commands include:
        quiet, verbose, newlog, version, locale, nolazsipdll
        --------
        """
        cmd = 'canopymodel'
        params = [surfacefile, cellsize, xyunits, zunits, coordsys, zone,
                  horizdatum, vertdatum, datafiles]
        self.run(cmd, **kwargs, *params)

    def catalog(self, datafile, catalogfile=None, **kwargs):
        """Produces a set of descriptive reports describing several important
        characteristics of LIDAR data sets.

        It is most often used to evaluate a new acquisition for internal
        quality, completeness of data coverage and return or pulse density. The
        primary output of Catalog is a web page that contains a summary of all
        data tiles evaluated including attribute summaries for each tile and
        overall summaries for the entire data set. Catalog provides options that
        will create the index files needed to use the LIDAR data with FUSION
        making it the logical first step in any analysis procedure. In addition
        to the web page, Catalog can produce images representing the coverage
        area, pulse and return densities, and intensity values for the entire
        acquisition. When data are stored in LAS format, Catalog includes a
        summary of points by classification code from the LAS data. All images
        produced by Catalog have associated world files so they can be used
        within FUSION to provide a frame-of-reference for analysis. Catalog also
        produces a FUSION hotspot file that provides specific details for each
        data tile in the FUSION environment.

        Parameters
        ----------
        datafile: string, path to file (required)
            LIDAR data file template or name of a text file containing a list of
            file names (list file must have .txt extension).
        catalogfile: string, path to file (optional)
            Base name for the output catalog file (extensions will be added).

        **Kwargs (optional), aka "Switches" in FUSION
        --------
        image: boolean
            Create image files showing the coverage area for each LIDAR file.
        index: boolean
            Create LIDAR data file indexes if they don't already exist.
        newindex: boolean
            Create new LIDAR data file indexes for all files (even if they
            already exist).
        drawtiles: boolean
            Draw data file extents and names on the intensity image.
        coverage: boolean
            Create one image that shows the nominal coverage area for all data
            files included in the catalog. Also creates a FUSION hotspot file
            that provides details for each file in the catalog.
        countreturns: boolean
            Adds columns in the CSV and HTML output to show the number of
            returns by return number for each data file and all data files
            combined. Runs that use this option can take much longer to process
            because Catalog has to read every point in the data files to count
            up the different returns. In theory, LAS files have this information
            in their header. However, file produced by some version of TerraScan
            do not have these fields populated with the actual number of data
            points by return number.
        -------
        additional boolean kwargs available for most FUSION commands include:
        quiet, verbose, newlog, version, locale, nolazsipdll
        -------
        """
        cmd = 'catalog'
        params = [datafile, catalogfile]
        self.run(cmd, **kwargs, *params)

    def clipdata(self, InputSpecifier, SampleFile, MinX=None, MinY=None,
                 MaxX=None, MaxY=None, **kwargs):
        """Creates sub-samples of LIDAR data for various analysis tasks.

        The sub-sample can be round or rectangular and can be large or small.
        ClipData provides many of the same sampling options found in FUSION but
        it is not used by FUSION to perform subsampling of LIDAR data sets
        (FUSION has its own logic to accomplish this task). ClipData is often
        used to create sample of LIDAR returns around a specific point of
        interest such as a plot center or GPS measurement point. Subsequent
        analyses using programs like CloudMetrics facilitate comparing field
        data to LIDAR point cloud metrics. ClipData can extract a single sample
        or multiple samples using a single command. When creating several
        samples, it is much more efficient to use the optional syntax to clip
        several samples using a single command line.

        ClipData can also sub-sample data within the sample area using the
        elevation values for the returns. When used in conjunction with a
        bare-earth surface model, this logic allows for sampling a range of
        heights above ground within the sample area.

        ClipData can extract specific returns (1st, 2nd, etc) or first and last
        returns (LAS files only) for the sample area. This capability, when used
        with a large sample area, can extract specific returns from an entire
        data file.

        As part of the sampling process, ClipData can add (or subtract) a fixed
        elevation from each return elevation effecting adjusting the entire
        sample up or down. This capability, when used with a large sample area,
        can adjust entire data files up or down to help align data from
        different LIDAR acquisitions.

        Parameters
        ----------
        InputSpecifier: string (required)
            LIDAR data file template, name of a text file containing a list of
            file names (must have .txt extension), or a FUSION Catalog CSV file.
        SampleFile: string (required)
            Name for subsample file (extension will be added) or a text file
            containing sample information for 1 or more samples. Each line in
            the text file should have the subsample filename and the MinX MinY
            MaxX MaxY values for the sample area separated by spaces or commas.
            The output filename cannot contain spaces.
        MinX, MinY, MaxX, MaxY: int (optional)
            Defines the lower left corner (MinX, MinY) and upper right corner
            (MaxX, MaxY) of the sample area bounding box.

        **Kwargs (optional), aka "Switches" in FUSION
        --------
        shape: int
            Shape of the sample area:
                0 rectangle
                1 circle
        decimate: int
            Skip # points between included points (must be > 0).
        ground: string, path to ground dtmfile
            Use the specified bare-earth surface model to normalize the LIDAR
            data (subtract the bare-earth surface elevation from each lidar
            point elevation). Use with /zmin to include points above zmin or
            with /zmax to include points below zmax (file must be FUSION/PLANS
            format). file may be wildcard or text list file (extension .txt
            only) that specifies more than one ground surface model. In
            operation, only the models that cover the sample area will be used
            to normalize point data.
        zmin: numeric
            Include points above # elevation. Use with /dtm to include points
            above # height.
        zmax: numeric
            Include points below # elevation. Use with /dtm to include points
            below # height.
        zpercent: numeric
            Include only the upper # percent of the points. If # is (-) only the
            lower # percent of the points. # can be -100 to +100.
        height: boolean
            Convert point elevations into heights above ground using the
            specified DTM file. Always Used with /dtm.
        timemin: numeric
            Include points with GPS times greater than # (LAS only).
        timemax: numeric
            Include points with GPS times less than or equal to # (LAS only).
            Interpretation of # depends on the GPS time recorded in the LAS
            point records.
        anglemin: numeric
            Include points with scan angles greater than # (LAS only).
        anglemax: numeric
            Include points with scan angles less than or equal to # (LAS only).
        zero: boolean
            Save subsample files that contain no data points. This is useful
            when automating conversion and analysis tasks and expecting a
            subsample file every time ClipData is executed.
        biaselev: numeric
            Add an elevation offset to every LIDAR point: # can be + or -.
        return: string or int
            Specifies the returns to be included in the sample. String can
            include A,1,2,3,4,5,6,7,8,9,F,L. A includes all returns. For LAS
            files only: F indicates first and only returns, L indicates last of
            many returns. F and L will not work with non-LAS files.
        class: string or list-like
            Used with LAS format files only. Specifies that only points with
            classification values listed are to be included in the subsample.
            Classification values should be separated by a comma e.g. (2,3,4,5)
            and can range from 0 to 31. If the first character of string is “~”,
            all classes except those listed will be used.
        line: numeric
            LAS files only: Only include returns from the specified flight line.
            Line numbering varies by acquisition so you need to know your data
            to specify values for the flight line number.
        noindex: boolean
            Do not use the data index files to access the data. This is useful
            when the order of the data points is important or when all returns
            for a single pulse need to stay together in the subsample file.
        index: boolean
            Create FUSION index files for the SampleFile.
        lda: boolean
            Write output files using FUSION's LDA format when using LAS input
            files. The default behavior after FUSION version 3.00 is to write
            data in LAS format when the input data are in LAS format. When using
            input data in a format other than LAS, sample files are written in
            LDA format.
        nooffset: boolean
            Produce an output point file that no longer has the correct
            geo-referencing. This is used when you need to work with the point
            cloud but cannot reveal the actual location of the features
            represented in the point cloud. This option modifies the header
            values in the LAS header for the output files.
        precision: 3-tuple or list-like (scaleX,scaleY,scaleZ)
            Control the scale factor used for X, Y, and Z values in output LAS
            files. These values will override the values in the source LAS
            files. There is rarely any need for the scale parameters to be
            smaller than 0.001.
        -------
        additional boolean kwargs available for most FUSION commands include:
        quiet, verbose, newlog, version, locale, nolazsipdll
        -------
        """
        cmd = 'canopymodel'
        params = [surfacefile, cellsize, xyunits, zunits, coordsys, zone,
                  horizdatum, vertdatum, datafiles]
        self.run(cmd, **kwargs, *params)

    def clipdtm(self, InputDTM, OutputDTM, MinX, MinY, MaxX, MaxY, **kwargs):
        """Clips a portion of the gridded surface model and stores it in a new
        file. The extent of the clipped model is specified using the lower left
        and upper right corner coordinates.

        Parameters (required)
        ----------
        InputDTM: string, path to file
            Name of the existing PLANS format DTM file to be clipped.
        OutputDTM: string, path to file
            Name for the new PLANS format DTM file.
        MinX, MinY: numeric
            Lower left corner for the output DTM.
        MaxX, MaxY: numeric
            Upper right corner for the output DTM.

        **Kwargs (optional), aka "Switches" in FUSION
        --------
        shrink: boolean
            Shrink the extent of the input model by the amounts specified by
            MinX MinY MaxX MaxY. MinX is removed from left side, MinY is removed
            from bottom, MaxX is removed from right side, and MaxY is removed
            from top.
        -------
        additional boolean kwargs available for most FUSION commands include:
        quiet, verbose, newlog, version, locale, nolazsipdll
        -------
        """
        cmd = 'clipdtm'
        params = [InputDTM, OutputDTM, MinX, MinY, MaxX, MaxY]
        self.run(cmd, **kwargs, *params)

    def cloudmetrics(self, InputDataSpecifier, OutputFileName, **kwargs):
        """Computes a variety of statistical parameters describing a LIDAR data
        set.

        Metrics are computed using point elevations and intensity values (when
        available). In operation, CloudMetrics produces one record of output for
        each data file processed. Input can be a single LIDAR data file, a file
        template that uses DOS file specifier rules, a simple text file
        containing a list of LIDAR data file names, or a LIDAR data catalog
        produced by the Catalog utility. Output is appended to the specified
        output file unless the /new switch is used to force the creation of a
        new output data file. Output is formatted as a comma separated value
        (CSV) file that can be easily read by database, statistical, and
        MS-Excel programs.

        CloudMetrics is most often used with the output from the ClipData
        program to compute metrics that will be used for regression analysis in
        the case of plot-based LIDAR samples or for tree classification in the
        case of individual tree LIDAR samples.

        Parameters (required)
        ----------
        InputDataSpecifier: string, path to file
            LIDAR data file template, name of text file containing a list of
            LIDAR data file names (must have .txt extension), or a catalog file
            produced by the Catalog utility.
        OutputFileName: string, path to file
            Name for output file to contain cloud metrics (using a .csv will
            associate the files with MS-Excel).

        **Kwargs (optional), aka "Switches" in FUSION
        --------
        above: numeric
            Compute various cover estimates using the specified heightbreak (#).
            See the technical detail for specific cover metrics that are
            computed.
        new: boolean
            Creates a new output file and deletes any existing file with the
            same name. A header is written to the new output file.
        firstinpulse: boolean
            Use only the first return for a pulse to compute metrics. Such
            returns may not always be labeled as return 1.
        firstreturn: boolean
            Use only first returns to compute metrics.
        highpoint: boolean
            Produce a limited set of metrics that includes only the highest
            return within the data file.
        subset: boolean
            Produce a limited set of metrics ([ID], #pts, Mean ht, Std dev ht,
            75th percentile, cover). Must be used with the /above:# option.
        id: boolean
            Parse the data file name to create an identifier for the output
            record. Data file names should include a number (e.g. sample003.lda)
            or the default identifier of 0 will be assigned to the file. The
            identifier is placed in the first column of the output record before
            the input file name.
        rid: boolean
            Parse the data file name to create an identifier for the output
            record but start at the end of the filename. Data file names can
            include any characters but the end of the name should include a
            number preceded by a non-numeric character
            (e.g. 2017_01_13_sample003.las). The identifier is placed in the
            first column of the output record before the input file name.
        minht: numeric
            Use only returns above # (use when data in the input data files have
            been normalized using a ground surface model. In older versions of
            CloudMetrics this switch was htmin.
        maxht: numeric
            Use only returns below # (use when data is normalized to ground) to
            compute metrics. The maxht is not used when computing metrics
            related to the /strata or /intstrata options.
        outlier: 2-tuple or list-like of numerics (low,high)
            Omit points with elevations below low and above high. When used with
            data that has been normalized using a ground surface, low and high
            are interpreted as heights above ground. You should use care when
            using /outlier:low,high with /minht and /maxht options. If the low
            value specified with /outlier is above the value specified with
            /minht, the value for /outlier will override the value specified for
            /minht. Similarly, if the high value specified with /outlier is less
            than the value specified for /maxht, the /outlier value will
            override the value for /maxht.
        strata: list-like of numerics [#,#,#,...]
            Count returns in various height strata. # gives the upper limit for
            each strata. Returns are counted if their height is >= the lower
            limit and < the upper limit. The first strata contains points < the
            first limit. The last strata contains points >= the last limit.
            Default strata: 0.15, 1.37, 5, 10, 20, 30.
        intstrata: list-like of numerics [#,#,#,…]
            Compute metrics using the intensity values in various height strata.
            Strata for intensity metrics are defined in the same way as the
            /strata option. Default strata: 0.15, 1.37.
        kde: 2-tuple or list-like [window,mult]
            Compute the number of modes and minimum and maximum node using a
            kernal density estimator. Window is the width of a moving average
            smoothing window in data units and mult is a multiplier for the
            bandwidth parameter of the KDE. Default window is 2.5 and the
            multiplier is 1.0
        rgb: string
            Compute intensity metrics using the color value from the RGB color
            for the returns. Valid with LAS version 1.2 and newer data files
            that contain RGB information for each return (point record types 2
            and 3). Valid color values are R, G, or B.
        relcover: boolean
            Compute the proportion of first (or all) returns above the mean and
            mode values.
        alldensity: boolean
            Use all returns when computing density (percent cover, cover above
            the mean and cover above the mode) default is to use only first
            returns when computing density.
        -------
        additional boolean kwargs available for most FUSION commands include:
        quiet, verbose, newlog, version, locale, nolazsipdll
        -------
        """
        if kwargs['relcover']:
            warnings.warn("""relcover is obsolete as of CloudMetrics version
            2.0. Metrics are computed as part of the default set of metrics.""",
            DeprecationWarning)
        if kwargs['alldensity']:
            warnings.warn("""alldensity is obsolete as of CloudMetrics version
            2.0. Metrics are computed as part of the default set of metrics.""",
            DeprecationWarning

        cmd = 'cloudmetrics'
        params = [InputDataSpecifier, OutputFileName]
        self.run(cmd, **kwargs, *params)

    def cover(self, groundfile, coverfile, heightbreak, cellsize, xyunits,
              zunits, coordsys, zone, horizdatum, vertdatum, datafile,
              **kwargs):
        """Computes estimates of canopy closure using a grid.

        Output values for cover estimates range from 0.0 to 100.0 percent.
        Canopy closure us defined as the number of returns over a specified
        height threshold divided by the total number of returns within each
        cell. In addition, Cover can compute the proportion of pulses that are
        close to a bare-ground surface model to help assess canopy penetration
        by the laser scanner. Wit the addition of an upper height limit, Cover
        can compute the proportion of returns falling within specific height
        ranges providing estimates of relative vegetation density for various
        height strata.

        Parameters (required)
        ----------
        groundfile: string, path to file
            File specifier for the bare-ground surface model used to normalize
            all return elevations. The file specifier can be a single file name,
            a “wildcard” specifier, or the name of a text file containing a list
            of model files (must have “.txt” extension). In operation, Cover
            will determine which models are needed by examining the extents of
            the input point data.
        coverfile: string, path to file
            Name for the cover data file. The cover data is stored in the PLANS
            DTM format using floating point values.
        heightbreak: numeric
            Height break for the cover calculation.
        cellsize: numeric
            Grid cell size for the cover data.
        xyunits: string
            Units for LIDAR data XY:
                'M' for meters,
                'F' for feet.
        zunits: string
            Units for LIDAR data elevations:
                'M' for meters,
                'F' for feet.
        coordsys: int
            Coordinate system for the cover data:
                0 for unknown
                1 for UTM
                2 for state plane
        zone: int
            Coordinate system zone for the cover data (0 for unknown).
        horizdatum: int
            Horizontal datum for the cover data:
                0 for unknown
                1 for NAD27
                2 for NAD83
        vertdatum: int
            Vertical datum for the cover data:
                0 for unknown
                1 for NGVD29
                2 for NAVD88
                3 for GRS80
        datafile: string, or list-like of strings, path to file(s)
            LIDAR data file (LDA, LAS, ASCII LIDARDAT formats)... may be
            wildcard or name of text file listing the data files. If wildcard or
            text file is used, no other datafile# parameters will be recognized.
            Several data files can be specified. The limit depends on the length
            of each file name. When using multiple data files, it is best to use
            a wildcard for datafile1 or create a text file containing a list of
            the data files and specifying the list file as datafile1.

        **Kwargs (optional), aka "Switches" in FUSION
        --------
        all: boolean
            Use all returns to calculate the cover data. The default is to use only first returns.
        class: string or list-like
            Used with LAS format files only. Specifies that only points with
            classification values listed are to be included in the subsample.
            Classification values should be separated by a comma e.g. (2,3,4,5)
            and can range from 0 to 31. If the first character of string is “~”,
            all classes except those listed will be used.
        penetration: boolean
            Compute the proportion of returns close to the ground surface by
            counting the number of returns within +-heightbreak units of the
            ground.
        upper: numeric
            Use an upperlimit when computing the cover value. This allows you to
            calculate the proportion of returns between the heightbreak and
            upperlimit.
        -------
        additional boolean kwargs available for most FUSION commands include:
        quiet, verbose, newlog, version, locale, nolazsipdll
        -------
        """
        cmd = 'cover'
        params = [groundfile, coverfile, heightbreak, cellsize, xyunits, zunits,
                  coordsys, zone, horizdatum, vertdatum, datafile]
        self.run(cmd, **kwargs, *params)

    def csv2grid(self, inputfile, column, outputfile, **kwargs):
        """Converts data stored in comma separated value (CSV) format into ASCII
        raster format.

        In operation, users specify the column from the CSV file to convert.
        CSV2Grid expects a header file that corresponds to the input file. The
        header file name is formed from the input file name by appending the
        text “_ascii_header” and changing the extension to “.txt”. Normally, the
        CSV files used with CSV2Grid are produced by GridMetrics.

        Parameters (required)
        ----------
        inputfile: string, path to file
            Name of the input CSV file. This file is normally output from
            GridMetrics.
        column: int
            Column number for the values to populate the grid file (column
            numbers start with 1).
        outputfile: string, path to file
            Name for the output ASCII raster file.

        **Kwargs (optional), aka "Switches" in FUSION
        --------
        multiplier: numeric
            Multiply all data values by the constant (#).
        ndzero: numeric
            If the value in the target column is NODATA, look at the value in
            column # and, if it is a valid value (not NODATA), change the value
            for the target column to 0.0 for output to the ASCII grid file. This
            option is useful when the ASCII grid file will be used for further
            analysis in GIS or statistical packages.
        -------
        additional boolean kwargs available for most FUSION commands include:
        quiet, verbose, newlog, version, locale, nolazsipdll
        -------
        """
        cmd = 'csv2grid'
        params = [inputfile, column, outputfile]
        self.run(cmd, **kwargs, *params)

    def densitymetrics(self, groundfile, cellsize, slicethickness, outputfile,
                       datafile, **kwargs):
        """Produces a series of grids where each grid contains density
        information for a specific range of heights above ground.

        Densities are reported as the proportion of the returns within the
        layer. Output consists of a CSV file with columns that correspond to the
        layers and PLANS format DTM files (one for each layer) containing the
        point density information.

        Parameters (required)
        ----------
        groundfile: string, path to file
            File specifier for the bare-ground surface model used to normalize
            all return elevations. The file specifier can be a single file name,
            a “wildcard” specifier, or the name of a text file containing a list
            of model files (must have “.txt” extension). In operation,
            DensityMetrics will determine which models are needed by examining
            the extents of the input point data.
        cellsize: numeric
            Desired grid cell size for the point density data in the same units
            as the point data.
        slicethickness: numeric
            Thickness for each “slice” in the same units as the point
            elevations.
        outputfile: string, path to file
            Base file name for output. Metrics are stored in CSV format with the
            extension .csv unless the /nocsv switch is specified, Other outputs
            are stored in files named using the base name and additional
            descriptive information.
        datafile: string, or list-like of strings, path(s) to files
            LIDAR data file(s) (LDA, LAS, ASCII LIDARDAT formats)... may be
            wildcard or name of text file listing the data files. If wildcard or
            text file is used, no other datafile# parameters will be recognized.
            Several data files can be specified. The limit depends on the length
            of each file name. When using multiple data files, it is best to use
            a wildcard for datafile1 or create a text file containing a list of
            the data files and specifying the list file as datafile1.

        **Kwargs (optional), aka "Switches" in FUSION
        --------
        outlier: 2-tuple or list-like of numerics (low,high)
            Ignore points with elevations below low and above high. Low and high
            are interpreted as heights above ground as defined by the
            groundfile.
        maxsliceht: numeric
            Limit the range of height slices to 0 to high.
        nocsv: boolean
            Do not create a CSV output file for cell metrics.
        class: string, or list-like
            Used with LAS format files only. Specifies that only points with
            classification values listed are to be included when computing
            density metrics. Classification values should be separated by a
            comma e.g. (2,3,4,5) and can range from 0 to 31. If the first
            character of string is “~”, all classes except those listed will be
            used.
        first: boolean
            Use only first returns to compute all metrics. The default is to use
            all returns to compute the metrics.
        slices: list-like of numerics [#,#,#,…]
            Use specific slice height breaks rather that evenly spaced breaks
            based on the range of heights in the data. You can specify a maximum
            of 64 slice heights. The first slice always starts at 0.0. Slice
            heights must be specified in ascending order. The highest slice will
            contain the count of all points with heights greater than or equal
            to the last height break. Slice height ranges are defined as: lower
            ht <= point height < upper height.
        grid: 4-tuple or list-like of numerics (X,Y,W,H)
            Force the origin of the output grid to be (X,Y) instead of computing
            an origin from the data extents and force the grid to be W units
            wide and H units high...W and H will be rounded up to a multiple of
            cellsize.
        gridxy: 4-tuple or list-like of numerics (X1,Y1,X2,Y2)
            Force the origin of the output grid (lower left corner) to be
            (X1,Y1) instead of computing an origin from the data extents and
            force the upper right corner to be (X2, Y2). X2 and Y2 will be
            rounded up to a multiple of cellsize.
        align: string, path to dtmfile
            Force alignment of the output grid to use the origin (lower left
            corner), width and height of the specified dtmfile. Behavior is the
            same as /gridxy except the X1,Y1,X2,Y2 parameters are read from the
            dtmfile.
        buffer: numeric
            Add an analysis buffer of the specified width (same units as LIDAR
            data) around the data extent when computing metrics but only output
            metrics for the area specified via /grid, /gridxy, or /align. When
            /buffer is used without one of these options, metrics are output for
            an area that is inside the actual extent of the return data as
            metrics within the buffer area are not output.
        cellbuffer: int
            Add an analysis buffer specified as the number of extra rows and
            columns around the data extent when computing metrics but only
            output metrics for the area specified via /grid, /gridxy, or /align.
            When /cellbuffer is used without one of these options, metrics are
            output for an area that is inside the actual extent of the return
            data as metrics for the buffer area are not output.
        -------
        additional boolean kwargs available for most FUSION commands include:
        quiet, verbose, newlog, version, locale, nolazsipdll
        -------
        """
        cmd = 'densitymetrics'
        params = [groundfile, cellsize, slicethickness, outputfile, datafile]
        self.run(cmd, **kwargs, *params)

    def dtm2ascii(self, inputfile, outputfile=None, **kwargs):
        """Converts data stored in the PLANS DTM format into ASCII raster files.

        Such files can be imported into GIS software such as ArcInfo. DTM2ASCII
        provides the same functionality as the Tools... Terrain model... Export
        model... menu option in FUSION.

        Parameters (required)
        ----------
        inputfile: string, path to file
            Name of the PLANS DTM file to be converted into ASCII raster format.
        outputfile: string, path to file
            Name for the converted file. If outputfile is omitted, the output
            file name will be constructed from the inputfile name and the
            extension .asc. When the csv switch is specified, the default
            extension used to construct an output file name is .csv.

        **Kwargs (optional), aka "Switches" in FUSION
        --------
        csv: boolean
            Output data values in comma separated value format. Header is the
            column number. Data are arranged in rows with the northern-most row
            first in the file.
        raster: boolean
            Interpret the DTM points as the attribute for a cell and adjust the
            origin of the ASCII grid file so that the lower left data point is
            the center of the lower left grid cell. For almost all applications,
            you should use the /raster option.
        multiplier: numeric
            Multiply the output values by the constant (#).
        -------
        additional boolean kwargs available for most FUSION commands include:
        quiet, verbose, newlog, version, locale, nolazsipdll
        -------
        """
        cmd = 'dtm2acsii'
        params = [inputfile, outputfile]
        self.run(cmd, **kwargs, *params)

    def dtm2envi(self, inputfile, outputfile=None, **kwargs):
        """Converts data stored in the PLANS DTM format into ENVI standard
        format raster files.

        Such files can be imported into GIS software such as ENVI and ArcInfo.

        Parameters
        ----------
        inputfile: string, path to file (required)
            Name of the PLANS DTM file to be converted into ASCII raster format.
        outputfile: string, path to file (optional)
            Name for the converted file. If outputfile is omitted, the output
            file name will be constructed from the inputfile name and the
            extension .nvi. The associated ENVI header file is named by
            appending “.hdr” to the inputfile name.

        **Kwargs (optional), aka "Switches" in FUSION
        --------
        south: boolean
            Specifies that data are located in the southern hemisphere
        -------
        additional boolean kwargs available for most FUSION commands include:
        quiet, verbose, newlog, version, locale, nolazsipdll
        -------
        """
        cmd = 'dtm2envi'
        params = [inputfile, outputfile]
        self.run(cmd, **kwargs, *params)

    def dtm2tif(self, inputfile, outputfile=None, **kwargs):
        """Converts data stored in the PLANS DTM format into a TIFF image and
        creates a world file that provides coordinate system reference data for
        the image.

        Such images can be imported into GIS software or used in other analysis
        processes.

        Parameters
        ----------
        inputfile: string, path to file (required)
            Name of the PLANS DTM file to be converted into ASCII raster format.
        outputfile: string, path to file (optional)
            Name for the converted file. If outputfile is omitted, the output
            file name will be constructed from the inputfile name and the
            extension .tif.

        **Kwargs (optional), aka "Switches" in FUSION
        --------
        mask: boolean
            Produces a mask image showing the areas in the DTM with valid data
            values. In the mask image, a value of 0 indicates a cell with
            invalid data (NODATA value) and a value of 255 indicates a cell with
            a valid data value.
        -------
        additional boolean kwargs available for most FUSION commands include:
        quiet, verbose, newlog, version, locale, nolazsipdll
        -------
        """
        cmd = 'dtm2tif'
        params = [inputfile, outputfile]
        self.run(cmd, **kwargs, *params)

    def dtm2xyz(self, inputfile, outputfile=None, **kwargs):
        """Converts data stored in the PLANS DTM format into ASCII text files
        containing XYZ points.

        Such files can be imported into GIS software as point data with the
        elevation as an attribute or used in other analysis processes.

        Parameters
        ----------
        inputfile: string, path to file (required)
            Name of the PLANS DTM file to be converted into ASCII raster format.
        outputfile: string, path to file (optional)
            Name for the converted file. If outputfile is omitted, the output
            file name will be constructed from the inputfile name and the
            extension .xyz. If the /csv switch is used, the extension will be
            .csv.

        **Kwargs (optional), aka "Switches" in FUSION
        --------
        csv: boolean
            Output XYZ points in comma separated value format (CSV). If /csv is
            used with no outputfile, an extension of .csv will be used to form
            the output file name.
        void: boolean
            Output points from DTM with NODATA value (default is to omit).
            NODATA value is -9999.0 for the elevation.
        noheader: boolean
            Do not include the column headings in CSV output files. Ignored if
            /csv is not used
        -------
        additional boolean kwargs available for most FUSION commands include:
        quiet, verbose, newlog, version, locale, nolazsipdll
        -------
        """
        cmd = 'dtm2xyz'
        params = [inputfile, outputfile]
        self.run(cmd, **kwargs, *params)

    def dtmdescribe(self, inputfile, outputfile, **kwargs):
        """Reads header information for PLANS format DTM files and outputs the
        information to an ASCII text file compatible with most spreadsheet and
        database programs. DTMDescribe can provide information for a single file
        or multiple files.

        Parameters (required)
        ----------
        inputfile: string, path to file
            DTM file name, DTM file template, or name of a text file containing
            a list of file names (must have .txt extension).
        outputfile: string, path to file
            Name for the output ASCII CSV file. If no extension is provided, an
            extension (.csv) will be added.

        **Kwargs (optional), aka "Switches" in FUSION
        --------
        ...
        -------
        additional boolean kwargs available for most FUSION commands include:
        quiet, verbose, newlog, version, locale, nolazsipdll
        -------
        """
        cmd = 'dtmdescribe'
        params = [intputfile, outputfile]
        self.run(cmd, **kwargs, *params)

    def dtmheader(self, filename=None):
        """Launches DTMHeader, an interactive program to examine and modify
        PLANS DTM file header information.

        DTMHeader allows you to easily view and change the header information
        for a PLANS DTM file. To make it most convenient, associate the .dtm
        extension with DTMHeader so you can simply double-click a .dtm file to
        view the header.

        The values in the header that can be modified are:
            Planimetric units
            Elevation units
            Descriptive name
            Coordinate system and zone
            Horizontal datum
            Vertical datum

        Parameters (optional)
        ----------
        filename: string, path to file
            Name of the PLANS DTM file to be examined.
        """
        cmd = 'dtmheader'
        params = [filename]
        self.run(cmd, *params)

    def filterdata(self, FilterType, FilterParms, WindowSize, OutputFile,
                   DataFile, **kwargs):
        """Applies various filters to return data files to produce new return
        data files with only the returns that meet the filter requirements.

        The most common application for FilterType is to remove “outliers” from
        return data files. Other filter options overlay the return data with a
        user-specified grid and produce output return files that contain only
        the returns with the minimum or maximum elevation for each grid cell.

        Parameters (required)
        ----------
        FilterType: 'outlier', 'outlier2', 'minimum' or 'maximum'
            Filtering algorithm used to remove returns from the DataFile(s).
            The following options (by name) are supported:
                outlier: removes returns above or below the mean elevation plus
                    or minus FilterParms * standard deviation of the elevations
                outlier2: More robust outlier removal (experimental)
                minimum:  removes all returns except the return with the minimum
                    elevation
                maximum: removes all returns except the return with the maximum
                    elevation
        FilterParms: numeric
            Parameter specific to the filtering method. For outlier this is the
            multiplier applied to the standard deviation. For minimum and
            maximum, FilterParms is ignored (but a value must be included on the
            command line...use 0)
        WindowSize: numeric
            Size of the window used to compute the standard deviation of
            elevations or the minimum/maximum return
        OutputFile: string, path to file
            Name of the output file. If any part of the name includes spaces,
            include the entire name in double quotation marks
        DataFile: string, path to file
            LIDAR data file name or template or name of a text file containing a
            list of file names (list file must have .txt extension).

        **Kwargs (optional), aka "Switches" in FUSION
        --------
        index: boolean
            Create FUSION index files for the output file.
        minsd: numeric
            Minimum standard deviation for points within a comparison window for
            filtering to take place. Default is 1.0 (same units as elevation
            data). This switch is only useful when using the outlier filter.
        minpts: int
            Minimum number of points in the comparison window for filtering to
            take place. This option can be used with all filters but must
            specify at least 3 points when used with the outlier filter.
        minrange: numeric
            Minimum range in elevations within a window for outlier filtering to
            take place. Default is 150.0 elevation units Used only with the
            outlier2 filter.
        mingap: numeric
            Minimum vertical distance that define a gap. Used to isolate points
            above the majority of points in the filter window. Used only with
            the outlier2 filter.
        gapratio: numeric
            Proportion of points in window that can be above a vertical gap.
            Ranges from 0.0 to 1.0 Used only with the outlier2 filter.
        class: string or list-like
            Used with LAS format files only. Specifies that only points with
            classification values listed are to be included in the subsample.
            Classification values should be separated by a comma e.g. (2,3,4,5)
            and can range from 0 to 31. If the first character of string is “~”,
            all classes except those listed will be used.
        lda: boolean
            Write output files using FUSION's LDA format when using LAS input
            files. The default behavior after FUSION version 3.00 is to write
            data in LAS format when the input data are in LAS format. When using
            input data in a format other than LAS, sample files are written in
            LDA format.
        precision: 3-tuple or list-like of numerics (scaleX,scaleY,scaleZ)
            Control the scale factor used for X, Y, and Z values in output LAS
            files. These values will override the values in the source LAS
            files. There is rarely any need for the scale parameters to be
            smaller than 0.001.
        reclass: int
            Change the classification code for points identified as outliers and
            write them to the output file. The optional value is the
            classification code assigned to the points. Only valid when used
            with the outlier and outlier2 filters.
        -------
        additional boolean kwargs available for most FUSION commands include:
        quiet, verbose, newlog, version, locale, nolazsipdll
        -------
        """
        cmd = 'filterdata'
        params = [FilterType, FilterParms, WindowSize, OutputFile, DataFile]
        self.run(cmd, **kwargs, *params)

    def firstlastreturn(self, OutputFile, DataFile, **kwargs):
        """Extracts first and last returns from a LIDAR point cloud.

        It is most commonly used when the point cloud data are provided in a
        format that does not identify the last return of a pulse.
        FirstLastReturn provided two definitions of last returns: the last
        return recorded for each pulse and the last return recorded for pulse
        with more than one return. The former includes first returns that are
        also the last return recorded for a pulse and the latter does not.

        Parameters (required)
        ----------
        OutputFile: string, path to file
            Base file name for output data files. First and last returns are
            written to separate files that are named by appending
            “_first_returns” and “_last_returns” to the base file name.
        DataFile: string, path to file
            LIDAR data file template or name of a text file containing a list of
            file names (list file must have .txt extension).

        **Kwargs (optional), aka "Switches" in FUSION
        --------
        index: boolean
            Create FUSION index files for the files containing the first and
            last returns.
        lastnotfirst: boolean
            Do not included first returns that are also last returns in the last
            returns output file.
        uselas: boolean
            Use information stored in the LAS point records to determine which
            returns are first and last returns.
        lda: boolean
            Write output files using FUSION's LDA format when using LAS input
            files. The default behavior after FUSION version 3.00 is to write
            data in LAS format when the input data are in LAS format. When using
            input data in a format other than LAS, sample files are written in
            LDA format.
        precision: 3-tuple or list-like of numerics (scaleX,scaleY,scaleZ)
            Control the scale factor used for X, Y, and Z values in output LAS
            files. These values will override the values in the source LAS
            files. There is rarely any need for the scale parameters to be
            smaller than 0.001.
        -------
        additional boolean kwargs available for most FUSION commands include:
        quiet, verbose, newlog, version, locale, nolazsipdll
        -------
        """
        cmd = 'firstlastreturn'
        params = [Outputfile, DataFile]
        self.run(cmd, **kwargs, *params)

    def gridmetrics(self, groundfile, heightbreak, cellsize, outputfile,
                    datafile, **kwargs):
        """Computes a series of descriptive statistics for a LIDAR data set.

        Output is a raster (grid) represented in database form with each record
        corresponding to a single grid cell. GridMetrics is similar to
        CloudMetrics except it computes metrics for all returns within each cell
        in the output grid. Cloudmetrics computes a single set of metrics for
        the entire data set. The default output from GridMetrics is an ASCII
        text file with comma separated values (CSV format). Field headings are
        included and the files are easily read into database and spreadsheet
        programs. Optionally, GridMetrics can output raster layers stored in
        PLANS DTM format. GridMetrics compute statistics using both elevation
        and intensity values in the same run. GridMetrics can apply the fuel
        models developed to predict canopy fuel characteristics in Douglas-fir
        forest type in Western Washington (Andersen, et al. 2005). Application
        of the fuel models to other stand types or geographic regions may
        produce questionable results.

        Parameters (required)
        ----------
        groundfile: string, path to file
            Name for ground surface model(s) (PLANS DTM with .dtm extension)...
            may be wildcard or name of text file listing the data files.
            Multiple ground models can be used to facilitate processing of large
            areas where a single model for the entire acquisition is too large
            to hold in memory.
        heightbreak: numeric
            Height break for cover calculation.
        cellsize: numeric
            Desired grid cell size in the same units as LIDAR data.
        outputfile: string
            Base name for output file. Metrics are stored in CSV format with
            .csv extension unless the /nocsv switch is used. Other outputs are
            stored in files named using the base name and additional descriptive
            information.
        datafile: string or list-like of strings with path(s) to lidar file(s)
            First LIDAR data file (LDA, LAS, ASCII LIDARDAT formats)...may be
            wildcard or name of text file listing the data files. If wildcard or
            text file is used, no other datafile# parameters will be recognized.
            Several data files can be specified. The limit depends on the length
            of each file name. When using multiple data files, it is best to use
            a wildcard for datafile1 or create a text file containing a list of
            the data files and specifying the list file as datafile1.

        **Kwargs (optional), aka "Switches" in FUSION
        --------
        outlier: 2-tuple (low,high)
            Omit points with elevations below low and above high. low and high
            are interpreted as heights above ground.
        class: string or list-like
            Used with LAS format files only. Specifies that only points with
            classification values listed are to be included in the subsample.
            Classification values should be separated by a comma e.g. (2,3,4,5)
            and can range from 0 to 31. If the first character of string is “~”,
            all classes except those listed will be used.
        id: string
            Include the identifier string as the last column in every record in
            the outputfile. The identifier will be included in all files
            containing metrics (elevation, intensity, and topo). The identifier
            cannot include spaces.
        minpts: int
            Minimum number of points in a cell required to compute metrics
            (default is 4 points).
        minht: numeric
            Minimum height used for points used to compute metrics. Density is
            always computed using all points including those with heights below
            the specified minimum height.
        nocsv: boolean
            Do not create an output file for cell metrics.
        noground: boolean
            Do not use a ground surface model. When this option is specified,
            the groundfile parameter should be omitted from the command line.
            Cover estimates, densitytotal, densityabove, and densitycell metrics
            are meaningless when no ground surface model is used unless the
            LIDAR data have been normalize to the ground surface using some
            other process.
        nointdtm: boolean
            Do not create an internal DTM to use when normalizing point
            elevations. The default behavior is to create an internal model that
            corresponds to the extent of the point data (or the area specified
            using the /grid, /gridxy, or /align switches). In some cases,
            creating the internal model causes problems with processing. Most
            often this caused problems for small areas with metrics being
            computed for a large cell size. The internal model was created to
            cover a slightly larger area than the data extent resulting in bad
            metrics along the top and right sides of the data extent.
        diskground: boolean
            Do not load ground surface models into memory. When this option is
            specified, larger areas can be processed but processing may be 4 to
            5 times slower. Ignored when /noground option is used.
        alldensity: boolean
            This switch is obsolete as of GridMetrics version 3.0.
            Use all returns when computing density (percent cover) default is to
            use only first returns when computing density.
        first: boolean
            Use only first returns to compute all metrics. Default is to use all
            returns for metrics.
        intensity: boolean
            This switch is obsolete as of GridMetrics version 3.0.
            Compute metrics using intensity values (default is elevation).
        nointensity: boolean
            Do not compute metrics using intensity values (default is to
            compute metrics using both intensity and elevation values).
        rgb: string
            Compute intensity metrics using the color value from the RGB color
            for the returns. Valid with LAS version 1.2 and newer data files
            that contain RGB information for each return (point record types 2
            and 3). Valid color values are R, G, or B.
        fuel: boolean
            Apply fuel parameter models (cannot be used with /first switch).
        grid: 4-tuple or list-like of numerics (X,Y,W,H)
            Force the origin of the output grid to be (X,Y) instead of computing
            an origin from the data extents and force the grid to be W units
            wide and H units high...W and H will be rounded up to a multiple of
            cellsize.
        gridxy: 4-tuple or list-like of numerics (X1,Y1,X2,Y2)
            Force the origin of the output grid (lower left corner) to be
            (X1,Y1) instead of computing an origin from the data extents and
            force the upper right corner to be (X2, Y2). X2 and Y2 will be
            rounded up to a multiple of cellsize.
        align: string, path to dtmfile
            Force alignment of the output grid to use the origin (lower left
            corner), width and height of the specified dtmfile. Behavior is the
            same as /gridxy except the X1,Y1,X2,Y2 parameters are read from the
            dtmfile.
        extent: string, path to dtmfile
            Force the origin and extent of the output grid to match the lower
            left corner and extent of the specified PLANS format DTM file but
            adjust the origin to be an even multiple of the cell size and the
            width and height to be multiples of the cell size.
        buffer: numeric
            Add an analysis buffer of the specified width (same units as LIDAR
            data) around the data extent when computing metrics but only output
            metrics for the area specified via /grid, /gridxy, or /align. When
            /buffer is used without one of these options, metrics are output for
            an area that is inside the actual extent of the return data as
            metrics within the buffer area are not output.
        cellbuffer: numeric
            Add an analysis buffer specified as the number of extra rows and
            columns around the data extent when computing metrics but only
            output metrics for the area specified via /grid, /gridxy, or /align.
            When /cellbuffer is used without one of these options, metrics are
            output for an area that is inside the actual extent of the return
            data as metrics for the buffer area are not output.
        strata: list-like of numerics [#,#,#,…]
            Count returns in various height strata. # gives the upper limit for
            each strata. Returns are counted if their height is >= the lower
            limit and < the upper limit. The first strata contains points < the
            first limit. The last strata contains points >= the last limit.
            Default strata: 0.15, 1.37, 5, 10, 20, 30.
        intstrata: list-like of numerics [#,#,#,…]
            Compute metrics using the intensity values in various height strata.
            Strata for intensity metrics are defined in the same way as the
            /strata option. Default strata: 0.15, 1.37.
        kde: 2-tuple or list-like (window,mult)
            Compute the number of modes and minimum and maximum node using a
            kernel density estimator. Window is the width of a moving average
            smoothing window in data units and mult is a multiplier for the
            bandwidth parameter of the KDE. Default window is 2.5 and the
            multiplier is 1.0
        ascii: boolean
            Store raster files in ASCII raster format for direct import into
            ArcGIS. Using this option preserves metrics with negative values.
            Such values are lost when raster data are stored using the PLANS DTM
            format. This switch is ignored unless it is used with the /raster
            switch.
        topo: 2-tuple or list-like (dist,lat)
            Compute topographic metrics using the groundfile(s) and output them
            in a separate file. Distance is the cell size for the 3 by 3 cell
            analysis area and lat is the latitude (+north, -south).
        raster: string or list-like of strings
            Create raster files containing the point cloud metrics. layers is a
            list of metric names separated by commas. Raster files are stored in
            PLANS DTM format or ASCII raster format when the /ascii switch is
            used. Topographic metrics are not available with the /raster:layers
            switch.

            Available metrics are:
                count: Number of returns above the minimum height
                densitytotal: total returns used for calculating cover
                densityabove: returns above heightbreak
                densitycell: Density of returns used for calculating cover
                min: minimum value for cell
                max: maximum value for cell
                mean: mean value for cell
                mode: modal value for cell
                stddev: standard deviation of cell values
                variance: variance of cell values
                cv: coefficient of variation for cell
                cover: cover estimate for cell
                abovemean: proportion of first (or all) returns above the mean
                abovemode: proportion of first (or all) returns above the mode
                skewness: skewness computed for cell
                kurtosis: kurtosis computed for cell
                AAD: average absolute deviation from mean for the cell
                p01: 1st percentile value for cell (must be p01, not p1)
                p05: 5th percentile value for cell (must be p05, not p5)
                p10: 10th percentile value for cell
                p20: 20th percentile value for cell
                p25: 25th percentile value for cell
                p30: 30th percentile value for cell
                p40: 40th percentile value for cell
                p50: 50th percentile value (median) for cell
                p60: 60th percentile value for cell
                p70: 70th percentile value for cell
                p75: 75th percentile value for cell
                p80: 80th percentile value for cell
                p90: 90th percentile value for cell
                p95: 95th percentile value for cell
                p99: 99th percentile value for cell
                iq: 75th percentile minus 25th percentile for cell
                90m10: 90th percentile minus 10th percentile for cell
                95m05: 95th percentile minus 5th percentile for cell
                r1count: Count of return 1 points above the minimum height
                r2count: Count of return 2 points above the minimum height
                r3count: Count of return 3 points above the minimum height
                r4count: Count of return 4 points above the minimum height
                r5count: Count of return 5 points above the minimum height
                r6count: Count of return 6 points above the minimum height
                r7count: Count of return 7 points above the minimum height
                r8count: Count of return 8 points above the minimum height
                r9count: Count of return 9 points above the minimum height
                rothercount: Count of other returns above the minimum height
                allcover: (all returns above cover ht) / (total returns)
                afcover: (all returns above cover ht) / (total first returns)
                allcount: number of returns above cover ht
                allabovemean: (all returns above mean ht) / (total returns)
                allabovemode: (all returns above ht mode) / (total returns)
                afabovemean: (all returns above mean ht) / (total first returns)
                afabovemode: (all returns above ht mode) / (total first returns)
                fcountmean: number of first returns above mean ht
                fcountmode: number of first returns above ht mode
                allcountmean: number of returns above mean ht
                allcountmode: number of returns above ht mode
                totalfirst: total number of 1st returns
                totalall: total number of returns
        -------
        additional boolean kwargs available for most FUSION commands include:
        quiet, verbose, newlog, version, locale, nolazsipdll
        -------
        """
        if kwargs['raster']:
            warnings.warn(
            """It is likely that the /raster option will be removed at some
            point. The amount of code required to implement this option is quite
            large and the DTM files produced by the option cannot support
            negative numbers. There are better ways to get individual metrics
            for input into other analyses. For example, you can use the CSV2Grid
            utility to extract specific columns from the .CSV files produced by
            GridMetrics. Use of the /raster option is discouraged.""",
            PendingDeprecationWarning
            )

        cmd = 'gridmetrics'
        params = [groundfile, heightbreak, cellsize, outputfile, datafile]
        self.run(cmd, **kwargs, *params)

    def commandname(self, positional_args, **kwargs):
        """...

        Parameters
        ----------
        ...: type
            description

        **Kwargs (optional), aka "Switches" in FUSION
        --------
        ...: type
            description
        -------
        additional boolean kwargs available for most FUSION commands include:
        quiet, verbose, newlog, version, locale, nolazsipdll
        -------
        """
        cmd = 'commandname'
        params = [positional_args]
        self.run(cmd, **kwargs, *params)
