#-----------------------------------------------------------------------------
# Name:        PersonalNode.py
# Purpose:     platform magic
#              
# Created:     2003/05/06
# RCS-ID:      $Id: PersonalNode.py,v 1.1 2004-03-12 05:35:24 judson Exp $
# Copyright:   (c) 2002
# Licence:     See COPYING.TXT
#-----------------------------------------------------------------------------
"""
"""
__revision__ = "$Id: PersonalNode.py,v 1.1 2004-03-12 05:35:24 judson Exp $"

from AccessGrid.Platform import isWindows, isLinux, isOSX

if isWindows():
    from AccessGrid.Platform.win32.PersonalNode import *
elif isLinux():
    from AccessGrid.Platform.linux2.PersonalNode import *
elif isOSX():
    from AccessGrid.Platform.darwin.PersonalNode import *
else:
    log.warn("Platform doesn't have a platform-specific module for %s",
             sys.platform)
