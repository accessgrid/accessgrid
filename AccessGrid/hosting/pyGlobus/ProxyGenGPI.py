
"""
Globus proxy generation using external grid_proxy_init.

"""

import sys
import os
import os.path
import popen2
import logging

log = logging.getLogger("AG.hosting.pyGlobus.ProxyGenGPI")

class ProxyRequestError(Exception):
    pass

class PassphraseRequestCancelled(ProxyRequestError):
    pass

class InvalidPassphraseException(ProxyRequestError):
    pass

class GridProxyInitError(ProxyRequestError):
    pass

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
        
