
"""
Globus proxy generation using external grid_proxy_init.

"""

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

    raise NotImplementedError
