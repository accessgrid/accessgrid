#-----------------------------------------------------------------------------
# Name:        CertificateManager.py
# Purpose:     Cert management code.
# Created:     2003
# RCS-ID:      $Id: CertificateManager.py,v 1.41 2005-04-05 18:32:36 turam Exp $
# Copyright:   (c) 2002
# Licence:     See COPYING.TXT
#-----------------------------------------------------------------------------
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

__revision__ = "$Id: CertificateManager.py,v 1.41 2005-04-05 18:32:36 turam Exp $"

import re
import os
import os.path
import shutil
import getpass
import sys
import time

from stat import *

from AccessGrid import Log
from AccessGrid import Utilities
from AccessGrid.Security import GlobusConfig
from AccessGrid.Security import CertificateRepository
from AccessGrid.Security import CRSClient
from AccessGrid import Platform

log = Log.GetLogger(Log.CertificateManager)


class CertificateManagerError(Exception):
    pass

class NoIdentityCertificateError(CertificateManagerError):
    pass

class NoCertificates(Exception):
    pass

class NoDefaultIdentity(Exception):
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
        'userProfileDir',
        'certRepoPath',
        'certRepo',
        'caDir',
        'defaultIdentity',
        'issuedGlobusWarning',
        'useDefaultDN',
        'useCertFile',
        'useKeyFile',
        'globusConfig'
        ]

    def __init__(self, userProfileDir):
        """
        CertificateManager constructor.

        userProfileDir - directory in which this user's profile information is
        kept. The CM uses this directory to store the certificate repository.
        """

        self.userProfileDir = userProfileDir
        self.certRepoPath = os.path.join(userProfileDir, "certRepo")
        self.caDir = os.path.join(userProfileDir, "trustedCACerts")
        self.defaultIdentity = None
        self.issuedGlobusWarning = 0

        try:
            self.globusConfig = GlobusConfig.GetConfig(initIfNeeded=1)
        except Exception, e:
            log.warn("Globus Configuration problem")
            self.globusConfig = None
            
        self.useDefaultDN = None
        self.useCertFile = None
        self.useKeyFile = None

        # Do some initial sanity checking.
        # user profile directory needs to exist and be writable
        # system ca cert dir needs to exist and be readable
        #
        # TODO: these could vector a message through the user interface
        # to let the user know of the errors.

        if not os.path.isdir(self.userProfileDir) or \
           not os.access(self.userProfileDir, os.R_OK | os.W_OK):
            raise Exception("User profile directory %s does not exist or is not  writable" \
                            % (self.userProfileDir))


        if not os.path.isdir(self.caDir):
            os.mkdir(self.caDir)

        # Configure the certificate mgr.

        # Attempt to initialize the certificate repository. First try
        # to initialize one without specifying the create option.

        try:
            self.certRepo = CertificateRepository.CertificateRepository(self.certRepoPath,
                                                                        create = 0)
            log.debug("Opened repository %s", self.certRepoPath)
        except CertificateRepository.RepoDoesNotExist:
            # We don't have a cert repo.
            # Initialize ourselves.

            self.InitializeRepository()

        # We need to do some sanity checking here (ensure we have at least one
        # identity certificate, for instance)

        self.CheckConfiguration()

        # Look for new CA Certificates in the system to import
        if self.globusConfig:
            log.debug("Searching for new CA certificates.")
            for ca_cert in [f for f in os.listdir(self.globusConfig)
                            if f.endswith(".0")]:
                cpath = os.path.join(self.globusConfig.GetDistCACertDir(),
                                     ca_cert)
                try:
                    repo.ImportCertificatePEM(cpath)
                except CertificateRepository.RepoInvalidCertificate:
                    self.log.warn("Not importing cert %s", cpath)
                except:
                    self.log.exception("Error during ca initialization.")
            log.debug("Finished searching for new CA certificates.")
                
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
            # We really shouldn't be here. Raise an exception.
            log.exception("repo already exists")
            raise Exception, "Received RepoAlreadyExists exception after we determined that it didn't actually exist"

        self.InitRepoFromGlobus(self.certRepo)

    def InitRepoFromGlobus(self, repo):
        """
        Initialize the given repository from the Globus cert state.

        If we cannot find an identity certificate, do a callback on the user interface
        when we're done with the rest of the initialization so that the user
        has an opportunity to request a certificate.

        If we cannot find any globus state, callback to the user interface for that
        as well. That's a harder problem to solve, but it's not up to us down here.
        """
        # If globus isn't available
        if self.globusConfig is None:
            return
        
        userCert = self.globusConfig.GetDistCertFileName()
        userKey = self.globusConfig.GetDistKeyFileName()
        caDir = self.globusConfig.GetDistCACertDir()

        log.debug("Initializing from %s", caDir)

        # First the user cert.
        if userCert is not None and userKey is not None:
            # Shh, don't tell. Create a cert object so we can
            # extract the subject name to tell the user.
            try:
                certObj = CertificateRepository.Certificate(userCert)
            except IOError:
                if userCert.endswith(os.path.join("globus", "usercert.pem")):
                    log.warn("Didn't find certficate in old globus path: %s",
                             userCert)
                else:
                    self.GetUserInterface().ReportError(
                        "Identity certificate does not exist at\n" +
                        userCert + "\n" +
                 "You will have to import a valid identity certificate later.")
                certObj = None

            impCert = None

            if certObj is not None:

                caption = "Initial import of identity certificate"
                message = "Import certificate for %s. \nPlease enter the passphrase for the private key of this certificate." % (certObj.GetSubject())

                # Import the identity cert.
                # Loop until either it succeeds, or until the user cancels.
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
                        self.GetUserInterface().ReportError("Your identity certificate is invalid or already present; not importing.")
                        break

                    except CertificateRepository.RepoBadPassphrase:
                        log.exception("badd passphrase on import")
                        cont = self.GetUserInterface().ReportBadPassphrase()
                        if not cont:
                            break

                    except:
                        log.exception("Unknown error on import")
                        self.GetUserInterface().ReportError("Unknown error on initial certificate import; ignoring your identity certificate")
                        break


                if impCert is not None:
                    idCerts = self.GetDefaultIdentityCerts()
                    if len(idCerts) == 0:
                        self.SetDefaultIdentity(impCert)
            
        # Now handle the CA certs.
        if caDir is not None:
            try:
                files = os.listdir(caDir)
            except:
                self.GetUserInterface().ReportError("Error reading CA certificate directory\n" +
                                                    caDir + "\n" +
                                                    "You will have to import trusted CA certificates later.")
                files = []

            # Extract the files from the caDir that match OpenSSL's
            # 8-character dot index format.
            regexp = re.compile(r"^[\da-fA-F]{8}\.\d$")
            possibleCertFiles = filter(lambda f, r = regexp: r.search(f), files)

            for f in possibleCertFiles:

                path = os.path.join(caDir, f);
                log.info("%s might be a cert" % (path))

                # Check for existence of signing policy
                certbasename = f.split('.')[0]
                signingPolicyFile = '%s.signing_policy' % (certbasename,)
                signingPath = os.path.join(caDir,signingPolicyFile)
                if not os.path.isfile(signingPath):
                    log.info("Not importing CA cert %s; couldn't find signing policy file %s",
                             f,signingPath)
                    continue
                    
                try:
                
                    # Import the certificate
                    desc = self.ImportCACertificatePEM(repo, path)
                    
                    # Copy the signing policy file
                    shutil.copyfile(signingPath,
                                        desc.GetFilePath("signing_policy"))
                    
                    log.info("Imported cert as %s.0", desc.GetSubject().get_hash())
                    
                except:
                    log.exception("failure importing %s", path)

    def ImportRequestedCertificate(self, userCert):
        repo = self.GetCertificateRepository()

        defID = self.GetDefaultIdentity()
        
        impCert = repo.ImportRequestedCertificate(userCert)
        log.debug("imported requested cert %s", impCert.GetSubject())
        
        impCert.SetMetadata("AG.CertificateManager.certType", "identity")

        if defID is None:
            self.SetDefaultIdentity(impCert)
            self.GetUserInterface().InitGlobusEnvironment()
        
        repo.NotifyObservers()
        return impCert
        
    def ImportIdentityCertificatePEM(self, repo, userCert, userKey, passphraseCB):
        impCert = repo.ImportCertificatePEM(userCert, userKey, passphraseCB)
        
        impCert.SetMetadata("AG.CertificateManager.certType", "identity")
        repo.NotifyObservers()
        return impCert
        
    def ImportIdentityCertificateX509(self, repo, certObj, pkeyObj, passphraseCB):
        impCert = repo.ImportCertificateX509(certObj, pkeyObj, passphraseCB)
        
        impCert.SetMetadata("AG.CertificateManager.certType", "identity")
        repo.NotifyObservers()
        return impCert
        
    def ImportCACertificatePEM(self, repo, cert):
        impCert = repo.ImportCertificatePEM(cert)
        
        impCert.SetMetadata("AG.CertificateManager.certType", "trustedCA")
 
        repo.NotifyObservers()
        return impCert
        
    def CheckValidity(self, cert):
        """
        Check a certificate for validity.
        
        Return "Expired", "OK", "Not yet valid", "Invalid CA Chain", "Missing private key"
        """


        if self.IsIdentityCert(cert):

            hsh = cert.GetModulusHash()
            pkeyPath = self.GetCertificateRepository().GetPrivateKeyPath(hsh)
            if not pkeyPath or not os.path.isfile(pkeyPath):
                return "Missing private key"

        now = time.time()
        notbefore = cert.GetNotValidBefore()
        notafter = cert.GetNotValidAfter()

        if now < notbefore:
            valid = "Not yet valid"
        elif now > notafter:
            valid = "Expired"
        else:
            # Check the certificate path.
            if self.VerifyCertificatePath(cert):
                valid = "OK"
            else:
                valid = "Invalid CA chain"

        return valid

    def VerifyCertificatePath(self, cert):
        """
        Verify that we have CA certificates for the issuing chain of this cert.
        """

        good = 0
        repo = self.GetCertificateRepository()
        c = cert
        checked = {}
        while 1:
            subj = str(c.GetSubject())
            if c.GetSubject().get_der() == c.GetIssuer().get_der():
                good = 1
                break

            # If we come back to a place we've been before, we're in a cycle
            # and won't get anywhere. Bail.
            if subj in checked:
                return 0
            checked[subj] = 1
            
            issuers = repo.FindCertificatesWithSubject(str(c.GetIssuer()))

            issuers = filter(lambda x: not x.IsExpired(), issuers)
            
            if len(issuers) == 0:
                break
            
            if len(issuers) > 1:
                log.error("Multiple non-expired issuers! choosing one")

            c = issuers[0]

        return good

    def GetCertificatePath(self, cert):
        """
        Return the certification path for cert.
        """

        path = []
        repo = self.GetCertificateRepository()
        c = cert
        checked = {}
        while 1:
            subj = str(c.GetSubject())
            path.append(c)
            if c.GetSubject().get_der() == c.GetIssuer().get_der():
                break

            # If we come back to a place we've been before, we're in a cycle
            # and won't get anywhere. Bail.

            if subj in checked:
                return ""
            checked[subj] = 1
            
            issuers = repo.FindCertificatesWithSubject(str(c.GetIssuer()))

            validIssuers = filter(lambda x: not x.IsExpired(), issuers)

            # Find an issuer to return. If none is valid, pick one to return.
            if len(validIssuers) == 0:
                if len(issuers) > 0:
                    path.append(issuers[0])
                break
            
            c = issuers[0]

        return path

    def GetCertificateRepository(self):
        return self.certRepo

    def SetTemporaryDefaultIdentity(self,
                                    useDefaultDN = None,
                                    useCertFile = None,
                                    useKeyFile = None):
        """
        Set the default identity to use for this instance of the
        certificate manager.

        """
        # Disallow the use of both a specified DN and a specified cert file.
        if useDefaultDN is not None and useCertFile is not None:
            log.error("CertificateManger.SetTemporaryDefaultIdentity(): Cannot specify both a default DN and a certificate file")
            raise CertificateManagerError("Cannot specify both a default DN and a certificate file")

        self.useDefaultDN = useDefaultDN
        self.useCertFile = useCertFile
        self.useKeyFile = useKeyFile

    def InitEnvironment(self):
        """
        Configure the process environment to correspond to the chosen
        configuration.

        This method does not attempt to remedy any problems in the
        configuration; rather, if the situation is not to its liking,
        it raises an exception telling the caller what the problem
        is. It is safe to reinvoke this method as needed.

        If self.useDefaultDN is set, use the given DN to be the default
        for this instance of the class.

        If self.useCertFile is set, use that certificate as the default.

        Otherwise,

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
            X509_RUN_AS_SERVER: set to override any lingering proxy
                                cert setting


        This method sets self.defaultIdentity as a side effect. It
        should be viewed as the current appropriate mechanism for
        setting defaultIdentity.
        """
        # Write out the trusted CA dir as well, and set that
        # environment variable. We do this first so that we
        # can use it later on.
        self._InitializeCADir()

        if self.useDefaultDN is not None:
            log.debug("Configuring env with default DN %s", self.useDefaultDN)
            return self.InitEnvironmentWithDN(self.useDefaultDN)
        elif self.useCertFile is not None and self.useKeyFile is not None:
            log.debug("Configuring env with cert file %s key %s",
                      self.useCertFile, self.useKeyFile)
            return self.InitEnvironmentWithCert(self.useCertFile,
                                                self.useKeyFile)
        else:
            log.debug("Configuring standard environment")
            return self.InitEnvironmentStandard()

    def InitEnvironmentWithDN(self, dn):
        """
        Set up the cert mgr to run with the specified DN as the default
        for this instance. Do not modify the default identity keys in
        the repository.
        """
        # Find the certificate with this dn.
        certs = self.certRepo.FindCertificatesWithSubject(dn)

        validCerts = filter(lambda a: not a.IsExpired(), certs)
        
        if len(validCerts) == 0:
            raise NoIdentityCertificateError("No certificate found with dn " + str(dn))

        if len(validCerts) > 1:
            log.warn("More than one valid cert with dn %s found, choosing one at random.",
                     dn)

        self.defaultIdentity = validCerts[0]

        log.debug("Loaded identity %s" % self.defaultIdentity.GetVerboseText())

        # Lock down the repository so it doesn't get modified.
        self.certRepo.LockMetadata()

    def InitEnvironmentWithCert(self, certFile, keyFile):
        """
        Set up the cert mgr to run with the specified cert and file.
        Do not modify the default identity keys in the repository.
        """

        defaultCert = CertificateRepository.Certificate(certFile,
                                                                 keyFile,
                                                                 self.certRepo)
        self.defaultIdentity = CertificateRepository.CertificateDescriptor(defaultCert,
                                                         self.certRepo)

        log.debug("Cert: %s, Key: %s", certFile, keyFile)
        log.debug("Loaded identity ---\n%s\n---", self.defaultIdentity.GetVerboseText())

        # Lock down the repository so it doesn't get modified.
        self.certRepo.LockMetadata()

    def InitEnvironmentStandard(self):
        
        idCerts, defaultIdCerts, defaultIdentity = self.CheckConfiguration()

        if defaultIdentity:
            log.debug("Using default identity %s", defaultIdentity.GetSubject())
        else:
            log.debug("No default identity found")

        self.defaultIdentity = defaultIdentity

    def _InitializeCADir(self):
        """
        Initialize the app's trusted CA certificate directory from the
        cert repo.

        We first clear out all state, then copy the certs and signing_policy
        files from each of the certificates in the repo marked as being
        trusted CA certs.
        """
        # Clear out the ca dir first.
        for f in os.listdir(self.caDir):
            path = os.path.join(self.caDir, f)
            os.unlink(path)
            
        for c in self.GetCACerts():
            nameHash = c.GetSubject().get_hash()

            i = 0
            while 1:
                destPath = os.path.join(self.caDir, "%s.%d" % (nameHash, i))
                if not os.path.isfile(destPath):
                    break
                i = i + 1
                    
            shutil.copyfile(c.GetPath(), destPath)

            # Look for a signing policy
            spath = c.GetFilePath("signing_policy")
            if os.path.isfile(spath):
                shutil.copyfile(spath, os.path.join(self.caDir, "%s.signing_policy" % (nameHash)))

        self.globusConfig.SetActiveCACertDir(self.caDir)

    def _InitEnvWithCert(self):

        log.debug("Initializing environment with unencrypted cert %s",
                  self.defaultIdentity.GetSubject())

        certPath = self.defaultIdentity.GetPath()
        keyPath = self.defaultIdentity.GetKeyPath()
        
        #
        # Check permissions on cert and key file according to 
        # globus requirements, and set them if possible
        #
        # - Certificate file
        s = os.stat(certPath)
        if s[0] & (S_IXUSR |
                   S_IWGRP | S_IXGRP |
                   S_IWOTH | S_IXOTH):
            if Platform.IsWindows() or (s[ST_UID] == os.getuid()) :
                log.info("Setting permissions on certificate %s to 644", certPath)
                os.chmod(certPath,0644)
            else:
                raise Exception, "Invalid permissions on certificate %s (must be 644 or less)" % (certPath)

        # - Key file
        s = os.stat(keyPath)
        if s[0] & (S_IXUSR |
                   S_IRGRP | S_IWGRP | S_IXGRP |
                   S_IROTH | S_IWOTH | S_IXOTH):
            if Platform.IsWindows() or (s[ST_UID] == os.getuid()) :
                log.info("Setting permissions on certificate %s to 600", keyPath)
                os.chmod(keyPath,0600)
            else:
                raise Exception, "Invalid permissions on private key %s (must be 600 or less)" % (keyPath)

        self.globusConfig.SetUserCert(certPath, keyPath)

    def SetDefaultIdentity(self, certDesc):
        """
        Make the identity represented by certDesc the default identity.

        This only affects the cert repository; a followup call to InitEnvironment
        is necessary to effect the change in the environment.

        @param certDesc: certificate which is to be the default.
        @type certDesc: CertificateDescriptor
        """
        # First clear the default identity state from all id certs.
        for c in self.GetIdentityCerts():
            c.SetMetadata("AG.CertificateManager.isDefaultIdentity", "0")

        # And set this one to be default.
        certDesc.SetMetadata("AG.CertificateManager.isDefaultIdentity", "1")

    def GetGlobusConfig(self):
        return self.globusConfig
    
    def GetDefaultIdentity(self):
        return self.defaultIdentity

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
    
    def IsIdentityCert(self, c):
        idkey = "AG.CertificateManager.certType"
        idval = "identity"

        return c.GetMetadata(idkey) == idval
    
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
        # First see if we have any identity certificates in the
        # identity cert repository.
        identityCerts = self.GetIdentityCerts()

        if len(identityCerts) == 0:
            log.warn("No identity certs found")

        if len(identityCerts) == 1:
            identityCerts[0].SetMetadata("AG.CertificateManager.isDefaultIdentity", "1")
        # Find the default identity.
        defaultIdCerts = self.GetDefaultIdentityCerts()
        
        if len(defaultIdCerts) == 0:
            log.warn("No default identity certificate found")
            defaultId = None
        elif len(defaultIdCerts) > 1:
            log.warn("Found multiple (%s) default identities, using the first",
                     len(defaultIdCerts))
            defaultId = defaultIdCerts[0]
        else:
            defaultId = defaultIdCerts[0]

        return (identityCerts, defaultIdCerts, defaultId)

    # Certificate request stuff
    def GetPendingRequests(self):
        """
        Return a list of the certificate requests in the repository
        for which we don't have a certificate, and for which the
        metadata AG.CertificateManager.requestToken is set.

        Return is actually a list of tuples
        (certReqDescriptor, requestToken, serverURL, creationDate)

        """

        cr = self.GetCertificateRepository()

        tokenKey = "AG.CertificateManager.requestToken"
        pred = lambda c: c.GetMetadata(tokenKey) is not None
        reqs = cr.FindCertificateRequests(pred)

        out = []
        for req in reqs:
            token = req.GetMetadata(tokenKey)
            server = req.GetMetadata("AG.CertificateManager.requestURL")
            created = req.GetMetadata("AG.CertificateManager.creationTime")

            # See if this request has a corresponding certificate.
            modhash = req.GetModulusHash()
            mpred = lambda c, modhash = modhash: c.GetModulusHash() == modhash
            certs = list(cr.FindCertificates(mpred))

            if len(certs) > 0:
                continue

            out.append((req, token, server, created))

        return out

    def CheckRequestedCertificate(self, req, token, server, proxyHost = None,
                                  proxyPort = None):
        """
        Check the server to see if the given request has been granted.
        Return a tuple of (success, msg). If successful, success=1
        and msg is the granted certificate. If not successful, success=0
        and msg is an error message.
        """
        log.debug("CheckRequestedCertificate: req=%s, token=%s, server=%s",
                  req, token, server)
        
        client = CRSClient.CRSClient(server, proxyHost, proxyPort)
        try:
            certRet = client.RetrieveCertificate(token)
            log.debug("Retrieve returns %s", certRet)
        except CRSClient.CRSClientConnectionFailed:
            log.error("Connection failed connecting to server %s via proxy %s:%s",
                      server, proxyHost, proxyPort)
            certRet = (0, "Connection failed")
        except:
            log.exception("Error retrieving certificate")
            certRet = (0, "Error retrieving certificate")
            
        return certRet
    
