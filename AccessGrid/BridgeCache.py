from AccessGrid.Utilities import LoadConfig, SaveConfig
from AccessGrid.Platform.Config import UserConfig
from AccessGrid.Descriptions import BridgeDescription

import os

class BridgeCache:
    def __init__(self):
        self.bridges = []
        self.config = UserConfig.instance(initIfNeeded=0)
        self.configPath = self.config.GetBridges()
      
    def GetBridges(self):
        # Get bridges from the local config directory
        self.bridges = []
        bridges = {}
       
        if os.path.exists(self.configPath):
            config = LoadConfig(self.config.GetBridges())
        else:
            # Cache does not exist, return
            return self.bridges
        
        # Parse config dict and create bridge descriptions
        for key in config.keys():
            bridgeid = key.split(".")[0]
            val = key.split(".")[1]

            if not bridges.has_key(bridgeid):
                bridges[bridgeid] = BridgeDescription(bridgeid, "", "", "", "", "")
                         
            if val == "name":
                bridges[bridgeid].name = config[key]
            elif val == "host":
                bridges[bridgeid].host = config[key]
            elif val == "port":
                bridges[bridgeid].port = config[key]
            elif val == "serverType":
                bridges[bridgeid].serverType = config[key]
            elif val == "description":
                bridges[bridgeid].description = config[key]
            elif val == "status":
                bridges[bridgeid].status = config[key]
            elif val == "rank":
                bridges[bridgeid].rank = int(config[key])

        for b in bridges.values():
            self.bridges.append(b)

        return self.bridges
                                
    def StoreBridges(self, bridges):
        self.bridges = bridges
        
        # Store bridges in local config directory
        tempDict = {}
        
        for b in bridges:
            tempDict[""+b.guid+".name"] = b.name
            tempDict[""+b.guid+".host"] = b.host
            tempDict[""+b.guid+".port"] = b.port
            tempDict[""+b.guid+".serverType"] = b.serverType
            tempDict[""+b.guid+".description"]= b.description
            tempDict[""+b.guid+".status"]= b.status
            tempDict[""+b.guid+".rank"]= int(b.rank)
        
        SaveConfig(self.config.GetBridges(), tempDict)
