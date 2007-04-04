#-----------------------------------------------------------------------------
# Name:        ProxyGen.py
# Purpose:     Proxy Generation utitities.
# Created:     2003/08/02
# RCS-ID:      $Id: ProxyGen.py,v 1.26 2007-04-04 22:24:58 turam Exp $
# Copyright:   (c) 2002-2003
# Licence:     See COPYING.txt
#-----------------------------------------------------------------------------

"""
Proxy certificate generation.
"""

__revision__ = "$Id: ProxyGen.py,v 1.26 2007-04-04 22:24:58 turam Exp $"

import sys
import os
import os.path
import popen2
import re
import time

from AccessGrid import Log

from M2Crypto import X509
from M2Crypto.RSA import RSAError
import proxylib # lbl proxy generating code


log = Log.GetLogger(Log.ProxyGen)
Log.SetDefaultLevel(Log.ProxyGen, Log.DEBUG)

class ProxyRequestError(Exception):
    """
    Baseclass for proxy generation exceptions.
    """
    pass

class PassphraseRequestCancelled(ProxyRequestError):
    """
    The user cancelled this request.
    """
    pass

class InvalidPassphraseException(ProxyRequestError):
    """
    The user entered an invalid passphrase.
    """
    pass

class GridProxyInitError(ProxyRequestError):
    """
    Some other error has occured. The description is in
    exception.args[0].
    """
    pass

class GridProxyInitUnknownSSLError(ProxyRequestError):
    """
    We've received an exception that don't understand.

    Pass along the SSL error queue as args[0], any
    "certificate:" data as args[1].
    """
    pass

        
#
# Functions defined in the globus sslutils.c.
#
# Used to attempt to decode ssl error messages meaningfully.
#
SslutilsFunctions = """
proxy_genreq
proxy_sign
verify_callback
proxy_marshal_tmp
proxy_init_cred
proxy_local_create
proxy_pw_cb
get_ca_signing_policy_path
proxy_sign_ext
proxy_check_subject_name
proxy_construct_name
ssl_utils_setup_ssl_ctx""".split()

def CreateProxy(passphrase, certFile, keyFile, certDir,
                outFile=None, bits=1024, hours=12, start=0):
    """
    Create a proxy.

    certFile - filename of user certificate
    keyFile - filename of user key
    certDir - directory containing trusted CA certificates
    outFile - filename for generated proxy certificate
    bits - keysize of generated proxy certificate
    hours - lifetime (in hours) of generated proxy certificate
    """

    try:
        kw = {}
        kw['cert'] = certFile
        kw['key'] = keyFile
        kw['valid'] = (hours,0)
        kw['callback'] = passphrase
        kw['full'] = 0
        kw['bits'] = bits
        kw['start'] = long(time.time() - 3600)
        proxy_factory = proxylib.ProxyFactory(kw)
        proxy_factory.generate()
        proxy_cert = proxy_factory.getproxy()
        proxy_cert.write(outFile)


    except RSAError,e:
        reason = e[0]
        if reason == "bad decrypt":
            raise InvalidPassphraseException(reason)
        if reason == "bad password read" or reason == "wrong pass phrase":
            raise InvalidPassphraseException(reason)
    
    except:
        import traceback
        traceback.print_exc()
        raise

