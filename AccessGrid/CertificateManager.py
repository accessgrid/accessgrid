"""
Certificate management module.

Main classes:

Certificate - wraps an individual X.509 certificate.

CertificateRequest - wraps an X.509 cert request.

CertificateRepository - wraps a directory that contains zero or more
certificates.

There are several different kinds of repositories.

An identity certificate repository holds the user's identity certs. Each
certificate is stored in a file <name-hash>.<idx>. If that certificate
requires a private key, the key is stored in <name-hash>.<idx>.key.

A CA certificate repository holds the client's trusted CA
certificates. Each certificate is stored in a file <name-hash>.<idx>.
Each certificate also has a related signing policy file, used by the
Globus toolkit. This file is stored in <name-hash>.signing_policy.

"""

import re
import os
import os.path
import popen2
import time
import logging
import ConfigParser
import getpass
import string
import sys

from AccessGrid import Platform

try:
    import _winreg
    import win32api

    HaveWin32Registry = 1

except:
    HaveWin32Registry = 0

from OpenSSL_AG import crypto

log = logging.getLogger("AG.CertificateManager")

class CertificateManagerError(Exception):
    pass

class NoIdentityCertificateError(CertificateManagerError):
    pass

class ProxyRequestError(Exception):
    pass

class PassphraseRequestCancelled(ProxyRequestError):
    pass

class InvalidPassphraseException(ProxyRequestError):
    pass

class GridProxyInitError(ProxyRequestError):
    pass

