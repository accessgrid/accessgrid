#-----------------------------------------------------------------------------
# Name:        DisplayService.py
# Purpose:     Generic display service for use on Win32/X11 displays
# Created:     2003/31/03
# RCS-ID:      
# Copyright:   (c) 2003
# Licence:     See COPYING.TXT
#-----------------------------------------------------------------------------
import sys
import os

from wxPython import wx

from AccessGrid.Platform import isWindows, isLinux
from AccessGrid.Platform.Config import SystemConfig
from AccessGrid.GUID import GUID

from AccessGrid.hosting import Server
from AccessGrid.hosting.SOAPInterface import SOAPInterface, SOAPIWrapper

if isWindows():
   from DisplayWin32 import GetWindowList
elif isLinux():
   from DisplayLinux import *
   
class DisplayService:
   """
   id : string
   location : string [protocol://<host>:<port>/]  
      - examples: 
      - x://host:0
      - windows://host
      - vnc://host:port/
      - rdp://host:port/)
   
   displayWidth : integer
   displayHeight : integer
   displayDepth : integer
   windowList : list of window Id's
   regionList : list of empty regions
   """
   def __init__(self):
      self.id = str(GUID())
      self.location = None
      self.displayWidth = -1
      self.displayHeight = -1
      self.displayDepth = -1
      self.windowList = list()
      self.regionList = list()

      self._Initialize()
      
   def _GetLocation(self):
      """
      """
      hn = SystemConfig.instance().GetHostname()
      if isWindows():
         return "windows://" + hn
      elif isLinux():
         if os.getenv("DISPLAY"):
            return "X11://" + hn + ":" + os.getenv("DISPLAY").split(":")[-1]
         else:
            return "X11://" + hn + ":0.0"
      else:
         return "unknown://hn"

   def _Initialize(self):
      """
      """
      self.location = self._GetLocation()
      size = wx.wxGetDisplaySize()
      self.displayWidth = size.GetWidth()
      self.displayHeight = size.GetHeight()
      self.displayDepth = wx.wxGetDisplayDepth()
      self.windowList = GetWindowList()
      
   def GetId(self):
      return self.id
   
   def GetLocation(self):
      return self.location
   
   def GetWidth(self):
      return self.displayWidth
   
   def GetHeight(self):
      return self.displayHeight
   
   def GetDepth(self):
      return self.displayDepth
   
   def GetWindows(self):
      return self.windowList
   
   def GetRegions(self):
      return self.regionList
   
class DisplayServiceI(SOAPInterface):
   """
   """
   def __init__(self, impl):
      SOAPInterface.__init__(self, impl)
      
   def GetLocation(self):
      return self.impl.GetLocation()
   
   def GetWindows(self):
      return self.impl.GetWindows()
   
   def GetRegions(self):
      return self.impl.GetRegions()
   
   def GetLocation(self):
      return self.impl.GetLocation()
   
   def GetId(self):
      return self.impl.GetId()
   
   def GetWidth(self):
      return self.impl.GetWidth()
   
   def GetHeight(self):
      return self.impl.GetHeight()
   
   def GetDepth(self):
      return self.impl.GetDepth()

class DisplayServiceIW(SOAPIWrapper):
   def __init__(self, url):
      SOAPIWrapper.__init__(self, url)

   def GetLocation(self):
      return self.proxy.GetLocation()

   def GetWindows(self):
      return self.proxy.GetWindows()

   def GetRegions(self):
      return self.proxy.GetRegions()

   def GetLocation(self):
      return self.proxy.GetLocation()
   
   def GetId(self):
      return self.proxy.GetId()

   def GetWidth(self):
      return self.proxy.GetWidth()

   def GetHeight(self):
      return self.proxy.GetHeight()

   def GetDepth(self):
      return self.proxy.GetDepth()
   
if __name__ == '__main__':
   from AccessGrid.Toolkit import CmdlineApplication
   import pprint
   
   # Do env init
   app = CmdlineApplication()
   app.Initialize("DisplayServiceTest")
   
   # Create a local hosting environment
   hn = SystemConfig.instance().GetHostname()
   hn = 'localhost'
   server = Server((hn, int(sys.argv[1])))

   # Create the display service
   dispService = DisplayService()

   # Then it's interface
   dispServiceI = DisplayServiceI(dispService)

   # Then register the display service with the hosting environment
   service = server.RegisterObject(dispServiceI, path = "/DisplayService")

   # Get the url and print it
   url = server.FindURLForObject(dispService)
   print "Starting server at", url

   # run the hosting environment until interrupted
   server.RunInThread()

   # Create a client
   dispClient = DisplayServiceIW(url)

   # Call the methods to test it
   print "Location: ", dispClient.GetLocation()
   print "ID: ", dispClient.GetId()
   print "Width: ", dispClient.GetWidth()
   print "Height: ", dispClient.GetHeight()
   print "Depth: ", dispClient.GetDepth()
   print "Windows: "
   for w in dispClient.GetWindows():
      pprint.pprint(w)
   print "Regions: "
   for r in dispClient.GetRegions():
      pprint.pprint(r)

   # Shutdown the service
   server.Stop()