# 
# FIXME:  Need to handle exceptions raised by proxylib,
#         may be able to use globus exceptions as a guide
#
#
#     except sslutilsc.SSLException, e:
#         #
#         # The lower-level globus code may fail, raising an SSLException.
#         # The arguments of the exception contain tuples
#         # (errcode, libname, func name, reason, additional data, filename,
#         # line number) corresponding to the errors in the OpenSSL error
#         # queue.
#         #
#         # We translate common errors seen here to higher-level exceptions
#         # where possible. If not possible, an exception is raised with the
#         # error list included.
#         #
# 
#         #for arg in e.args:
#         #   print "arg: ", arg[2], arg[3], arg[4].strip()
# 
#         for arg in e.args:
#             reason = arg[3]
#             data = arg[4].strip()
#             
#             if reason == "bad password read" or reason == "wrong pass phrase":
#                 raise InvalidPassphraseException(reason)
# 
#             elif reason == "problems creating proxy file":
#                 raise GridProxyInitError(reason, data)
# 
#             elif reason == "user private key cannot be accessed":
#                 raise GridProxyInitError(reason, data)
# 
#             elif reason == "user certificate not found":
#                 raise GridProxyInitError(reason, data)
# 
#             elif reason == "user key and certificate don't match":
#                 raise GridProxyInitError(reason, data)
# 
#             elif reason == "cannot find CA certificate for local credential":
#                 data = findCertInArgs(e.args)
#                 raise GridProxyInitError(reason, data)
# 
#             elif reason == "remote certificate has expired":
#                 data = findCertInArgs(e.args)
#                 raise GridProxyInitError(reason, data)
# 
#             elif reason == "could not find CA policy file":
#                 data = findCertInArgs(e.args)
#                 raise GridProxyInitError(reason, data)
#                 
#         #
#         # We didn't find a reason we knew about in the error queue.
#         # Raise a GridProxyInitUnknownSSLError with the error queue.
#         #
# 
#         #
#         # Scan the arguments to see if there's an error from the sslutils.c
#         # module. Also find (and otherwise ignore) a "certificate:" message.
#         #
# 
#         data = ""
#         reason = ""
#         cert = ""
#         for arg in e.args:
#             if arg[3] == "certificate:":
#                 cert = arg[4].strip()
#             elif arg[2] in SslutilsFunctions:
#                 #
#                 # Looks like we found what we're looking for. Raise
#                 # a gpi error.
#                 #
# 
#                 reason = arg[3]
#                 data = arg[4]
# 
#         if reason != "":
#             if cert != "" and data != "":
#                 arg = cert + "\n" + data
#             else:
#                 arg = cert + data
#             raise GridProxyInitError(reason, arg) 
#                 
#         log.exception("grid_proxy_init raised an unknown exception")
# 
#         cert = findCertInArgs(e.args)
#         raise GridProxyInitUnknownSSLError(e.args, cert)
# 

def IsProxyCert(cert):
    try:
        ext = cert.get_ext('proxyCertInfo')
        return 1
    except LookupError:
        pass
    except Exception,e:
        log.exception('Unexpected exception raised while checking whether cert is a proxy cert')

    return 0

def IsProxyFile(certfile):
    """
    From RFC 3820, section 3.8:
    
    If a certificate is a Proxy Certificate, then the proxyCertInfo
    extension MUST be present, and this extension MUST be marked as
    critical.

    If a certificate is not a Proxy Certificate, then the proxyCertInfo
    extension MUST be absent.
    """
    c = X509.load_cert(certfile)
    return IsProxyCert(c)
        
def IsValidProxy(certfile):

    # check whether the file exists
    if not os.path.isfile(certfile):
        return 0
        
    # try to load certificate
    try:
        c = X509.load_cert(certfile)
    except:
        return 0
        
    # check if it's even a proxy cert
    if not IsProxyCert(c):
        return 0
        
    # check if it has expired (or is not yet valid, which is another possibility)
    if c.is_expired():
        return 0
    
    # appears to be ok
    return 1

def findCertInArgs(args):
    """
    Look for the certificate in the rest of the error queue.
    """

    try:
        x = filter(lambda a: a[3] == "certificate:", args)
        if len(x) > 0:
            data = x[0][4].strip()
        else:
            data = ""
    except:
        log.exception("findCertInArgs raised exception")
        data = ""

    return data

    
if '__main__' == __name__:
    proxyFile = 'proxy'
    CreateProxy(None,sys.argv[1],sys.argv[2],
                '',proxyFile,1024,12)
    print IsValidProxy(proxyFile)
                


