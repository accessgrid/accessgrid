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

from AccessGrid import Platform

try:
    import _winreg
    import win32api

    HaveWin32Registry = True

except:
    HaveWin32Registry = False

from OpenSSL import crypto
from wxPython.wx import *

log = logging.getLogger("AG.CertificateManager")

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

    def __init__(self, userProfileDir, userInterface):
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
        # At this point we're good to go.
        # However, the local environment variables have not been set up
        # yet. We leave it for the user to invoke the InitEnvironment()
        # method at a time of his choosing.
        # 

    def GetUserInterface(self):
        return self.userInterface

    def ConfigureProxy(self):
        """
        Configure the proxy cert for our default identity cert.

        First check to see if we have an unexpired proxy already. If so, and if
        it has a long enough lifetime left, just return.

        If we need to create a new proxy, invoke the user interface's
        QueryForPrivateKeyPassphrase() method, passing along the
        certificate from which we will 
        
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

        if pcert is None:
            #
            # We don't have a valid proxy, so we need to create one.
            #

            pcert = self.CreateProxy()

        #
        # pcert now has information on our current proxy certificate.
        # right now, we don't really need it.
        #

        pcert = None

    def CreateProxy(self):
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
            raise Exception, err

        (passphrase, hours, bits) = self.GetUserInterface().GetProxyInfo(cert)

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
            raise Exception, msg

        certPath = cert.GetPath()
        keyPath = cert.GetKeyPath()
        caPath = self.systemCACertDir
        outPath = self.proxyCertPath

        #
        # turn on gpi debugging
        #
        debugFlag = "-debug"
        #debugFlag = ""

        cmd = '""%s" %s -pwstdin -bits %s -hours %s -cert "%s" -key "%s" -certdir "%s" -out "%s""'
        cmd = cmd % (gpiPath, debugFlag, bits, hours, certPath, keyPath, caPath, outPath)
        f = open("try.bat", "w")
        f.write(cmd + "\n")
        f.close()
        log.debug("Running command: '%s'", cmd)

        (rd, wr) = popen2.popen4(cmd)

        wr.write(passphrase + "\n")

        while 1:
            l = rd.readline()
            if l == '':
                break
            log.debug("Proxy returns: %s", l.rstrip())

        rd.close()
        wr.close()

        # 
        # TODO: doublecheck that the newly-generated proxy is indeed
        # correct. Also to parse the grid-proxy-init output for errors and
        # status.
        #
        

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

        """

        #
        # for now, just assume that we're going to be using a proxy
        # TODO: add a determination of non-proxy certs that we
        # might use.
        #

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

        os.environ['X509_USER_PROXY'] = proxyPath
        os.environ['X509_CERT_DIR'] = caPath

    def setupRepositories(self):
        """
        Create the CertificateRepository objects.

        We have one for user identities and one for system CA certs.

        """

        self.userCertRepo = CertificateRepository(self.userCertPath)
        self.trustedCARepo = CertificateRepository(self.systemCACertDir)

    def loadConfiguration(self, isConfigReloadRetry = False):
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
            self.loadConfiguration(True)

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
            user = Platform.GetUsername()
            self.proxyCertPath = os.path.join(Platform.GetTempDir(), "x509_up_" + user)


        if 'x509_cert_dir' in gcerts:
            self.systemCACertDir = gcerts['x509_cert_dir']

        self.useSystemCADir = True

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

    def GetProxyInfo(self, cert):
        """
        Return the information required to create a proxy from cert.

        The return value must be a tuple (passphrase, hours, bits) where
        passphrase is the passphrase for the private key for the cert; hours is the
        desired lifetime of the certificate in hours; and bits is the length of the
        key (valid values are 512, 1024, 2048, 4096).
        """

        #
        # The default interface here retrieves the password from the command line.
        #

        passphrase = getpass.getpass("Enter passphrase for certificate: ")
        bits = 1024
        hours = 1

        return (passphrase, hours, bits)

