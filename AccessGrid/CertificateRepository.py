#-----------------------------------------------------------------------------
# Name:        CertificateRepository.py
# Purpose:     Cert management code.
#
# Author:      Robert Olson
#
# Created:     2003
# RCS-ID:      $Id: CertificateRepository.py,v 1.8 2003-08-15 16:39:33 olson Exp $
# Copyright:   (c) 2002
# Licence:     See COPYING.TXT
#-----------------------------------------------------------------------------

"""
Certificate management module.

The on-disk repository looks like this:

<repo_root>/
            metadata.db
            certificates/<subject_hash>/
                               <issuer_serial_hash>/cert.pem
                                                    user_files/
                               <modulus_hash>.req.pem
            privatekeys/
                        <modulus_hash>


"""

from __future__ import generators

import re
import os
import os.path
import time
import logging
import string
import md5
import struct
import bsddb
import operator
from AccessGrid import Utilities

log = logging.getLogger("AG.CertificateRepository")

from OpenSSL_AG import crypto

class RepoAlreadyExists(Exception):
    """
    Thrown if repository already exists, and the CertificateRepository
    constructor was invoked with create=1.
    """
    pass

class RepoDoesNotExist(Exception):
    """
    Thrown if repository does not exist, and the CertificateRepository
    constructor was invoked with create=0.
    """
    pass

class RepoInvalidCertificate(Exception):
    """
    Thrown if an attempt was made to use an invalid certificate.
    """
    pass

class RepoBadPassphrase:
    pass

