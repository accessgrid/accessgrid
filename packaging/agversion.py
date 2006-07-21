#!/usr/bin/python
#-----------------------------------------------------------------------------
# Name:        agversion.py
# Purpose:     Support AccessGrid module version selection
# Created:     2006/07/21
# RCS-ID:      $Id: agversion.py,v 1.1 2006-07-21 17:04:14 turam Exp $
# Copyright:   (c) 2006
# Licence:     See COPYING.txt
#-----------------------------------------------------------------------------
"""
"""
__revision__ = "$Id: agversion.py,v 1.1 2006-07-21 17:04:14 turam Exp $"

import sys
import os

class VersionError(Exception):
    pass

def select(ver):

    # If we get here then this is the first time wxversion is used, 
    # ensure that wxPython hasn't been imported yet.
    if sys.modules.has_key('AccessGrid'):
        raise VersionError("agversion.select() must be called before AccessGrid is imported")

    if sys.platform in ['win32']:

        import _winreg

        key = "Software\Python\PythonCore\%s\InstallPath"%sys.version[:3]
        pythonKey = _winreg.OpenKey(_winreg.HKEY_LOCAL_MACHINE, key)
        installpath, valuetype = _winreg.QueryValueEx(pythonKey, "")
        installpath = os.path.join(installpath,'lib','site-packages','AccessGrid%s'%ver)

    elif sys.platform in ['darwin']:
        installpath = '/Applications/AccessGridToolkit3.app/Contents/Resources/lib/python%s/site-packages/AccessGrid%s' % (sys.version[:3],ver)

    elif sys.platform in ['linux2','freebsd5','freebsd6']:
        installpath = '%s/lib/python%s/site-packages/AccessGrid%s' % (sys.prefix,sys.version[:3],ver)

    
    if not os.path.exists(installpath):
        raise VersionError('Requested version (%s) of AccessGrid not found' % ver)

    sys.path.insert(0,installpath)
