#-----------------------------------------------------------------------------
# Name:        Toolkit.py
# Purpose:     Toolkit-wide initialization and state management.
#
# Author:      Robert Olson
#
# Created:     2003/05/06
# RCS-ID:      $Id: Toolkit.py,v 1.2 2003-05-20 20:06:01 olson Exp $
# Copyright:   (c) 2002
# Licence:     See COPYING.TXT
#-----------------------------------------------------------------------------

import logging

log = logging.getLogger("AG.toolkit")

#
# Global application instance object.
#
# Access this through the GetApplication interface only.
#

import CertificateManager
from AccessGrid import Platform

def GetApplication():
    return Application.instance

class Application:
    instance = None

    def __init__(self):

        if Application.instance is not None:
            raise Exception, "Only one instance of Application is allowed"

        Application.instance = self

        self.userConfigDir = Platform.GetUserConfigDir()
        log.debug("userConfigDir: %s", self.userConfigDir)

    def Initialize(self):
        """

        """

        pass

    def Finalize(self):
        pass

    def GetCertificateManager(self):
        return self.certificateManager

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
    def Initialize(self):
        Application.Initialize(self)


        self.certificateManager.InitEnvironment()

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


        self.certificateManager.InitEnvironment()

        
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

    def Initialize(self):
        Application.Initialize(self)

        self.certificateManager.InitEnvironment()

        

class WXGUIApplication(Application):
    def __init__(self):
        Application.__init__(self)

        from CertificateManagerWXGUI import CertificateManagerWXGUI
        self.gui = CertificateManagerWXGUI()
        self.certificateManager = CertificateManager.CertificateManager(self.userConfigDir,
                                                                        self.gui)


    def Initialize(self):
        Application.Initialize(self)

        self.certificateManager.InitEnvironment()

