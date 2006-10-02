import os
import re
import sys

from AccessGrid import Log
from AccessGrid.VenueClientObserver import VenueClientObserver
from AccessGrid.Platform import IsWindows
from AccessGrid.Platform.ProcessManager import ProcessManager

from wxPython.wx import *

log = Log.GetLogger("Plugin")

class Plugin(VenueClientObserver):
    def __init__(self, directory, name, description, commandline, icon):
        self.directory = directory
        self.name = name
        self.description = description

        if not self.description or len(self.description)==0:
            #
            # Fallback to at least something for the description
            #
            self.description = self.name
        
        self.commandline = commandline
        if self.commandline and len(self.commandline) == 0:
            self.commandline = None
            
        self.icon = icon
        if self.icon and len(self.icon) == 0:
            self.icon = None

        self.processManager = ProcessManager()

        self.__venueClient = None
        self.__venueClientController = None

    def Attach(self, venueClient, venueClientController):
        self.__venueClient = venueClient
        self.__venueClientController = venueClientController
        
    def Start(self):
        if self.__venueClient:
            self.__venueClient.AddObserver(self)
        else:
            log.debug("Starting without reference to VenueClient.")


    def Stop(self):
        if self.__venueClient:
            self.__venueClient.RemoveObserver(self)

        #
        # Kill all external processes (if any)
        #
        self.processManager.TerminateAllProcesses()

    def CreateMenu(self, frame):
        items = self.CreateMenuItems()

        return self.__create_menu_from_itemlist(frame, self.name, items)
        
    def CreateToolbar(self, frame, toolbar, toolsize):
        items = self.CreateToolbarItems()

        if not items:
            return

        if len(items) == 0:
            return

        for item in items:
            if len(item) != 4:
                log.debug("Invalid toolbar item.")
                continue

            name, desc, icon, cb = item

            if type(name) != str:
                log.debug("Invalid toolbar name, expected string.")
                continue

            if type(desc) != str:
                log.debug("Invalid toolbar description, expected string.")
                continue

            if type(icon) != str:
                log.debug("Invalid toolbar icon, expected string.")
                continue

            if not callable(cb):
                log.debug("Invalid toolbar callback. It is not callable.")
                continue

            #
            # Try and load the icon
            #
            icon = os.path.join(self.directory, icon)
            try:
                img = wxImage(icon, wxBITMAP_TYPE_ANY)
            except Exception, e:
                log.debug("Failed to load icon %s: %s" % (icon, e))
                continue

            toolid = wxNewId()
            
            callback = lambda event, description="Toolbar: " + name, callback=cb: self.__callback_wrapper(description, callback)

            button = wxBitmapButton(toolbar,
                                    toolid,
                                    wxBitmapFromImage(img),
                                    size=toolsize)

            button.SetToolTip(wxToolTip(desc))
            toolbar.AddControl(button)

            EVT_BUTTON(frame, toolid, callback)
        
    def CreateMenuItems(self):
        if self.commandline:
            log.debug("Plugin %s: creating basic executable menu item." % self.name)
            return [(self.name, self.StartExecutable)]
        else:
            log.debug("Plugin %s: no menu items." % self.name)
            return None

    def CreateToolbarItems(self):
        if self.commandline and self.icon:
            log.debug("Plugin %s: creating basic toolbar item." % self.name)
            return [(self.name, self.description, self.icon, self.StartExecutable)]
        else:
            log.debug("Plugin %s: no icon." % self.name)
            return None

    def StartExecutable(self):
        if not self.commandline:
            log.exception("Commandline is NULL.")
            return

        if len(self.commandline) == 0:
            log.exception("Commandline is empty.")
            return

        if not self.__venueClient or not self.__venueClientController:
            log.exception("Plugin has not been attached to a venue client.")
            return
    
        namedVars = dict()
        namedVars['python'] = sys.executable
        namedVars['pluginName'] = self.name
        namedVars['pluginDesc'] = self.description
        # This is NOT on every description type, so we're not using it yet
        # namedVars['appMimeType'] = objDesc.mimeType
        namedVars['localFilePath'] = self.directory
        
        namedVars['venueUrl'] = self.__venueClient.GetVenue()
        namedVars['venueClientUrl'] = self.__venueClient.GetWebServiceUrl()
        namedVars['connectionId'] = self.__venueClient.GetConnectionId()
        
        # We're doing some icky munging to make our lives easier
        # We're only doing this for a single occurance of a windows
        # environment variable
        prog = re.compile("\%[a-zA-Z0-9\_]*\%")
        result = prog.match(self.commandline)
                
        if result != None:
            subStr = result.group()

            realCommand = self.commandline.replace(subStr, "DORKYREPLACEMENT") % namedVars
            realCommand = realCommand.replace("DORKYREPLACEMENT", subStr)
        else:
            try:
                realCommand = self.commandline % namedVars
            except:
                import pprint
                log.exception("Command failed, probably misconfigured. \
                Tried to run, %s with named arguments %s", self.commandline,
                              pprint.pformat(namedVars))
                return

        if IsWindows():
            #shell = os.environ['ComSpec']
            #realCommand = "%s %s %s" % (shell, "/c", realCommand)
            log.info("StartCmd starting command: %s", realCommand)
            cmd = realCommand
            argList = []
        else:
            log.info("StartCmd starting command: %s", realCommand)
            aList = realCommand.split(' ')
            cmd = aList[0]
            argList = aList[1:]

        olddir = os.getcwd()
        try:
            os.chdir(self.directory)
        except OSError, e:
            log.exception("Failed to change directory to %s." % self.directory)
            return
            
        self.processManager.StartProcess(cmd,argList)

        os.chdir(olddir)
        
        self.Start()
        
    #
    # The following methods are the abstract methods of VenueClientObserver
    # which need to be overridden to prevent exceptions being through when
    # a plugin does not wish to handle particular callbacks.
    #
    def AddUser(self,profile):
        pass

    def RemoveUser(self,profile):
        pass

    def ModifyUser(self,profile):
        pass

    def AddData(self, dataDescription):
        pass

    def RemoveData(self, dataDescription):
        pass
    
    def UpdateData(self, dataDescription):
        pass

    def AddService(self, serviceDescription):
        pass

    def RemoveService(self, serviceDescription):
        pass

    def UpdateService(self, serviceDescription):
        pass

    def AddApplication(self,appDescription):
        pass

    def RemoveApplication(self,appDescription):
        pass
    
    def UpdateApplication(self,appDescription):
        pass
    
    def AddConnection(self,connDescription):
        pass

    def RemoveConnection(self,connDescription):
        pass

    def SetConnections(self,connDescriptionList):
        pass

    def AddStream(self, streamDesc):
        pass

    def RemoveStream(self, streamDesc):
        pass

    def ModifyStream(self, streamDesc):
        pass

    def AddText(self,name,text):
        pass

    def EnterVenue(self, URL, warningString="", enterSuccess=1):
        pass

    def ExitVenue(self):
        pass

    def HandleError(self,err):
        pass

    def UpdateMulticastStatus(self,status):
        pass
    

    def __callback_wrapper(self, description, callback):
        """
        A wrapper function to catch any exceptions by custom plugins
        to prevent problems for the VenueClient.

        Exceptions are caught, logged, and ignored.
        """
        
        try:
            callback()
        except Exception, e:
            log.exception("Plugin %s callback error in %s: %s" % (self.name, description, e))
                         
    def __create_menu_from_itemlist(self, frame, name, itemlist):
        """
        Returns a wxMenuItem based on the list of items in item list.

        """
        
        if not itemlist:
            log.debug("Null item list.")
            return None

        if len(itemlist) == 0:
            log.debug("Empty item list.")
            return None

        if len(itemlist) == 1:
            #
            # Special case: if there is only one item, don't create a
            # sub-menu for it.
            #
            return self.__create_menu_from_item(frame, itemlist[0])

        else:
            menu = wxMenu(name)
            itemCount = 0

            for item in itemlist:
                t = self.__create_menu_from_item(frame, item)
                if t:
                    menu.Append(t)
                    itemCount = itemCount + 1

            if itemCount > 0:
                return wxMenuItem(NULL, -1, name, "", wxITEM_NORMAL, menu)
            else:
                #
                # Don't want empty menus hanging around so return None in
                # this case.
                #
                log.debug("Returning empty sub-menu.")
                return None

    def __create_menu_from_item(self, frame, item):
        """
        Create a wxMenuItem from one item in an item list. Sets up callbacks
        as required.

        """
        
        if not item:
            log.debug("Null item.")
            return None

        if len(item) != 2:
            log.debug("Expected tuple of (name, callback or submenu).")
            return None

        name, cb = item

        if type(name) != str:
            log.debug("Expected string for menu name.")
            return None
        
        if callable(cb):
            itemid = wxNewId()
            item = wxMenuItem(NULL, itemid, name, "", wxITEM_NORMAL, NULL)
            callback = lambda event, description=name, callback=cb: self.__callback_wrapper(description, callback)
            EVT_MENU(frame, itemid, callback)

            return item
            
        elif type(cb) == list:
            submenu = self.__create_menu_from_itemlist(cb)
            if not submenu:
                return None

            return wxMenuItem(NULL, -1, name, "", wxITEM_NORMAL, submenu)
        else:
            log.debug("Expected callback or submenu for second element of tuple.")
            return None
        
            
