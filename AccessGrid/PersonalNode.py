#-----------------------------------------------------------------------------
# Name:        PersonalNode.py
# Purpose:     Support for PersonalNode startup.
#
# Author:      Robert Olson
#
# Created:     2002/12/12
# RCS-ID:      $Id: PersonalNode.py,v 1.9 2003-04-23 19:26:23 olson Exp $
# Copyright:   (c) 2002
# Licence:     See COPYING.TXT
#-----------------------------------------------------------------------------

import sys

if sys.platform == "win32":

    import PersonalNodeWin32
    PersonalNodeManager = PersonalNodeWin32.PersonalNodeManager
    PN_NodeService = PersonalNodeWin32.PN_NodeService
    PN_ServiceManager = PersonalNodeWin32.PN_ServiceManager

else:

    import PersonalNodeLinux
    PersonalNodeManager = PersonalNodeLinux.PersonalNodeManager
    PN_NodeService = PersonalNodeLinux.PN_NodeService
    PN_ServiceManager = PersonalNodeLinux.PN_ServiceManager

    
