#!/home/FuturesLab/Software/Python-2.3/bin/python2.3

#
# This is a trivial certificate request management
#

from SimpleXMLRPCServer import CGIXMLRPCRequestHandler
import md5
import smtplib
import os, os.path
import re

import cgitb
cgitb.enable()

certStore = "/home/FuturesLab/agdev-ca"
certEmail = ["agdev-ca@mcs.anl.gov"]
smtpServer = "cliff.mcs.anl.gov"

def RequestCertificate(reqEmail, certReq):
    certEmail = "agdev-ca@mcs.anl.gov"
    fromUser = "judson@mcs.anl.gov"

    token = md5.new(certReq).hexdigest()

    w,r = os.popen2("/usr/bin/openssl req -text -noout"); 
    w.write(certReq)
    w.close()
    opensslTxt = r.read()
    r.close()
    w,r = (None, None)

    m = re.search("Subject:(.*)$", opensslTxt, re.MULTILINE)
    opensslSubject = m.group(1)
    subject = "Cert Req: %s" % opensslSubject

    # Save Request
    #  - make a directory named <token>
    #  - store the req
    certReqPath = os.path.join(certStore, token)
    try:
        os.mkdir(certReqPath)
	os.chmod(certReqPath, 0777)
    except:
        cgitb.handler()

    fn = os.path.join(certStore, token, "certreq.pem")
    cf = file(fn, "w")
    cf.write(certReq)
    cf.close()
    os.chmod(fn, 0777)

    # Save meta information
    fn = os.path.join(certStore, token, "metainfo.txt")
    cf = file(fn, "w")
    envString = "EMAIL %s\n" % reqEmail
    for key in os.environ.keys():
	envString += "%s\t%s\n" % (key, os.environ[key])
    cf.write(envString)
    cf.close()
    os.chmod(fn, 0777)

    # Send email to local address
    message = """\
To: %(certEmail)s
Subject: %(subject)s
Reply-To: agdev-ca@mcs.anl.gov
From: %(fromUser)s
X-Mailer: Python CGI Script

A new certificate has been requested for: 

Subject: %(opensslSubject)s
Email: %(reqEmail)s

Instructions for signing certificates:
--------------------------------------
	
In order to sign this certificate please execute the following commands from a machine on the MCS network.

> ssh fl-caserver.mcs.anl.gov
> cd /disks/space0/agdev-ca
> sudo -H bash
> ./sign_certs.sh

Then you'll be prompted for your password to copy the pending requests locally to the CA server. Then you'll be prompted for the CA signing password for each cert you sign. Then you'll be prompted for your password to copy all the newly signed certs back to the web accessible directory.

-- The AG Dev CA Service
	
%(certReq)s 
------------- OpenSSL Dump -------------
%(opensslTxt)s
------------- Calling environment -------------
%(envString)s
"""

    SendMail(smtpServer, fromUser, [certEmail], message % locals())

    # Return token    
    return token

def RetrieveCertificate(token):
    retString = ""
    success = 1

    if os.path.exists(os.path.join(certStore, token)):
	try:
	    cf = file(os.path.join(certStore, token, "cert.pem"))
	except:
	    success = 0
	    retString = "Couldn't open certificate file."

        # Retrieve certificate
	try:
	    retString = cf.read()
	except:
	    success = 0
	    retString = "Couldn't read from certificate file."
    else:
	success = 0
	retString = "There is no certificate for this token."

    return (success, retString)

def SendMail(server, fromAddr, toAddr, message):
    server = smtplib.SMTP(server)
    server.sendmail(fromAddr, toAddr, message)
    server.quit()

server = CGIXMLRPCRequestHandler()
server.register_function(RequestCertificate)
server.register_function(RetrieveCertificate)
server.handle_request()


