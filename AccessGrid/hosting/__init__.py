#-----------------------------------------------------------------------------
# Name:        __init__.py
# Purpose:     
#
# Author:      Ivan R. Judson, Robert D. Olson
#
# Created:     2003/08/02
# RCS-ID:      $Id: __init__.py,v 1.10 2004-03-04 22:40:33 judson Exp $
# Copyright:   (c) 2003
# Licence:     See COPYING.txt
#-----------------------------------------------------------------------------
"""
AG Hosting environment tools.
"""
__revision__ = "$Id: __init__.py,v 1.10 2004-03-04 22:40:33 judson Exp $"
__docformat__ = "restructuredtext en"

# External imports
import os

# mechanisms to support multiple hosting environments and to set defaults
__hostingImpl = "SOAPpy"

# pointers to methods and objects, helpful magic
Server = lambda x: None
InsecureServer = lambda x: None
GetSOAPContext = lambda x: None
Client = lambda x: None
Decorate = lambda x: None
Reconstitute = lambda x: None
__root = lambda x: None

def GetHostingImpl():
    """
    Return the currently selected hosting implementation.

    @return: string
    """
    global __hostingImpl
    return __hostingImpl

def SetHostingImpl(choice):
    """
    Set the hosting implementation to the one specifed.

    @param choice: the hosting implementation to use
    @type choice: string

    @return: 1 if successful, None if not
    """
    global __hostingImpl, __root, Server, Client, Decorate, Reconstitute
    global GetSOAPContext, SecureServer, InsecureServer
    
    __hostingImpl = choice
    
    nis = ".".join([__name__, __hostingImpl, "Server"])
    nic = ".".join([__name__, __hostingImpl])
    nit = ".".join([__name__, __hostingImpl, "Tools"])

    try:
        s = __import__(nis, globals(), locals(), ["SecureServer",
                                                  "InsecureServer",
                                                  "GetSOAPContext"])
        Server = s.SecureServer
        InsecureServer = s.InsecureServer
        GetSOAPContext = s.GetSOAPContext
    except ImportError:
        raise
    
    try:
        c = __import__(nic, globals(), locals(), ["Client"])
        Client = c.Client
    except ImportError:
        raise

    try:
        t = __import__(nit, globals(), locals(), ["Decorate",
                                                  "Reconstitute"])
        Decorate = t.Decorate
        Reconstitute = t.Reconstitute
    except ImportError:
        raise
    
    return 1

def ListHostingImpls():
    """
    This method lists the hosting implementations currently isntalled.

    @return: a list of hosting implementation names.
    """
    global __root
    retList = list()
    for e in os.listdir(__root):
        ae = os.path.join(__root, e)
        if os.path.isdir(ae):
            # Just in case we're using dev source
            if e != 'CVS':
                retList.append(e)
    return retList

# Set the default
SetHostingImpl(__hostingImpl)

