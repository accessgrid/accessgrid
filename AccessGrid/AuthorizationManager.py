
class AuthorizationManager:
   """
   AuthorizationManager : encapsulation of an authorization list and authorization against it
   """


   def __init__( self ):
      self.authorizedUsers = []

   def GetAuthorizedUsers( self ):
      """Get the list of authorized users"""
      return self.authorizedUsers

   def SetAuthorizedUsers( self, authorizedUsers ):
      """Set the list of authorized users"""
      self.authorizedUsers = authorizedUsers

   def AddAuthorizedUser( self, user ):
      """Add user to list of authorized users"""
      if user not in self.authorizedUsers:
         self.authorizedUsers.append( user )

   def RemoveAuthorizedUser( self, user ):
      """Remove user from list of authorized users"""
      del self.authorizedUsers[user]

   def Authorize( self, user ):
      """Check for user in list of authorized users"""
      if user in self.authorizedUsers:
         print "authorized", user
         return True
      else:
         print "did NOT authorize", user
         return False