class CertificateManager:
    """
    A CertificateManager manages the certificates for a user.

    It has two main repositories: the identity cert repository and the
    trusted CA cert repository.

    User proxy certificates are managed in the context of the identity
    cert repository.

    The cert manager will also be configured with a repository
    of system-defined trusted CA certificates. If the user
    adds or removes one of the system CA certs, a per-user
    trusted certificate directory is created and the appropriate
    system-defined trusted CA certificates are copied there.
    (This functionality will not be implemented in the first phase).

    We keep track of the following per-user state information. It is
    kept in a ConfigParser-maintained initialization file in
    the userProfile directory:

       defaultIdentity: DN of the user's default identity cert

       useSystemCADir: "yes" if the user is to use the system's
       trusted CA directory, "no" otherwise

    We will assume that if the initialization file is not present,
    that the user has not run the software before. In this case we
    will have to do some initialization of the user's state:

        Create the init file.

        Determine defaults:
            defaultIdentity is the current one according
            to the standard Globus defaults.

            useSystemCADir defaults to "yes"

    When we start up, we'll need to do the following:

        Set up the user's environment to point at the
        appropriate local settings. (os.environ)

        Determine if a valid proxy is in place. If not,
        call grid-proxy-init to create one.

    We also support a mechanism for determining if the
    existing proxy will expire soon, and provide a way
    to as the user for a renewal of it.

    """

    CONFIG_FILE = "certmgr.cfg"
    CONFIG_FILE_SECTION = "CertificateManager"

    USER_CERT_DIR = "identity_certificates"

    def __init__(self, userProfileDir, userInterface,
                 identityCert = None,
                 identityKey = None,
                 inheritIdentity = 0):
        """
        CertificateManager constructor.

        userProfileDir - directory in which this user's profile information is
        kept. The CM uses this directory to store the user's identity certificates,
        the user-specific CA certs (if present), and the certificate management
        configuration ifle.

        systemCACertDir - the directory in which to find the system store
        of trusted CA certificates.

        userInterface - the CMUserInterface object through which interactions
        with the user are managed.

        """

        self.userInterface = userInterface
        self.userProfileDir = userProfileDir
        self.userCertPath = os.path.join(userProfileDir, self.USER_CERT_DIR)

        #
        # Flags that modify default runtime environment behavior
        #

        self.forceCertFile = None
        self.forceKeyFile = None
        self.forceCert = None
        self.inheritIdentity = None

        #
        # Certificate mgr options.
        #

        self.defaultIdentityDN = None
        self.proxyCertPath = None
        self.systemCACertDir = None
        self.useSystemCADir = 0

        #
        # Tie the user interface to the cert mgr.
        #
        if userInterface is not None:
            userInterface.SetCertificateManager(self)

        #
        # Do some initial sanity checking.
        # user profile directory needs to exist and be writable
        # system ca cert dir needs to exist and be readable
        #
        # TODO: these could vector a message through the user interface
        # to let the user know of the errors.
        #

        if not os.path.isdir(self.userProfileDir) or \
           not os.access(self.userProfileDir, os.R_OK | os.W_OK):
            raise Exception("User profile directory %s does not exist or is not  writable" \
                            % (self.userProfileDir))


        #
        # Configure the certificate mgr.
        #
        # First, load the config file.
        #
        self.loadConfiguration()

        #
        # Then create the local CertificateRepository objects for the identity
        # certificates and the trusted CA certs.
        #
        self.setupRepositories()

        #
        # Check for the special cases as passed on the command line.
        # There are two valid and mutually exclusive possibilities:
        #     both identityCert and identityKey set
        #     inheritIdentity set
        #

        if identityCert is not None:
            if identityKey is None or inheritIdentity:
                msg = "CertificateManager: invalid usage: identityCert=%s identityKey=%s inheritIdentity=%s" % (
                    identityCert,
                    identityKey,
                    inheritIdentity)
                log.error(msg)

                raise Exception, msg

            #
            # We're okay, and have an identity to use.
            #

            self.SetForcedIdentity(identityCert, identityKey)

        elif inheritIdentity:
            if identityKey is not None or identityCert is not None:
                msg = "CertificateManager: invalid usage: identityCert=%s identityKey=%s inheritIdentity=%s" % (
                    identityCert,
                    identityKey,
                    inheritIdentity)
                log.error(msg)

                raise Exception, msg

            #
            # We're okay here too, and want to inherit the certificate
            # management from the process environment.
            #

            self.SetInheritedIdentity()
            
        #
        # At this point we're good to go.
        # However, the local environment variables have not been set up
        # yet. We leave it for the user to invoke the InitEnvironment()
        # method at a time of his choosing.
        #

        #
        # We need to do some sanity checking here (ensure we have at least one
        # identity certificate, for instance)
        #

        self.CheckConfiguration()

    def SetForcedIdentity(self, cert, key):
        """
        Use the identity certificate and private key as passed on
        the command line as the identity for this process.
        """

        #
        # First see if the files exist.
        #

        if not os.access(cert, os.R_OK):
            log.critical("SetForcedIdentity: Cannot read certificate %s", cert)
            raise Exception, "SetForcedIdentity: Cannot read certificate ", cert
        
        if not os.access(key, os.R_OK):
            log.critical("SetForcedIdentity: Cannot read private key %s", key)
            raise Exception, "SetForcedIdentity: Cannot read private key %s" % (key,)

        #
        # Now try to create a certificate obj to ensure it's actually a cert.
        #

        try:
            certObj = Certificate(cert, key)

        except crypto.Error, e:
            log.exception("Error reading certificate from %s %s", cert, key)
            raise Exception, "SetForcedIdentity: invalid certificate %s %s: %s" % (cert, key, e)

        #
        # Okay, we're cool. Log a message and set us up for forcing.
        #

        log.debug("Forcing identity to %s", certObj.GetSubject())

        self.forceCertFile = cert
        self.forceKeyFile = key
        self.forceCert = certObj

    def SetInheritedIdentity(self):
        """
        Use the identity as defined in the process environment.

        We must have settings for either X509_USER_PROXY or
        all of X509_USER_CERT, X509_USER_KEY, and X509_RUN_AS_SERVER.
        """

        prox = os.getenv("X509_USER_PROXY")
        cert = os.getenv("X509_USER_CERT")
        key = os.getenv("X509_USER_KEY")
        server = os.getenv("X509_RUN_AS_SERVER")

        log.debug("SetInheritedIdentity: X509_USER_PROXY=%s X509_USER_CERT=%s X509_USER_KEY=%s X509_RUN_AS_SERVER=%s",
                  prox, cert, key, server)

        #
        # Sanity checks.
        #

        if prox is not None:
            if cert is not None or key is not None or server is not None:
                log.warn("X509_USER_PROXY set, but cert/key is also set")
        else:
            if cert is None or key is None or server is None:
                log.warn("X509_USER_PROXY not set, but not all of cert/key/run_as_server are set")

        #
        # Possibly more sanity checking, but later. Calling process should have
        # set up the environment properly.
        #
        
        self.inhertIdentity = 1

    def GetUserInterface(self):
        return self.userInterface

    def HaveValidProxy(self):
        """
        Returns 1 if there is a valid proxy configured.
        """

        p = self.GetCurrentProxy()
        return p is not None

    def GetCurrentProxy(self):
        """
        Returns a Certificate object representing the
        current proxy, if it is valid.
        """
        
        #
        # Attempt to load the proxy certificate so that we can check its
        # validity.
        #

        try:
            pcert = Certificate(self.proxyCertPath)
        except IOError, e:
            log.debug("proxy certificate does not exist")
            pcert = None

        if pcert is not None:
            if pcert.IsExpired():
                log.debug("Proxy cert %s is expired", self.proxyCertPath)
                pcert = None
            else:
                log.debug("Proxy %s is valid", self.proxyCertPath)

        return pcert
    
    def ConfigureProxy(self):
        """
        Configure the proxy cert for our default identity cert.

        First check to see if we have an unexpired proxy already. If so, and if
        it has a long enough lifetime left, just return.

        If we need to create a new proxy, invoke the user interface's
        QueryForPrivateKeyPassphrase() method, passing along the
        certificate from which we will

        """

        pcert = self.GetCurrentProxy()

        userMessage = ""
        if pcert is None:
            #
            # We don't have a valid proxy, so we need to create one.
            #

            while 1:
                try:

                    #
                    # Create the proxy.
                    #
                    # This may fail in a number of ways (the user may cancel
                    # the passphrase request since he doesn't know the passphrase,
                    # he may type in a bad passphrase, the certificate may be invalid,
                    # permissions may be wrong, etc).
                    #
                    # Some things we can recover from; if so, we retry the creation
                    # (perhaps with a message to the user).
                    #
                    # Others we don't attempt to recover from, and leave the
                    # application without a valid proxy. In that event, we're
                    # likely to end up back here the next time the user
                    # attempts an operation that requires the proxy. Hopefully, he
                    # has fixed the problem that led to the error.
                    #

                    pcert = self.CreateProxy(userMessage)
                    break

                except PassphraseRequestCancelled:
                    break

                except InvalidPassphraseException:
                    userMessage = "Passphrase incorrect, please try again."

                except GridProxyInitError, e:
                    userMessage = "Error encountered during grid-proxy-init: " + e.args[1]

                except ProxyRequestError, e:
                    #
                    # These errors are not recoverable ... reraise
                    #

                    log.exception("Unrecoverable error during proxy creation attempt")
                    raise e

        #
        # pcert now has information on our current proxy certificate.
        # right now, we don't really need it.
        #

        pcert = None

    def CreateProxy(self, userMessage = ""):
        """
        Create a proxy certificate from our default identity certificate.

        We snag the certificate from our identity cert repository
        so that we can pass it to the user interface to present to the
        user when they are asked for a password for the cert.

        """

        
        cert = self.userCertRepo.FindCertificateByDN(self.defaultIdentityDN)

        if cert is None:
            err = "Could not find certificate for %s" % (self.defaultIdentityDN)
            log.error(err)
            raise ProxyRequestError(err)

        ret = self.GetUserInterface().GetProxyInfo(cert, userMessage)

        if ret is None:
            raise PassphraseRequestCancelled

        #
        # initialize the excpetion that we might raise if there is a problem
        #
        # We don't actually raise it until the process has completed, in order
        # to ensure clean shutdown of that child process.
        #
        
        exceptionToRaise = None
        (passphrase, hours, bits) = ret

        #
        # We are going to assume Globus here. In particular, we are going
        # to assume that we can use the commandline grid-proxy-init
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

        certPath = cert.GetPath()
        keyPath = cert.GetKeyPath()
        caPath = self.systemCACertDir
        outPath = self.proxyCertPath

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


    def InitEnvironment(self):
        """
        Configure the process environment to correspond to the chosen configuration.

        We set the following variables if we are not configured to use a
        Globus proxy:

            X509_USER_CERT: user's certificate
            X509_USER_KEY: user's private key
            X509_RUN_AS_SERVER: set if we need to override a proxy cert setting
            (perhaps in the registry)

        If a proxy is in use, we set the following variables:

            X509_USER_PROXY: user proxy cert

        In any event, we set this:

            X509_CERT_DIR: location of trusted CA certificates

        It is possible for this function to raise an exception. If it does,
        the certificate manager is still in a valid state, but the client
        will not have a properly configured security environment, and will
        have to attempt to call InitEnvironment again after fixing
        the problem.

        """

        #
        # First determine if we're forcing a particular identity or if we're
        # inheriting from our environment.
        #

        if self.forceCertFile is not None:
            #
            # We're forcing. Set the X509_USER_CERT, X509_USER_KEY, X509_RUN_AS_SERVER
            # environment variables.
            #

            log.debug("InitEnvironment: force to identity %s via %s %s",
                      self.forceCert.GetSubject(), self.forceCertFile, self.forceKeyFile)
            os.environ['X509_USER_CERT'] = self.forceCertFile
            os.environ['X509_USER_KEY'] = self.forceKeyFile
            os.environ['X509_RUN_AS_SERVER'] = "1"
            return

        elif self.inheritIdentity:
            #
            # We're inheriting our calling process's environment.
            #
            # Don't touch that environment
            #
            
            log.debug("InitEnvironment: inheriting process environment")
            return

        #
        # Special cases handled, go on with the usual.
        #

        log.debug("InitEnvironment: using standard proxy setup")

        self.ConfigureProxy()

        #
        # If we're on windows, make these mangled paths without
        # spaces
        #

        if sys.platform == "win32":
            proxyPath = win32api.GetShortPathName(self.proxyCertPath)
            caPath = win32api.GetShortPathName(self.systemCACertDir)
        else:
            proxyPath = self.proxyCertPath
            caPath = self.systemCACertDir

        log.debug("Set X509_USER_PROXY to %s", proxyPath)
        log.debug("Set X509_CERT_DIR to %s", caPath)
        os.environ['X509_USER_PROXY'] = proxyPath
        os.environ['X509_CERT_DIR'] = caPath

    def setupRepositories(self):
        """
        Create the CertificateRepository objects.

        We have one for user identities and one for system CA certs.

        """

        self.userCertRepo = CertificateRepository(self.userCertPath)
        self.trustedCARepo = CertificateRepository(self.systemCACertDir)

    def loadConfiguration(self, isConfigReloadRetry = 0):
        """
        Load the certificate manager configuration information.

        We load from certmgr.cfg in the user profile directory.

        If the certmgr.cfg file does not exist, invoke
        setupInitialConfig() to create it from defaults.
        """

        self.configFile = os.path.join(self.userProfileDir, self.CONFIG_FILE)

        if not os.access(self.configFile, os.R_OK):
            log.debug("setting up initial configuration")
            self.setupInitialConfig()
        else:
            log.debug("using existing configuration")

        #
        # Here, config file should exist. Doublecheck that
        # we will be able to write to it.
        #

        if not os.access(self.configFile, os.W_OK):
            log.warn("Configuration file %s may not be writable", self.configFile)

        cp = self.configParser = ConfigParser.ConfigParser()
        cp.read(self.configFile)

        self.options = ConfigParserSection(cp, self.CONFIG_FILE_SECTION)

        #
        # Initialize local state from config file.
        #

        try:
            self.defaultIdentityDN = self.options['defaultIdentityDN']
            self.useSystemCADir = self.options['useSystemCADir']
            self.systemCACertDir = self.options['systemCACertDir']
            self.proxyCertPath = self.options['proxyCertPath']
        except KeyError, e:
            log.exception("exception on loadConfiguration")

            if isConfigReloadRetry:
                log.error("Configuration file did not load properly, even after reloading defaults")
                raise Exception, "Configuration file did not load properly, even after reloading defaults"
            log.info("Configuration file is invalid, reloading from defaults")
            self.setupInitialConfig()
            self.loadConfiguration(1)

    def writeConfiguration(self):
        """
        Write out the current state of the configuration object.
        """

        fp = open(self.configFile, "w")
        self.configParser.write(fp)
        fp.close()

    def setupInitialConfig(self):
        """
        There was not a configuration file in the user's profile directory.

        Create one with the defaults.
        Also, set up the user environment:
            Create the user certificate directory.
            Copy the default Globus user cert, if present, to it.
            Set the default identity to the identity of the default globus cert
            Copy the anonymous user cert, if present, to it
        """

        if not os.path.isdir(self.userCertPath):
            try:
                os.makedirs(self.userCertPath)
            except os.error, e:
                log.exception("Error creating user certificate path %s", self.userCertPath)
                raise e

        #
        # Determine where Globus thinks the user certs are
        #

        gcerts = FindGlobusCerts()

        if 'x509_user_cert' in gcerts and 'x509_user_key' in gcerts:
            #
            # We have a user cert and key.
            #
            # Initialize a certificate object with them, and import to the
            # user certificate repository.
            #

            cert = Certificate(gcerts['x509_user_cert'],
                               keyPath = gcerts['x509_user_key'])

            #
            # Write the cert out to the newly-created user certificate directory
            #

            cert.WriteToRepoDir(self.userCertPath)

            #
            # Set the default identity to this cert's DN.
            #
            # TODO: this needs to actually use the hash of the DN,
            # in the event that we have multiple certs with the same DN.
            # (perhaps in the case where there's an expired cert and a new cert..)
            #

            self.defaultIdentityDN = cert.GetSubject()
            log.debug("Loaded initial cert %s", cert.GetSubject())

        if 'x509_user_proxy' in gcerts:
            #
            # The environment defined a user proxy location.
            # Go ahead and use this location for our purposes.
            # This will make us a little more compatible, and it
            # is already in a usable temporary storage.
            #

            self.proxyCertPath = gcerts['x509_user_proxy']
        else:
            #
            # Otherwise, use the system temp dir.
            #

            #
            # We do an explicit check for the existence of
            # os.getuid() so that we can align our proxy with the defualt
            # globus proxy location on unixlike platforms.
            #

            if hasattr(os, 'getuid'):
                uid = os.getuid()
                self.proxyCertPath = os.path.join(Platform.GetTempDir(),
                                                  "x509up_u%s" % (uid,))
            else:
                user = Platform.GetUsername()
                self.proxyCertPath = os.path.join(Platform.GetTempDir(), "x509_up_" + user)


        if 'x509_cert_dir' in gcerts:
            self.systemCACertDir = gcerts['x509_cert_dir']

        self.useSystemCADir = 1

        #
        # We haven't defined how the anonymous certs are done yet,
        # so ignore this for now.
        #

        #
        # Write out the config file
        #

        cp = ConfigParser.ConfigParser()
        options = ConfigParserSection(cp, self.CONFIG_FILE_SECTION)

        options['defaultIdentityDN'] = self.defaultIdentityDN
        options['systemCACertDir'] = self.systemCACertDir
        options['useSystemCADir'] = self.useSystemCADir
        options['proxyCertPath'] = self.proxyCertPath
        fp = open(self.configFile, "w")
        cp.write(fp)
        fp.close()

    def CheckConfiguration(self):
        """
        Perform a sanity check on the security execution environment
        """

        #
        # First see if we have any identity certificates in the
        # identity cert repository.
        #

        if len(self.userCertRepo.GetCertificates()) == 0:
            #
            # No certificates found.
            #
            # Determine where Globus thinks the user certs are, and try to
            # load one from there.
            #

            gcerts = FindGlobusCerts()

            if 'x509_user_cert' in gcerts and 'x509_user_key' in gcerts:
                #
                # We have a user cert and key.
                #
                # Initialize a certificate object with them, and import to the
                # user certificate repository.
                #

                cert = Certificate(gcerts['x509_user_cert'],
                                   keyPath = gcerts['x509_user_key'])
                
                #
                # Write the cert out to the newly-created user certificate directory
                #

                cert.WriteToRepoDir(self.userCertPath)

                #
                # And update the repository.
                #
                self.userCertRepo.RescanRepository()


                #
                # Set the default identity to this cert's DN.
                #
                # TODO: this needs to actually use the hash of the DN,
                # in the event that we have multiple certs with the same DN.
                # (perhaps in the case where there's an expired cert and a new cert..)
                #

                self.defaultIdentityDN = cert.GetSubject()
                log.debug("Reloaded initial cert %s", cert.GetSubject())

        #
        # Ensure that the default DN has a certificate. If it does not,
        # log a warning.
        #

        log.debug("Checking that default dn %s has a certificate", self.defaultIdentityDN)

        cert = self.userCertRepo.FindCertificateByDN(self.defaultIdentityDN)

        if cert is None:
            log.warn("No certificate found for default identity %s", self.defaultIdentityDN)


