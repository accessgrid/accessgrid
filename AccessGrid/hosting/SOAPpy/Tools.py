#-----------------------------------------------------------------------------
# Name:        Tools.py
# Purpose:     
#
# Author:      Ivan R. Judson
#
# Created:     2003/08/02
# RCS-ID:      $Id: Tools.py,v 1.4 2004-02-27 19:16:58 judson Exp $
# Copyright:   (c) 2002-2003
# Licence:     See COPYING.txt
#-----------------------------------------------------------------------------
"""
SOAPpy tools for making life easier.

This module defines methods for making serialization and other things simpler
when using the SOAPpy module.
"""

__revision__ = "$Id: Tools.py,v 1.4 2004-02-27 19:16:58 judson Exp $"
__docformat__ = "restructuredtext en"

import sys
import types

from AccessGrid.hosting.SOAPpy import Client

class InvalidURL(Exception):
    pass

class ConnectionFailed(Exception):
    pass

class IWrapper:
    def __init__(self, url=None):
        self.proxy = None
        self.url = url
        if url != None:
            try:
                self.proxy = Client.Handle(self.url).GetProxy()
            except Exception, e:
                self.proxy = None
                print "Exception connecting authorization client: ", e
                raise ConnectionFailed
        else:
            raise InvalidURL

    def IsValid(self):
        return self.proxy.IsValid()
    
def Decorate(obj):
    """
    This method traverses a object hierarchy rooted at object. It tags each
    object with an attribute ag_class with the class this is. This makes it
    possible to rebuild these classes on the other side of a SOAP call.
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
        setattr(obj, "ag_class", cp)
        for k in obj.__dict__.keys():
            setattr(obj, k, Decorate(obj.__dict__[k]))
        retval = obj
    else:
        retval = obj

    print "TOM LOVES THIS"
    print retval
    print "IVAN DOESN'T"
    
    return retval
    
from SOAPpy.Types import structType, typedArrayType, arrayType
    
def Reconstitute(obj):
    """
    """
    if isinstance(obj, structType):
        if hasattr(obj, "ag_class"):
            k = obj.ag_class
            delattr(obj, "ag_class")
            f = CreateBlank(k)
            for ok in obj._keys():
                setattr(f, ok, Reconstitute(obj[ok]))
        else:
            f = obj
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

    if isinstance(f, structType):
        print f
        raise "HELLIFIKNOW"

    return f

def CreateBlank(p):
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
    pass
