#-----------------------------------------------------------------------------
# Name:        VenueClient.py
# Purpose:     This is the client side object of the Virtual Venues Services.
#
# Author:      Ivan R. Judson, Thomas D. Uram
#
# Created:     2002/12/12
# RCS-ID:      $Id: AppDb.py,v 1.10 2003-09-29 20:59:21 judson Exp $
# Copyright:   (c) 2003
# Licence:     See COPYING.TXT
#-----------------------------------------------------------------------------
"""
This is the application database for the accessgrid toolkit. It is
used by client software that wants to keep track of what AG specific
tools are appropriate for specific data types. It also keeps track of
how to invoke those tools.
"""
__revision__ = "$Id: AppDb.py,v 1.10 2003-09-29 20:59:21 judson Exp $"
__docformat__ = "restructuredtext en"

import os
import sys
import shutil

from AccessGrid.Utilities import LoadConfig, SaveConfig
from AccessGrid.Platform import GetUserConfigDir, GetUserAppPath
from AccessGrid.Descriptions import ApplicationDescription
from AccessGrid.GUID import GUID

"""
Type management for access grid toolkit:

What we know:

(name, mimeType, extension, command Dictionary)

Storage in Config Parser Format:

[name]
priv_key = mimetype

[extension]
extension = mimeType

[<mimeType>]
priv_key = command

[name_map]
priv_key = name

[cmd_map]
priv_key = command_name

Functions:

mimeType = GetMimeType(name = None, extension = None)
(int, string) = AddMimeType(name, extension, mimeType)
(int, string) = RemoveMimeType(name = None, extension = None, mimeType = None)

commandNameList = GetCommandNames(mimeType)
commandLine = GetCommandLine(mimeType, cmdName, vars=None)
(int, string) = AddCommand(mimeType, cmdName, cmdString)
(int, string) = RemoveCommand(mimeType, cmdName)

int = RegisterApplication(name, mimeType, extension, commandDictionary, fileList, workingDir)
int = UnregisterApplication(name = None, mimeType = None, extension = None)
"""

