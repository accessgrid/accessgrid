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
            self.proxy = ServerProxy(url, verbose = 1)
        else:
            raise CRSClientInvalidURL

    def RequestCertificate(self, certReq):
        """
        certificateToken = CRSClient.RequestCertificate(certificateRequest)

            certificateRequest is the PEM-formatted certificate request.

            certificateToken is a unique token used to retrieve the certificate
                when it's ready.
                
        """

        log.debug("request certificate")
        try:
            token = self.proxy.RequestCertificate(certReq)
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