class CertificateManagerWXGUI(CertificateManagerUserInterface):
    """
    wxWindows-based user interfact to the certificate mgr.
    """

    def __init__(self):
        CertificateManagerUserInterface.__init__(self)

    def GetProxyInfo(self, cert):
        """
        Construct and show a dialog to retrieve proxy creation information from user.

        """

        dlg = PassphraseDialog(None, -1, "Enter passphrase", cert)
        rc = dlg.ShowModal()
        if rc == wxID_OK:
            return dlg.GetInfo()
        else:
            return None

    def GetMenu(self, win):
        certMenu = wxMenu()

        i = wxNewId()
        certMenu.Append(i, "View &Trusted CA Certificates...")
        EVT_MENU(win, i, 
                 lambda event, win=win, self=self: self.OpenTrustedCertDialog(event, win))

        i = wxNewId()
        certMenu.Append(i, "View &Identity Certificates...")
        EVT_MENU(win, i,
                 lambda event, win=win, self=self: self.OpenIdentityCertDialog(event, win))

        return certMenu

    def OpenTrustedCertDialog(self, event, win):
        dlg = TrustedCertDialog(win, -1, "View trusted certificates",
                                self.certificateManager.trustedCARepo)
        dlg.ShowModal()
        dlg.Destroy
        
    def OpenIdentityCertDialog(self, event, win):
        dlg = TrustedCertDialog(win, -1, "View user identity certificates",
                                self.certificateManager.userCertRepo)
        dlg.ShowModal()
        dlg.Destroy
        
class PassphraseDialog(wxDialog):
    def __init__(self, parent, id, title, cert):

        self.cert = cert
        
        wxDialog.__init__(self, parent, id, title)

        sizer = wxBoxSizer(wxVERTICAL)

        t = wxStaticText(self, -1, "Create a proxy for %s" % cert.GetSubject())
        sizer.Add(t, 0, wxEXPAND | wxALL, 4)

        grid = wxFlexGridSizer(cols = 2, hgap = 3, vgap = 3)
        sizer.Add(grid, 1, wxEXPAND | wxALL, 4)

        t = wxStaticText(self, -1, "Passphrase:")
        grid.Add(t, 0, wxALL, 4)

        self.passphraseText = wxTextCtrl(self, -1,
                                         style = wxTE_PASSWORD)
        grid.Add(self.passphraseText, 0, wxEXPAND | wxALL, 4)

        t = wxStaticText(self, -1, "Key size:")
        grid.Add(t, 0, wxALL, 4)

        self.keyList = wxComboBox(self, -1,
                                  style = wxCB_READONLY,
                                  choices = ["512", "1024", "2048", "4096"])
        self.keyList.SetSelection(1)
        grid.Add(self.keyList, 1, wxEXPAND | wxALL, 4)

        t = wxStaticText(self, -1, "Proxy lifetime (hours):")
        grid.Add(t, 0, wxALL, 4)
        
        self.lifetimeText = wxTextCtrl(self, -1, "8")
        grid.Add(self.lifetimeText, 0, wxEXPAND | wxALL, 4)

        grid.AddGrowableCol(1)

        h = wxBoxSizer(wxHORIZONTAL)

        sizer.Add(h, 0, wxALIGN_CENTER | wxALL, 4)

        b = wxButton(self, -1, "OK")
        h.Add(b, 0, wxALL, 4)
        EVT_BUTTON(self, b.GetId(), self.OnOK)

        b = wxButton(self, -1, "Cancel")
        h.Add(b, 0, wxALL, 4)
        EVT_BUTTON(self, b.GetId(), self.OnCancel)

        self.SetSizer(sizer)
        self.SetAutoLayout(True)
        self.Fit()

    def GetInfo(self):
        return (self.passphraseText.GetValue(),
                self.lifetimeText.GetValue(),
                self.keyList.GetValue())

    def OnOK(self, event):
        self.EndModal(wxID_OK)
         
    def OnCancel(self, event):
        self.EndModal(wxID_CANCEL)
         

