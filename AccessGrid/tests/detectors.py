# -*- Mode: Python; tab-width: 4 -*-

import sys
import types
import gc

def get_refcounts():
    """
    get reference counts from sys.modules.
    """
    d = {}
    sys.modules
    # collect all classes
    for m in sys.modules.values():
        for sym in dir(m):
            o = getattr (m, sym)
            if type(o) is types.ClassType:
                d[o] = sys.getrefcount (o)
    # sort by refcount
    pairs = map (lambda x: (x[1],x[0]), d.items())
    pairs.sort()
    pairs.reverse()
    return pairs

def print_top_N(n):
    """
    print out the top N reference counts from sys.modules.
    """
    for n, c in get_refcounts()[:n]:
        print '%10d %s' % (n, c.__name__)

def gc_histo(hist=None, typeList=None):
    """
    create a histogram from objects in the garbage
    """
    obj_dict = dict()
    obj_list = gc.get_objects()
    if hist == None:
        hist = dict()
    for o in obj_list:
        t = type(o)
        if t in typeList:
            if hist.has_key(t):
                hist[t] = hist[t] + 1
            else:
                hist[t] = 1
            if obj_dict.has_key(t):
                obj_dict[t].append(o)
            else:
                obj_dict[t] = [o]

    obj_list = None
    
    return obj_dict, hist
