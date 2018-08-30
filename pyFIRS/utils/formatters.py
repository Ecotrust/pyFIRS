# helper functions for formatting command line arguments

def listlike(arg):
    '''Checks whether an argument is list-like, returns boolean'''
    return not hasattr(arg, "strip") and (hasattr(arg, "__getitem__") or
            hasattr(arg, "__iter__"))

def format_lastools_kws(**kwargs):
    '''Formats keyword arguments for LAStools command line usage'''
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
    '''Formats keyword arguments for FUSION command line usage'''
    kws = []
    for key, value in kwargs.items():
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
        return str(arg)