class CertificateRepository:

    #
    # Private key types.
    #

    KEYTYPE_RSA = crypto.TYPE_RSA
    KEYTYPE_DSA = crypto.TYPE_DSA

    #
    # Valid name components for cert request DNs. Lowercased
    # for easy comparison.
    #

    validNameComponents = [
        "cn",
        "c",
        "l",
        "st",
        "o",
        "ou",
        "emailaddress"
        ]
    
    def __init__(self, dir, create = 0):
        """
        Create the repository.

        dir - directory in which to store certificates.

        """

        self.dir = dir
        self.dbPath = os.path.join(self.dir, "metadata.db")

        if create:
            if os.path.isdir(self.dir):
                raise RepoAlreadyExists
            os.makedirs(self.dir)
            os.mkdir(os.path.join(self.dir, "user_files"))
            os.mkdir(os.path.join(self.dir, "privatekeys"))
            os.mkdir(os.path.join(self.dir, "requests"))
            os.mkdir(os.path.join(self.dir, "certificates"))
            #
            # Create the dbhash too.
            #

            self.db = bsddb.hashopen(self.dbPath, 'n')
        else:
            #
            # Just check for directory existence now; we can/should
            # add more checks that the repo dir actually does contain
            # a valid repository.
            #
            
            if not os.path.isdir(self.dir):
                raise RepoDoesNotExist

            #
            # Look for other stuff too
            #

            invalidRepo = 0

            for mustExist in ('user_files', 'privatekeys', 'requests', 'certificates'):
                if not os.path.isdir(os.path.join(self.dir, mustExist)):
                    invalidRepo = 1

            if not os.path.isfile(self.dbPath):
                invalidRepo = 1

            try:
                self.db = bsddb.hashopen(self.dbPath, 'w')
            except bsddb.error:
                log.exception("exception opening hash %s", self.dbPath)
                invalidRepo = 1

            if invalidRepo:
                #
                # The repository is corrupted somehow.
                #
                # Rename it, log an error, and raise an exception.#
                #

                newname = "%s.corrupt.%s" % (self.dir, int(time.time()))
                os.rename(self.dir, newname)
                log.error("Detected corrupted repository, renaming to %s", newname)
                raise RepoDoesNotExist

    def ImportCertificatePEM(self, certFile, keyFile = None,
                             passphraseCB = None):
        """
        Import a PEM-formatted certificate from certFile.

        If keyFile is not None, load it as a private key for cert.

        We don't currently inspect the key itself to ensure it matches
        the certificate, as that may require a passphrase.
        """

        #
        # Load the cert into a pyOpenSSL data structure.
        #

        cert = Certificate(certFile, keyFile, self)
        path = self._GetCertDirPath(cert)
        # print "Would put cert in dir ", path

        #
        # Double check that someone's not trying to import a
        # globus proxy cert.
        #

        if cert.IsGlobusProxy():
            raise RepoInvalidCertificate, "Cannot import a Globus proxy certificate"

        #
        # If the path already exists, we already have this (uniquely named)
        # certificate.
        #

        if os.path.isdir(path):
            raise RepoInvalidCertificate, "Certificate already in repository at %s" % (path)

        #
        # Load the private key. This will require getting the
        # passphrase for the key. Do that here, so we can pass
        # that passphrase down to the importPrivateKey call
        # so it is imported with the same passphrase.
        #
        # We try to load the key without a passphrase first.
        #

        pkey = None
        if keyFile is not None:
            keyText = open(keyFile).read()

            #
            # We try to load the key without a passphrase first.
            #
            
            try:
                pkey = crypto.load_privatekey(crypto.FILETYPE_PEM, keyText, "")

                #
                # Success.
                #

                passphrase = None

            except crypto.Error:

                #
                # We need a passphrase. Get one from the user,
                # and then try again.
                #

                if passphraseCB is None:
                    raise Exception, "This private key requires a passphrase"

                passphrase = passphraseCB(0)

                try:
                    pkey = crypto.load_privatekey(crypto.FILETYPE_PEM, keyText,
                                                  passphrase)

                except crypto.Error:
                    log.exception("load error")
                    raise RepoBadPassphrase

            #
            # At this point pkey has is the privatekey.
            # Doublecheck that the pubkey modulus on the
            # certificate we're importing matches hte
            # modulus on this private key. Otherwise,
            # they're not a matching pair.
            #

            if pkey.get_modulus() != cert.GetModulus():
                raise Exception, "Private key does not match certificate"
            else:
                print "Modulus match: ", pkey.get_modulus()

        #
        # Preliminary checks successful. We can go ahead and import.
        #
        # Import the private key first, so that if we get an exception
        # on the passphrase we're not left with intermediate state.
        # (aie, transactions anyone?)
        #

        if pkey is not None:
            self._ImportPrivateKey(pkey, passphrase)

        self._ImportCertificate(cert, path)

        #
        # Import done, set the metadata about the cert.
        #

        cert.SetMetadata("System.importTime", str(time.time()))
        cert.SetMetadata("System.certImportedFrom", certFile)
        if keyFile:
            cert.SetMetadata("System.keyImportedFrom", keyFile)
            cert.SetMetadata("System.hasKey", "1")
        else:
            cert.SetMetadata("System.hasKey", "0")

        return CertificateDescriptor(cert, self)
            
    def _ImportCertificate(self, cert, path):
        """
        Import a certificate. We've already done the due diligence
        that this is a valid cert that is okay to just copy into place.
        """

        log.debug("_ImportCertificate: create %s", path)
        os.makedirs(path)

        certPath = os.path.join(path, "cert.pem")
        cert.WriteCertificate(certPath)
        
    def _ImportCertificateRequest(self, req):
        """
        Import the given certificate request into the repository.

        req is an OpenSSL_AG.crypto.X509Req object.

        The pathname of the imported request will be
        <repo_root>/requests/<modulus_hash>.pem.
        """

        desc = CertificateRequestDescriptor(req, self)

        hash = desc.GetModulusHash()

        path = os.path.join(self.dir,
                            "requests",
                            "%s.pem" % (hash))

        print "Writing to ", path
        fh = open(path, 'w')
        fh.write(crypto.dump_certificate_request(crypto.FILETYPE_PEM, req))
        fh.close()

        return desc

    def _ImportPrivateKey(self, pkey, passwdCB):
        """
        Import the given private key into the repository.

        passwdCB is passed to the underlying pyOpenSSL routine if it is
        present and not None. It can be either a string, in which case
        it represents the passphrase, or a python callable object, in which
        case it will be invoked by the underlying pyOpenSSL code to
        retrieve the desired passphrase.
        """

        #
        # Compute the directory to store the key in based on a
        # md5 hash of the key's public-key modulus.
        #

        dig = md5.new(pkey.get_modulus())
        hash = dig.hexdigest()

        path = os.path.join(self.dir,
                            "privatekeys",
                            "%s.pem" % (hash))

        print "Importing pkey to ", path
        #
        # If passwdCB is none, don't encrypt.
        #

        if passwdCB is None:
            pktext = crypto.dump_privatekey(crypto.FILETYPE_PEM,
                                            pkey)
            self.SetPrivatekeyMetadata(hash, "System.encrypted", "0")

        else:
            pktext = crypto.dump_privatekey(crypto.FILETYPE_PEM,
                                            pkey,
                                            "DES3",
                                            passwdCB)
            self.SetPrivatekeyMetadata(hash, "System.encrypted", "1")
            
        fh = open(path, 'w')
        fh.write(pktext)
        fh.close()
        #
        # Make the private key unreadable. Necessary for Unix-based Globus.
        #
        os.chmod(path, 0400)

    def _GetCertDirPath(self, cert):
        """
        Compute the path name for the directory the cert will use
        """

        path = os.path.join(self.dir,
                            "certificates",
                            cert.GetSubjectHash(),
                            cert.GetIssuerSerialHash())
        return path

    def RemoveCertificate(self, cert):
        """
        Remove the specificed certificate from the repository.
        """

        #
        # Determine the certificate path.
        #

        if isinstance(cert, CertificateDescriptor):
            cert = cert.cert

        certDir = self._GetCertDirPath(cert)
        if not os.path.isdir(certDir):
            log.debug("RemoveCertificate: Cannot find path %s", certDir)
            return

        try:
            log.debug("Remove %s", certDir)
            Utilities.removeall(certDir)
            os.rmdir(certDir)
        except:
            log.exception("Error removing cert directories at %s", certDir)

        #
        # Remove stuff from the metadata database.
        #

        metaPrefix = "|".join(["certificate",
                               cert.GetSubjectHash(),
                               cert.GetIssuerSerialHash()])
        pkeyMetaPrefix = "|".join(["privatekey",
                                   cert.GetModulusHash()])
        for key in self.db.keys():
            if key.startswith(metaPrefix):
                del self.db[key]
                print "Delete ", key
            if key.startswith(pkeyMetaPrefix):
                del self.db[key]
                print "Delete ", key
        self.db.sync()

        #
        # Remove any private keys.
        #

        pkeyfile = os.path.join(self.dir,
                                "privatekeys",
                                "%s.pem" % (cert.GetModulusHash()))

        if not os.path.isfile(pkeyfile):
            log.debug("No private key dir found at %s", pkeyfile)
        else:
            try:
                #
                # Need to chmod it writable before we can remove.
                #
                os.chmod(pkeyfile, 0600)
                os.remove(pkeyfile)
            except:
                log.exception("Error removing private key directory at %s", pkeyfile)
        
    #
    # Certificate Request support
    #

    def CreateCertificateRequest(self, nameEntries, passphraseCB,
                                 keyType = KEYTYPE_RSA,
                                 bits = 1024,
                                 messageDigest = "md5",
                                 extensions = None):
        """
        Create a new certificate request and store it in the repository.
        Returns a CertificateRequestDescriptor for that request.

        nameEntries is a list of pairs (key, value) where key is
        a standard distinguished name key, and value is the value to
        be used for that key.

        extensions is a list of triples (name, critical, value) to be used
        to set the requests extensions. If passed in as none, a useful
        default set of extensions will be used.
        """

        #
        # make sure nameEntries is what we expect it to be.
        #

        if not operator.isSequenceType(nameEntries):
            raise Exception, "nameEntries must be a sequence"
        
        try:
            for k, v in nameEntries:
                if k.lower() not in self.validNameComponents:
                    raise Exception, "Invalid name component %s" % (k)
        except ValueError:
            raise Exception, "Invalid value in nameEntry list"
        except TypeError:
            raise Exception, "nameEntries may not be a list"

        #
        # Name list is okay. Create the cert request obj and set up the
        # subject.
        #

        req = crypto.X509Req()
        sub = req.get_subject()

        for (k, v) in nameEntries:
            sub.add(k, v)

        #
        # set our extensions.
        #
        
        if extensions is None:
            extensions = [("nsCertType", 0, "client,server,objsign,email"),
                          ("basicConstraints", 1, "CA:false")
                          ]

        xextlist = []
        for name, critical, value in extensions:
            xext = crypto.X509Extension(name, critical, value)
            xextlist.append(xext)
        req.add_extensions(xextlist)

        #
        # Generate our private key, stash it in the repo,
        # and sign the cert request.
        #

        pkey = crypto.PKey()
        pkey.generate_key(keyType, bits)

        req.set_pubkey(pkey)
        req.sign(pkey, messageDigest)

        self._ImportPrivateKey(pkey, passphraseCB)
        desc = self._ImportCertificateRequest(req)

        return desc
        

    #
    # Certificate database querying methods
    #
    
        
    def _GetCertificates(self):
        """
        This is a generator function that will walk through all of the
        certificates we have.
        """

        certDir = os.path.join(self.dir, "certificates")
        subjHashes = os.listdir(certDir)
        for subjHash in subjHashes:
            subjHashDir = os.path.join(certDir, subjHash)
            isHashes = os.listdir(subjHashDir)
            for isHash in isHashes:
                certFile = os.path.join(subjHashDir, isHash, "cert.pem")
                desc = CertificateDescriptor(Certificate(certFile, repo = self), self)
                yield desc

    def GetAllCertificates(self):
        return self._GetCertificates()

    def FindCertificates(self, pred):
        """
        Return a list of certificates for which pred(cert) returns true.
        """

        #
        # This is also a generator. That way, we can short-circuit the
        # search if we only want some.
        #

        for cert in self._GetCertificates():
            if pred(cert):
                yield cert

    def FindCertificatesWithSubject(self, subj):
        return list(self.FindCertificates(lambda c: str(c.GetSubject()) == subj))
    
    def FindCertificatesWithIssuer(self, issuer):
        return list(self.FindCertificates(lambda c: str(c.GetIssuer()) == issuer))
    
    def FindCertificatesWithMetadata(self, mdkey, mdvalue):
        return list(self.FindCertificates(lambda c: c.GetMetadata(mdkey) == mdvalue))

    def SetPrivatekeyMetadata(self, modulus, key, value):
        hashkey = "|".join(["privatekey",
                            modulus,
                            key])
        self.SetMetadata(hashkey, value)

    def GetPrivatekeyMetadata(self, modulus, key):
        hashkey = "|".join(["privatekey",
                            modulus,
                            key])
        return self.GetMetadata(hashkey)

    def SetMetadata(self, key, value):
        self.db[key] = value
        self.db.sync()
    
    def GetMetadata(self, key):
        if self.db.has_key(key):
            return self.db[key]
        else:
            return None
    
