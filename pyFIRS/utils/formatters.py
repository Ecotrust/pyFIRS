# helper functions for formatting command line arguments

def listlike(arg):
    '''Checks whether an argument is list-like, returns boolean'''
    return not hasattr(arg, "strip") and (hasattr(arg, "__getitem__") or
            hasattr(arg, "__iter__"))

def format_lastools_kws(arg):
    '''Formats keyword arguments for LAStools command line usage'''
    if isinstance(arg, bool):
        return ''
    elif listlike(arg):
        return ' '.join(str(x) for x in arg)
    else:
        return str(arg)

def format_fusion_kws(arg):
    '''Formats keyword arguments for FUSION command line usage'''
    if isinstance(arg, bool):
        return ''
    elif listlike(arg):
        return ':'+",".join(str(x) for x in arg)
    else:
        return ':' + str(arg)

def format_fusion_args(arg):
    '''Formats positional arguments for FUSION command line usage'''
    if listlike(arg):
        return " ".join(str(x) for x in arg)
    else:
        return str(arg)
