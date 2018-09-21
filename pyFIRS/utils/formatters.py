# helper functions for formatting command line arguments

def listlike(arg):
    '''Checks whether an argument is list-like, returns boolean'''
    return not hasattr(arg, "strip") and (hasattr(arg, "__getitem__") or
            hasattr(arg, "__iter__"))

def format_lastools_kws(**kwargs):
    '''Formats keyword arguments for LAStools command line usage.'''
    kws = []
    for key, value in kwargs.items():
        if isinstance(value, bool):
            kws.append('-{}'.format(key))
        elif listlike(value):
            kws.append('-{}'.format(key))
            for arg in value:
                kws.append(str(arg))
        else:
            kws.append('-{}'.format(key))
            kws.append(str(value))
    return kws

def format_fusion_kws(**kwargs):
    '''Formats keyword arguments for FUSION command line usage.'''
    kws = []
    for key, value in kwargs.items():
        # catch and replace kwarg names python doesn't like (class, ascii)
        if key == 'las_class': # can't specify 'class' as a kwarg
            key = 'class'
        if key == 'asc': # can't specify 'ascii' as a kwarg
            key == 'ascii'

        # make sure forward slashes in kwargs are replaced with backslashes
        if type(value) == str:
            value = value.replace('/','\\')

        if isinstance(value, bool):
            kws.append('/{}'.format(key))
        elif listlike(value):
            kws.append('/{}:'.format(key))
            kws.append(','.join(str(x) for x in value))
        else:
            kws.append('/{}:'.format(key))
            kws.append(str(value))
    return kws

def format_fusion_args(arg):
    '''Formats positional arguments for FUSION command line usage'''
    if listlike(arg):
        return " ".join(str(x) for x in arg)
    else:
        return str(arg).replace('/','\\')

def timefmt(seconds):
    '''Formats a time given in seconds in human-readable format.'''
    m, s = divmod(seconds, 60)
    h, m = divmod(m, 60)
    return '{:.0f} hrs, {:.0f} min, {:.1f} sec'.format(h,m,s)

def run_speed(res):
    """Reports time spent processing jobs using ipyparallel.

    Parameters (required)
    ----------
    res: an ipyparallel AsyncResult object
        Produced, for example, when you map a function to a list of inputs,
        as in `res = view.map_async(my_func, inputs)`
    """
    print('Human time spent:', timefmt(res.wall_time))
    print('Computer time spent:', timefmt(res.serial_time))
    print('Parallel speedup:', '{:.2f}x'.format(res.serial_time/res.wall_time))
    print('Human time per job:', '{:.2f} sec'.format(res.wall_time/res.progress))
    print('Computer time per job:', '{:.2f} sec'.format(res.serial_time/res.progress))
