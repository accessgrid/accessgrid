#-----------------------------------------------------------------------------
# Name:        Toolkit.py
# Purpose:     Toolkit-wide initialization and state management.
#
# Author:      Robert Olson
#
# Created:     2003/05/06
# RCS-ID:      $Id: Toolkit.py,v 1.10 2003-08-22 19:17:45 judson Exp $
# Copyright:   (c) 2002
# Licence:     See COPYING.TXT
#-----------------------------------------------------------------------------

import logging
import os

from AppDb import AppDb

log = logging.getLogger("AG.toolkit")

AG_TRUE = 1
AG_FALSE = 0

#
# Global application instance object.
#
# Access this through the GetApplication interface only.
#

import CertificateManager

from AccessGrid import Platform

# Call GetVersion() to get AGTK version information.
MAJOR_VERSION = 2
MINOR_VERSION = 1
POINT_VERSION = 1


class Version:
    """
    Version details: MAJOR.MINOR.POINT
    Works with the following operators : >, >=, ==, <>, <=, <
    """
    def __init__(self):
        self.major = 0
        self.minor = 0
        self.point = 0

    def __repr__(self):
        return self.AsString()

    def AsString(self):
        return str(self.major) + "." + str(self.minor) + "." + str(self.point)

    def AsTuple3(self):
        return (int(self.major), int(self.minor), int(self.point))

    def __lt__(self, other):
        if (int(self.major) < int(other.major)):
            return AG_TRUE
        elif (int(self.major) == int(other.major)):
            if (int(self.minor) < int(other.minor)):
                return AG_TRUE
            elif (int(self.minor) == int(other.minor)):
                if (int(self.point) < int(other.point)):
                    return AG_TRUE
        return AG_FALSE

    def __le__(self, other):
        if (int(self.major) <= int(other.major)):
            if (int(self.minor) <= int(other.minor)):
                if (int(self.point) <= int(other.point)):
                    return AG_TRUE
        return AG_FALSE

    def __eq__(self, other):
        if (int(self.major) == int(other.major)):
            if (int(self.minor) == int(other.minor)):
                if (int(self.point) == int(other.point)):
                    return AG_TRUE
        return AG_FALSE

    def __ne__(self, other):
        if (int(self.major) == int(other.major)):
            if (int(self.minor) == int(other.minor)):
                if (int(self.point) == int(other.point)):
                    return AG_FALSE
        return AG_TRUE

    def __gt__(self, other):
        if (int(self.major) > int(other.major)):
            return AG_TRUE
        elif (int(self.major) == int(other.major)):
            if (int(self.minor) > int(other.minor)):
                return AG_TRUE
            elif (int(self.minor) == int(other.minor)):
                if (int(self.point) > int(other.point)):
                    return AG_TRUE
        return AG_FALSE

    def __ge__(self, other):
        if (int(self.major) >= int(other.major)):
            if (int(self.minor) >= int(other.minor)):
                if (int(self.point) >= int(other.point)):
                    return AG_TRUE
        return AG_FALSE


def CreateVersionFromTuple3( (major, minor, point) ):
    ver = Version()
    ver.major = int(major)
    ver.minor = int(minor)
    ver.point = int(point)
    return ver

def CreateVersionFromString(strng):
    ver_list = strng.split(".")
    if len(ver_list) > 3 or len(ver_list) < 2:
        raise "InvalidVersionString"
    ver = Version()
    ver.major = int(ver_list[0])
    ver.minor = int(ver_list[1])
    if len(ver_list) == 3:
        ver.point = int(ver_list[2])
    return ver

agtk_version = CreateVersionFromTuple3( (MAJOR_VERSION, MINOR_VERSION, POINT_VERSION) )

def GetVersion():
    """ Use this to get the current version of AGTK. """
    return agtk_version

def CreateVersionFromTuple3( (MAJOR_VERSION, MINOR_VERSION, POINT_VERSION) ):
    strng = str(MAJOR_VERSION) + "." + str(MINOR_VERSION) + "." + str(POINT_VERSION)
    return strng


def GetApplication():
    return Application.instance

class Application:
    instance = None

    def __init__(self):

        if Application.instance is not None:
            raise Exception, "Only one instance of Application is allowed"

        Application.instance = self

        self.userConfigDir = Platform.GetUserConfigDir()
        
        if not os.path.exists(self.userConfigDir):
            try:
                os.makedirs(self.userConfigDir)
            except OSError, e:
                log.exception("Toolkit.Initialize: could not mkdir %s",
                              self.userConfigDir)

        log.debug("userConfigDir: %s", self.userConfigDir)

        if not os.path.exists(Platform.GetUserAppPath()):
            try:
                os.mkdir(Platform.GetUserAppPath())
            except:
                log.exception("Couldn't make user app directory.")
                
        self.AppDb = AppDb()

    def Initialize(self):
        """

        """

        pass

    def Finalize(self):
        pass

    def GetCertificateManager(self):
        return self.certificateManager

    def InitGlobusEnvironment(self):
        return self.GetCertificateManager().GetUserInterface().InitGlobusEnvironment()

    def GetDefaultIdentityDN(self):
        ident = self.certificateManager.GetDefaultIdentity()
        if ident is None:
            return None
        else:
            return str(ident.GetSubject())

    def GetAppDatabase(self):
        return self.AppDb
    
class CmdlineApplication(Application):
    """
    An application that's going to run without a gui.


    """

    def __init__(self):
        Application.__init__(self)
        
        userInterface = CertificateManager.CertificateManagerUserInterface()
        self.certificateManager = \
            CertificateManager.CertificateManager(self.userConfigDir,
                                                  userInterface)

class ServiceApplicationWithIdentity(Application):
    """
    An application that's going to run as a service.

    This implies no graphical UI, and that the identity cert and key are
    explicitly specified.

    """

    def __init__(self, cert, key):
        Application.__init__(self)

        self.cert = cert
        self.key = key
        
        userInterface = CertificateManager.CertificateManagerUserInterface()
        self.certificateManager = \
            CertificateManager.CertificateManager(self.userConfigDir,
                                                  userInterface,
                                                  identityCert = self.cert,
                                                  identityKey = self.key)
    def Initialize(self):
        Application.Initialize(self)

        
class ServiceApplicationInheritIdentity(Application):
    """
    An application that's going to run as a service.

    This implies no graphical UI, and that the app uses the identity
    from the process environment.

    """

    def __init__(self):
        Application.__init__(self)
        userInterface = CertificateManager.CertificateManagerUserInterface()
        self.certificateManager = \
            CertificateManager.CertificateManager(self.userConfigDir,
                                                  userInterface,
                                                  inheritIdentity = 1)

class WXGUIApplication(Application):
    def __init__(self):
        Application.__init__(self)

        from CertificateManagerWXGUI import CertificateManagerWXGUI
        self.gui = CertificateManagerWXGUI()
        self.certificateManager = CertificateManager.CertificateManager(self.userConfigDir,
                                                                        self.gui)