def FindGlobusCertsWin32():

    vals = {}

    reg = _winreg.ConnectRegistry(None, _winreg.HKEY_CURRENT_USER)

    try:
        k = _winreg.OpenKey(reg, r"Software\Globus\GSI")

    except WindowsError:
        return {}

    if k is None:
        return vals

    for name in ('x509_cert_dir', 'x509_cert_file', 'x509_user_proxy',
              'x509_user_cert', 'x509_user_key'):
        try:
            (val, type) = _winreg.QueryValueEx(k, name)

            if os.access(val, os.R_OK):
                vals[name] = val
        except Exception, e:
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

    def GetCertificates(self):
        return self.certDict.values()

    def FindCertificateByDN(self, dn):
        """
        Find a certificate that matches the given dn.

        For now, we just do an exact match; we will likely move the
        keying of certificates to be DN hashes as computed by
        OpenSSL from the certificate itself, as that should be more reliable.
        """

        match = filter(lambda x, dn=dn: str(x.GetSubject()) == dn, self.GetCertificates())

        if len(match) == 0:
            return None
        else:
            return match[0]

    def __scanDir(self):
        """
        Scan the certificate directory and initialize cert dict.
        """

        self.certDict = {}
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
        while True:
            certPath = os.path.join(repoPath, "%s.%d" % (hash, suffix))
            if not os.access(certPath, os.R_OK):
                break
            suffix += 1

        fh = open(certPath, "w")
        fh.write(crypto.dump_certificate(crypto.FILETYPE_PEM, self.cert))
        fh.close()

        if self.keyPath is not None:
            fh = open(certPath + ".key", "w")
            fh.write(self.keyText)
            fh.close()

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

