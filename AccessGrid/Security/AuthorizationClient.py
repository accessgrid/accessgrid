#-----------------------------------------------------------------------------
# Name:        AuthorizationClient.py
# Purpose:     The class that does the authorization work.
#
# Author:      Ivan R. Judson
#
# Created:     
# RCS-ID:      $Id: AuthorizationClient.py,v 1.2 2004-02-24 21:33:07 judson Exp $
# Copyright:   (c) 2002
# Licence:     See COPYING.TXT
#-----------------------------------------------------------------------------

"""
Authorization Client Object, to simplify client side programming.
"""

__revision__ = "$Id: AuthorizationClient.py,v 1.2 2004-02-24 21:33:07 judson Exp $"
__docformat__ = "restructuredtext en"

class AuthorizationClient:
    """
    This object is designed to provide a simple interface that hides
    the network plumbing between clients and servers.
    """
    def __init__(self, url=None):
        self.proxy = None
        self.url = url
        if url != None:
            self.Connect()

    def Connect(self):
        if self.proxy == None:
            try:
                self.proxy = Client.Handle(self.url).GetProxy()
            except Exception, e:
                print "Exception connecting authorization client: ", e

    
    def AddRole(self, name):
        pass

    def RemoveRole(self, name):
        pass

    def ListRoles(self):
        """
        """
        return self.proxy.ListRoles()        

    def AddAction(self, name):
        pass

    def RemoveAction(self, name):
        pass

    def ListActions(self):
        """
        """
        return self.proxy.ListActions()

    def ListSubjectsInRole(self, role):
        pass

    def ListRolesInAction(self, action):
        pass
    
    def AddSubjectToRole(self, subj, role):
        pass

    def AddRoleToAction(self, role, action):
        pass

    def RemoveSubjectFromRole(self, subj, role):
        pass

    def RemoveRoleFromAction(self, role, action):
        pass

    def IsAuthorized(self, subject, action):
        """
        """
        return self.proxy.IsAuthorized(subject, action)


    
        
