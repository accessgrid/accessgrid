
import ConfigParser



class ServiceProfile:
    """
    ServiceProfile class used for identifying credentials
    utilized by services in the AGTk
    """

    def __init__(self, serviceType, 
                 certfile = None, keyfile = None,
                 subject = None ):
        if serviceType and ( certfile or keyfile ):
            raise ValueError("subject and (certfile|keyfile) args are mutually exclusive")
         
        self.serviceType = serviceType
        self.subject = subject
        self.certfile = certfile
        self.keyfile = keyfile
        
    SECTION = "ServiceProfile"
    SERVICE_TYPE = "serviceType"
    SUBJECT = "subject"
    
    def Export(self,file):
    
        f = open(file,"w")
        f.write(self.AsINIBlock())
        f.close()
    
    def Import(self,file):
    
        cp = ConfigParser.ConfigParser()
        cp.read(file)
        self.serviceType = cp.get(self.SECTION,self.SERVICE_TYPE)
        self.subject = cp.get(self.SECTION,self.SUBJECT)
        return self
        
    def AsINIBlock(self):
        
        iniBlock = ""
        iniBlock += "[%s]\n" %(self.SECTION)
        iniBlock += "%s = %s\n" % (self.SERVICE_TYPE,self.serviceType)
        iniBlock += "%s = %s\n" % (self.SUBJECT,self.subject)
        return iniBlock


def CompareProfiles(serviceProfile,serviceProfile2):
    return (serviceProfile.serviceType == serviceProfile2.serviceType and
            serviceProfile.subject == serviceProfile2.subject and 
            serviceProfile.certfile == serviceProfile2.certfile and
            serviceProfile.keyfile == serviceProfile2.keyfile )
        
if __name__ == "__main__":
    
    profileFile = "/tmp/VenueServerProfile"
    
    try:
        ServiceProfile("VenueServer",subject="MY DN",certfile="file",keyfile="key")
    except ValueError:
        print "Exception setting too many attrs in ServiceProfile"
    
    serviceProfile = ServiceProfile("VenueServer", subject = "MY DN")
    serviceProfile.Export(profileFile)
    serviceProfile2 = serviceProfile.Import(profileFile)
    
    if CompareProfiles(serviceProfile,serviceProfile2):
        print "Export/import of service profile verified"
    else:
        print "Export/import of service profile failed"
        

    
