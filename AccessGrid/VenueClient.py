#-----------------------------------------------------------------------------
# Name:        VenueClient.py
# Purpose:     This is the client side object of the Virtual Venues Services.
#
# Author:      Ivan R. Judson
#
# Created:     2002/12/12
# RCS-ID:      $Id: VenueClient.py,v 1.2 2003-01-07 20:27:13 judson Exp $
# Copyright:   (c) 2002
# Licence:     See COPYING.TXT
#-----------------------------------------------------------------------------

from AccessGrid.hosting.pyGlobus import Client
from AccessGrid.CoherenceClient import CoherenceClient
from AccessGrid.ClientProfile import ClientProfile

class VenueClient:
	"""
	This is the client side object that maintains a stateful
	relationship with a Virtual Venue. This object provides the
	programmatic interface to the Access Grid for a Venues User
	Interface.  The VenueClient can only be in one venue at a
	time.
	"""
	profile = None
	currentVenue = None

	venueState = None
	coherenceClient = None

	nodeService = None
	workspaceDock = None
	
	def __init__(self, profile = None):
		"""
		This client class is used on shared and personal nodes.
		"""
		self.profile = profile
		self.nodeService = None
		self.workspaceDock = None

	def SetProfile(self, profile):
		self.profile = profile
		
	def coherenceCallback(self, data):
		print "Got coherence event: " + str(data)
		
	def EnterVenue(self, URL):
		"""
		EnterVenue puts this client into the specified venue.
		"""
		self.currentVenue = Client.Handle(URL).get_proxy()
		state = self.currentVenue.Enter(self.profile)
		print dir(state)
		print state['users']
		print dir(state['users'])
		cl = state['coherenceLocation']
		self.coherenceClient = CoherenceClient(cl['host'], cl['port'],
						       self.coherenceCallback)
		self.coherenceClient.start()
		
	def ExitVenue(self):
		"""
		ExitVenue removes this client from the specified venue.
		"""
		self.currentVenue.Exit()
		
	def GetVenue(self):
		"""
		GetVenue gets the venue the client is currently in.
		"""
		
	def AddService(self, serviceDescription):
		"""
		AddService adds a service to the client. The expected
		minimum set of services always present include:
		Workspace Docking Service
		Node Service
		"""
		
	def RemoveService(self, serviceDescription):
		"""
		RemoveService removes a service from the client.
		"""
		
	def ModifyService(self, serviceDescription):
		"""
		ModifyService modifies a service description for a
		service in the Venue.
		"""
		
	def GetServices(self):
		"""
		GetServices returns the list of services provided by this client.
		"""
		
	def GetHomeVenue(self):
		"""
		GetHomeVenue returns the default venue for this venue client.
		"""
		
	def SetHomeVenue(self, venueURL):
		"""
		SetHomeVenue sets the default venue for this venue client.
		"""
		
	def FollowNode(self, clientProfile):
		"""
		FollowNode tells this venue client to follow the node
		specified.
		"""
		
	def UnfollowNode(self, clientProfile):
		"""
		UnfollowNode tells this venue client to stop following
		the node specified.
		"""
		
	def LeadNode(self, clientProfile):
		"""
		LeadNode tells this venue client to drag the specified
		node with it.
		"""

if __name__ == "__main__":
	from AccessGrid.hosting.pyGlobus import Client
	profile = ClientProfile('userProfileExample')
	
	vms = Client.Handle('https://localhost:8000/VenueServer').get_proxy()
	vc = VenueClient(profile)
	vc.EnterVenue(vms.GetDefaultVenue())

		
