#-----------------------------------------------------------------------------
# Name:        CommandLineVenueClient.py
# Purpose:     This is the client software for the user, in a command line.
#
# Author:      Eric Olson
#
# Created:     2003/06/02
# RCS-ID:      $Id: CommandLineVenueClient.py,v 1.9 2004-03-10 23:17:09 eolson Exp $
# Copyright:   (c) 2002-2003
# Licence:     See COPYING.TXT
#-----------------------------------------------------------------------------

from AccessGrid.hosting.pyGlobus import Client
import os, time, threading
import cmd
from threading import Thread

from  AccessGrid.ClientProfile import ClientProfile
from AccessGrid.Platform import GetUserConfigDir

log = Log.GetLogger(Log.VenueClient)

from AccessGrid.VenueClient import VenueClient
from AccessGrid.Toolkit import CmdlineApplication, GetApplication
from AccessGrid.VenueClientEventSubscriber import VenueClientEventSubscriber
from AccessGrid.hosting.AccessControl import Subject

class CommandLineVenueClient(VenueClientEventSubscriber):
    """
    A VenueClient that can be interacted with through the command line.
    VenueClientEventSubscriber provides predefined callbacks that are called
        by AccessGrid.VenueClient.  If we add ourselves to a venueclient with
        AddEventSubscriber, we will get the events.
    An external class, such as CmdLineController below, does the actual
        reading and writing to the command line.

    NOTE that currently the operation is much more input driven than in
        GuiVenueClient.  For example, we currently don't print out every change 
        when the venue state changes.
    """

    history = []
    accessGridPath = GetUserConfigDir()
    profileFile = os.path.join(accessGridPath, "profile" )
    isPersonalNode = 0
    debugMode = 0
    transferEngine = None

    def __init__(self):
        self.app = None
        self.__setLogger()

        self.app = GetApplication()
        if self.app == None:
            try:
                self.app = CmdlineApplication()
            except Exception, e:
                log.exception("bin.CommandLineVenueClient__init__ Toolkit.CmdlineApplication creation failed")

        try:
            self.app.InitGlobusEnvironment()
        except Exception, e:
            log.exception("bin.CommandLineVenueClient__init__ app.InitGlobusEnvironment failed.")

        if not os.path.exists(self.accessGridPath):
            try:
                os.mkdir(self.accessGridPath)
            except OSError, e:
                log.exception("bin.VenueClient::__init__: Could not create base path")

        self.venueClient = VenueClient()
        self.venueClient.AddEventSubscriber(self)

        # Set profile, if not set, is default
        self.venueClient.profile = ClientProfile(self.profileFile)

        self.defaultVenue = "https://localhost:8000/Venues/default"

        # Default to printing to stdout.
        self.cmdLineInterface = None

        # Setup caches
        self.ClearCaches()

    def SetCmdLineInterface(self, cmdLineInterface):
        self.cmdLineInterface = cmdLineInterface

    def PreEnterVenue(self, URL, back=0):
        """
        Before we enter any venues, make sure we have a valid certificate.
        """

        #
        # Check to see if we have a valid grid proxy
        # If not, run grid proxy init
        #
        if not self.app.certificateManager.HaveValidProxy():
            log.debug("VenueClient::EnterVenue: You don't have a valid proxy")
            self.app.certificateManager.CreateProxy()

    def __setLogger(self):
        """
        Sets the logging mechanism.
        """
        self.logFile = None
        log = Log.GetLogger(Log.VenueClient)

        if self.logFile is None:
            logname = "VenueClient.log"
        else:
            logname = self.logFile

        hdlr = Log.FileHandler(logname)
        hdlr.setLevel(Log.DEBUG)
        hdlr.setFormatter(Log.GetFormatter())
        Log.HandleLoggers(hdlr, Log.GetDefaultLoggers())

        if self.debugMode:
            hdlr = Log.StreamHandler()
            hdlr.setFormatter(Log.GetLowDetailFormatter())
            Log.HandleLoggers(hdlr, Log.GetDefaultLoggers())

    def ClearCaches(self):
        # Cache exits when they are listed so user can type a number to identify them. 
        self.cachedExitList = []


    # --- Callbacks called from AccessGrid.VenueClient() ---

    def EnterVenue(self, URL, back = 0, warningString="", enterSuccess=1):
        if enterSuccess == 1:
            self.ClearCaches() # clear exits, etc. from last venue
            self.OutputText("Successfully entered venue: " + URL)
        else:
            self.OutputText("Failed to enter venue: " + URL)


    # --- Commands to be initiated from the command line. ---

    # return isSuccess, output string

    def InitiateEnterVenue(self, venue):
        if len(venue) > 0:
            v = venue
        else:
            v = self.defaultVenue

        self.venueClient.EnterVenue(v)
        return self.venueClient.isInVenue

    def InitiateExitVenue(self, keep_quiet=0):
        wasInVenue = self.venueClient.isInVenue
        self.venueClient.ExitVenue()
        if wasInVenue:
            if not keep_quiet:
                self.OutputText("Successfully exited venue.")
            return 1
        else:
            if not keep_quiet:
                self.OutputText("Attempted to Exit venue.  You were not in a venue.")
            return 0

    def ListParticipants(self):    
        if self.venueClient.isInVenue:
            strng = ""
            for client in self.venueClient.venueState.clients.values():
                strng += client.name + "\n"
            self.OutputText("Participants:\n" + strng)
            return 1
        else:
            self.OutputText("You are not in a venue and are unable to list participants.")
            return 0

    def ListExits(self):
        if self.venueClient.isInVenue:
            strng = ""
            exitList = []
            index = 1
            for exit in self.venueClient.venueState.connections.values():
                strng += "(" + str(index) + ") " + exit.name + "\n"
                exitList.append(exit)
                index = index + 1
            self.OutputText("Exits:\n" + strng)
            # Replace exit list with new exit list.
            self.cachedExitList = exitList
            return 1
        else:
            self.OutputText("You are not in a venue and are unable to list exits.")
            return 0

    def UseExit(self, index):
        if len(self.cachedExitList) == 0:
            self.ListExits() # retrieve list of exits if we don't have one
        # Note the passed in index is 1-based and array index is 0-based
        if index > 0 and index <= len(self.cachedExitList):
            exit = self.cachedExitList[index-1]
            self.OutputText("Using exit (" + str(index) + ") " + exit.name + "  ")
            self.InitiateEnterVenue(exit.uri)

    def InitiateShutdown(self):
        self.venueClient.Shutdown()
        return 1

    def GetStatus(self):
        if self.venueClient.isInVenue:
            self.OutputText("You are connected to venue: " + self.venueClient.venueState.name + ", " + self.venueClient.venueUri)
        else:
            self.OutputText("You are not connected to a venue.")

    def ListData(self):
        if self.venueClient.isInVenue:
            strng = ""
            for data in self.venueClient.venueState.data.values():
                strng += data.name + "\n"
            if len(strng) == 0:
                strng = "There is no data in the venue.\n"
            else:
                strng = "Data:\n" + strng
            self.OutputText(strng)
            return 1
        else:
            self.OutputText("You are not in a venue and are unable to list data.")
            return 0

    def AddUserToRole(self, user, role):
        if self.venueClient.isInVenue:
            if self.venueClient.venueProxy.AddSubjectToRole(user, role):
                self.OutputText("Successfully added user: " + user + "  to role: " + role)
                return 1
            else:
                self.OutputText("Failed to add user: " + user + "  to role: " + role)
        else:
            self.OutputText("You are not in a venue and are unable to add a user to a role.")
        return 0

    def ListUsersInRole(self, role):
        if self.venueClient.isInVenue:
            users = self.venueClient.venueProxy.GetUsersInRole(role)
            strng = "Users in Role: " + role + "\n"
            for u in users:
                if type(u) is type(""):
                    strng = strng + u + ", "
                else:
                    raise "InvalidSubjectTypeError (expected string within the list)"
            self.OutputText(strng)
        else:
            self.OutputText("You are not in a venue and are unable to list the users of a role.")

    def ListRoles(self):
        if self.venueClient.isInVenue:
            roles = self.venueClient.venueProxy.GetRoleNames()
            strng = "Roles:\n"
            for r in roles:
                strng = strng + r + ", "
            self.OutputText(strng)
        else:
            self.OutputText("You are not in a venue and so are unable to list a venue's roles.")

    def DetermineRoles(self):
        if self.venueClient.isInVenue:
            roles = self.venueClient.venueProxy.DetermineSubjectRoles()
            strng = "User's Roles:\n"
            for r in roles:
                strng = strng + r + ", "
            self.OutputText(strng)
        else:
            self.OutputText("You are not in a venue and so are unable to determine the current user's venue roles.")

    # Allow output to be channeled to a single place.
    def OutputText(self, strng):
       if self.cmdLineInterface:
           self.cmdLineInterface.OutputText(strng) 
       else:
           print strng


