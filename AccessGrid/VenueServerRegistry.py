#-----------------------------------------------------------------------------
# Name:        VenueServerRegistry.py
# Purpose:     This serves to keep track of venues servers.
#
# Author:      Ivan R. Judson
#
# Created:     2002/18/12
# RCS-ID:      $Id: VenueServerRegistry.py,v 1.4 2003-02-10 14:47:37 judson Exp $
# Copyright:   (c) 2003
# Licence:     See COPYING.TXT
#-----------------------------------------------------------------------------
import shelve
import string
import time
import ConfigParser

import scheduler

from AccessGrid.hosting.pyGlobus import ServiceBase

class VenueServerRegistry(ServiceBase.ServiceBase):
    store = None
    scheduler = None
    configFile = ''
    config = {
        "VenueServerRegistry.storage" : 'VenueServerRegistry',
        "VenueServerRegistry.checkpointPeriod" : 30,
        "VenueServerRegistry.log" : 'VenueServerRegistry.log'
        }  
    def __init__(self, configFile = ''):
        """ """
        classpath = string.split(str(self.__class__), '.')
        if configFile == '': 
            self.configFile = classpath[0]+'.cfg'
        else:
            self.configFile = configFile
        
        # Instantiate a new config parser
        self.LoadConfig(configFile, self.config)

        self.store = shelve.open(self.config['VenueServerRegistry.storage'], 'c')
        self.scheduler = scheduler.Scheduler()
        self.scheduler.AddTask(self.Checkpoint, 
                               self.config['VenueServerRegistry.checkpointPeriod'], 0)
        self.scheduler.StartAllTasks()
        
    def LoadConfig(self, file, config={}):
        """
        Returns a dictionary with keys of the form <section>.<option> and 
        the corresponding values.
        This is from the python cookbook credit: Dirk Holtwick.
        """
        config = config.copy()
        cp = ConfigParser.ConfigParser()
        cp.read(file)
        for sec in cp.sections():
            name = string.lower(sec)
            for opt in cp.options(sec):
                config[name + "." + string.lower(opt)] = string.strip(
                    cp.get(sec, opt))
        return config

    def Checkpoint(self):
        # This guarantees a flush of everything to storage
        print "Checkpointing at %s" % time.asctime()
        self.store.close()
        self.store = shelve.open(self.config['VenueServerRegistry.storage'])
        
    def Register(self, connectionInfo, venueServerURL, registrationInformation):
        """ This allows the registration of a server. """
        self.store[venueServerURL] = registrationInformation
        
    Register.pass_connection_info = 1
    Register.soap_export_as = "Register"
       
    def ListServers(self, connectionInfo):
        """ This should list all the servers registered. """
        return self.store.keys()
    
    ListServers.pass_connection_info = 1
    ListServers.soap_export_as = "ListServers"

#     def ListCommunities(self, connection_info):
#         """ This lists all the communities this registry knows about."""
#         return self.communities.keys()

#     ListCommunities.pass_connection_info = 1
#     ListCommunities.soap_export_as = "ListCommunities"

#     def AddCommunity(self, connection_info, communityDescription):
#         """Add a new community to this registry service."""
#         self.communities[communityDescription.key] = communityDescription.value
