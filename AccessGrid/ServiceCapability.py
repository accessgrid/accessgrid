import xml.dom.minidom
import re
                                     
class ServiceCapability:
    # General options
    TITLE = 'ServiceCapability'
    PRODUCER = 'producer'
    CONSUMER = 'consumer'
    TRANSFORMER = 'transformer'
    
    # Configuration options
    ENCODING_NAME = 'ENCODING_NAME'
    ENCODING_QUALITY = 'ENCODING_QUALITY'
    ENCODING_BIT_RATE = 'ENCODING_BITRATE'
    ENCODING_SIZE = 'ENCODING_SIZE'
    DEVICE_SAMPLE_RATE = 'DEVICE_SAMPLE_RATE'
    DEVICE_SAMPLE_SIZE = 'DEVICE_SAMPLE_SIZE'
    DEVICE_SAMPLE_FORMAT = 'DEVICE_SAMPLE_FORMAT'
    RTP_PAYLOAD_TYPE = 'RTP_PAYLOAD_TYPE'
    RTP_PROFILE = 'RTP_PROFILE'
       
    def __init__(self, name, role, type, config):
        '''
        Initiates the class.

        **Arguments:**

        *name* The name of the service (string)
        *role* The role of service (producer/consumer)
        *type* The type of service (audio/video/text)
        '''

        self.__name = name
        self.role = role
        self.type = type
        self.parms = {}
        self.__config = config
            
    def CreateServiceCapability(xmlDoc):
        '''
        Static method that creates a ServiceCapability object
        from an xml document.

        ** Arguments **

        *xmlDoc* xml document that describing a ServiceCapability object.
        '''

        config = {}
        xmlDoc = str(xmlDoc)

        # We can't persist crlf or cr or lf, so we replace them
        # on each end (when storing and loading)
        xmlDoc = re.sub("<CRLF>", "\r\n", xmlDoc)
        xmlDoc = re.sub("<CR>", "\r", xmlDoc)
        xmlDoc = re.sub("<LF>", "\n", xmlDoc)
        
        domP = xml.dom.minidom.parseString(xmlDoc)
        
        capabilityElements = domP.getElementsByTagName("General")
        name = capabilityElements[0].attributes["name"].value
        role = capabilityElements[0].attributes["role"].value
        type = capabilityElements[0].attributes["type"].value

        configElements = domP.getElementsByTagName("Configuration")
        
        for element in configElements:
            for key in element.attributes.keys():
                config[str(key)] = str(element.attributes[key].value)

        return ServiceCapability(name, role, type, config)

    # Makes it possible to access the method without an instance.
    CreateServiceCapability = staticmethod(CreateServiceCapability)

    def Matches(self, capability):
        '''
        Compares this instance to another capability.  If the type and
        configuration parameters are equal, the capabilities match.

        ** Arguments **

        *capability* Capability to compare.

        ** Returns **
        
        *int* 1 if the capabilities match, otherwise 0.
        '''

        if self.type != capability.GetType():
            print 'type %s does not match %s'%(self.type, capability.GetType())
            return 0

        otherConfig = capability.GetConfiguration()
        
        for key in otherConfig.keys():
            if not otherConfig.has_key(key):
                print 'key %s is not in config' %key
                return 0

            if not self.__config.has_key(key):
                print 'key %s is not in config' %key
                return 0
            
            if self.__config[key] != otherConfig[key]:
                print 'value mismatch for %s.%s: %s != %s' %(self.__name, key, self.__config[key], otherConfig[key])
                return 0

        return 1
            
    def SetConfiguration(self, config):
        '''
        Set configuration dictionary.

        ** Arguments **

        * config * Dictionary containing configuration options and their values (option:value)
        '''

        self.__config = config

    def GetConfiguration(self):
        '''
        Get configuration dictionary.

        ** Returns **

        * config * Dictionary containing configuration options and their values (option:value)
        '''
        
        return self.__config

    def SetConfigOption(self, option, data):
        '''
        Set a configuration option.

        ** Arguments **

        * option * Configuration option (for example, ServiceCapability.ENCODING_NAME)

        * data * Configuration data as a string (for example, H.261)
        '''

        # Make sure the config option is a string.
        self.__config[option] = str(data)

    def HasConfigOption(self, option):
        '''
        Check if a configuration option exists.

        ** Arguments **
        
        * option * Configuration option (for example, ServiceCapability.ENCODING_NAME)

        ** Returns **

        * data * Corresponding data for option.
        '''
        
        return self.__config.has_key(option)
    
    def SetName(self, name):
        '''
        Set the name of this capability.
        
        ** Arguments **

        * name * The name of describing the capability.
        '''
        self.__name = name

    def GetName(self):
        '''
        Get the name of this capability.
        
        ** Returns **

        *name* The name of the capability
         '''
        return self.__name
        
    def SetRole(self, role):
        '''
        Set the role of this capability

        ** Arguments **

        * role * the role of this capability (consumer/producer)
        '''
        
        self.role = role

    def GetRole(self):
        '''
        Get the role of this capability

        ** Returns **

        * role * the role of this capability (consumer/producer)
        '''
        return self.role

    def SetType(self, type):
        '''
        Set the type of this capability

        ** Arguments **

        * type * the type of this capability (audio/video/text)
        '''
        self.type = type

    def GetType(self):
        '''
        Get the type of this capability.

        ** Returns **
        
        * type * the type of this capability (audio/video/text) 
        '''
        return self.type
               
    def ToXML(self):
        '''
        Creates an xml document describing this capability.

        ** Returns **
        
        *doc* xml document
        '''
        # Build xml document
        domImpl = xml.dom.minidom.getDOMImplementation()
        self.doc = domImpl.createDocument(xml.dom.minidom.EMPTY_NAMESPACE,
                                          "ServiceCapability", '')
        self.xmlDoc = self.doc.documentElement
        
        # Set type; Consumer/Producer/Transformer
        optionsDoc = self.doc.createElement('General')
        optionsDoc.setAttribute("name", self.__name)
        optionsDoc.setAttribute("role", self.role)
        optionsDoc.setAttribute("type", self.type)
        self.xmlDoc.appendChild(optionsDoc)
        
        confDoc = self.doc.createElement("Configuration")
        for option in self.__config.keys():
            confDoc.setAttribute(option, self.__config[option])
            
        self.xmlDoc.appendChild(confDoc)

        x = self.doc.toxml()

        # We can't persist crlf or cr or lf, so we replace them
        # on each end (when storing and loading)
        x = re.sub("\r\n", "<CRLF>", x)
        x = re.sub("\r", "<CR>", x)
        x = re.sub("\n", "<LF>", x)
                                     
        return x