class CertificateRequestInfo:
    """
    A CertificateRequestInfo holds the information required
    to create a request, and holds the logic for creating
    the appropriate Distinguished Name from it.

    It exists to be subclassed for identity and service certs.
    """

    def __init__(self):
        self.name = None
        self.email = None
        self.type = None
        self.host = None
        self.domain = None

    def GetDNBase(self):
        """
        Return the common parts of a full distinguished name.

        If we move to using different CAs, we can parameterize here.
        """

        name = [("O", "Access Grid"),
                ("OU", "agdev-ca.mcs.anl.gov")]
        return name

    def GetDN(self):
        raise NotImplementedError

    def GetType(self):
        return self.type

    def GetName(self):
        return self.name

    def GetEmail(self):
        return self.email

    def IsIdentityRequest(self):
        return self.type == "identity"

    def __str__(self):
        return "Cert request: type=%(type)s name=%(name)s email=%(email)s domain=%(domain)s host=%(host)s" % self.__dict__

class IdentityCertificateRequestInfo(CertificateRequestInfo):
    def __init__(self, name, domain, email):
        CertificateRequestInfo.__init__(self)
        self.name = name
        self.domain = domain
        self.email = email
        self.type = "identity"

    def GetDN(self):

        dn = self.GetDNBase()
        dn.extend([("OU", self.domain),
                   ("CN", self.name)])

        return dn

