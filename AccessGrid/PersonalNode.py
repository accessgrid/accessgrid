#-----------------------------------------------------------------------------
# Name:        PersonalNode.py
# Purpose:     Support for PersonalNode startup.
#
# Author:      Robert Olson
#
# Created:     2002/12/12
# RCS-ID:      $Id: PersonalNode.py,v 1.11 2003-05-05 18:26:23 olson Exp $
# Copyright:   (c) 2002
# Licence:     See COPYING.TXT
#-----------------------------------------------------------------------------

import sys

if sys.platform == "win32":

    from AccessGrid import PersonalNodeWin32
    pnodeModule = PersonalNodeWin32

else:

    from AccessGrid import PersonalNodePipes
    pnodeModule = PersonalNodePipes

PersonalNodeManager = pnodeModule.PersonalNodeManager
PN_NodeService = pnodeModule.PN_NodeService
PN_ServiceManager = pnodeModule.PN_ServiceManager

    
