#-----------------------------------------------------------------------------
# Name:        CRSClient.py
# Purpose:     Certificate Request Service Client code.
#
# Author:      Ivan R. Judson
#
# Created:     2002/12/12
# RCS-ID:      $Id: CRSClient.py,v 1.2 2004-02-24 21:33:07 judson Exp $
# Copyright:   (c) 2002
# Licence:     See COPYING.TXT
#-----------------------------------------------------------------------------

"""
Sample code using a proxy.


from xmlrpc_urllib_transport import UrllibTransport
import os
os.environ['HTTP_PROXY']= 'http://localhost:3128'

transport = UrllibTransport()
url = "http://www-unix.mcs.anl.gov/~judson/certReqServer.cgi"
proxy = xmlrpclib.ServerProxy(url, transport = transport, verbose=1)

"""

__revision__ = "$Id: CRSClient.py,v 1.2 2004-02-24 21:33:07 judson Exp $"
__docformat__ = "restructuredtext en"

import xmlrpclib
import logging

log = logging.getLogger("AG.CRSClient")

class CRSClientInvalidURL(Exception):
    pass

class CRSClientConnectionFailed(Exception):
    pass

class CRSClient:
    def __init__(self, url, proxyHost = None, proxyPort = None):
        self.url = url
        log.debug('create client')

        if self.url is not None:

            if proxyHost is not None:
                if proxyPort is None:
                    proxyURL = "http://%s" % (proxyHost)
                else:
                    proxyURL = "http://%s:%s" % (proxyHost, proxyPort)

                transport = UrllibTransport(proxyURL)
            else:
                transport = None
                
            self.proxy = xmlrpclib.ServerProxy(url, transport = transport, verbose = 1)
        else:
            raise CRSClientInvalidURL

    def RequestCertificate(self, emailAddress, certReq):
        """
        certificateToken = CRSClient.RequestCertificate(certificateRequest)

            certificateRequest is the PEM-formatted certificate request.

            certificateToken is a unique token used to retrieve the certificate
                when it's ready.

        """

        log.debug("request certificate")
        try:
            token = self.proxy.RequestCertificate(emailAddress, certReq)
        except IOError, e:
            log.exception("IOError on Proxy.RequestCertificate")
            raise CRSClientConnectionFailed
        except StandardError, v:
            log.exception("Exception on xmlrpc RequestCertificate call")
            raise v

        #
        # this should also remove the token from the directory so
        # we don't have to request status for this cert again
        #

        return token

    def RetrieveCertificate(self, token):
        """
        certificate = CRSClient.RetrieveCertificate(certificateToken)
            certificateToken is a unique token used to retrieve the certificate
                when it's ready.
            certificate is the actual signed certificate from the CA
        """

        log.debug("retrieve certificate for token %s", token)

        try:
            certificate = self.proxy.RetrieveCertificate(token)
        except IOError, e:
            log.exception("IOError on Proxy.RetrieveCertificate")
            raise CRSClientConnectionFailed
        except StandardError, v:
            log.exception("error on proxy.RetrieveCertificate(%s)", token)
            raise v

        log.debug("retrieved certificate %s", certificate)
        return certificate

#
# The following code is from:
# http://starship.python.net/crew/jjkunce/python/xmlrpc_urllib_transport.py
#
class UrllibTransport(xmlrpclib.Transport):
	'''Handles an HTTP transaction to an XML-RPC server via urllib
	(urllib includes proxy-server support)
	jjk  07/02/99'''

        def __init__(self, proxy):
            self.proxy = proxy

	def request(self, host, handler, request_body, verbose = None):
		'''issue XML-RPC request
		jjk  07/02/99'''
		import urllib
		self.verbose = verbose
                urlopener = urllib.URLopener(proxies = {"http": self.proxy})
		urlopener.addheaders = [('User-agent', self.user_agent)]
		# probably should use appropriate 'join' methods instead of 'http://'+host+handler
		f = urlopener.open('http://'+host+handler, request_body)
		return(self.parse_response(f))


if __name__ == "__main__":
    req = """-----BEGIN CERTIFICATE REQUEST-----\nMIIB0TCCAToCADBgMRQwEgYDVQQKEwtBY2Nlc3MgR3JpZDEdMBsGA1UECxMUYWdk\nZXYtY2EubWNzLmFubC5nb3YxEjAQBgNVBAsTCW15LmRvbWFpbjEVMBMGA1UEAxMM\nUm9iZXJ0IE9sc29uMIGfMA0GCSqGSIb3DQEBAQUAA4GNADCBiQKBgQC5lvEXiR5R\na6QOJJpRpOXz4R0DxnTVBOvTKvPijSmcc6IbNnNimS7oE/4U+IJtQblOGGdqRwLX\nHOmVY3nDQ60yhQ34ynME3Sr3ntAp6zFp5Ek7LgjOWyEP3hIVWh0Paa36FHn6nCvm\nDYz/1/Ns9c17zK/fWy+PYKMz8Vz0cs2O1wIDAQABoDIwMAYJKoZIhvcNAQkOMSMw\nITARBglghkgBhvhCAQEEBAMCBPAwDAYDVR0TAQH/BAIwADANBgkqhkiG9w0BAQQF\nAAOBgQB5HQyPLAR7XaD6S3Rsso/Q9cbPSxHeWJE4ehF5Ohp+0yAuBpc3L7/LlDkX\nvHri5JGXrGzJGf0/cqzzduh0S/ejMGksNiupsSPlHzkVhQNtAvD6A9OT+25wMyHI\nzSidh+6OJkSBLVb2tkEK5wd844MLE+m0lgTKbNX2C9UAZmfkKw==\n-----END CERTIFICATE REQUEST-----\n"""
    email = "olson+catext@mcs.anl.gov"

    token = "412d8f4d766c6290bd3acc7e74763b72"

    import os

    w, r = os.popen4("openssl req -noout -text")
    w.write(req)
    w.close()
    print r.read()

    submitServerURL = "http://www-unix.mcs.anl.gov/~judson/certReqServer.cgi"
    print "Sending..."
    #certificateClient = CRSClient(submitServerURL)
    certificateClient = CRSClient(submitServerURL, "yips.mcs.anl.gov", 3128)
    #requestId = certificateClient.RequestCertificate(email, req)
    #print "Sent, got id ", requestId

    ret = certificateClient.RetrieveCertificate(token)
    print "got ret ", ret
