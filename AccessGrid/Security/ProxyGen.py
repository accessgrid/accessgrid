#-----------------------------------------------------------------------------
# Name:        ProxyGen.py
# Purpose:     Proxy Generation utitities.
#
# Author:      Robert D. Olson, Ivan R. Judson
#
# Created:     2003/08/02
# RCS-ID:      $Id: ProxyGen.py,v 1.10 2004-03-17 16:45:46 olson Exp $
# Copyright:   (c) 2002-2003
# Licence:     See COPYING.txt
#-----------------------------------------------------------------------------

"""
Globus proxy generation.
"""

__revision__ = "$Id: ProxyGen.py,v 1.10 2004-03-17 16:45:46 olson Exp $"
__docformat__ = "restructuredtext en"

import sys
import os
import os.path
import popen2
import re

from pyGlobus import security, io

from AccessGrid import Log
from AccessGrid import Platform

#
# Try importing this. We ensure further below that
# we won't try to use it if it wasn't imported.
#

try:
    from pyGlobus import sslutilsc
    haveOldGlobus = 1
except:
    haveOldGlobus = 0


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

    #
    # turn on gpi debugging
    #
    debugFlag = "-debug"

    cmd = '"%s" %s -pwstdin -bits %s -hours %s -cert "%s" -key "%s" -certdir "%s" -out "%s"'
    cmd = cmd % (gpiPath, debugFlag, bits, hours, certPath, keyPath, caPath, outPath)

    #
    # Windows pipe code needs to have the whole thing quoted. Linux doesn't.
    #

    if Platform.isWindows():
        cmd = '"%s"' % (cmd)

    log.debug("Running command: '%s'", cmd)

    try:
        (rd, wr) = popen2.popen4(cmd)


        #
        # There is ugliness here where on Linux, we need to close the
        # write pipe before we try to read. On Windows, we need
        # to leave it open.
        #

        #
        # Convert from list-of-numbers to a string.
        #
        # Replace this when pyOpenSSL fixed to understand lists.
        #

        if type(passphrase[0]) == int:
            passphrase = "".join(map(lambda a: chr(a), passphrase))
        else:
            passphrase = "".join(passphrase)

        wr.write(passphrase + "\n")

        if not Platform.isWindows():
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

        if Platform.isWindows():
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

    #
    # Convert from list-of-numbers to a string.
    #
    # Replace this when pyOpenSSL fixed to understand lists.
    #

    if type(passphrase[0]) == int:
        passphrase = "".join(map(lambda a: chr(a), passphrase))
    else:
        passphrase = "".join(passphrase)

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
                raise InvalidPassphraseException(reason)

            elif reason == "problems creating proxy file":
                raise GridProxyInitError(reason, data)

            elif reason == "user private key cannot be accessed":
                raise GridProxyInitError(reason, data)

            elif reason == "user certificate not found":
                raise GridProxyInitError(reason, data)

            elif reason == "user key and certificate don't match":
                raise GridProxyInitError(reason, data)

            elif reason == "cannot find CA certificate for local credential":
                data = findCertInArgs(e.args)
                raise GridProxyInitError(reason, data)

            elif reason == "remote certificate has expired":
                data = findCertInArgs(e.args)
                raise GridProxyInitError(reason, data)

            elif reason == "could not find CA policy file":
                data = findCertInArgs(e.args)
                raise GridProxyInitError(reason, data)
                
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
            raise GridProxyInitError(reason, arg) 
                
        log.exception("grid_proxy_init raised an unknown exception")

        cert = findCertInArgs(e.args)
        raise GridProxyInitUnknownSSLError(e.args, cert)
    

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