if __name__ == "__main__":
    # Create config.
    config = {ServiceCapability.DEVICE_SAMPLE_RATE:'20', ServiceCapability.DEVICE_SAMPLE_SIZE:'35',
              ServiceCapability.DEVICE_SAMPLE_FORMAT:'format1', ServiceCapability.ENCODING_NAME:'H.261',
              ServiceCapability.ENCODING_QUALITY:'10', ServiceCapability.ENCODING_BIT_RATE:'164',
              ServiceCapability.ENCODING_SIZE:'20'}
    
    nsc = ServiceCapability('Test Capability', ServiceCapability.CONSUMER, 'video', config)
    nsc2 = ServiceCapability.CreateServiceCapability(nsc.ToXML())
    print '================'
    print nsc2.ToXML()
         
    # Create XML document.
    xmlDoc = nsc.ToXML()
    print '--- XML document --- \n', xmlDoc

    # Create configs from xml.
    nsc2 = ServiceCapability.CreateServiceCapability(xmlDoc)
    nsc2.SetRole(ServiceCapability.PRODUCER)
    nsc2.SetType('audio')
    option = ServiceCapability.ENCODING_NAME
    nsc2.SetConfigOption(option, 'H.261')
    print '\ndo we have this config option', option, '?', nsc2.HasConfigOption(option)
    print '\ndo they match?', nsc2.Matches(nsc)
    print '\n*** Role: ', nsc2.GetRole()
    print '*** Type: ', nsc2.GetType()
    print '*** Config *** \n', nsc2.GetConfiguration()
                
    
   

    
