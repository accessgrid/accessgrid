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
import shutil
import logging
import getpass
import sys

from AccessGrid import Platform
from AccessGrid import CertificateRepository
from  AccessGrid.hosting.pyGlobus import ProxyGen

import pyGlobus.sslutilsc

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

class NoCertificates(Exception):
    pass

class NoDefaultIdentity(Exception):
    pass

class ProxyExpired(Exception):
    pass

class NoProxyFound(Exception):
    pass

class CertificateManager(object):
    """
    A CertificateManager manages the certificates for a user.

    It uses a CertificateRepository instance to maintain the certificates.
    The repository keeps its certificates in a single large pool; however,
    it provides a mechanism by which the user of the repository can
    tag certificates with metadata. The certificate manager uses this
    tagging mechanism to distinguish between a user's identity
    certificates and the user's set of trusted CA certificates.

    We accomplish this by defining a metadata tag for each certificate
    imported: AG.CertificateManager.certType is the key; the value is
    "identity" or "trustedCA".

    The user's default identity is marked in the repository as well with
    the metadat AG.CertificateManager.isDefaultIdentity, values 0/1. This default
    is then returned by the call

        repo.FindCertificatesWithMetadata("AG.CertificateManager.isDefaultIdentity",
                                           "1")

    The repo doesn't ensure that multiple certs get set to default; that
    is up to this code.

    This certificate manager will not use the system trusted CA directory
    directly; it maintains a local cache of trusted CA certs in the
    repository. Since OpenSSL and the Globus library expect these certificates
    to have a particular file layout, the certificate manager will regenerate
    this cache from the certificates in teh repository each time the set of
    trusted CA certificates  in the repo changes. This set of certificates can
    be determined by the call

        repo.FindCertificatesWithMetadata("AG.CertificateManager.certType",
                                           "trustedCA")

    Globus proxies are also stored in the repository's space. Since they do
    not have unique serial numbers, they are stored in filespace provided
    for users with each certificate:

        certDesc = defaultCert
        proxyPath = certDesc.GetFilePath("globus_proxy")
        CreateGlobusProxy(certDesc.GetCertPath(),
                          certDesc.GetKeyPath(),
                          proxyPath)


    Initialization
    --------------
        
    We will assume that if the repository  is not already present 
    that we've not run this app before and must therefore initialize
    the repository. It may be the case that the user has run an earlier
    version of the AG software and therefore has an AG2.0-style certificate
    repository already in place. We will ignore this, and initialize directly
    from globus state. It is not likely at this stage of the game that
    users already have a lot of new state built up in that repository.
    
    Runtime configuration
    ---------------------

    When an app starts up, we will need to do the following things
    to initialize the user's environment to work properly with the Globus
    toolkit:

        Set up the user's environment to point at the
        appropriate local settings by modifying os.environ.

        Determine if a valid proxy is in place. If not,
        call grid-proxy-init to create one.

    We also support a mechanism for determining if the
    existing proxy will expire soon, and provide a way
    to as the user for a renewal of it.

    Instance variables
    ------------------

    userInterface	Reference to the UI object responsbile
    			for manipulations on this manager.

    userProfileDir	Location of the per-user profile directory
    			for the user of this manager.

    repoPath		Location of the certificate repository used by this mgr.

    
    

    """

    __slots__ = [
        'userInterface',
        'userProfileDir',
        'certRepoPath',
        'certRepo',
        'caDir',
        'proxyPath',
        'defaultIdentity',
        ]

    def __init__(self, userProfileDir, userInterface):
        """
        CertificateManager constructor.

        userProfileDir - directory in which this user's profile information is
        kept. The CM uses this directory to store the certificate repository.

        userInterface - the CMUserInterface object through which interactions
        with the user are managed.


        """

        self.userInterface = userInterface
        self.userProfileDir = userProfileDir
        self.certRepoPath = os.path.join(userProfileDir, "certRepo")
        self.caDir = os.path.join(userProfileDir, "trustedCACerts")
        self.defaultIdentity = None

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


        if not os.path.isdir(self.caDir):
            os.mkdir(self.caDir)

        #
        # Configure the certificate mgr.
        #

        #
        # Attempt to initialize the certificate repository. First try to initialize
        # one without specifying the create option.
        #

        try:
            self.certRepo = CertificateRepository.CertificateRepository(self.certRepoPath,
                                                                        create = 0)
            log.debug("Opened repository %s", self.certRepoPath)
        except CertificateRepository.RepoDoesNotExist:
            #
            # We don't have a cert repo.
            # Initialize ourselves.
            #

            self.InitializeRepository()
            
        #
        # We need to do some sanity checking here (ensure we have at least one
        # identity certificate, for instance)
        #

        self.CheckConfiguration()

    def InitializeRepository(self):
        """
        Initiailize the cert repository as we don't already have one.

        We need to first create a new repository (by passing create=1
        to the constructor).

        Then we need to grope about in the system for the location of any
        existing certificates, both user identity and trusted CA.

        """

        log.debug("initializing repository")

        try:
            self.certRepo = CertificateRepository.CertificateRepository(self.certRepoPath,
                                                                        create = 1)
        except CertificateRepository.RepoAlreadyExists:
            #
            # We really shouldn't be here. Raise an exception.
            #

            raise Exception, "Receieved RepoAlreadyExists exception after we determined that it didn't actually exist"

        self.InitRepoFromGlobus(self.certRepo)

    def InitRepoFromGlobus(self, repo):
        """
        Initialize the given repository from the Globus cert state.

        If we cannot find an identity certificate, do a callback on the user interface
        when we're done with the rest of the initialization so that the user
        has an opportunity to request a certificate.

        If we cannot find any globus state, callback to the user interface for that
        as well. That's a harder problem to solve, but it's not up to us down here.

        We use the pyGlobus low-level sslutilsc.get_certificate_locations call
        to determine where Globus assumes things are going to be placed.
        
        """

        certLocations = pyGlobus.sslutilsc.get_certificate_locations()

        userCert = certLocations['user_cert']
        userKey = certLocations['user_key']
        caDir = certLocations['cert_dir']

        # userKey = userCert = None

        #
        # First the user cert.
        #

        if userCert is not None and userKey is not None:
            #
            # Shh, don't tell. Create a cert object so we can
            # extract the subject name to tell the user.
            #

            certObj = CertificateRepository.Certificate(userCert)

            caption = "Initial import of Globus identity certificate"
            message = "Import certificate for %s. Please enter the passphrase for the private key of this certificate." % (certObj.GetSubject())

            #
            # Import the identity cert.
            # Loop until either it succeeds, or until the user cancels.
            #

            while 1:

                impCert = None
                passphraseCB = self.GetUserInterface().GetPassphraseCallback(caption,
                                                                             message)
                try:
                    
                    impCert = self.ImportIdentityCertificatePEM(repo, userCert, userKey,
                                                                passphraseCB)
                    break

                except CertificateRepository.RepoInvalidCertificate:
                    log.exception("invalid cert on import")
                    self.GetUserInterface().ReportError("Your globus certificate is invalid; ignoring it.")
                    break

                except CertificateRepository.RepoBadPassphrase:
                    log.exception("badd passphrase on import")
                    cont = self.GetUserInterface().ReportBadPassphrase()
                    if not cont:
                        break

                except:
                    log.exception("Unknown error on import")
                    self.GetUserInterface().ReportError("Unknown error on Globus import; ignoring your globus identity certificate")
                    break

            if impCert is not None:
                impCert.SetMetadata("AG.CertificateManager.isDefaultIdentity", "1")
            
        #
        # Now handle the CA certs.
        #

        if caDir is not None:
            files = os.listdir(caDir)

            #
            # Extract the files from the caDir that match OpenSSL's
            # 8-character dot index format.
            #
            regexp = re.compile(r"^[\da-fA-F]{8}\.\d$")
            possibleCertFiles = filter(lambda f, r = regexp: r.search(f), files)

            for f in possibleCertFiles:

                path = os.path.join(caDir, f);
                print "%s might be a cert" % (path)

                try:
                    desc = self.ImportCACertificatePEM(repo, path)
                    
                    print "Imported ", desc.GetSubject()

                    #
                    # See if there's a signing policy file. It'll be named
                    # without the .0
                    #

                    signingPath = os.path.join(caDir,
                                               "%s.signing_policy" %
                                               (desc.GetSubject().get_hash()))
                    if os.path.isfile(signingPath):
                        print "Copying signing policy ", signingPath
                        shutil.copyfile(signingPath,
                                        desc.GetFilePath("signing_policy"))
                    
                except:
                    print "Failure to import ", path

    def ImportIdentityCertificatePEM(self, repo, userCert, userKey, passphraseCB):
        impCert = repo.ImportCertificatePEM(userCert, userKey, passphraseCB)
        
        impCert.SetMetadata("AG.CertificateManager.certType", "identity")
        return impCert
        
    def ImportCACertificatePEM(self, repo, cert):
        impCert = repo.ImportCertificatePEM(cert)
        
        impCert.SetMetadata("AG.CertificateManager.certType", "trustedCA")

        return impCert
        
    def VerifyCertificatePath(self, cert):
        """
        Verify that we have CA certificates for the issuing chain of this cert.
        """

        repo = self.GetCertificateRepository()
        c = cert
        while 1:
            issuers = repo.FindCertificatesWithIssuer(str(c.GetIssuer()))
            log.debug("Issuers of %s are %s", c.GetSubject(), issuers)
            break


    def GetUserInterface(self):
        return self.userInterface

    def GetCertificateRepository(self):
        return self.certRepo

    def CreateProxy(self):
        self.GetUserInterface().CreateProxy()

    def CreateProxyCertificate(self, passphrase, bits, hours):
        """
        Create a globus proxy.
        """

        ident = self.GetDefaultIdentity()
        ProxyGen.CreateGlobusProxy(passphrase,
                                   ident.GetPath(),
                                   ident.GetKeyPath(),
                                   self.caDir,
                                   self.proxyPath,
                                   bits,
                                   hours)
        

    def HaveValidProxy(self):
        """
        Return true if there is a valid proxy for the current identity.
        """

        try:
            pcert = self._VerifyGlobusProxy()
            log.debug("HaveValidProxy: found proxy ident %s",
                      str(pcert.GetSubject()))

            return 1
        except:
            return 0
        
    def InitEnvironment(self):
        """
        Configure the process environment to correspond to the chosen configuration.

        This method does not attempt to remedy any
        problems in the configuration; rather, if the situation is not
        to its liking, it raises an exception telling the caller what
        the problem is. It is safe to reinvoke this method as needed.

        If there are no identity certificates present, raise the
        NoCertificates exception.

        If there is exactly one identity certificate, mark it as the
        default certificate.

        If there are more than one identity certificates and none is
        marked default, or more than one is marked default, raise the
        NoDefaultIdentity exception.

        Examine the default identity certificate.

        If it has an encrypted private key, check for the existence of
        a Globus proxy for the cert. If one does not exist, raise the
        ProxyExpired exception.

        Otherwise, set the following environment variables:

            X509_USER_PROXY: user proxy cert
            X509_CERT_DIR: location of trusted CA certificates

        If the default identity certificate has an unencrypted private key,
        we can use it directly. Set the following environment variables:

            X509_USER_CERT: user's certificate
            X509_USER_KEY: user's private key
            X509_RUN_AS_SERVER: set to override any lingering proxy cert setting


        This method sets self.defaultIdentity as a side effect. It should be
        viewed as the current appropriate mechanism for setting defaultIdentity.
        
        """

        #
        # Write out the trusted CA dir as well, and set that
        # environment variable. We do this first so that we
        # can use it later on.
        #

        self._InitializeCADir()

        idCerts = self.GetIdentityCerts()

        if len(idCerts) == 0:
            raise NoCertificates

        if len(idCerts) == 1:
            idCerts[0].SetMetadata("AG.CertificateManager.isDefaultIdentity", "1")

        #
        # Now we know we have at least one certificate. Make sure we have a unique
        # default identity.
        #
        
        defaultIdCerts = self.GetDefaultIdentityCerts()

        if len(defaultIdCerts) != 1:
            raise NoDefaultIdentity

        defaultIdentity = defaultIdCerts[0]

        log.debug("Using default identity %s", defaultIdentity.GetSubject())

        self.defaultIdentity = defaultIdentity

        #
        # Now to see if we need a proxy.
        #

        if defaultIdentity.HasEncryptedPrivateKey():
            self._InitEnvWithProxy()
        else:
            self._InitEnvWithCert()

    def _InitializeCADir(self):
        """
        Initialize the app's trusted CA certificate directory from the cert repo.

        We first clear out all state, then copy the certs and signing_policy
        files from each of the certificates in the repo marked as being
        trusted CA certs.
        """
        
        #
        # Clear out the ca dir first.
        #

        for file in os.listdir(self.caDir):
            path = os.path.join(self.caDir, file)
            log.debug("Unlink %s", path)
            os.unlink(path)
            
        for c in self.GetCACerts():
            nameHash = c.GetSubject().get_hash()

            i = 0
            while 1:
                destPath = os.path.join(self.caDir, "%s.%d" % (nameHash, i))
                if not os.path.isfile(destPath):
                    break
                i = i + 1
                    
            print "CA cert %s: hash=%s dest=%s" % (c.GetSubject(), nameHash, destPath)
            shutil.copyfile(c.GetPath(), destPath)

            #
            # Look for a signing policy
            #

            spath = c.GetFilePath("signing_policy")
            if os.path.isfile(spath):
                shutil.copyfile(spath, os.path.join(self.caDir, "%s.signing_policy" % (nameHash)))
        os.environ['X509_CERT_DIR'] = self.caDir

    def _InitEnvWithProxy(self):
        """
        Set up the runtime environment for using a globus proxy to defaultIdentity.

        For now, when we're just doing single identities, we write the
        proxy out to the location where Globus is expecting it.

        Later we'll think about using a per-cert location.

        """

        defaultIdentity = self.defaultIdentity
        log.debug("Initializing environment with proxy cert for %s",
                  defaultIdentity.GetSubject())

        #
        # Check to see if we have a valid proxy.
        # This may raise a number of different exceptions; let them
        # filter to our caller.
        #
        # If it succeeds, it'll return a Certificate object for the
        # currently-valid certificate. 
        #

        proxyCert = self._VerifyGlobusProxy()

        #
        # We have a valid Globus proxy in place.
        # Set up the environment to use this proxy certificate.
        #

        log.debug("Configuring for user proxy issued from %s",
                  str(defaultIdentity.GetSubject()))
        log.debug("Proxy %s will expire %s",
                  proxyCert.GetPath(),
                  proxyCert.GetNotValidAfter())

        os.environ['X509_USER_PROXY'] = proxyCert.GetPath()

        #
        # Clear the X509_USER_CERT, X509_USER_KEY, and
        # X509_RUN_AS_SERVER environment variables,
        # as their settings will cause the proxy setting to be ignored.
        #

        for envar in ('X509_USER_CERT', 'X509_USER_KEY', 'X509_RUN_AS_SERVER'):
            if envar in os.environ:
                del os.environ[envar]

    def _VerifyGlobusProxy(self):
        """
        Perform some exhaustive checks to see if there
        is a valid globus proxy in place.
        """

        #
        # Ask globus where it wants the proxy put.
        #

        certLocations = pyGlobus.sslutilsc.get_certificate_locations()
        userProxy = certLocations['user_proxy']
        self.proxyPath = userProxy

        #
        # The basic scheme here is to test for the various possibilities
        # of *failure* for there to be a valid cert, and raise the appropriate
        # exception for each. If we get to the end, we're still in the running
        # and we can set up the environment.
        #
        # Doing it this way makes the code more readable than a deeply-nested
        # set of if-tests that culminate with success down deep in the nesting.
        # It also makes it easier to add additional tests if necessary.
        #

        #
        # Check to see if the proxy file exists.
        #

        if not os.path.isfile(userProxy):
            raise NoProxyFound
        
        #
        # Check to see if the proxy file is actually a certificate
        # of some sort.
        #
        
        try:
            proxyCert = CertificateRepository.Certificate(userProxy)

        except crypto.Error:
            raise NoProxyFound

        #
        # Check to see if the proxy cert we found is really a globus
        # proxy cert.
        #

        if not proxyCert.IsGlobusProxy():
            raise NoProxyFound

        #
        # If we got here, we were able to load the purported
        # proxy certificate into the var proxyCert.
        #
        # See if this proxy matches the default identity cert. We do this by
        # comparing the subject name on the identity cert
        # and the issuer name on the proxy.
        #

        proxyIssuer = proxyCert.GetIssuer()
        idSubject = self.defaultIdentity.GetSubject()
        if proxyIssuer.get_der() != idSubject.get_der():
            raise NoProxyFound

        #
        # Check to see if the proxy cert has expired.
        #

        if proxyCert.IsExpired():
            raise ProxyExpired

        #
        # We're okay. Return the certificate object.
        #

        return proxyCert
    

    def _InitEnvWithCert(self):

        log.debug("Initializing environment with unencrypted user cert %s",
                  self.defaultIdentity.GetSubject())

        certPath = self.defaultIdentity.GetPath()
        keyPath = self.defaultIdentity.GetKeyPath()

        if 'X509_USER_PROXY' in os.environ:
            del os.environ['X509_USER_PROXY']
        os.environ['X509_USER_CERT'] = certPath
        os.environ['X509_USER_KEY'] = keyPath
        os.environ['X509_RUN_AS_SERVER'] = '1'

    def SetDefaultIdentity(self, certDesc):
        """
        Make the identity represented by certDesc the default identity.

        This only affects the cert repository; a followup call to InitEnvironment
        is necessary to effect the change in the environment.
        """

        #
        # First clear the default identity state from all id certs.
        #

        for c in self.GetIdentityCerts():
            c.SetMetadata("AG.CertificateManager.isDefaultIdentity", "0")

        #
        # And set this one to be default.
        #

        certDesc.SetMetadata("AG.CertificateManager.isDefaultIdentity", "1")

    def GetDefaultIdentity(self):
        return self.defaultIdentity

    def GetProxyPath(self):
        return self.proxyPath

    def GetIdentityCerts(self):
        mdkey = "AG.CertificateManager.certType"
        mdval = "identity"
        identityCerts = self.certRepo.FindCertificatesWithMetadata(mdkey, mdval)
        return identityCerts

    def IsDefaultIdentityCert(self, c):
        idkey = "AG.CertificateManager.certType"
        idval = "identity"
        defkey = "AG.CertificateManager.isDefaultIdentity"
        defval = "1"

        return c.GetMetadata(idkey) == idval and c.GetMetadata(defkey) == defval
    
    def GetDefaultIdentityCerts(self):
        
        return list(self.certRepo.FindCertificates(lambda c, self=self: self.IsDefaultIdentityCert(c)))

    def GetCACerts(self):
        mdkey = "AG.CertificateManager.certType"
        mdval = "trustedCA"
        
        caCerts = self.certRepo.FindCertificatesWithMetadata(mdkey, mdval)
        return caCerts

    

    def CheckConfiguration(self):
        """
        Perform a sanity check on the security execution environment
        """

        #
        # First see if we have any identity certificates in the
        # identity cert repository.
        #

        identityCerts = self.certRepo.FindCertificatesWithMetadata("AG.CertificateManager.certType",
                                                                   "identity")
        print "Found id certs ", identityCerts
        if len(identityCerts) == 0:
            log.error("No identity certs found")

        #
        # Find the default identity.
        #

        defaultIdCerts = self.certRepo.FindCertificatesWithMetadata("AG.CertificateManager.isDefaultIdentity",
                                                                   "1")
        print "Default ident ", defaultIdCerts


