#-----------------------------------------------------------------------------
# Name:        Client.py
# Purpose:     
#
# Author:      Robert D. Olson, Ivan R. Judson
#
# Created:     2003/08/02
# RCS-ID:      $Id: Client.py,v 1.4 2004-02-27 22:38:21 judson Exp $
# Copyright:   (c) 2002-2003
# Licence:     See COPYING.txt
#-----------------------------------------------------------------------------
"""
SOAPpy client wrapper

This module provides a helper class Client that wraps
the creation of the SOAP server proxy.
"""

__revision__ = "$Id: Client.py,v 1.4 2004-02-27 22:38:21 judson Exp $"
__docformat__ = "restructuredtext en"

from SOAPpy import SOAPProxy
from SOAPpy.GSIServer import GSIConfig

import urllib

class Handle:
    def __init__(self, url, namespace = None, authCallback = None, debug = 0,
                 config = None):
        if config == None:
            self.config = GSIConfig()
        else:
            self.config = config
            
        self.config.debug = debug
        self.config.simplify_objects = 1
        self.url = url.replace("https", "httpg")
        self.proxy = None
        self.namespace = namespace
        self.authCallback = authCallback
        self.proxy = SOAPProxy(self.url, self.namespace, config = self.config)

    def GetURL(self):
        return self.url

    def GetProxy(self):
        return self.proxy

    def __repr__(self):
        return self.url

