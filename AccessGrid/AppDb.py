#-----------------------------------------------------------------------------
# Name:        VenueClient.py
# Purpose:     This is the client side object of the Virtual Venues Services.
#
# Author:      Ivan R. Judson, Thomas D. Uram
#
# Created:     2002/12/12
# RCS-ID:      $Id: AppDb.py,v 1.5 2003-09-15 15:01:03 judson Exp $
# Copyright:   (c) 2003
# Licence:     See COPYING.TXT
#-----------------------------------------------------------------------------

import os
import sys
import shutil

from AccessGrid.Utilities import LoadConfig, SaveConfig
from AccessGrid.Platform import GetUserConfigDir, GetUserAppPath
from AccessGrid.Descriptions import ApplicationDescription

"""
Type management for access grid toolkit:

What we know:

(name, mimeType, extension, command Dictionary)

Storage in Config Parser Format:

[name]
name = mimeType

[extension]
extension = mimeType

[<mimeType>]
command name = command

Functions:

mimeType = GetMimeType(name = None, extension = None)
(int, string) = AddMimeType(name, extension, mimeType)
(int, string) = RemoveMimeType(name = None, extension = None, mimeType = None)

commandNameList = GetCommandNames(mimeType)
commandLine = GetCommandLine(mimeType, cmdName, vars=None)
(int, string) = AddCommand(mimeType, cmdName, cmdString)
(int, string) = RemoveCommand(mimeType, cmdName)

int = RegisterApplication(name, mimeType, extension, commandDictionary, fileList)
int = UnregisterApplication(name = None, mimeType = None, extension = None)
"""