class CertificateManagerUserInterface:
    """
    Superclass for the UI interface to a CertificateManager.
    """

    def __init__(self):
        self.certificateManager = None

    def SetCertificateManager(self, cm):
        self.certificateManager = cm

    def GetCertificateManager(self):
        return self.certificateManager

    def GetProxyInfo(self, cert, userMessage = ""):
        """
        Return the information required to create a proxy from cert.

        userMessage is a string to be presented to the user before asking for the
        passphrase.

        The return value must be a tuple (passphrase, hours, bits) where
        passphrase is the passphrase for the private key for the cert; hours is the
        desired lifetime of the certificate in hours; and bits is the length of the
        key (valid values are 512, 1024, 2048, 4096).
        """

        #
        # The default interface here retrieves the password from the command line.
        #

        print ""
        if userMessage != "":
            print userMessage
        passphrase = getpass.getpass("Enter passphrase for %s: " % (str(cert.GetSubject()),))
        bits = 1024
        hours = 8

        return (passphrase, hours, bits)


def FindGlobusCertsWin32():

    vals = {}

    reg = _winreg.ConnectRegistry(None, _winreg.HKEY_CURRENT_USER)

    try:
        k = _winreg.OpenKey(reg, r"Software\Globus\GSI")

    except WindowsError:
        log.exception("FindGlobusCertsWin32: Could not open windows registry")
        return {}

    if k is None:
        log.warn("FindGlobusCertsWin32: Could not open windows registry")
        return vals

    for name in ('x509_cert_dir', 'x509_cert_file', 'x509_user_proxy',
              'x509_user_cert', 'x509_user_key'):
        try:
            (val, type) = _winreg.QueryValueEx(k, name)

            #
            # We bypass the existence test for the globus user proxy
            # in the event that it doesn't exist yet.
            #

            if name == 'x509_user_proxy':
                log.debug("FindGlobusCertsWin32: Found name=%s val=%s", name, val)
                vals[name] = val
            else:
                if os.access(val, os.R_OK):
                    log.debug("FindGlobusCertsWin32: Found name=%s val=%s", name, val)
                    vals[name] = val
                else:
                    log.debug("FindGlobusCertsWin32: Found name=%s val=%s, but file does not exist", name, val)
                    
        except Exception, e:
            log.exception("FindGlobusCertsWin32: %s not found", name)
            pass

    k.Close()

    return vals