class ServiceCertificateRequestInfo(CertificateRequestInfo):
    def __init__(self, name, host, email):
        CertificateRequestInfo.__init__(self)
        self.name = name
        self.host = host
        self.email = email
        self.type = "service"

    def GetDN(self):
        dn = self.GetDNBase()
        dn.append(("CN", "%s/%s" % (self.name, self.host)))

        return dn

class HostCertificateRequestInfo(CertificateRequestInfo):
    def __init__(self, host, email):
        CertificateRequestInfo.__init__(self)
        self.name = host
        self.host = host
        self.email = email
        self.type = "host"

    def GetDN(self):
        dn = self.GetDNBase()
        dn.append(("CN", self.host))

        return dn

class AnonymousCertificateRequestInfo(CertificateRequestInfo):
    def __init__(self):
        CertificateRequestInfo.__init__(self)
        self.name = "Anonymous"
        self.type = "anonymous"
        self.email = ""

    def GetDN(self):
        # Make some name, though it doesn't actually matter
        # since the cert creator service will give it a random name.
        dn = self.GetDNBase()
        dn.append(("CN", "Anonymous"))

        return dn

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

    def __init__(self, cm):
        self.certificateManager = cm

    def SetCertificateManager(self, cm):
        self.certificateManager = cm

    def GetCertificateManager(self):
        return self.certificateManager

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

            except Exception:
                log.exception("Error Initializing environment.")
                raise
                break

        log.debug("done, success=%s", success)

        return success

    def RequestCertificate(self, reqInfo, password,
                           proxyEnabled, proxyHost, proxyPort):
        """
        Request a certificate.

        reqInfo is an instance of CertificateManager.CertificateRequestInfo.

        Perform the actual certificate request mechanics.

        Returns 1 on success, 0 on failure.
        """

        log.debug("RequestCertificate: Create a certificate request")
        log.debug("Proxy enabled: %s value: %s:%s", proxyEnabled, proxyHost,
                  proxyPort)

        try:
            repo = self.certificateManager.GetCertificateRepository()

            # Ptui. Hardcoding name for the current AGdev CA.
            # Also hardcoding location of submission URL.
            submitServerURL = "http://www.mcs.anl.gov/fl/research/accessgrid/ca/agdev/server.cgi"

            name = reqInfo.GetDN()
            log.debug("Requesting certificate for dn %s", name)
            log.debug("reqinfo isident: %s info: %s", reqInfo.IsIdentityRequest(), str(reqInfo))

            # Service/host certs don't have encrypted private keys.
            if not reqInfo.IsIdentityRequest():
                password = None

            certificateRequest = repo.CreateCertificateRequest(name, password)

            pem =  certificateRequest.ExportPEM()

            log.debug("SubmitRequest:Validate: ExportPEM returns %s", pem)
            log.debug("SubmitRequest:Validate: subj is %s",
                      certificateRequest.GetSubject())
            log.debug("SubmitRequest:Validate: mod is %s",
                      certificateRequest.GetModulus())
            log.debug("SubmitRequest:Validate:modhash is %s",
                      certificateRequest.GetModulusHash())

            if proxyEnabled:
                certificateClient = CRSClient.CRSClient(submitServerURL,
                                                        proxyHost, proxyPort)
            else:
                certificateClient = CRSClient.CRSClient(submitServerURL)

            try:
                requestId = certificateClient.RequestCertificate(reqInfo.GetEmail(), pem)

                log.debug("SubmitRequest:Validate:Request id is %s", requestId)

                certificateRequest.SetMetadata("AG.CertificateManager.requestToken",
                                               str(requestId))
                certificateRequest.SetMetadata("AG.CertificateManager.requestURL",
                                               submitServerURL)
                certificateRequest.SetMetadata("AG.CertificateManager.requestType",
                                               reqInfo.GetType())
                certificateRequest.SetMetadata("AG.CertificateManager.creationTime",
                                               str(int(time.time())))

                repo.NotifyObservers()
                return 1
            
            except CRSClient.CRSClientInvalidURL:
                print "Certificate request failed: invalid request URL"
                log.error("Certificate request failed: invalid request URL")
                return 0

            except CRSClient.CRSClientConnectionFailed:
                if proxyEnabled:
                    log.error("Cert request failed with proxy address %s %s",
                              proxyHost, proxyPort)
                    print "Certificate request failed: Connection failed."
                    print "Did you specify the http proxy address correctly?",
                else:
                    log.error("Cert request failed")
                    print "Certificate request failed: Connection failed."
                    print "Do you need to configure an http proxy address?",
                return 0
            
            except:
                print "Unexpected error in cert request"
                log.exception("Unexpected error in cert request")
                return 0
            
            
        except CertificateRepository.RepoDoesNotExist:
            log.exception("SubmitRequest:Validate:You do not have a certificate repository. Certificate request can not be completed.")


            print "Your certificate repository is not initialized; certificate request cannot be completed"
            return 0

        except:
            log.exception("SubmitRequest:Validate: Certificate request can not be completed")
            print "Error occured. Certificate request can not be completed.",
            return 0

if __name__ == "__main__":

    h = Log.StreamHandler()
    h.setFormatter(Log.GetFormatter())
    Log.HandleLoggers(h, Log.GetDefaultLoggers())

    os.mkdir("foo")
    log.debug("foo")

    try:
        cm = CertificateManager("foo")
        ui = CertificateManagerUserInterface(cm)

        x = cm.ImportIdentityCertificatePEM(cm.certRepo,
                                            r"v\venueServer_cert.pem",
                                            r"v\venueServer_key.pem", None)
        
        if 0:
            passphraseCB = cm.GetUserInterface().GetPassphraseCallback("DOE cert", "")
            x = cm.ImportIdentityCertificatePEM(cm.certRepo,
                                                r"\temp\doe.pem",
                                                r"\temp\doe.pem", passphraseCB)

        cm.InitEnvironment()
    except Exception, e:
        print e 
        os.removedirs("foo")
