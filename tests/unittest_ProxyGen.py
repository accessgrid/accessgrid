#
# Unit tests for proxy generation.
#
# The overall plan here is to create a number of scenarios, some
# with valid certificates, some with various failures, and
# verify that the proxy generation code works properly (creating
# proxies or failing in the way we expect).
#

import unittest
import tempfile
import time
import os
import os.path

from OpenSSL_AG import crypto
from AccessGrid.Security import ProxyGen

def ConstructSigningPolicy(cert):
    """
    Construct a simple signing policy based on the subject name of cert.

    It might not be right, but it might be.

    We make it match on all parts of the cert's subject except for CN.
    """

    caName = str(cert.get_subject())

    subjs = filter(lambda a: a[0] != "CN", cert.get_subject().get_name_components())

    condSubjects = "/".join(map(lambda a: a[0] + "=" + a[1], subjs))

    sp = """
#
# Signing policy automatically generated.
#
 access_id_CA       X509      '%(caName)s'
 pos_rights         globus    CA:sign
 cond_subjects      globus    '"/%(condSubjects)s/*"'
""" % locals()

    return sp

#
# Certificate-holding class. This keeps track of the cert and key
# and allows easy manipulation of them for the tests.
#

class TestCert:
    def __init__(self, cert = None, key = None, bits = 512):

        self.cert = cert
        self.key = key
        self.bits = bits
        self.req = None
        
    def MakeKey(self):

        self.key = crypto.PKey()
        self.key.generate_key(crypto.TYPE_RSA, self.bits)

    def MakeRequest(self, name):

        self.req = crypto.X509Req()
        if self.key:
            self.req.set_pubkey(self.key)

        s = self.req.get_subject()
        for k, v in name:
            s.add(k, v)

    def SelfSign(self, start, end):

        c = self.cert = crypto.X509()
        c.set_serial_number(int(time.time()))
        c.set_version(2)

        c.set_pubkey(self.req.get_pubkey())

        c.gmtime_adj_notBefore(start - int(time.time()))
        c.gmtime_adj_notAfter(end - int(time.time()))

        c.set_subject(self.req.get_subject())
        c.set_issuer(self.req.get_subject())

        exts = [("nsCertType", 0, "client,server,objsign,email"),
                ("basicConstraints", 1, "CA:true"),
                ("nsComment", 0, "Generated by passwd check authenticator")]
        for name, critical, value in exts:
            c.add_extension(name, critical, value)

        digest = "md5"
        c.sign(self.key, digest)

    def SignRequest(self, rcert, start, end):
        """
        Turn the cert object passed in rcert into a signed cert.
        """

        c = rcert.cert = crypto.X509()
        c.set_serial_number(int(time.time()))
        c.set_version(2)

        c.set_pubkey(rcert.req.get_pubkey())

        c.gmtime_adj_notBefore(start - int(time.time()))
        c.gmtime_adj_notAfter(end - int(time.time()))

        c.set_subject(rcert.req.get_subject())
        c.set_issuer(self.cert.get_subject())

        exts = [("nsCertType", 0, "client,server,objsign,email"),
                ("basicConstraints", 1, "CA:false"),
                ("nsComment", 0, "Generated by passwd check authenticator")]
        for name, critical, value in exts:
            c.add_extension(name, critical, value)

        digest = "md5"
        c.sign(self.key, digest)


    def WriteTrustedCert(self, dir):
        """
        Write this cert as trusted cert in the given dir.
        """

        base = self.cert.get_subject().get_hash()

        certPath = os.path.join(dir, "%s.0" % (base))

        fh = open(certPath, "w")
        fh.write(crypto.dump_certificate(crypto.FILETYPE_PEM, self.cert))
        fh.close()

    def WriteSigningPolicy(self, dir):
        """
        Write a signing policy for this cert in dir.
        """

        base = self.cert.get_subject().get_hash()

        spPath = os.path.join(dir, "%s.signing_policy" %(base))

        fh = open(spPath, "w")
        fh.write(ConstructSigningPolicy(self.cert))
        fh.close()


    def Write(self, dir, basename, passphrase = None):
        """
        Write the cert out to dir, with base path of basename.
        """

        certPath = os.path.join(dir, "%s.cert.pem" %(basename))
        keyPath  = os.path.join(dir, "%s.key.pem" %(basename))

        fh = open(certPath, "w")
        fh.write(crypto.dump_certificate(crypto.FILETYPE_PEM, self.cert))
        fh.close()

        fh = open(keyPath, "w")

        if passphrase is None:
            fh.write(crypto.dump_privatekey(crypto.FILETYPE_PEM, self.key))
        else:
            fh.write(crypto.dump_privatekey(crypto.FILETYPE_PEM, self.key, "DES3", passphrase))
        fh.close()

        return certPath, keyPath
        
#
# We define helper functions that will create a set of
# certificates and keys with the desired properties.
#
# 

def CreateCA(start, end, name):
    """
    Create a test CA certificate with the given starting and ending
    dates and name. This will be a self-signed cert.

    """

    cert = TestCert()

    cert.MakeKey()
    cert.MakeRequest(name)
    cert.SelfSign(start, end)

    return cert

