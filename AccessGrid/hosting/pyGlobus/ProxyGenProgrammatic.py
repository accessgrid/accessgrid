#-----------------------------------------------------------------------------
# Name:        ProxyGenProgrammatic.py
# Purpose:     Generate certificate proxies programmatically.
#
# Author:      Robert D. Olson
#
# Created:     2003/08/02
# RCS-ID:      $Id: ProxyGenProgrammatic.py,v 1.4 2003-09-16 07:20:56 judson Exp $
# Copyright:   (c) 2002-2003
# Licence:     See COPYING.txt
#-----------------------------------------------------------------------------
"""
Globus proxy generation using the programmatic method. We can currently (circa AGTk
2.1) do this on windows only.

"""

__revision__ = "$Id: ProxyGenProgrammatic.py,v 1.4 2003-09-16 07:20:56 judson Exp $"
__docformat__ = "restructuredtext en"

from pyGlobus import security

def CreateGlobusProxy(passphrase, certFile, keyFile, certDir, outFile, bits, hours):
    """
    Create a globus proxy.

    certFile - filename of user certificate
    keyFile - filename of user key
    certDir - directory containing trusted CA certificates
    outFile - filename for generated proxy certificate
    bits - keysize of generated proxy certificate
    hours - lifetime (in hours) of generated proxy certificate
    """

    security.grid_proxy_init(verbose = 1,
                              certDir = certDir,
                              certFile = certFile,
                              keyFile = keyFile,
                              outFile = outFile,
                              bits = bits,
                              hours = hours,
                              passphraseString = passphrase)
    
