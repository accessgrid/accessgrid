#!/usr/bin/python
#-----------------------------------------------------------------------------
# Name:        agversion.py
# Purpose:     Support AccessGrid module version selection
# Created:     2006/07/21
# RCS-ID:      $Id: agversion.py,v 1.6 2006-08-04 16:08:32 turam Exp $
# Copyright:   (c) 2006
# Licence:     See COPYING.txt
#-----------------------------------------------------------------------------
"""
"""
__revision__ = "$Id: agversion.py,v 1.6 2006-08-04 16:08:32 turam Exp $"

import sys
import os
from distutils.sysconfig import get_python_lib 

class VersionError(Exception):
    pass

def select(ver):

    # establish platform-specific AccessGrid module path
    if sys.platform in ['win32']:

        import _winreg

        key = "Software\Python\PythonCore\%s\InstallPath"%sys.version[:3]
        pythonKey = _winreg.OpenKey(_winreg.HKEY_LOCAL_MACHINE, key)
        installpath, valuetype = _winreg.QueryValueEx(pythonKey, "")
        installpath = os.path.join(installpath,'lib','site-packages','AccessGrid%s'%ver)

    elif sys.platform in ['darwin']:
        installpath = '/Applications/AccessGridToolkit3.app/Contents/Resources/lib/python%s/site-packages/AccessGrid%s' % (sys.version[:3],ver)
    elif sys.platform in ['linux2','freebsd5','freebsd6']:
        installpath = '%s/AccessGrid%s' % (get_python_lib(),ver) 

    # confirm that the path exists
    if not os.path.exists(installpath):
        raise VersionError('Requested version (%s) of AccessGrid not found' % ver)

    # modify the in-process pythonpath and the environment pythonpath (for the sake of the children)
    sys.path.insert(0,installpath)
    if os.environ.has_key('PYTHONPATH'):
        os.environ['PYTHONPATH'] = os.pathsep.join([installpath, os.environ['PYTHONPATH']])
    else:
        os.environ['PYTHONPATH'] = installpath
        
