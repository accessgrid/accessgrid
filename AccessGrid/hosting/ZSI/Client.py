#-----------------------------------------------------------------------------
# Name:        Client.py
# Purpose:     
# Created:     2003/08/02
# RCS-ID:      $Id: Client.py,v 1.1 2005-01-31 19:02:27 judson Exp $
# Copyright:   (c) 2002-2003
# Licence:     See COPYING.txt
#-----------------------------------------------------------------------------
"""
ZSI client wrapper
"""

__revision__ = "$Id: Client.py,v 1.1 2005-01-31 19:02:27 judson Exp $"

class _Handle:
    """
    A class that encapsulates a SOAP proxy.
    """
    def __init__(self, url, namespace = None, authCallback = None, debug = 0,
                 config = None, faultHandler = None):
        """
        @param url: the url to the service
        @param namespace: the namespace for the service
        @param authCallback: LEGACY
        @param debug: a debugging flag
        @type url: string
        @type namespace: string
        @type authCallback: python method
        @type debug: 0 or 1
        """
        if config == None:
            self.config = SOAPConfig(debug = debug)
        else:
            self.config = config
            
        self.config.debug = debug
        self.config.faultHandler = faultHandler
        print "URL: ", url
        self.url = url.replace('https', 'http')
        self.proxy = None
        self.namespace = namespace
        self.authCallback = authCallback
        self.proxy = SOAPProxy(self.url, self.namespace, config = self.config)

    def GetURL(self):
        """
        This method accesses the url for the service.

        @return: a string of the URL
        """
        return self.url

    def GetProxy(self):
        """
        This method accesses the internal proxy object.

        @return: a SOAPPy.SOAPProxy object.
        """
        return self.proxy

    def __repr__(self):
        """
        This method makes a human readable form of the Hanle object.

        @returns: a string of the URL
        """
        return self.url

class InsecureHandle(_Handle):
    pass

class SecureHandle(_Handle):
    """
    A class that encapsulates a SOAP proxy.
    """
    pass
