#-----------------------------------------------------------------------------
# Name:        Tools.py
# Purpose:     
#
# Author:      Ivan R. Judson
#
# Created:     2003/08/02
# RCS-ID:      $Id: Tools.py,v 1.2 2004-02-24 21:30:51 judson Exp $
# Copyright:   (c) 2002-2003
# Licence:     See COPYING.txt
#-----------------------------------------------------------------------------
"""
SOAPpy tools for making life easier.

This module defines methods for making serialization and other things simpler
when using the SOAPpy module.
"""

__revision__ = "$Id: Tools.py,v 1.2 2004-02-24 21:30:51 judson Exp $"
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
    
def Decorate(object):
    """
    This method traverses a object hierarchy rooted at object. It tags each
    object with an attribute ag_class with the class this is. This makes it
    possible to rebuild these classes on the other side of a SOAP call.
    """
    if type(object) == types.TupleType or type(object) == types.ListType:
        for i in range(0, len(object)):
            object[i] = Decorate(object[i])
        return object
    elif type(object) == types.DictType:
        for k,v in object.items():
            object[k] = Decorate(v)
        return object
    if type(object) == types.InstanceType:
        cp = ".".join([object.__class__.__module__, object.__class__.__name__])
        setattr(object, "ag_class", cp)
        for k in object.__dict__.keys():
            setattr(object, k, Decorate(object.__dict__[k]))
        return object
    else:
        return object

from SOAPpy.Types import structType, typedArrayType
    
def Reconstitute(object):
    """
    """
    if isinstance(object, structType):
        if hasattr(object, "ag_class"):
            k = object.ag_class
            delattr(object, "ag_class")
            c = CreateBlank(k)
            for ok in object._keys():
                setattr(c, ok, Reconstitute(object[ok]))
            return c
        else:
            return object
    elif isinstance(object, typedArrayType):
        f = list()
        for o in object:
            f.append(Reconstitute(o))
        return f
    else:
        return object

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
