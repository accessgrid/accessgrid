#
# Certificate Request Service Client
#
from xmlrpclib import ServerProxy

import logging

log = logging.getLogger("AG.CRSClient")

class CRSClientInvalidURL(Exception):
    pass

class CRSClient:
    def __init__(self, url):
        self.url = url
        log.debug('create client')

        if self.url is not None:
            self.proxy = ServerProxy(url, verbose = 0)
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
        except StandardError, v:
            log.exception("error on proxy.RetrieveCertificate(%s)", token)
            raise v

        log.debug("retrieved certificate %s", certificate)
        return certificate

if __name__ == "__main__":
    req = """-----BEGIN CERTIFICATE REQUEST-----\nMIIB0TCCAToCADBgMRQwEgYDVQQKEwtBY2Nlc3MgR3JpZDEdMBsGA1UECxMUYWdk\nZXYtY2EubWNzLmFubC5nb3YxEjAQBgNVBAsTCW15LmRvbWFpbjEVMBMGA1UEAxMM\nUm9iZXJ0IE9sc29uMIGfMA0GCSqGSIb3DQEBAQUAA4GNADCBiQKBgQC5lvEXiR5R\na6QOJJpRpOXz4R0DxnTVBOvTKvPijSmcc6IbNnNimS7oE/4U+IJtQblOGGdqRwLX\nHOmVY3nDQ60yhQ34ynME3Sr3ntAp6zFp5Ek7LgjOWyEP3hIVWh0Paa36FHn6nCvm\nDYz/1/Ns9c17zK/fWy+PYKMz8Vz0cs2O1wIDAQABoDIwMAYJKoZIhvcNAQkOMSMw\nITARBglghkgBhvhCAQEEBAMCBPAwDAYDVR0TAQH/BAIwADANBgkqhkiG9w0BAQQF\nAAOBgQB5HQyPLAR7XaD6S3Rsso/Q9cbPSxHeWJE4ehF5Ohp+0yAuBpc3L7/LlDkX\nvHri5JGXrGzJGf0/cqzzduh0S/ejMGksNiupsSPlHzkVhQNtAvD6A9OT+25wMyHI\nzSidh+6OJkSBLVb2tkEK5wd844MLE+m0lgTKbNX2C9UAZmfkKw==\n-----END CERTIFICATE REQUEST-----\n"""
    email = "olson+catext@mcs.anl.gov"

    import os

    w, r = os.popen4("openssl req -noout -text")
    w.write(req)
    w.close()
    print r.read()

    submitServerURL = "http://www-unix.mcs.anl.gov/~judson/certReqServer.cgi"
    print "Sending..."
    certificateClient = CRSClient(submitServerURL)
    requestId = certificateClient.RequestCertificate(email, req)
    print "Sent, got id ", requestId