class AppDb:
    """
    The AppDb class provides an interface for the Toolkit to store
    information on a per user basis about what applications are
    installed and how to run them.
    """
    defaultPath = GetUserConfigDir()
    defaultName = "ApplicationDatabase"
    defaultFile = os.path.join(defaultPath, defaultName)
    defaultSeparator = ":"

    def __init__(self, file=defaultFile):
        """
        The constructor for the AppDb, it uses a file for persistent storage.
        """
        self.fileName = file
        self.AppDb = dict()

        try:
            self.AppDb = LoadConfig(self.fileName, dict(), self.defaultSeparator)
        except:
            print sys.exc_info()
            print "Couldn't open application database: %s" % self.fileName

    def Load(self, fileName=None):
        """
        Load the app db from the file it's stored in.
        """
        if fileName == None:
            fileName = self.fileName

        try:
            self.AppDb = LoadConfig(fileName, self.defaultSeparator)
        except:
            print sys.exc_info()
            print "Couldn't open application database: %s" % fileName

    def _Flush(self):
        """
        Flush the current db out to file storage.
        """
        try:
            SaveConfig(self.fileName, self.AppDb, self.defaultSeparator)
        except:
            print "Couldn't flush the db to disk."

    def _GetPrivName(self, name):
        """
        Look up the private name for the exposed name.

        returns name as string or None
        """
        pname = None
        for key in self.AppDb.keys():
            (section, option) = key.split(self.defaultSeparator)
            if section == "priv_names":
                if self.AppDb[key] == name:
                    pname = option
        return pname

    def _GetNiceName(self, pName):
        """
        Get a user friendly name for a private name.
        """
        for key in self.AppDb.keys():
            (section, option) = key.split(self.defaultSeparator)
            if section == "priv_names":
                if option == pName:
                    return self.AppDb[key]

    def _GetPrivVerb(self, verb, mimeType):
        """
        Look up the private verb for the exposed verb.
        """
        pVerb = None

        for key in self.AppDb.keys():
            (section, option) = key.split(self.defaultSeparator)
            if section == "priv_cmds":
                mtCheckKey = self.defaultSeparator.join([mimeType, option])
                if self.AppDb[key] == verb and self.AppDb.has_key(mtCheckKey):
                    pVerb = option

        return pVerb

    def _GetNiceVerb(self, pVerb):
        """
        Get a user friendly name for a private verb.
        """
        for key in self.AppDb.keys():
            (section, option) = key.split(self.defaultSeparator)
            if section == "priv_cmds":
                if option == pVerb:
                    return self.AppDb[key]

    def GetMimeType(self, name = None, extension = None):
        """
        Find a mimetype for the specified app name or extension.

        returns a mimeType in a string.
        """
        mimeType = None

        if name != None:
            privName = self._GetPrivName(name)
            lookupName = self.defaultSeparator.join(["name", privName])
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
            (section, option) = key.split(self.defaultSeparator)
            if section == "name":
                mt = self.AppDb[key]
                if mt == mimeType:
                    appName = self._GetNiceName(option)

        return appName

    def GetExtForMimeType(self, mimeType):
        """
        returns a extension in a string.
        """
        ext = None

        for key in self.AppDb.keys():
            (section, option) = key.split(self.defaultSeparator)
            if section == "extension":
                mt = self.AppDb[key]
                if mt == mimeType:
                    ext = option

        return ext

    def AddMimeType(self, name, extension, mimeType):
        """
        returns a tuple of (int, string). Success is (1, mimeType),
        failure is (0, reason)
        """

        namekey = self._GetPrivName(name)
        if namekey == None:
            namekey = str(GUID())

        privName = self.defaultSeparator.join(["priv_names", namekey])
        nameStr = self.defaultSeparator.join(["name", namekey])
        extStr = self.defaultSeparator.join(["extension", extension])
        mimeStr = self.defaultSeparator.join([mimeType, "None"])

        self.AppDb[privName] = name
        self.AppDb[nameStr] = mimeType
        self.AppDb[extStr] = mimeType
        self.AppDb[mimeStr] = None

        self._Flush()

        return (1, mimeType)

    def RemoveMimeType(self, name = None, extension = None, mimeType = None):
        """
        returns a tuple of (int, string). Success is (1, mimeType),
        failure is (0, reason)
        """

        if name == None and extension == None and mimeType == None:
            return (0, "Not enough information to remove mime type.")

        if name != None:
            namekey = self._GetPrivName(name)
            privName = self.defaultSeparator.join(["priv_names", namekey])
            name = self.AppDb[privName]
            mt = self.GetMimeType(name = name)
            mimeStr = self.defaultSeparator.join([mt, "None"])
            nameStr = self.defaultSeparator.join(["name", namekey])
            ext = self.GetExtForMimeType(mt)
            extStr = self.defaultSeparator.join(["extension", ext])
        elif mimeType != None:
            mimeStr = self.defaultSeparator.join([mimeType, "None"])
            name = self.GetNameForMimeType(mimeType)
            namekey = self._GetPrivName(name)
            privName = self.defaultSeparator.join(["priv_names", namekey])
            nameStr = self.defaultSeparator.join(["name", namekey])
            ext = self.GetExtForMimeType(mimeType)
            extStr = self.defaultSeparator.join(["extension", ext])
        elif extension != None:
            mimeType = self.GetMimeType(extension = extension)
            mimeStr = self.defaultSeparator.join([mimeType, "None"])
            name = self.GetNameForMimeType(mimeType)
            namekey = self._GetPrivName(name)
            privName = self.defaultSeparator.join(["priv_names", namekey])
            nameStr = self.defaultSeparator.join(["name", namekey])
            ext = self.GetExtForMimeType(mimeType)
            extStr = self.defaultSeparator.join(["extension", extension])

        if self.AppDb.has_key(privName):
            del self.AppDb[privName]

        if self.AppDb.has_key(nameStr):
            del self.AppDb[nameStr]

        if self.AppDb.has_key(extStr):
            del self.AppDb[extStr]

        if self.AppDb.has_key(mimeStr):
            del self.AppDb[mimeStr]

        self._Flush()

        return (1, mimeType)

    def GetCommandNames(self, mimeType):
        """
        returns a list of command names for this mime type.
        """
        cmds = list()

        for key in self.AppDb.keys():
            (section, option) = key.split(self.defaultSeparator)
            if section == mimeType:
                nName = self._GetNiceVerb(option)
                if nName != None:
                    cmds.append(nName)

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

        pCmd = self._GetPrivVerb(cmdName, mimeType)
        if pCmd != None:
            key = self.defaultSeparator.join([mimeType, pCmd])
        else:
            return cmdStr

        try:
            cmdStr = self.AppDb[key]
        except KeyError:
            return cmdStr

        if vars != None:
            cmdStr = self.AppDb[key] % vars

        return cmdStr

    def AddCommand(self, mimeType, cmdName, cmdString):
        """
        returns a tuple (int, string). Success is (1, cmdName),
        failure is (0, reason).
        """

        pCmd = self._GetPrivVerb(cmdName, mimeType)
        if pCmd == None:
            pCmd = str(GUID())
        cmdkey = self.defaultSeparator.join([mimeType, pCmd])
        pcmdkey = self.defaultSeparator.join(["priv_cmds", pCmd])

        self.AppDb[cmdkey] = cmdString
        self.AppDb[pcmdkey] = cmdName

        self._Flush()

        return (1, cmdName)

    def RemoveCommand(self, mimeType, cmdName):
        """
        returns a tuple (int, string). Success is (1, cmdName),
        failure is (0, reason).
        """

        pCmd = self._GetPrivVerb(cmdName, mimeType)
        cmdkey = self.defaultSeparator.join([mimeType, pCmd])
        if self.AppDb.has_key(cmdkey):
            del self.AppDb[cmdkey]
            
        pcmdkey = self.defaultSeparator.join(["priv_cmds", pCmd])
        if self.AppDb.has_key(pcmdkey):
            del self.AppDb[pcmdkey]

        self._Flush()

        return (1, cmdName)

    def RegisterApplication(self, name, mimeType, extension, commandDict,
                            fileList, srcPath, dstPath=None):
        """
        Encapsulate all the actions required to register a new application.
        returns 0 on failure, 1 on success
        """

        (ret, retStr) = self.AddMimeType(name, extension, mimeType)

        if ret:
            for cmdName in commandDict.keys():
                cmdStr = commandDict[cmdName]
                (result, resultString) = self.AddCommand(mimeType, cmdName,
                cmdStr)
                if not result:
                    return 0

            if dstPath == None:
                noSpaceName = '_'.join(name.split(' '))
                dstPath = os.path.join(GetUserAppPath(), noSpaceName)

            if not os.path.exists(dstPath):
                try:
                    os.mkdir(dstPath)
                except:
                    print "Couldn't make app directory (%s)." % dstPath

            for appFile in fileList:
                try:
                    srcf = os.path.join(srcPath, appFile)
                    dstf = os.path.join(dstPath, appFile)
                    shutil.copyfile(srcf, dstf)
                                    
                except:
                    print "Couldn't copy file into place (undoing register)."
                    self.UnregisterApplication(name=name,mimeType=mimeType)
        else:
            return 0

        self._Flush()

        return 1

    def ListApplications(self):
        """
        """
        apps = list()

        for key in self.AppDb.keys():
            (section, option) = key.split(self.defaultSeparator)
            if section == 'name':
                apps.append(self._GetNiceName(option))

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
                name = self._GetNiceName(option)
                mimetype = self.AppDb[key]
                apps.append(ApplicationDescription(None, name, None, None, mimetype))

        return apps

    def UnregisterApplication(self, name=None, mimeType=None, extension=None):
        """
        Encapsulate all the actions required to unregister an application.
        returns 0 on failure, 1 on success
        """

        if mimeType == None:
            mimeType = self.GetMimeType(name, extension)

        if mimeType == None:
            print "MimeType: %s not found." % mimeType
            return 0
        
        cmdList = self.GetCommandNames(mimeType)

        (ret, retStr) = self.RemoveMimeType(name, extension, mimeType)
        if ret:
            for cmdName in cmdList:
                (result, resultString) = self.RemoveCommand(mimeType,
                                                            cmdName)
                if not result:
                    print "Error removing verb, continuing."
                    
        noSpaceName = '_'.join(name.split(' '))
        dstPath = os.path.join(GetUserAppPath(), noSpaceName)

        if os.path.exists(dstPath):
            try:
                shutil.rmtree(dstPath)
            except:
                print "App directory error -- can't remove (%s)." % dstPath

        return 1