class AppDb:

    defaultPath = GetUserConfigDir()
    defaultName = "ApplicationDatabase"
    defaultFile = os.path.join(defaultPath, defaultName)
    defaultSeparator = ":"
    
    def __init__(self, file=defaultFile):
        self.fileName = file
        self.AppDb = dict() 

        try:
            self.AppDb = LoadConfig(self.fileName, dict(), self.defaultSeparator)
        except:
            print sys.exc_info()
            print "Couldn't open application database: %s" % self.fileName

    def Load(self, fileName=None):
        if fileName == None:
            fileName = self.fileName
            
        try:
            self.AppDb = LoadConfig(fileName, self.defaultSeparator)
        except:
            print sys.exc_info()
            print "Couldn't open application database: %s" % fileName
            
    def Flush(self):
        try:
            SaveConfig(self.fileName, self.AppDb, self.defaultSeparator)
        except:
            print "Couldn't flush the db to disk."

    def GetMimeType(self, name = None, extension = None):
        """
        returns a mimeType in a string.
        """
        mimeType = None
    
        if name != None:
            lookupName = self.defaultSeparator.join(["name", name])
            try:
                mimeType = self.AppDb[lookupName]
            except KeyError:
                mimeType = None
    
        if extension != None:
            lookupExt = self.defaultSeparator.join(["extension", extension])
            try:
                mimeType = self.AppDb[lookupExt]
            except KeyError, k:
                mimeType = None
    
        return mimeType
    
    def GetNameForMimeType(self, mimeType):
        """
        returns a name in a string.
        """
        appName = None
    
        for key in self.AppDb.keys():
            if self.AppDb[key] == mimeType:
                (section, option) = key.split(self.defaultSeparator)
                if section == "name" and self.AppDb[key] == mimeType:
                    appName = option
    
        return appName
    
    def AddMimeType(self, name, extension, mimeType):
        """
        returns a tuple of (int, string). Success is (1, mimeType),
        failure is (0, reason)
        """
    
        nameStr = self.defaultSeparator.join(["name", name])
        extStr = self.defaultSeparator.join(["extension", extension])
        mimeStr = self.defaultSeparator.join([mimeType, "None"])
        
        self.AppDb[nameStr] = mimeType
        self.AppDb[extStr] = mimeType
        self.AppDb[mimeStr] = None
    
        self.Flush()

        return (1, mimeType)
    
    def RemoveMimeType(self, name = None, extension = None, mimeType = None):
        """
        returns a tuple of (int, string). Success is (1, mimeType),
        failure is (0, reason)
        """
    
        if name == None and extension == None and mimeType == None:
            return (0, "Not enough information to remove mime type.")
    
        if name != None:
            nameStr = self.defaultSeparator.join(["name", name])
        elif mimeType != None:
            for key in self.AppDb.keys():
                if self.AppDb[key] == mimeType:
                    (section, option) = key.split(self.defaultSeparator)
                    if section == "name":
                        nameStr = key
    
        if extension != None:
            extStr = self.defaultSeparator.join(["extension", extension])
        elif mimeType != None:
            for key in self.AppDb.keys():
                if self.AppDb[key] == mimeType:
                    (section, option) = key.split(self.defaultSeparator)
                    if section == "extension":
                        extStr = key
    
        if mimeType == None:
            mimeType = GetMimeType(name, extension)
    
        if self.AppDb[nameStr] == self.AppDb[extStr] == mimeType:
            del self.AppDb[nameStr]
            del self.AppDb[extStr]
    
        self.Flush()
    
        return (1, mimeType)
    
    def GetCommandNames(self, mimeType):
        """
        returns a list of command names for this mime type.
        """
        cmds = list()

        for key in self.AppDb.keys():
            (section, option) = key.split(self.defaultSeparator)
            if section == mimeType:
                cmds.append(option)
    
        return cmds
    
    def GetCommandLine(self, mimeType, cmdName, vars=None):
        """
        returns a string containing the commandline used to execute the viewer,
        optionally if vars is a dictionary, of name = value, named parameter
        substitution is done for the command line.
        """
        cmdStr = ""

        if mimeType == None or cmdName == None:
            return cmdStr
        
        if vars != None:
            try:
                cmdStr = self.AppDb[self.defaultSeparator.join([mimeType, cmdName])] % vars
            except KeyError:
                return cmdStr
        else:
            try:
                cmdStr = self.AppDb[self.defaultSeparator.join([mimeType, cmdName])]
            except KeyError:
                return cmdStr
    
        return cmdStr
    
    def AddCommand(self, mimeType, cmdName, cmdString):
        """
        returns a tuple (int, string). Success is (1, cmdName),
        failure is (0, reason).
        """
        self.AppDb[self.defaultSeparator.join([mimeType, cmdName])] = cmdString
    
        self.Flush()
    
        return (1, cmdName)
    
    def RemoveCommand(self, mimeType, cmdName):
        """
        returns a tuple (int, string). Success is (1, cmdName),
        failure is (0, reason).
        """
    
        del self.AppDb[self.defaultSeparator.join([mimeType, cmdName])]
    
        self.Flush()
    
        return (1, cmdName)

    def RegisterApplication(self, name, mimeType, extension, commandDict, fileList, srcPath):
        """
        Encapsulate all the actions required to register a new application.
        returns 0 on failure, 1 on success
        """
    
        (ret, retStr) = self.AddMimeType(name, extension, mimeType)
    
        if ret:
            for cmdName in commandDict.keys():
                cmdStr = commandDict[cmdName]
                (result, resultString) = self.AddCommand(mimeType, cmdName, cmdStr)
                if not result:
                    return 0

            noSpaceName = ''.join(name.split(' '))

            dstPath = os.path.join(GetUserAppPath(), noSpaceName)

            if not os.path.exists(dstPath):
                try:
                    os.mkdir(dstPath)
                except:
                    print "Couldn't make app directory (%s)." % dstPath
                    
            for appFile in fileList:
                try:
                    shutil.copyfile(os.path.join(srcPath, appFile),
                                    os.path.join(dstPath, appFile))
                except IOError:
                    print "Couldn't copy file into place."
                                
        else:
            return 0

        self.Flush()
        
        return 1

    def ListApplications(self):
        """
        """
        apps = list()
        
        for key in self.AppDb.keys():
            (section, option) = key.split(self.defaultSeparator)
            if section == 'name':
                apps.append(option)
    
        return apps

    def ListMimeTypes(self):
        """
        """
        mt = list()
        
        for key in self.AppDb.keys():
            try:
                (section, option) = key.split(self.defaultSeparator)
            except ValueError:
                continue
            
            if section != 'name' and section != 'extension':
                mt.append(option)
    
        return mt

    def ListAppsAsAppDescriptions(self):
        """
        """
        apps = list()
        
        for key in self.AppDb.keys():
            try:
                (section, option) = key.split(self.defaultSeparator)
            except ValueError:
                continue
            if section == 'name':
                name = option
                mimetype = self.AppDb[key]
                apps.append(ApplicationDescription(None, name, None, None, mimetype))
                
        return apps
        
    def UnregisterApplication(self, name=None, mimeType=None, extension=None):
        """
        Encapsulate all the actions required to unregister an application.
        returns 0 on failure, 1 on success
        """
    
        if mimeType == None:
            mimeType = GetMimeType(name, extension)
    
        cmdList = GetCommandNames(mimeType)
    
        (ret, retStr) = RemoveMimeType(name, extension, mimeType)
        if ret:
            for cmdName in cmdList:
                (result, resultString) = RemoveCommand(mimeType, cmdName)
                if not result:
                    return 0
        else:
            return 0
    
        return 1