def FindGlobusCertsUnix():

    vals = {}
    try:
        globusUserDir = os.path.join(os.environ['HOME'], ".globus")
        userCert = os.path.join(globusUserDir, "usercert.pem")
        userKey = os.path.join(globusUserDir, "userkey.pem")
        if os.access(userCert, os.R_OK):
            vals['x509_user_cert'] = userCert
        if os.access(userKey, os.R_OK):
            vals['x509_user_key'] = userKey

        #
        # Find the system CA directory
        #

        path = os.path.join(globusUserDir, "certificates")
        if os.path.isdir(path):
            vals['x509_cert_dir'] = path
        else:
            env = None
            if os.environ.has_key('X509_CERT_DIR'):
                env = os.environ['X509_CERT_DIR']

            if env is not None and env != "":
                vals['x509_cert_dir'] = env
            else:
                #
                # Ugh. Nasty, but it matches the GT2.0 code.
                #
                path = "/etc/grid-security/certificates"
                vals['x509_cert_dir'] = path

    except:
        log.exception("Exception in FindGlobusCertsUnix")

    return vals

if HaveWin32Registry:
    FindGlobusCerts = FindGlobusCertsWin32
else:
    FindGlobusCerts = FindGlobusCertsUnix

class CertificateRepository:
    def __init__(self, dir):
        """
        Create the repository.

        dir - directory in which to store certificates.

        """

        self.dir = dir

        self.__scanDir()

    def RescanRepository(self):
        self.__scanDir()

    def GetCertificates(self):
        return self.certDict.values()

    def FindCertificateByDN(self, dn):
        """
        Find a certificate that matches the given dn.

        For now, we just do an exact match; we will likely move the
        keying of certificates to be DN hashes as computed by
        OpenSSL from the certificate itself, as that should be more reliable.
        """

        match = filter(lambda x, dn=dn: str(x.GetSubject()) == str(dn), self.GetCertificates())

        if len(match) == 0:
            return None
        else:
            return match[0]

    def __scanDir(self):
        """
        Scan the certificate directory and initialize cert dict.
        """

        self.certDict = {}
        log.debug("CertificateRepository: scanning %s", self.dir)
        for file in os.listdir(self.dir):
            if re.search("^[0-9A-Fa-f]+\.[0-9]$", file):
                # print "Found cert file ", file

                cert = self.loadCertFromFile(os.path.join(self.dir, file))
                self.certDict[file] = cert

    def loadCertFromFile(self, path):
        """
        Load a certificate from a file.

        Returns the certificate object.

        If we specialize the CertificateRepository, we can override the
        default mechanism provided here.

        """

        key_path = path +  ".key"
        if not os.path.exists(key_path):
            key_path = None

        #
        # Hrm. The signing policy file doesn't use the trailing digit.
        # Let's just doublecheck to make sure there's not more than
        # one cert file with this hash.
        #

        policy_path = None
        (dir, file) = os.path.split(path)
        m = re.search("^([0-9A-Fa-f]+)\.[0-9]$", file)
        if m:
            hash = m.group(1)
            policy_path = os.path.join(dir, hash + ".signing_policy")
            if not os.path.exists(policy_path):
                policy_path = None


        #print "Have key %s" % (key_path)
        #print "Have policy %s" % (policy_path)

        cert = Certificate(path, keyPath = key_path, policyPath = policy_path)

        return cert