def CreateGlobusProxyProgrammatic_GT24(passphrase, certFile, keyFile, certDir,
                                       outFile, bits, hours):
    """
    Create a globus proxy, GT2.4 version.

    certFile - filename of user certificate
    keyFile - filename of user key
    certDir - directory containing trusted CA certificates
    outFile - filename for generated proxy certificate
    bits - keysize of generated proxy certificate
    hours - lifetime (in hours) of generated proxy certificate

    Errors we might see:

    bad password:

    pyGlobus.security.GSIException: globus_gsi_credential.c:1092: globus_gsi_cred_read_key: Error reading user credential: Can't read credential's private key from PEM

    Missing CA cert or expired cert. Would be nice to be able to differentiate these.

    pyGlobus.security.GSIException: globus_gsi_cred_handle.c:1518: globus_gsi_cred_verify_proxy_cert_chain: Error verifying credential: Failed to verify credential


    The corresponding error messages from grid-proxy-init from globus are as follows. Missing ca cert:

    grid_proxy_init.c:947:
    globus_gsi_cred_handle.c:1518: globus_gsi_cred_verify_proxy_cert_chain: Error verifying credential: Failed to verify credential
    OpenSSL Error: (null):0: in library: (null), function (null): (null)
    globus_gsi_callback.c:283: globus_i_gsi_callback_create_proxy_callback: Could not verify credential
    globus_gsi_callback.c:443: globus_i_gsi_callback_cred_verify: Could not verify credential: unable to get issuer certificate

    Expired cert:

    grid_proxy_init.c:947:
    globus_gsi_cred_handle.c:1518: globus_gsi_cred_verify_proxy_cert_chain: Error verifying credential: Failed to verify credential
    OpenSSL Error: (null):0: in library: (null), function (null): (null)
    globus_gsi_callback.c:283: globus_i_gsi_callback_create_proxy_callback: Could not verify credential
    globus_gsi_callback.c:436: globus_i_gsi_callback_cred_verify: The certificate has expired: Credential with subject: /C=US/O=Globus/CN=Globus Certification Authority has expired.


    Missing signing policy:

    globus_gsi_cred_handle.c:1518: globus_gsi_cred_verify_proxy_cert_chain: Error verifying credential: Failed to verify credential
    OpenSSL Error: (null):0: in library: (null), function (null): (null)
    globus_gsi_callback.c:283: globus_i_gsi_callback_create_proxy_callback: Could not verify credential
    globus_gsi_callback.c:490: globus_i_gsi_callback_cred_verify: Could not verify credential
    globus_gsi_callback.c:850: globus_i_gsi_callback_check_signing_policy: Error with signing policy
    globus_gsi_callback.c:927: globus_i_gsi_callback_check_gaa_auth: Error with signing policy: The signing policy file doesn't exist or can't be read

    Can't open key:

    globus_gsi_credential.c:1066: globus_gsi_cred_read_key: Error reading user credential: Can't open bio stream for key file: ~/.tcshrc for reading
    OpenSSL Error: bss_file.c:106: in library: BIO routines, function BIO_new_file: system lib
    OpenSSL Error: bss_file.c:104: in library: system library, function fopen: No such file or directory
    OpenSSL Error: pem_lib.c:666: in library: PEM routines, function PEM_read_bio: no start line

    Key file isn't actually a key:
    
    globus_gsi_credential.c:1092: globus_gsi_cred_read_key: Error reading user credential: Can't read credential's private key from PEM
    OpenSSL Error: pem_lib.c:666: in library: PEM routines, function PEM_read_bio: no start line
    OpenSSL Error: pem_lib.c:666: in library: PEM routines, function PEM_read_bio: no start line


    Cert file isn't actually a cert:
    globus_gsi_credential.c:1169: globus_gsi_cred_read_cert: Error reading user credential: Can't read credential cert from bio stream
    OpenSSL Error: pem_lib.c:666: in library: PEM routines, function PEM_read_bio: no start line


    """

    try:

        def cb(msg):
            print "gpi debug: ", msg
            
        print "call gpi"
        security.grid_proxy_init(verbose = 1,
                                 verify = 1,
                                 certDir = certDir,
                                 certFile = certFile,
                                 keyFile = keyFile,
                                 outFile = outFile,
                                 bits = bits,
                                 lifetime = hours * 60,
                                 passphrase = passphrase,
                                 debugCB = cb)
        print "gpi returns"

    except security.GSIException, e:

        print "Got exception ", e
        
        #
        # We failed. Rifle through the exception data to determine why the failure
        # happened.
        #
        # error_types is a list of tuples (regexp, message, exception-class) that attempts
        # to match the string of the exception with the high-level error that
        # caused it.
        #

        error_types = [
            ("Error reading user credential: Can't read credential's private key from PEM.*bad decrypt",
             "Invalid passphrase",
             InvalidPassphraseException),
            ("Failed to verify credential.*unable to get issuer certificate",
             "Missing CA Certificate",
             GridProxyInitError),
            ("Credential with subject:\s+(.*)\s+has expired",
             "Expired certificate for %s",
             GridProxyInitError),
            ("Error with signing policy: The signing policy file doesn't exist or can't be read",
             "Missing signing policy",
             GridProxyInitError),
            ("Can't open bio stream for key file:\s+(.*)\s+for reading.",
             "Missing key file %s",
             GridProxyInitError),
            ("Can't read credential's private key from PEM.*no start line",
             "Invalid key file",
             GridProxyInitError),
            ("Can't read credential private cert from bio stream*no start line",
             "Invalid certificate file",
             GridProxyInitError),
            ]

        err_short_string = e[0]
        err_list = e[1]

        err_str = "\n".join(err_list)
        print err_str
        
        error_match = None

        err_args = []

        for etype in error_types:
            m = re.search(etype[0], err_str, re.DOTALL)

            if m:
                print "Error matched! ", etype[1], m.groups()
                raise etype[2](etype[1] % m.groups())

        print "Did not match error"
        raise GridProxyInitError

    except Exception, e:
        print "Raised exception ", e
        raise

def IsGlobusProxy_Generic(certObj):
    name = certObj.GetSubject().get_name_components()
    lastComp = name[-1]
    return lastComp[0] == "CN" and lastComp[1] == "proxy"

def IsGlobusProxy_GT24(certObj):

    attrs = security.grid_proxy_info2(0, certObj.GetPath())

    return attrs['type'] is not None

if haveOldGlobus:

    if Platform.isWindows():
        CreateGlobusProxy = CreateGlobusProxyProgrammatic
    else:
        CreateGlobusProxy = CreateGlobusProxyGPI
    IsGlobusProxy = IsGlobusProxy_Generic

else:
    #
    # We're using a GT24 pyglobus; see if we have the very latest changes.
    #

    from pyGlobus import gsic
    if hasattr(gsic, "grid_proxy_init2"):
        print 'use new globus'
        CreateGlobusProxy = CreateGlobusProxyProgrammatic_GT24
        IsGlobusProxy = IsGlobusProxy_GT24
    else:
        print 'use old globus'
        CreateGlobusProxy = CreateGlobusProxyGPI
        IsGlobusProxy = IsGlobusProxy_Generic
        