class CmdlinePassphraseCallback:
    def __init__(self, caption, message):
        self.caption = caption
        self.message = message

    def __call__(self, rwflag):
        print self.caption
        print self.message
        return getpass.getpass("Certmgr passphrase: ")

class CertificateManagerUserInterface:
    """
    Base class for the UI interface to a CertificateManager.
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
    
    def ReportError(self, err):
        print ""
        print "Certificate manager error:"
        print "  ", err
        print ""

    def ReportBadPassphrase(self):
        print ""
        print "Incorrect passphrase. Try again? (y/n) ",
        reply = sys.stdin.readline()
        if reply[0].lower() == 'y':
            return 1
        else:
            return 0

    def GetPassphraseCallback(self, caption, message):
        return CmdlinePassphraseCallback(caption, message)

    def InitGlobusEnvironment(self):
        """
        Initialize the globus runtime environment.

        This method invokes certmgr.InitEnvironment().

        If the InitEnvrironment call succeeds, we are done.

        If it does not succeed, it may raise a number of different exceptions
        based on what in particular the error was. These must be handled
        before the InitGlobusEnvironment call can succeed.

        Since this is the user interface class, it can expect to do some
        work on behalf of the user to remedy the problems.
        """

        success  = 0
        while 1:
            try:
                self.certificateManager.InitEnvironment()
                # yay!
                success = 1
                break
            except NoCertificates:
                print ""
                print "There are no certificates loaded; application cannot use Globus communications"
                success = 0
                break

            except NoDefaultIdentity:
                print ""
                print "There are more than one certificates loaded and a unique default is not set"
                print "Using the first one."

                certs = self.certificateManager.GetIdentityCerts()
                self.certificateManager.SetDefaultIdentity(certs[0])
                # loop back to init env

            except NoProxyFound:
                print ""
                print "No globus proxy found, creating.."
                self.CreateProxy()

            except ProxyExpired:
                print ""
                print "No globus proxy found, creating.."
                self.CreateProxy()

            except Exception, e:
                print "Uncaught exception ", e.__class__
                break
                

        print "done, success=", success

        return success

    def CreateProxy(self):
        """
        Command-line interface for creating a Globus proxy.

        Collect the passphrase, lifetime in hours, and key-size from user.
        """

        lifetime = "12"
        bits = "1024"
        ident = self.certificateManager.GetDefaultIdentity()
        while 1:
            print ""
            print "Creating globus proxy for %s" % (str(ident.GetSubject()))
            passphrase = getpass.getpass("Passphrase: ")
            passphrase = passphrase.strip()

            if passphrase == "":
                print "Empty passphrase received; aborting."
                return
            
            print "Lifetime in hours [%s]: " % (lifetime,),
            inp_lifetime = sys.stdin.readline()
            inp_lifetime = inp_lifetime.strip()
            
            print "Keysize [%s]: " % (bits,),
            inp_bits = sys.stdin.readline()
            inp_bits = inp_bits.strip()

            if inp_lifetime == "":
                inp_lifetime = lifetime
            if not re.search(r"^\d+$", str(inp_lifetime)):
                print "Invalid lifetime."
                continue
            else:
                lifetime = int(inp_lifetime)

            if inp_bits == "":
                inp_bits = bits
            if not re.search(r"^\d+$", str(inp_bits)):
                print "Invalid lifetime."
                continue
            else:
                bits = int(inp_bits)

            #
            # Have input, try to create proxy.
            #

            try:
                self.certificateManager.CreateProxyCertificate(passphrase, bits, lifetime)
                print "Proxy created"
                break
            except:
                log.exception("create proxy raised excpetion")
                print ""
                print "Invalid passphrase."
                continue

if __name__ == "__main__":

    h = logging.StreamHandler()

    logging.root.setLevel(logging.DEBUG)
    logging.root.addHandler(h)

    os.system("rm -r foo")
    os.mkdir("foo")
    log.debug("foo")

    ui = CertificateManagerUserInterface()
    cm = CertificateManager("foo", ui)

    x = cm.ImportIdentityCertificatePEM(cm.certRepo,
                                    r"v\venueServer_cert.pem",
                                    r"v\venueServer_key.pem", None)

    if 0:
        passphraseCB = cm.GetUserInterface().GetPassphraseCallback("DOE cert", "")
        x = cm.ImportIdentityCertificatePEM(cm.certRepo,
                                            r"\temp\doe.pem",
                                            r"\temp\doe.pem", passphraseCB)

    # cm.SetDefaultIdentity(x)
    cm.InitEnvironment()