class CertificateDescriptor:
    def __init__(self, cert, repo):
        self.cert = cert
        self.repo = repo

    def GetPath(self):
        return self.cert.GetPath()

    def GetKeyPath(self):
        return self.cert.GetKeyPath()

    def GetIssuer(self):
        return self.cert.GetIssuer()

    def GetSubject(self):
        return self.cert.GetSubject()

    def GetMetadata(self, k):
        return self.cert.GetMetadata(k)

    def SetMetadata(self, k, v):
        return self.cert.SetMetadata(k, v)

    def GetFilePath(self, file):
        return self.cert.GetFilePath(file)

    def GetVerboseText(self):
        return self.cert.GetVerboseText()

    def GetModulus(self):
        return self.cert.GetModulus()

    def GetModulusHash(self):
        return self.cert.GetModulusHash()

    def HasEncryptedPrivateKey(self):
        mod = self.GetModulusHash()
        isEncrypted = self.repo.GetPrivatekeyMetadata(mod, "System.encrypted")
        if isEncrypted == "1":
            return 1
        else:
            return 0
    def GetNotValidBefore(self):
        return self.cert.GetNotValidBefore()
    
    def GetNotValidAfter(self):
        return self.cert.GetNotValidAfter()

    def IsExpired(self):
        return self.cert.IsExpired()