def CreateUser(start, end, caCert, userName):
    """
    Create a user cert signed by the given CA cert.
    """
    
    u = TestCert()
    u.MakeKey()
    u.MakeRequest(userName)

    caCert.SignRequest(u, start, end)

    return u

#
# Okay, start the tests
#

class ProxyTestCase(unittest.TestCase):

    def setUp(self):
        self.caName = [("O", "testCA"),
                       ("CN", "cert authority")]
        self.userCertName = [("O", "testCA"),
                            ("CN", "some user")]

        self.certDir = tempfile.mktemp()
        os.mkdir(self.certDir)

        self.userDir = tempfile.mktemp()
        os.mkdir(self.userDir)

        print "Cert dir: ", self.certDir
        print "User dir: ", self.userDir
        

    def tearDown(self):

        for f in os.listdir(self.certDir):
            if f == "." or f == "..":
                continue

            os.unlink(os.path.join(self.certDir, f))

        for f in os.listdir(self.userDir):
            if f == "." or f == "..":
                continue

            os.unlink(os.path.join(self.userDir, f))
            
        os.rmdir(self.certDir)
        os.rmdir(self.userDir)

    #
    # Test 1. Create a valid CA cert and user cert and create a proxy from them.
    #

    def test_01_ValidUser(self):

        now = time.time()
        start = now - 86400
        end = now + 86400

        passphrase = "abcd"
        
        caCert = CreateCA(start, end, self.caName)
        userCert = CreateUser(start, end, caCert, self.userCertName)

        caCert.WriteTrustedCert(self.certDir)
        caCert.WriteSigningPolicy(self.certDir)
        
        certPath, keyPath = userCert.Write(self.userDir, "usercert", passphrase)

        print "certPath: ", certPath
        print "keyPath: ", keyPath
        print "caDir: ", self.certDir

        outFile = os.path.join(self.userDir, "proxy.pem")

        ProxyGen.CreateGlobusProxy(passphrase, certPath, keyPath, self.certDir,
                                   outFile, 512, 12)

    def test_02_ValidUserBadPassphrase(self):

        now = time.time()
        start = now - 86400
        end = now + 86400

        passphrase = "abcd"
        badpassphrase = "abcde"
        
        caCert = CreateCA(start, end, self.caName)
        userCert = CreateUser(start, end, caCert, self.userCertName)

        caCert.WriteTrustedCert(self.certDir)
        caCert.WriteSigningPolicy(self.certDir)

        certPath, keyPath = userCert.Write(self.userDir, "usercert", passphrase)

        print "certPath: ", certPath
        print "keyPath: ", keyPath
        print "caDir: ", self.certDir

        outFile = os.path.join(self.userDir, "proxy.pem")

        self.assertRaises(ProxyGen.InvalidPassphraseException,
                          ProxyGen.CreateGlobusProxy,
                          badpassphrase, certPath, keyPath, self.certDir, outFile, 512, 12)

    def test_03_MissingCA(self):

        now = time.time()
        start = now - 86400
        end = now + 86400

        passphrase = "abcd"
        
        caCert = CreateCA(start, end, self.caName)
        userCert = CreateUser(start, end, caCert, self.userCertName)

        certPath, keyPath = userCert.Write(self.userDir, "usercert", passphrase)

        print "certPath: ", certPath
        print "keyPath: ", keyPath
        print "caDir: ", self.certDir

        outFile = os.path.join(self.userDir, "proxy.pem")

        self.assertRaises(ProxyGen.GridProxyInitError,
                          ProxyGen.CreateGlobusProxy,
                          passphrase, certPath, keyPath, self.certDir, outFile, 512, 12)

    def test_04_MissingSigningPolicy(self):

        now = time.time()
        start = now - 86400
        end = now + 86400

        passphrase = "abcd"
        
        caCert = CreateCA(start, end, self.caName)
        userCert = CreateUser(start, end, caCert, self.userCertName)

        caCert.WriteTrustedCert(self.certDir)
        
        certPath, keyPath = userCert.Write(self.userDir, "usercert", passphrase)

        print "certPath: ", certPath
        print "keyPath: ", keyPath
        print "caDir: ", self.certDir

        outFile = os.path.join(self.userDir, "proxy.pem")

        self.assertRaises(ProxyGen.GridProxyInitError,
                          ProxyGen.CreateGlobusProxy,
                          passphrase, certPath, keyPath, self.certDir, outFile, 512, 12)

def basic_test():
    x = CreateCA(int(time.time() - 86400),
                 int(time.time() + 86400),
                 [("O", "Me"
                   ), ("CN", "BobCA")])
    
    x.WriteTrusted(".")

    y = TestCert()
    y.MakeKey()
    y.MakeRequest([("O", "Me"), ("CN", "Bob")])

    x.SignRequest(y,
                  int(time.time() - 86400),
                  int(time.time() + 86400))

    y.Write(".", "bob")


def suite():

    suite1 = unittest.makeSuite(ProxyTestCase)
    return unittest.TestSuite([suite1])

if __name__ == "__main__":

    unittest.main(defaultTest = 'suite')
