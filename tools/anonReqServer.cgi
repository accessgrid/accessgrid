#!/home/FuturesLab/Software/Python-2.3/bin/python2.3

from SimpleXMLRPCServer import CGIXMLRPCRequestHandler
import md5
import os, os.path
import re
import sys
import time

sys.path.append('/home/olson/AG/pyopenssl/lib/python2.3/site-packages')
from  OpenSSL_AG import crypto

#import cgitb
#cgitb.enable()

ca_dir = "/home/olson/AG/auth/anonca"
certStore = "/home/olson/AG/auth/anon_certs"

def RequestCertificate(reqEmail, certReq):

    #if not 'SSL_PROTOCOL' in os.environ:
    #    return (0, "Must use https")

    txt = open(os.path.join(ca_dir, "cacert.pem")).read()
    ca = crypto.load_certificate(crypto.FILETYPE_PEM, txt)
    pk = crypto.load_privatekey(crypto.FILETYPE_PEM,
                                open(os.path.join(ca_dir, "private", "cakey.pem")).read())

    req = crypto.load_certificate_request(crypto.FILETYPE_PEM, certReq)


    #
    # Create the CN for the new cert.
    # We ignore whatever they sent and fill in the anon one.
    #

    ca_name_parts = filter(lambda a: a[0] != "CN" and a[0] != 'USERID', ca.get_subject().get_name_components())

    #
    # Okay, go ahead and create a new cert and sign it.
    #


    cert = crypto.X509()
    cert.set_serial_number(int(time.time()))
    cert.set_version(2)

    cert.gmtime_adj_notAfter(86400 * 365)
    cert.gmtime_adj_notBefore(-10)

    for n in ca.get_subject().get_name_components():
        cert.get_issuer().add(n[0], n[1])

    for n in ca_name_parts:
        cert.get_subject().add(n[0], n[1])

    rfh = open("/dev/urandom");
    
    rhash = md5.new(certReq)
    rhash.update(str(time.time()))
    rhash.update(rfh.read(1024))
    rval = rhash.hexdigest()
    rfh.close()
    
    cert.get_subject().add("CN", "Anonymous User " + rval)

    cert.set_pubkey(req.get_pubkey())
    exts = [("nsCertType", 0, "client,server,objsign,email"),
            ("basicConstraints", 1, "CA:false"),
            ("nsComment", 0, "Generated by passwd check authenticator")]

    xextlist = []
    for name, critical, value in exts:
        cert.add_extension(name, critical, value)

    digest = "md5"

    cert.sign(pk, digest)
        
    #
    # Write out to the local space so it can get picked up later.
    #

    token = md5.new(certReq).hexdigest()

    localfh = open(os.path.join(certStore, token), "w")
    print >>localfh,  crypto.dump_certificate(crypto.FILETYPE_PEM, cert)
    localfh.close()

    return token

def RetrieveCertificate(token):
    retString = ""
    success = 1

    try:
        fh = open(os.path.join(certStore, token))
        retString = fh.read()
        fh.close()
        
    except:
        success = 0
        retString = "Couldn't read from certificate file."


    return (success, retString)

def RetrieveCACertificate():
    try:
        fh = open(os.path.join(ca_dir, "cacert.pem"))
        txt = fh.read()
        fh.close()
    except IOError:
        return (0, "Error reading cert file")
    
    return (1, txt)
    
def RetrieveSigningPolicy():
    try:
        fh = open(os.path.join(ca_dir, "cacert.policy"))
        txt = fh.read()
        fh.close()
    except IOError:
        return (0, "Error reading signing policy")
    
    return (1, txt)
    

server = CGIXMLRPCRequestHandler()
server.register_function(RequestCertificate)
server.register_function(RetrieveCertificate)
server.register_function(RetrieveCACertificate)
server.register_function(RetrieveSigningPolicy)
server.handle_request()