class Certificate:
    def __init__(self,  path, keyPath = None, policyPath = None):
        """
        Create a certificate object.

        This wraps an underlying OpenSSL X.509 cert object.

        path - pathname of the stored certificate
        keyPath - pathname of the private key for the certificate
        poicyPath - pathame of the policy definition file for this CA cert
        """

        self.path = path
        self.keyPath = keyPath
        self.policyPath = policyPath

        fh = open(self.path, "r")
        self.certText = fh.read()
        self.cert = crypto.load_certificate(crypto.FILETYPE_PEM, self.certText)
        log.debug("Loaded certificate for %s", self.cert.get_subject())
        fh.close()

        #
        # We don't load the privatekey with the load_privatekey method,
        # as that requires the passphrase for the key.
        # We'll just cache the text here.
        #

        if keyPath is not None:
            fh = open(keyPath, "r")
            self.keyText = fh.read()
            fh.close()

        #
        # Also cache the text of the signing policy
        #

        if policyPath is not None:
            fh = open(policyPath, "r")
            self.policyText = fh.read()
            fh.close()

    def WriteToRepoDir(self, repoPath):
        """
        Write this certificate to the repository directory <repoPath>.

        We determine the hash for this cert, and if there is already
        a certificate written using that hash. (Hmm - what if we're trying
        to write the same certficate twice?)

        Compute the right numeric suffix for the certificate pathnames.

        The cert itself is written as <hash>.<suffix>
        The key is written <hash>.<suffix>.key
        The signing policy is written <hash>.signing_policy.
        Note the last doesn't use a suffix; this is the Globus toolkit
        file naming policy, which has the potential of causing problems.

        """

        hash = self.cert.get_subject().get_hash()

        suffix = 0
        while 1:
            certPath = os.path.join(repoPath, "%s.%d" % (hash, suffix))
            if not os.access(certPath, os.R_OK):
                break
            suffix += 1

        fh = open(certPath, "w")
        fh.write(crypto.dump_certificate(crypto.FILETYPE_PEM, self.cert))
        fh.close()

        if self.keyPath is not None:
            nkpath = certPath + ".key"
            fh = open(nkpath, "w")
            fh.write(self.keyText)
            fh.close()
            os.chmod(nkpath, 0600)

        if self.policyPath is not None:
            fh = open(os.path.join(repoPath, "%s.signing_policy" % (hash)), "w")
            fh.write(self.policyText)
            fh.close()

    def GetPath(self):
        return self.path

    def GetKeyPath(self):
        return self.keyPath

    def GetSubject(self):
        return self.cert.get_subject()

    def GetIssuer(self):
        return self.cert.get_issuer()

    def IsExpired(self):
        return self.cert.is_expired()

