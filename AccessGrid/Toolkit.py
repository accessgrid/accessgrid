#-----------------------------------------------------------------------------
# Name:        Toolkit.py
# Purpose:     Toolkit-wide initialization and state management.
#
# Author:      Robert Olson
#
# Created:     2003/05/06
# RCS-ID:      $Id: Toolkit.py,v 1.15 2004-03-02 22:43:58 judson Exp $
# Copyright:   (c) 2002
# Licence:     See COPYING.TXT
#-----------------------------------------------------------------------------
"""
"""
__revision__ = "$Id: Toolkit.py,v 1.15 2004-03-02 22:43:58 judson Exp $"
__docformat__ = "restructuredtext en"

import logging
import os

from AccessGrid.AppDb import AppDb
from AccessGrid.Security import CertificateManager
from AccessGrid.Platform import GetUserConfigDir, GetUserAppPath

log = logging.getLogger("AG.toolkit")

#
# Global application instance object.
#
# Access this through the GetApplication interface only.
#

def GetApplication():
   return Application.instance
 
class Application:
    instance = None

    def __init__(self):

        if Application.instance is not None:
            raise Exception, "Only one instance of Application is allowed"

        Application.instance = self

        self.userConfigDir = GetUserConfigDir()
        
        if not os.path.exists(self.userConfigDir):
            try:
                os.makedirs(self.userConfigDir)
            except OSError, e:
                log.exception("Toolkit.Initialize: could not mkdir %s",
                              self.userConfigDir)

        log.debug("userConfigDir: %s", self.userConfigDir)

        if not os.path.exists(GetUserAppPath()):
            try:
                os.mkdir(GetUserAppPath())
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

