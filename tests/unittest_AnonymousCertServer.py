
import tempfile
import unittest
import xmlrpclib
import os
import os.path
import operator
import re

ANON_SERVER_URL = "http://www-unix.mcs.anl.gov/~olson/AG/auth/anonReqServer.cgi"

class AnonReqServerTestCase(unittest.TestCase):

    def setUp(self):
        self.url = ANON_SERVER_URL
        self.proxy = xmlrpclib.ServerProxy(self.url)

    def test_01_RequestCACert(self):

        cacert = self.proxy.RetrieveCACertificate()

        self.failUnless(operator.isSequenceType(cacert),
                        "RetrieveCACertificate returns a non-sequence")
        
        self.failUnless(len(cacert) == 2,
                        "RetrieveCACertificate returns a tuple of len != 2")
        
        self.failUnless(type(cacert[1]) == str,
                        "cacert[1] is not a string")
        
        self.assert_(cacert[0],
                     "RetrieveCACertificate returned failure: " + cacert[1])

        tmp = tempfile.mktemp()
        fh = open(tmp, "w")
        fh.write(cacert[1])
        fh.close()
        
        fh = os.popen("openssl x509 -noout -subject -in %s" % (tmp), "r")
        subj = fh.read()
        fh.close()

        m = re.search(r"^subject=\s+(.*)", subj)

        self.assert_(m is not None, "Did not match subject")

        global issuer
        issuer = m.group(1)

        os.unlink(tmp)

        # print cacert[1]

    def test_02_RequestSigningPolicy(self):

        policy = self.proxy.RetrieveSigningPolicy()

        self.failUnless(operator.isSequenceType(policy),
                        "RetrieveSigningPolicy returns a non-sequence")
        
        self.failUnless(len(policy) == 2,
                        "RetrieveSigningPolicy returns a tuple of len != 2")
        
        self.failUnless(type(policy[1]) == str,
                        "policy[1] is not a string")
        
        self.assert_(policy[0],
                     "RetrieveSigningPolicy returned failure: " + policy[1])

        # print policy[1]

    def test_03_RequestCertificate(self):

        #
        # Use openssl to create a request.
        #

        configText = """
[ req ]
default_bits           = 1024
default_keyfile        = privkey.pem
distinguished_name     = req_distinguished_name
prompt                 = no

[ req_distinguished_name ]
O = Some Organization
OU = Some unit
CN = Anonymous Name

"""
        try:

            fileBase = tempfile.mktemp()

            configFile = fileBase + ".config"

            fh = open(configFile, "w")
            fh.write(configText)
            fh.close()


            reqFile = fileBase + ".req"
            keyFile = fileBase + ".key"

            rc = os.system("openssl req -new -newkey rsa:1024 -out %s -keyout %s -nodes -config %s" %
                      (reqFile, keyFile, configFile))

            self.assertEqual(rc, 0, "openssl req command failed")

            #
            # Read the request.
            #

            fh = open(reqFile)
            reqText = fh.read()
            fh.close()

            #
            # And submit.
            #

            token = self.proxy.RequestCertificate("", reqText)

            self.failUnless(type(token) == str, "Returned token is not a string")
            self.assertNotEqual(token, "")

            # print "got token ", token

            certinfo = self.proxy.RetrieveCertificate(token)

            # print "Got ", certinfo

            self.failUnless(operator.isSequenceType(certinfo),
                            "RetrieveCertificate returns a non-sequence")

            self.failUnless(len(certinfo) == 2,
                            "RetrieveCertificate returns a tuple of len != 2")

            self.failUnless(type(certinfo[1]) == str,
                            "certinfo[1] is not a string")

            self.assert_(certinfo[0],
                         "RetrieveCertificate returned failure: " + certinfo[1])

            # print "Retrieved certificate ", certinfo[1]

            #
            # Check the issuer to see if it matches the CA cert.
            #
            
            tmp = tempfile.mktemp()
            fh = open(tmp, "w")
            fh.write(certinfo[1])
            fh.close()

            fh = os.popen("openssl x509 -noout -issuer -in %s" % (tmp), "r")
            txt = fh.read()
            fh.close()

            global issuer

            m = re.search(r"^issuer=\s+(.*)", txt)

            self.assert_(m is not None, "Did not find issuer")

            myIssuer = m.group(1)

            # print "Cert issuer is '%s'" % (issuer)
            # print "My   issuer is '%s'" % (myIssuer)
            # print issuer == myIssuer, type(issuer), type(myIssuer)

            self.assert_(myIssuer == issuer, "Issuers do not match")

        finally:

            try:
                os.unlink(tmp)
            except:
                pass
            
            try:
                os.unlink(reqFile)
            except:
                pass

            try:
                os.unlink(keyFile)
            except:
                pass
            
            try:
                os.unlink(configFile)
            except:
                pass

            

def suite():

    
    suite1 = unittest.makeSuite(AnonReqServerTestCase)
    return unittest.TestSuite([suite1])

if __name__ == "__main__":

    unittest.main(defaultTest = 'suite')
        

        
