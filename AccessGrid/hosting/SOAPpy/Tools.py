#-----------------------------------------------------------------------------
# Name:        Tools.py
# Purpose:     
#
# Author:      Ivan R. Judson
#
# Created:     2003/08/02
# RCS-ID:      $Id: Tools.py,v 1.9 2004-04-06 18:06:44 eolson Exp $
# Copyright:   (c) 2002-2003
# Licence:     See COPYING.txt
#-----------------------------------------------------------------------------
"""
SOAPpy tools for making life easier.

This module defines methods for making serialization and other things simpler
when using the SOAPpy module.
"""

__revision__ = "$Id: Tools.py,v 1.9 2004-04-06 18:06:44 eolson Exp $"

# External imports
import sys
import types

def Decorate(obj):
    """
    This method traverses a object hierarchy rooted at object. It tags each
    object with an attribute ag_class with the class this is. This makes it
    possible to rebuild these classes on the other side of a SOAP call.

    @param obj: an object to annotate
    @type obj: a python object

    @returns: obj with annotations
    """
    if type(obj) == types.TupleType:
        res = map(lambda x: Decorate(x), obj)
        retval = tuple(res)
    elif type(obj) == types.ListType:
        for i in range(0, len(obj)):
            obj[i] = Decorate(obj[i])
        retval = obj
    elif type(obj) == types.DictType:
        for k,v in obj.items():
            obj[k] = Decorate(v)
        retval = obj
    if type(obj) == types.InstanceType:
        cp = ".".join([obj.__class__.__module__, obj.__class__.__name__])
        obj.ag_class = cp
        for k in obj.__dict__.keys():
            setattr(obj, k, Decorate(obj.__dict__[k]))
        retval = obj
    else:
        retval = obj

    return retval

# External imports
from SOAPpy.Types import structType, typedArrayType, arrayType
from types import DictType

def Reconstitute(obj):
    """
    This method takes an object that has been sent across the network
    via SOAPpy and rebuilds a real python object from it.

    @param obj: an annotated object from the network
    @type obj: SOAPpy typed object

    @return: a native python object.
    """
    if isinstance(obj, structType):
        if hasattr(obj, "ag_class"):
            k = obj.ag_class
            # Not optimal, but for now, don't delete "ag_class" attribute
            #  in case this struct is referenced more than once.
            # delattr(obj, "ag_class")
            f = CreateBlank(k)
            for ok in obj._keys():
                setattr(f, ok, Reconstitute(obj[ok]))
        else:
            f = obj
    elif isinstance(obj, DictType):
        if obj.has_key("ag_class"):
            k = obj["ag_class"]
            del obj["ag_class"]
            f = CreateBlank(k)
            for ok in obj.keys():
                setattr(f, ok, Reconstitute(obj[ok]))
        else:
            f = obj
            for ok in obj.keys():
                f[ok] = Reconstitute(obj[ok])
    elif isinstance(obj, typedArrayType):
        f = list()
        for o in obj:
            f.append(Reconstitute(o))
    elif isinstance(obj, arrayType):
        f = list()
        for o in obj:
            f.append(Reconstitute(o))
    else:
        f = obj

#     if isinstance(f, structType):
#         print f
#         raise "HELLIFIKNOW"
# 

    return f

def CreateBlank(p):
    """
    This is a utility method to create an object of a specified class.

    @param p: the module/class name
    @type p: string

    @return: a python object of class p
    """
    parts = p.split('.')
    name = parts[-1]
    parts.remove(parts[-1])
    module = ".".join(parts)
    __import__(module)
    mod = sys.modules[module]
    klass = getattr(mod, name)
    r = _a()
    r.__class__ = klass
    return r

class _a:
    """
    a dummy class we use to create an object, then set it's class.
    """
    pass
