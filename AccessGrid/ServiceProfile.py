#-----------------------------------------------------------------------------
# Name:        ServiceProfile.py
# Purpose:     Describe credentials for a service (e.g., VenueServer)
# Created:     2004/03/18
# RCS-ID:      $Id: ServiceProfile.py,v 1.2 2004-03-18 19:54:49 turam Exp $
# Copyright:   (c) 2002
# Licence:     See COPYING.TXT
#-----------------------------------------------------------------------------

"""
This class exports/imports service profile files in INI format, as follows:

[ServiceProfile]
serviceType = VenueServer
cred = Cred1


[Cred1]
# subject refers to a certificate in the user's cert repository
authType = x509
subject = /O=Access Grid/OU=agdev-ca.mcs.anl.gov/OU=mcs.anl.gov/CN=Thomas Uram

[Cred2]
# certfile/keyfile refer to certificate and key files
authType = x509
certfile = /home/smith/VenueServer_cert.pem
keyfile = /home/smith/VenueServer_key.pem


"""

import ConfigParser


class InvalidServiceProfile(Exception):
    pass


class ServiceProfile:
    """
    ServiceProfile class used for identifying credentials
    utilized by services in the AGTk
    """

    def __init__(self, serviceType = None, 
                 authType = None,
                 certfile = None, keyfile = None,
                 subject = None ):
                 
        if serviceType and ( certfile or keyfile ):
            raise ValueError(
                    "Only one of subject and (certfile/keyfile) is allowed")
         
        self.serviceType = serviceType
        self.authType = authType
        
        self.subject = subject
        self.certfile = certfile
        self.keyfile = keyfile
        
    PROFILE_SECTION = "ServiceProfile"
    SERVICE_TYPE = "serviceType"
    CRED = "cred"
    
    CRED_SECTION = "Cred"
    AUTHTYPE = "authType"
    SUBJECT = "subject"
    CERTFILE = "certfile"
    KEYFILE = "keyfile"
    
    def Export(self,filepath):
    
        f = open(filepath,"w")
        f.write(self.AsINIBlock())
        f.close()
    
    def Import(self,filepath):
    
        cp = ConfigParser.ConfigParser()
        cp.read(filepath)
        
        if (cp.has_option(self.PROFILE_SECTION,self.SUBJECT) and
            cp.has_option(self.PROFILE_SECTION,self.CERTFILE) and
            cp.has_option(self.PROFILE_SECTION,self.KEYFILE) ):
            raise InvalidServiceProfile(
                    "Only one of subject and (certfile/keyfile) is allowed")
        
        # ServiceProfile section
        self.serviceType = cp.get(self.PROFILE_SECTION,self.SERVICE_TYPE)
        
        # Credential section
        if cp.has_option(self.CRED_SECTION,self.AUTHTYPE):
            self.authType = cp.get(self.CRED_SECTION,self.AUTHTYPE)
        if cp.has_option(self.CRED_SECTION,self.SUBJECT):
            self.subject = cp.get(self.CRED_SECTION,self.SUBJECT)
        if cp.has_option(self.CRED_SECTION,self.CERTFILE):
            self.certfile = cp.get(self.CRED_SECTION,self.CERTFILE)
        if cp.has_option(self.CRED_SECTION,self.KEYFILE):
            self.keyfile = cp.get(self.CRED_SECTION,self.KEYFILE)
        
    def AsINIBlock(self):
        
        iniBlock = ""
        iniBlock += "[%s]\n" %(self.PROFILE_SECTION)
        iniBlock += "%s = %s\n" % (self.SERVICE_TYPE,self.serviceType)
        iniBlock += "%s = %s\n" % (self.CRED,self.CRED_SECTION)
        iniBlock += "[%s]\n" % (self.CRED_SECTION)
        if self.authType:  iniBlock += "%s = %s\n" % (self.AUTHTYPE,self.authType)
        if self.subject:   iniBlock += "%s = %s\n" % (self.SUBJECT,self.subject)
        if self.certfile:  iniBlock += "%s = %s\n" % (self.CERTFILE,self.certfile)
        if self.keyfile:   iniBlock += "%s = %s\n" % (self.KEYFILE,self.keyfile)
        return iniBlock
        
        
    def Print(self):
        print self.AsINIBlock()


    def Compare(self,serviceProfile2):
        return (self.serviceType == serviceProfile2.serviceType and
                self.subject == serviceProfile2.subject and 
                self.certfile == serviceProfile2.certfile and
                self.keyfile == serviceProfile2.keyfile )

if __name__ == "__main__":
    
    profileFile = "/tmp/VenueServerProfile"
    
    try:
        ServiceProfile("VenueServer",subject="MY DN",certfile="file",keyfile="key")
    except ValueError, e:
        print "Exception setting too many attrs in ServiceProfile"
    
    serviceProfile = ServiceProfile("VenueServer", authType = "x509", subject = "MY DN")
    serviceProfile.Export(profileFile)
    serviceProfile2 = ServiceProfile()
    serviceProfile2.Import(profileFile)
    
    serviceProfile.Print()
    serviceProfile2.Print()
    
    if serviceProfile.Compare(serviceProfile2):
        print "Export/import of service profile verified"
    else:
        print "Export/import of service profile failed"
        

    
