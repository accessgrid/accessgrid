#-----------------------------------------------------------------------------
# Name:        __init__.py
# Purpose:     
#
# Author:      Ivan R. Judson, Robert D. Olson
#
# Created:     2003/08/02
# RCS-ID:      $Id: __init__.py,v 1.8 2004-03-01 20:03:37 turam Exp $
# Copyright:   (c) 2003
# Licence:     See COPYING.txt
#-----------------------------------------------------------------------------
"""
AG Hosting environment tools.
"""
__revision__ = "$Id: __init__.py,v 1.8 2004-03-01 20:03:37 turam Exp $"
__docformat__ = "restructuredtext en"

import os

# mechanisms to support multiple hosting environments and to set defaults
__hostingImpl = "SOAPpy"

def GetHostingImpl():
    global __hostingImpl
    return __hostingImpl

def SetHostingImpl(choice):
    global __hostingImpl, __root, Server, Client, Decorate, Reconstitute
    global IWrapper, GetSOAPContext, SecureServer, InsecureServer
    
    __hostingImpl = choice
    
    nis = ".".join([__name__, __hostingImpl, "Server"])
    nic = ".".join([__name__, __hostingImpl])
    nit = ".".join([__name__, __hostingImpl, "Tools"])

    try:
        s = __import__(nis, globals(), locals(), ["SecureServer",
                                                  "InsecureServer",
                                                  "GetSOAPContext"])
        Server = getattr(s,"SecureServer")
        InsecureServer = getattr(s,"InsecureServer")
        GetSOAPContext = getattr(s,"GetSOAPContext")
    except ImportError: 
        raise
    try:
        c = __import__(nic, globals(), locals(), ["Client"])
        Client = getattr(c, "Client")
    except ImportError:
        raise
    try:
        t = __import__(nit, globals(), locals(), ["Decorate",
                                                  "Reconstitute",
                                                  "IWrapper"])
        Decorate = getattr(t, "Decorate")
        Reconstitute = getattr(t, "Reconstitute")
        IWrapper = getattr(t, "IWrapper")
    except ImportError:
        raise
    
    return 1

def ListHostingImpls():
    global __root
    retList = list()
    for e in os.listdir(__root):
        ae = os.path.join(__root, e)
        if os.path.isdir(ae):
            # Just in case we're using dev source
            if e != 'CVS':
                retList.append(e)
    return retList

SetHostingImpl(__hostingImpl)

# Hostname glue
from AccessGrid.NetUtilities import GetHostname