class ConfigParserSection:
    def __init__(self, cp, sectionName):
        self.cp = cp
        self.sectionName = str(sectionName)

        if not cp.has_section(self.sectionName):
            cp.add_section(self.sectionName)

    def __getitem__(self, key):
        key = str(key)
        try:
            val = self.cp.get(self.sectionName, key)
        except ConfigParser.NoOptionError, e:
            raise KeyError, e.args[0]
        return val

    def __setitem__(self, key, val):
        key = str(key)
        self.cp.set(self.sectionName, key, val)

    def __delitem__(self, key):
        key = str(key)
        self.cp.remove_option(self.sectionName, key)

    def keys(self):
        return self.cp.options(self.sectionName)

    def values(self):
        for k in self.keys():
            return self[k]

#
# YYMMDDHHMMSSZ
#

def utc2tuple(t):
    if len(t) == 13:
        year = int(t[0:2])
        if year >= 50:
            year = year + 1900
        else:
            year = year + 2000

        month = t[2:4]
        day = t[4:6]
        hour = t[6:8]
        min = t[8:10]
        sec = t[10:12]
    elif len(t) == 15:
        year = int(t[0:4])
        month = t[4:6]
        day = t[6:8]
        hour = t[8:10]
        min = t[10:12]
        sec = t[12:14]

    ttuple = (year, int(month), int(day), int(hour), int(min), int(sec), 0, 0, -1)
    return ttuple

