#-----------------------------------------------------------------------------
# Name:        ProxyGen.py
# Purpose:     Proxy Generation utitities.
#
# Author:      Robert D. Olson, Ivan R. Judson
#
# Created:     2003/08/02
# RCS-ID:      $Id: ProxyGen.py,v 1.3 2004-03-04 21:23:21 olson Exp $
# Copyright:   (c) 2002-2003
# Licence:     See COPYING.txt
#-----------------------------------------------------------------------------

"""
Globus proxy generation.
"""

__revision__ = "$Id: ProxyGen.py,v 1.3 2004-03-04 21:23:21 olson Exp $"
__docformat__ = "restructuredtext en"

import sys
import os
import os.path
import popen2
import logging

from pyGlobus import security, io

#
# Try importing this. We ensure further below that
# we won't try to use it if it wasn't imported.
#

try:
    from pyGlobus import sslutilsc
    haveOldGlobus = 1
except:
    haveOldGlobus = 0

from AccessGrid.Platform import isWindows

log = logging.getLogger("AG.Security.ProxyGen")
log.setLevel(logging.DEBUG)

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

def CreateGlobusProxyGPI(passphrase, certFile, keyFile, certDir, outFile,
                         bits, hours):
    """
    Create a globus proxy.

    certFile - filename of user certificate
    keyFile - filename of user key
    certDir - directory containing trusted CA certificates
    outFile - filename for generated proxy certificate
    bits - keysize of generated proxy certificate
    hours - lifetime (in hours) of generated proxy certificate
    """

    #
    # We are using the commandline grid-proxy-init
    # program with the -pwstdin flag.
    #
    # The other required options to grid-proxy-init are:
    #
    #   -hours <proxy lifetime in hours>
    #   -bits <size of key in bits>
    #   -cert <user cert file>
    #   -key <user key file>
    #   -certdir <trusted cert directory>
    #   -out <proxyfile>
    #

    #
    # Find grid-proxy-init in the globus directory.
    #
    # TODO: this could likely be factored, possibly to Platform,
    # possibly to some other place.
    #

    if sys.platform == "win32":
        exe = "grid-proxy-init.exe"
    else:
        exe = "grid-proxy-init"

    gpiPath = os.path.join(os.environ['GLOBUS_LOCATION'], "bin", exe)

    if not os.access(gpiPath, os.X_OK):
        msg = "grid-proxy-init not found at %s" % (gpiPath)
        log.error(msg)
        raise ProxyRequestError(msg)

    exceptionToRaise = None

    #
    # Rename args, want to make the fn signature match the
    # programmatic one, but don't want to change the code below.
    #

    certPath = certFile
    keyPath = keyFile
    caPath = certDir
    outPath = outFile

    isWindows = sys.platform == "win32"

    #
    # turn on gpi debugging
    #
    debugFlag = "-debug"
    #debugFlag = ""

    cmd = '"%s" %s -pwstdin -bits %s -hours %s -cert "%s" -key "%s" -certdir "%s" -out "%s"'
    cmd = cmd % (gpiPath, debugFlag, bits, hours, certPath, keyPath, caPath, outPath)

    #
    # Windows pipe code needs to have the whole thing quoted. Linux doesn't.
    #

    if isWindows:
        cmd = '"%s"' % (cmd)

    log.debug("Running command: '%s'", cmd)

    try:
        (rd, wr) = popen2.popen4(cmd)


        #
        # There is ugliness here where on Linux, we need to close the
        # write pipe before we try to read. On Windows, we need
        # to leave it open.
        #

        wr.write(passphrase + "\n")

        if not isWindows:
            wr.close()

        while 1:
            l = rd.readline()
            if l == '':
                break

            #
            # Check for errors. The response from grid-proxy-init
            # will look something like this:
            #
            # error:8006940B:lib(128):proxy_init_cred:wrong pass phrase:sslutils.c:3714
            #

            if l.startswith("error"):

                err_elts = l.strip().split(":")
                if len(err_elts) == 7:
                    err_num = err_elts[1]
                    err_str = err_elts[4]

                    if err_str == "wrong pass phrase":
                        exceptionToRaise = InvalidPassphraseException()

                    else:
                        exceptionToRaise = GridProxyInitError("Unknown grid-proxy-init error", l.strip())

                else:
                    exceptionToRaise = GridProxyInitError("Unknown grid-proxy-init error", l.strip())

            log.debug("Proxy returns: %s", l.rstrip())

        rd.close()

        if isWindows:
            wr.close()

    except IOError:
        log.exception("Got an IO error in proxy code, ignoring")
        pass

    if exceptionToRaise is not None:
        raise exceptionToRaise
        
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

def CreateGlobusProxyProgrammatic(passphrase, certFile, keyFile, certDir,
                                  outFile, bits, hours):
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
        # (errcode, libname, func name, reason, additional data, filename,
        # line number) corresponding to the errors in the OpenSSL error
        # queue.
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

if isWindows() and haveOldGlobus:
    CreateGlobusProxy = CreateGlobusProxyProgrammatic
else:
    CreateGlobusProxy = CreateGlobusProxyGPI
    