class CertificateRequestDescriptor:
    def __init__(self, req, repo):
        self.req = req
        self.repo = repo
        self.modulusHash = None

    def GetSubject(self):
        return self.req.get_subject()

    def GetModulus(self):
        key = self.req.get_pubkey()
        return key.get_modulus()

    def GetModulusHash(self):
        if self.modulusHash is None:
            m = self.GetModulus()
            dig = md5.new(m)
            self.modulusHash = dig.hexdigest()
        return self.modulusHash

    def _GetMetadataKey(self, key):
        hashkey = "|".join(["request",
                            self.GetModulusHash(),
                            key])
        return hashkey

    def GetMetadata(self, key):
        return self.repo.GetMetadata(self._GetMetadataKey(key))

    def SetMetadata(self, key, value):
        return self.repo.SetMetadata(self._GetMetadataKey(key), value)

    def ExportPEM(self):
        """
        Returns the PEM-formatted version of the certificate request.
        """

        return crypto.dump_certificate_request(crypto.FILETYPE_PEM, self.req)

class Certificate:
    def __init__(self,  path, keyPath = None, repo = None):
        """
        Create a certificate object.

        This wraps an underlying OpenSSL X.509 cert object.

        path - pathname of the stored certificate
        keyPath - pathname of the private key for the certificate
        """

        self.path = path
        self.keyPath = keyPath
        self.repo = repo

        #
        # Cached hash values.
        #
        self.subjectHash = None
        self.issuerSerialHash = None
        self.modulusHash = None

        fh = open(self.path, "r")
        self.certText = fh.read()
        self.cert = crypto.load_certificate(crypto.FILETYPE_PEM, self.certText)
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

    def GetKeyPath(self):
        #
        # Key path is based on the modulus.
        #

        path = os.path.join(self.repo.dir,
                            "privatekeys",
                            "%s.pem" % (self.GetModulusHash()))
        return path

    def GetPath(self):
        return self.path

    def GetSubject(self):
        return self.cert.get_subject()

    def GetIssuer(self):
        return self.cert.get_issuer()

    def GetSubjectHash(self):

        if self.subjectHash is None:
            subj = self.cert.get_subject().get_der()
            dig = md5.new(subj)
            self.subjectHash = dig.hexdigest()

        return self.subjectHash

    def GetIssuerSerialHash(self):

        if self.issuerSerialHash is None:
            issuer = self.cert.get_issuer().get_der()
            #
            # Get serial number in its 4-byte form
            #
            serial = struct.pack("l", self.cert.get_serial_number())
            dig = md5.new(issuer)
            dig.update(serial)
            self.issuerSerialHash = dig.hexdigest()

        return self.issuerSerialHash

    def GetModulus(self):
        key = self.cert.get_pubkey()
        return key.get_modulus()

    def GetModulusHash(self):
        if self.modulusHash is None:
            m = self.GetModulus()
            dig = md5.new(m)
            self.modulusHash = dig.hexdigest()
        return self.modulusHash

    def IsExpired(self):
        return self.cert.is_expired()


    def IsGlobusProxy(self):
        name = self.GetSubject().get_name_components()
        lastComp = name[-1]
        return lastComp[0] == "CN" and lastComp[1] == "proxy"

    def WriteCertificate(self, file):
        """
        Write the certificate to the given file.
        """

        fh = open(file, "w")
        fh.write(crypto.dump_certificate(crypto.FILETYPE_PEM, self.cert))
        fh.close()

    def _GetMetadataKey(self, key):
        hashkey = "|".join(["certificate",
                            self.GetSubjectHash(),
                            self.GetIssuerSerialHash(),
                            key])
        return hashkey

    def GetFilePath(self, filename):
        dir = os.path.join(self.repo._GetCertDirPath(self), "user_files")
        if not os.path.isdir(dir):
            log.debug("GetFilePath: create %s", dir)
            os.mkdir(dir)
        return os.path.join(dir, filename)

    def GetMetadata(self, key):
        hashkey = self._GetMetadataKey(key)
        val = self.repo.GetMetadata(hashkey)
        return val

    def SetMetadata(self, key, value):
        hashkey = self._GetMetadataKey(key)
        self.repo.SetMetadata(hashkey, value)

    def GetNotValidBefore(self):
        notBefore = self.cert.get_not_before()
        return time.strftime("%x %X", utc2tuple(notBefore))

    def GetNotValidAfter(self):
        notAfter = self.cert.get_not_after()
        return time.strftime("%x %X", utc2tuple(notAfter))

    def GetVerboseText(self):
        fmt = ""
        
        cert = self.cert
        fmt += "Certificate version: %s\n" % (cert.get_version())
        fmt += "Serial number: %s\n" % (cert.get_serial_number())

        notBefore = cert.get_not_before()
        notAfter = cert.get_not_after()

        fmt += "Not valid before: %s\n" % (time.strftime("%x %X", utc2tuple(notBefore)))
        fmt += "Not valid after: %s\n" % (time.strftime("%x %X", utc2tuple(notAfter)))

        (type, fp) = cert.get_fingerprint()
        fmt += "%s Fingerprint: %s\n"  % (type,
                                          string.join(map(lambda a: "%02X" % (a), fp), ":"))
        fmt += "Certificate location: %s\n" % (self.GetPath(),)
        fmt += "Private key location: %s\n" % (self.GetKeyPath(),)

        return fmt
    