def utc2time(t):
    ttuple = utc2tuple(t)
    print "Tuple is ", ttuple
    saved_timezone = time.timezone
    saved_altzone = time.altzone
    ret1 = int(time.mktime(ttuple))
    time.timezone = time.altzone = 0
    ret = int(time.mktime(ttuple))
    # time.timezone = saved_timezone
    # time.altzone = saved_altzone
    print "ret=%s ret1=%s" % (ret, ret1)
    return ret

if __name__ == "__main__":
    dir = "c:\\program Files\\winglobus\\certificates"

    cr = CertificateRepository(dir)
    c = cr.GetCertificates()[0]
    print "got cert ", c
    s = c.GetSubject()
    print "subj ", s
    x = s.O
    x = s.CN
    print x


    app = wxPySimpleApp()

    fr = wxFrame(None, -1, "test", size = wxSize(400,300))
    panel = wxPanel(fr, -1)

    s = wxBoxSizer(wxVERTICAL)

    panel.SetSizer(s)
    p = RepositoryBrowser(panel, -1, cr)
    s.Add(p, 1, wxEXPAND)

    b = wxButton(panel, -1, "OK")
    s.Add(b, 0, wxALIGN_CENTER)

    panel.Fit()
    fr.Show(1)

    app.MainLoop()
