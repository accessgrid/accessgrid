
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
      self.authorizedUsers.remove(user)

   def Authorize( self, user ):
      """Check for user in list of authorized users"""

      return 1
      """

      if user in self.authorizedUsers:
         print "authorized", user
         return 1
      else:
         print "did NOT authorize", user
         return 0
      """