if __name__ == "__main__":

    certPath = os.path.join(os.environ["HOME"], ".globus", "usercert.pem")
    keyPath = os.path.join(os.environ["HOME"], ".globus", "userkey.pem")
    c = Certificate(certPath)

    proxy = r"\Documents and Settings\olson\Local Settings\Temp\x509_up_olson"
    print proxy
    print "hash = ", c.GetSubjectHash(), c.GetIssuerSerialHash()

    repo = CertificateRepository("repo", 1)
    print "Importing ", certPath

    try:
        repo.ImportCertificatePEM(certPath, keyPath)
    except RepoInvalidCertificate:
        print "Cert already there maybe"

    #
    # Import some CA certs
    #

    caDir = r"\Program Files\Windows Globus\certificates"
    for certFile in os.listdir(caDir):
        if re.search(r"\.\d+$", certFile):
            try:
                repo.ImportCertificatePEM(os.path.join(caDir, certFile))
            except RepoInvalidCertificate:
                print "yup, you can't import a proxy"
    
    try:
        repo.ImportCertificatePEM(proxy)
    except RepoInvalidCertificate:
        print "yup, you can't import a proxy"

    certlist = list(repo._GetCertificates())
    print "Certs: "
    for c in certlist:
        print "%s %s" % (c.GetIssuer(), c.GetSubject())

    globus = "/C=US/O=Globus/CN=Globus Certification Authority"
    me = "/O=Grid/O=Globus/OU=mcs.anl.gov/CN=Bob Olson"
    print "My certs: ", repo.FindCertificatesWithSubject(me)
    print "Globus certs: ", repo.FindCertificatesWithIssuer(globus)

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

