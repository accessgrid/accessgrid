#-----------------------------------------------------------------------------
# Name:        PersonalNode.py
# Purpose:     Support for PersonalNode startup.
#
# Author:      Robert Olson
#
# Created:     2002/12/12
# RCS-ID:      $Id: PersonalNode.py,v 1.12 2003-09-16 07:20:18 judson Exp $
# Copyright:   (c) 2002
# Licence:     See COPYING.TXT
#-----------------------------------------------------------------------------
"""
"""
__revision__ = "$Id: PersonalNode.py,v 1.12 2003-09-16 07:20:18 judson Exp $"
__docformat__ = "restructuredtext en"

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

    
