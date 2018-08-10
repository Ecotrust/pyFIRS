# LAStools wrappers

class useLAStools(object):
    "A class for executing LAStools functions as methods"
    os = __import__('os')
    subprocess = __import__('subprocess')

    def __init__(self,src):
        "Initialize with a path to the LAStools executables"
        self.src = src

    def test_run(self, input):
        print(str(input))

    def run(self, cmd, *args, **kwargs):
        "A helper function to execute a LAStools command using subprocess"
        args = ['-{}'.format(arg) for arg in args]
        kws = [('-{} '.format(key), str(value)) for (key, value) in kwargs.items()]
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
        "http://www.cs.unc.edu/~isenburg/laszip/download/lasview_README.txt"
        cmd = 'lasview'
        self.run(cmd, *args, **kwargs)

    def lasinfo(self, *args, **kwargs):
        "http://www.cs.unc.edu/~isenburg/laszip/download/lasinfo_README.txt"
        cmd = 'lasinfo'
        self.run(cmd, *args, **kwargs)

    def lasground(self, *args, **kwargs):
        "http://www.cs.unc.edu/~isenburg/laszip/download/lasground_README.txt"
        cmd = 'lasground'
        self.run(cmd, *args, **kwargs)

    def lasclassify(self, *args, **kwargs):
        "http://www.cs.unc.edu/~isenburg/laszip/download/lasclassify_README.txt"
        cmd = 'lasclassify'
        self.run(cmd, *args, **kwargs)

    def las2dem(self, *args, **kwargs):
        "http://www.cs.unc.edu/~isenburg/laszip/download/las2dem_README.txt"
        cmd = 'las2dem'
        self.run(cmd, *args, **kwargs)

    def las2iso(self, *args, **kwargs):
        "http://www.cs.unc.edu/~isenburg/laszip/download/las2iso_README.txt"
        cmd = 'las2iso'
        self.run(cmd, *args, **kwargs)

    def lascolor(self, *args, **kwargs):
        "http://www.cs.unc.edu/~isenburg/laszip/download/lascolor_README.txt"
        cmd = 'lascolor'
        self.run(cmd, *args, **kwargs)

    def lasgrid(self, *args, **kwargs):
        "http://www.cs.unc.edu/~isenburg/laszip/download/lasgrid_README.txt"
        cmd = 'lasgrid'
        self.run(cmd, *args, **kwargs)

    def lasoverlap(self, *args, **kwargs):
        "http://www.cs.unc.edu/~isenburg/laszip/download/lasoverlap_README.txt"
        cmd = 'lasoverlap'
        self.run(cmd, *args, **kwargs)

    def lasoverage(self, *args, **kwargs):
        "http://www.cs.unc.edu/~isenburg/laszip/download/lasoverage_README.txt"
        cmd = 'lasoverage'
        self.run(cmd, *args, **kwargs)

    def lasboundary(self, *args, **kwargs):
        "http://www.cs.unc.edu/~isenburg/laszip/download/lasboundary_README.txt"
        cmd = 'lasboundary'
        self.run(cmd, *args, **kwargs)

    def lasclip(self, *args, **kwargs):
        "http://www.cs.unc.edu/~isenburg/laszip/download/lasclip_README.txt"
        cmd = 'lasclip'
        self.run(cmd, *args, **kwargs)

    def lasheight(self, *args, **kwargs):
        "http://www.cs.unc.edu/~isenburg/laszip/download/lasheight_README.txt"
        cmd = 'lasheight'
        self.run(cmd, *args, **kwargs)

    def lastrack(self, *args, **kwargs):
        "http://www.cs.unc.edu/~isenburg/laszip/download/lastrack_README.txt"
        cmd = 'lastrack'
        self.run(cmd, *args, **kwargs)

    def lascanopy(self, *args, **kwargs):
        "http://www.cs.unc.edu/~isenburg/laszip/download/lascanopy_README.txt"
        cmd = 'lascanopy'
        self.run(cmd, *args, **kwargs)

    def lasthin(self, *args, **kwargs):
        "http://www.cs.unc.edu/~isenburg/laszip/download/lasthin_README.txt"
        cmd = 'lasthin'
        self.run(cmd, *args, **kwargs)

    def lassort(self, *args, **kwargs):
        "http://www.cs.unc.edu/~isenburg/laszip/download/lassort_README.txt"
        cmd = 'lassort'
        self.run(cmd, *args, **kwargs)

    def lasduplicate(self, *args, **kwargs):
        "http://www.cs.unc.edu/~isenburg/laszip/download/lassort_README.txt"
        cmd = 'lasduplicate'
        self.run(cmd, *args, **kwargs)

    def lascontrol(self, *args, **kwargs):
        "http://www.cs.unc.edu/~isenburg/laszip/download/lascontrol_README.txt"
        cmd = 'lascontrol'
        self.run(cmd, *args, **kwargs)

    def lastile(self, *args, **kwargs):
        "http://www.cs.unc.edu/~isenburg/laszip/download/lastile_README.txt"
        cmd = 'lastile'
        self.run(cmd, *args, **kwargs)

    def lassplit(self, *args, **kwargs):
        "http://www.cs.unc.edu/~isenburg/laszip/download/lassplit_README.txt"
        cmd = 'lassplit'
        self.run(cmd, *args, **kwargs)

    def txt2las(self, *args, **kwargs):
        "http://www.cs.unc.edu/~isenburg/laszip/download/txt2las_README.txt"
        cmd = 'txt2las'
        self.run(cmd, *args, **kwargs)

    def blast2dem(self, *args, **kwargs):
        "http://www.cs.unc.edu/~isenburg/laszip/download/blast2dem_README.txt"
        cmd = 'blast2dem'
        self.run(cmd, *args, **kwargs)

    def blast2iso(self, *args, **kwargs):
        "http://www.cs.unc.edu/~isenburg/laszip/download/blast2iso_README.txt"
        cmd = 'blast2iso'
        self.run(cmd, *args, **kwargs)

    def las2las(self, *args, **kwargs):
        "http://www.cs.unc.edu/~isenburg/laszip/download/las2las_README.txt"
        cmd = 'las2las'
        self.run(cmd, *args, **kwargs)

    def las2shp(self, *args, **kwargs):
        "http://www.cs.unc.edu/~isenburg/laszip/download/las2shp_README.txt"
        cmd = 'las2shp'
        self.run(cmd, *args, **kwargs)

    def las2tin(self, *args, **kwargs):
        "http://www.cs.unc.edu/~isenburg/laszip/download/las2tin_README.txt"
        cmd = 'las2shp'
        self.run(cmd, *args, **kwargs)

    def lasvoxel(self, *args, **kwargs):
        "http://www.cs.unc.edu/~isenburg/laszip/download/lasvoxel_README.txt"
        cmd = 'lasvoxel'
        self.run(cmd, *args, **kwargs)

    def lasreturn(self, *args, **kwargs):
        "http://www.cs.unc.edu/~isenburg/laszip/download/lasreturn_README.txt"
        cmd = 'lasreturn'
        self.run(cmd, *args, **kwargs)

    def laszip(self, *args, **kwargs):
        "http://www.cs.unc.edu/~isenburg/laszip/download/laszip_README.txt"
        cmd = 'laszip'
        self.run(cmd, *args, **kwargs)

    def lasindex(self, *args, **kwargs):
        "http://www.cs.unc.edu/~isenburg/laszip/download/lasindex_README.txt"
        cmd = 'lasindex'
        self.run(cmd, *args, **kwargs)
