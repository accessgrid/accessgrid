
# Schema: module, import, class
mapping = {
    "ClientProfile" : ("AccessGrid.ClientProfile", "ClientProfile"),
    "ConnectionDescription" : ("AccessGrid.Descriptions", "ConnectionDescription"),
    "ApplicationDescription" : ("AccessGrid.Descriptions", "ApplicationDescription"),
    "ApplicationCmdDescription" : ("AccessGrid.Descriptions", "ApplicationCmdDescription"),
    "AppDataDescription" : ("AccessGrid.Descriptions", "AppDataDescription"),
    "ServiceDescription" : ("AccessGrid.Descriptions", "ServiceDescription"),
    "DataDescription" : ("AccessGrid.Descriptions", "DataDescription"),
    "VenueDescription" : ("AccessGrid.Descriptions", "VenueDescription"),
    "StreamDescription" : ("AccessGrid.Descriptions", "StreamDescription"),
    "EventDescription" : ("AccessGrid.Descriptions", "EventDescription"),
    "NetworkLocation" : ("AccessGrid.NetworkLocation", "NetworkLocation"),
    "MulticastNetworkLocation" : ("AccessGrid.NetworkLocation", "MulticastNetworkLocation"),
    "UnicastNetworkLocation" : ("AccessGrid.NetworkLocation", "UnicastNetworkLocation"),
    "ProviderProfile" : ("AccessGrid.NetworkLocation", "ProviderProfile"),
    "AppParticipantDescription" : ("AccessGrid.Descriptions", "AppParticipantDescription"),
    "SharedAppState" : ("AccessGrid.Descriptions", "SharedAppState"),
    "VenueState" : ("AccessGrid.Descriptions", "VenueState"),
    "ResourceDescription" : ("AccessGrid.Descriptions", "ResourceDescription"),
    
    # Node management
    "NodeConfigDescription" : ("AccessGrid.Descriptions", "NodeConfigDescription"),
    "AGServiceManagerDescription" : ("AccessGrid.Descriptions", "AGServiceManagerDescription"),
    "AGServicePackageDescription" : ("AccessGrid.Descriptions", "AGServicePackageDescription"),
    "AGServiceDescription" : ("AccessGrid.Descriptions", "AGServiceDescription"),
    "Capability" : ("AccessGrid.Descriptions", "Capability"),
    "ValueParameter" : ("AccessGrid.AGParameter", "ValueParameter"),
    "TextParameter" : ("AccessGrid.AGParameter", "TextParameter"),
    "OptionSetParameter" : ("AccessGrid.AGParameter","OptionSetParameter"),
    "RangeParameter" : ("AccessGrid.AGParameter","RangeParameter"),

    
    
    # Authorization Manager
    "Role" : ("AccessGrid.Security.Role", "Role"),
    "Action" : ("AccessGrid.Security.Action", "Action"),
    "Subject" : ("AccessGrid.Security.Subject", "Subject"),
    "X509Subject" : ("AccessGrid.Security.X509Subject", "X509Subject"),


    
}

