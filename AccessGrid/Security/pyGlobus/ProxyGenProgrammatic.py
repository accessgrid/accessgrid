#-----------------------------------------------------------------------------
# Name:        ProxyGenProgrammatic.py
# Purpose:     Generate certificate proxies programmatically.
#
# Author:      Robert D. Olson
#
# Created:     2003/08/02
# RCS-ID:      $Id: ProxyGenProgrammatic.py,v 1.3 2004-02-24 21:57:24 judson Exp $
# Copyright:   (c) 2002-2003
# Licence:     See COPYING.txt
#-----------------------------------------------------------------------------
"""
Globus proxy generation using the programmatic method. We can currently (circa AGTk
2.1) do this on windows only.

"""

__revision__ = "$Id: ProxyGenProgrammatic.py,v 1.3 2004-02-24 21:57:24 judson Exp $"
__docformat__ = "restructuredtext en"

import logging

log = logging.getLogger("AG.hosting.pyGlobus.ProxyGenProgrammatic")

from AccessGrid.Security.pyGlobus import ProxyGenExceptions
from pyGlobus import security, sslutilsc


#
# Enable SSL exceptions from Globus.
#

security.RaiseExceptions = 1

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

    try:
        security.grid_proxy_init(verbose = 1,
                                 certDir = certDir,
                                 certFile = certFile,
                                 keyFile = keyFile,
                                 outFile = outFile,
                                 bits = bits,
                                 hours = hours,
                                 passphraseString = passphrase)

    except sslutilsc.SSLException, e:
        #
        # The lower-level globus code may fail, raising an SSLException.
        # The arguments of the exception contain tuples
        # (errcode, libname, func name, reason, additional data, filename, line number)
        # corresponding to the errors in the OpenSSL error queue.
        #
        # We translate common errors seen here to higher-level exceptions
        # where possible. If not possible, an exception is raised with the
        # error list included.
        #

        for arg in e.args:
            print "arg: ", arg[2], arg[3], arg[4].strip()

        for arg in e.args:
            reason = arg[3]
            data = arg[4].strip()
            
            if reason == "bad password read" or reason == "wrong pass phrase":
                raise ProxyGenExceptions.InvalidPassphraseException(reason)

            elif reason == "problems creating proxy file":
                raise ProxyGenExceptions.GridProxyInitError(reason, data)

            elif reason == "user private key cannot be accessed":
                raise ProxyGenExceptions.GridProxyInitError(reason, data)

            elif reason == "user certificate not found":
                raise ProxyGenExceptions.GridProxyInitError(reason, data)

            elif reason == "user key and certificate don't match":
                raise ProxyGenExceptions.GridProxyInitError(reason, data)

            elif reason == "cannot find CA certificate for local credential":
                data = findCertInArgs(e.args)
                raise ProxyGenExceptions.GridProxyInitError(reason, data)

            elif reason == "remote certificate has expired":
                data = findCertInArgs(e.args)
                raise ProxyGenExceptions.GridProxyInitError(reason, data)

            elif reason == "could not find CA policy file":
                data = findCertInArgs(e.args)
                raise ProxyGenExceptions.GridProxyInitError(reason, data)
                

        #
        # We didn't find a reason we knew about in the error queue.
        # Raise a GridProxyInitUnknownSSLError with the error queue.
        #

        #
        # Scan the arguments to see if there's an error from the sslutils.c
        # module. Also find (and otherwise ignore) a "certificate:" message.
        #

        data = ""
        reason = ""
        cert = ""
        for arg in e.args:
            print "Try ", arg[2]
            if arg[3] == "certificate:":
                cert = arg[4].strip()
            elif arg[2] in SslutilsFunctions:
                #
                # Looks like we found what we're looking for. Raise
                # a gpi error.
                #

                print "Found it"
                reason = arg[3]
                data = arg[4]

        if reason != "":
            if cert != "" and data != "":
                arg = cert + "\n" + data
            else:
                arg = cert + data
            raise ProxyGenExceptions.GridProxyInitError(reason, arg) 
                
        log.exception("grid_proxy_init raised an unknown exception")

        cert = findCertInArgs(e.args)
        raise ProxyGenExceptions.GridProxyInitUnknownSSLError(e.args, cert)
    

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