class CmdLineController(cmd.Cmd, Thread):

    def __init__(self, cmd_line_venueclient):
        """
        Interacts with command line and passes commands to CommandLineVenueClient
            through specific callbacks.
        We only have to pass the init to our super class for Thread
        setup and keep track of our callbacks.
        """
        cmd.Cmd.__init__(self)
        self.cmdLineVC = cmd_line_venueclient
        Thread.__init__(self)
        self.prompt = "VenueClient>" 
        #self.ListParticipantsCB = vc.listParticipants
        #self.EnterCB

    # Allow venuclient to output through us using our preferred method.
    def OutputText(self, strng):
        print strng

    def Run(self):
        self.cmdloop()

    # These methods are used by the command processor to recognize input
    # see the documentation on the command processor (cmd module) for
    # more information

    def do_listparticipants(self, argline):
        self.cmdLineVC.ListParticipants()

    do_lp = do_listparticipants

    def do_listexits(self, argline):
        self.cmdLineVC.ListExits()

    do_le = do_listexits

    def do_useexit(self, argline):
        index = int(argline)
        self.cmdLineVC.UseExit(index)

    do_ue = do_useexit

    def do_listdata(self, argline):
        self.cmdLineVC.ListData()

    do_ld = do_listdata

    def do_entervenue(self, argline):
        self.cmdLineVC.InitiateEnterVenue(argline)

    do_e = do_entervenue

    def do_exitvenue(self, argline):
        self.cmdLineVC.InitiateExitVenue()

    do_x = do_exitvenue

    def do_quit(self, argline):
        self.cmdLineVC.InitiateExitVenue(keep_quiet=1)
        self.cmdLineVC.InitiateShutdown()
 
        return 1 # stops cmdloop()

    do_q = do_quit

    def do_status(self, argline):
        self.cmdLineVC.GetStatus()

    do_s = do_status

    def do_listroles(self, argline):
        self.cmdLineVC.ListRoles()

    do_lr = do_listroles

    def do_determineroles(self, argline):
        self.cmdLineVC.DetermineRoles()

    do_dr = do_determineroles

    def do_role_listusers(self, argline):
        if len(argline) == 0:
            self.OutputText("Please provide the name of a role as an argument.")
        else:
            self.cmdLineVC.ListUsersInRole(argline)

    do_rlu = do_role_listusers

    def do_role_adduser(self, argline):
        args = argline.split(" ", 1)
        if len(args) >= 2:
            arg_string = ""
            for a in args[1:]:
                arg_string += a
            self.cmdLineVC.AddUserToRole(arg_string, args[0])
        else:
            args_strng  = ""
            for s in args:
                args_strng += "|" + s + "| "
            self.OutputText("role_adduser requires 2 arguments: role and user.  (you provided " + str(len(args)) + ") " + args_strng)

    do_rad = do_role_adduser

    def do_fulltest(self, argline):
        empty_argline = ""

        print "\nStarting full test"

        print "\n*** Performing tests while connected."
        self.do_entervenue(empty_argline)
        self.do_status(empty_argline)
        self.do_listparticipants(empty_argline)
        self.do_listdata(empty_argline)
        self.do_exitvenue(empty_argline)

        print "\n*** Performing tests while not connected."
        self.do_status(empty_argline)
        self.do_listparticipants(empty_argline)
        self.do_listdata(empty_argline)

        print "Finished full test\n"


if __name__ == "__main__":

    vc = CommandLineVenueClient()
    cmdline = CmdLineController(vc)
    vc.SetCmdLineInterface(cmdline) # give vc a place to send output messages.

    log.info("Starting CommandLineVenueClient")

    # Start prompting for command line input.
    cmdline.Run()

    # Perhaps should verify profile above.
    # Also need to try with personalnode still.
    
    """
    #
    # If we're running as a personal node, terminate the services.
    #
    if vc.isPersonalNode:
        log.debug("Terminating services")
        vc.personalNode.Stop()

    vc.venueClient.Shutdown()

    """

