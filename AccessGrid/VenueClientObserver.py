#!/usr/bin/python
#-----------------------------------------------------------------------------
# Name:        VenueClientObserver.py
# Purpose:    
#             
#
# Author:      Thomas D. Uram
#
# Created:     2004/02/02
# Copyright:   (c) 2002-2004
# Licence:     See COPYING.TXT
#-----------------------------------------------------------------------------

"""
"""

__revision__ = "$Id: VenueClientObserver.py,v 1.1 2004-02-24 17:04:56 turam Exp $"
__docformat__ = "restructuredtext en"


class PassiveVenueClientObserver:

    # User Methods
    def AddUser(self,profile):                      pass
    def RemoveUser(self,profile):                   pass
    def ModifyUser(self,profile):                   pass
    
    # Data Methods
    def AddData(self,dataDescription):              pass
    def RemoveData(self,dataDescription):           pass
    def UpdateData(self,dataDescription):           pass
    
    # Service Methods
    def AddService(self,serviceDescription):        pass
    def RemoveService(self,serviceDescription):     pass
    
    # Application Methods
    def AddApplication(self,appDescription):        pass
    def RemoveApplication(self,appDescription):     pass
    
    # Exit/Connection Methods
    def AddConnection(self,connDescription):        pass
    def RemoveConnection(self,connDescription):     pass
    def SetConnections(self,connDescriptionList):   pass
    
    def AddStream(self, streamDesc):                pass
    def RemoveStream(self, streamDesc):             pass
    def ModifyStream(self, streamDesc):             pass

    def AddText(self,name,text):                    pass
    
    def EnterVenue(self, URL, warningString="", enterSuccess=1): pass
    def ExitVenue(self):                            pass
    
    
class RestrictiveVenueClientObserver:

    # User Methods
    def AddUser(self,profile):
		raise Exception("VenueClientObserver.AddUser not implemented")

    def RemoveUser(self,profile):
		raise Exception("VenueClientObserver.RemoveUser not implemented")

    def ModifyUser(self,profile):
		raise Exception("VenueClientObserver.ModifyUser not implemented")
    
    # Data Methods
    def AddData(self,dataDescription):
		raise Exception("VenueClientObserver.AddData not implemented")

    def RemoveData(self,dataDescription):
		raise Exception("VenueClientObserver.RemoveData not implemented")

    def UpdateData(self,dataDescription):
		raise Exception("VenueClientObserver.UpdateData not implemented")
    
    # Service Methods
    def AddService(self,serviceDescription):
		raise Exception("VenueClientObserver.AddService not implemented")

    def RemoveService(self,serviceDescription):
		raise Exception("VenueClientObserver.RemoveService not implemented")
    
    # Application Methods
    def AddApplication(self,appDescription):
		raise Exception("VenueClientObserver.AddApplication not implemented")

    def RemoveApplication(self,appDescription):
		raise Exception("VenueClientObserver.RemoveApplication not implemented")

    # Exit/Connection Methods
    def AddConnection(self,connDescription):
		raise Exception("VenueClientObserver.AddConnection not implemented")

    def RemoveConnection(self,connDescription):
		raise Exception("VenueClientObserver.RemoveConnection not implemented")

    def SetConnections(self,connDescriptionList):
		raise Exception("VenueClientObserver.SetConnections not implemented")

    def AddStream(self, streamDesc):
		raise Exception("VenueClientObserver.AddStream not implemented")

    def RemoveStream(self, streamDesc):
		raise Exception("VenueClientObserver.RemoveStream not implemented")

    def ModifyStream(self, streamDesc):
		raise Exception("VenueClientObserver.ModifyStream not implemented")

    def AddText(self,name,text):
		raise Exception("VenueClientObserver.AddText not implemented")

    def EnterVenue(self, URL, warningString="", enterSuccess=1):
		raise Exception("VenueClientObserver.EnterVenue not implemented")

    def ExitVenue(self):
		raise Exception("VenueClientObserver.ExitVenue not implemented")


VenueClientObserver = RestrictiveVenueClientObserver




class TestVenueClientObserver(VenueClientObserver):

    def __init__(self):
        pass
        
    def Method(self,arg=0,name=0,arg2=0,arg3=0,arg4=0,arg5=0):
        print "Method %s got %s %s %s %s %s" % (self.m,arg,arg2,arg3,arg4,arg5)
    
    def __getattr__(self,name):
        self.m = name
        return self.Method
        
    def __nonzero__(self):
        return 1
    