class RepositoryBrowser(wxPanel):
    """
    A RepositoryBrowser provides the basic GUI for browsing certificates.

    It holds a list of certificates. When a cert is selected,
    the name and issuer appear in the dialog, along with the details of the cert.

    This browser supports the import/export/deletion of certs. It does not
    have more specific abilities with regards to the setting of default
    identity certificates, for instance. That functionality is delegated to
    a more specific dialog for handling id certs.
    """

    def __init__(self, parent, id, repo):
        """
        Create the RepositoryBrowser.

        repo - a CertificateRepository instance to browse.

        """

        wxPanel.__init__(self, parent, id)

        self.repo = repo

        self.__build()

    def __build(self):
        """
        Construct the GUI.

        self.sizer: overall vertical sizer
        hboxTop: top row horizontal sizer
        vboxTop: top row vertical sizer for the import/export buttons
        hboxMid: middle row sizer
        vboxMidL: middle row, left column vbox
        vboxMidR: middle row, right column vbox
        """

        self.sizer = wxBoxSizer(wxVERTICAL)
        hboxTop = wxBoxSizer(wxHORIZONTAL)
        hboxMid = wxBoxSizer(wxHORIZONTAL)
        vboxTop = wxBoxSizer(wxVERTICAL)
        vboxMidL = wxBoxSizer(wxVERTICAL)
        vboxMidR = wxBoxSizer(wxVERTICAL)

        #
        # Build the top row.
        #

        self.sizer.Add(hboxTop, 1, wxEXPAND)
        self.certList = wxListBox(self, -1, style = wxLB_SINGLE)

        certs = self.repo.GetCertificates()
        print certs
        for cert in certs:
            print "cert is ", cert, cert.GetSubject()
            name = str(cert.GetSubject().CN)
            print "name is ", name
            self.certList.Append(name, cert)
        print "done"
        hboxTop.Add(self.certList, 1, wxEXPAND)
        EVT_LISTBOX(self, self.certList.GetId(), self.OnSelectCert)

        hboxTop.Add(vboxTop, 0, wxEXPAND)

        b = wxButton(self, -1, "Import...")
        EVT_BUTTON(self, b.GetId(), self.OnImport)
        vboxTop.Add(b, 0, wxEXPAND)
        b.Enable(False)
        
        b = wxButton(self, -1, "Export...")
        EVT_BUTTON(self, b.GetId(), self.OnExport)
        vboxTop.Add(b, 0, wxEXPAND)
        b.Enable(False)
        
        b = wxButton(self, -1, "Delete")
        EVT_BUTTON(self, b.GetId(), self.OnDelete)
        vboxTop.Add(b, 0, wxEXPAND)
        b.Enable(False)

        #
        # Middle row
        #

        self.sizer.Add(hboxMid, 1, wxEXPAND)

        hboxMid.Add(vboxMidL, 1, wxEXPAND)
        t = wxStaticText(self, -1, "Certificate name")
        vboxMidL.Add(t, 0, wxEXPAND)

        self.nameText = wxTextCtrl(self, -1, style = wxTE_MULTILINE | wxTE_READONLY)
        vboxMidL.Add(self.nameText, 1, wxEXPAND)

        hboxMid.Add(vboxMidR, 1, wxEXPAND)
        t = wxStaticText(self, -1, "Issuer")
        vboxMidR.Add(t, 0, wxEXPAND)

        self.issuerText = wxTextCtrl(self, -1, style = wxTE_MULTILINE | wxTE_READONLY)
        vboxMidR.Add(self.issuerText, 1, wxEXPAND)
        
        #
        # Bottom row
        #

        self.certText = wxTextCtrl(self, -1, style = wxTE_MULTILINE | wxTE_READONLY)
        self.sizer.Add(self.certText, 1, wxEXPAND)

        self.SetSizer(self.sizer)
        self.SetAutoLayout(1)
        self.Fit()

    def OnSelectCert(self, event):
        sel = self.certList.GetSelection()
        cert = self.certList.GetClientData(sel)
        print "Selected cert ", sel, cert

        self.nameText.Clear()
        self.issuerText.Clear()
        self.certText.Clear()

        self.nameText.AppendText(self.__formatNameForGUI(cert.GetSubject()))
        self.issuerText.AppendText(self.__formatNameForGUI(cert.GetIssuer()))
        self.certText.AppendText(self.__formatCertForGUI(cert))

    def __formatNameForGUI(self, name):
        fmt = ''
        comps = name.get_name_components()
        comps.reverse()
        for id, val in comps:
            fmt += val + "\n"
        return fmt

    def __formatCertForGUI(self, cert):
        fmt = ''
        #
        # get the lowlevel cert object
        #
        cert = cert.cert
        fmt += "Certificate version: %s\n" % (cert.get_version())
        fmt += "Serial number: %s\n" % (cert.get_serial_number())

        notBefore = cert.get_not_before()
        notAfter = cert.get_not_after()

        fmt += "Not valid before: %s\n" % (time.strftime("%x %X", utc2tuple(notBefore)))
        fmt += "Not valid after: %s\n" % (time.strftime("%x %X", utc2tuple(notAfter)))

        (type, fp) = cert.get_fingerprint()
        fmt += "%s Fingerprint: %s\n"  % (type,
                                          string.join(map(lambda a: "%02X" % (a), fp), ":"))
        return fmt
                                

    def OnImport(self, event):
        print "Import"

    def OnExport(self, event):
        print "Export"

    def OnDelete(self, event):
        print "Delete"

class TrustedCertDialog(wxDialog):
    def __init__(self, parent, id, title, repo):
        wxDialog.__init__(self, parent, id, title, size = wxSize(400, 400))

        self.repo = repo

        sizer = wxBoxSizer(wxVERTICAL)
        cpanel = RepositoryBrowser(self, -1, self.repo)
        sizer.Add(cpanel, 1, wxEXPAND)

        b = wxButton(self, -1, "OK")
        EVT_BUTTON(self, b.GetId(), self.OnOK)
        sizer.Add(b, 0, wxALIGN_CENTER)

        self.SetSizer(sizer)
        self.SetAutoLayout(1)

    def OnOK(self, event):
        self.EndModal(wxOK)

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
    
        

