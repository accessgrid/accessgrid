
import sys
import os

import _winreg

# define install path of ag module
key = "Software\Python\PythonCore\%s\InstallPath"%sys.version[:3]
pythonKey = _winreg.OpenKey(_winreg.HKEY_LOCAL_MACHINE, key)
installpath, valuetype = _winreg.QueryValueEx(pythonKey, "")
installpath = os.path.join(installpath,'lib','site-packages','AccessGrid3')

# reset AGTK_LOCATION env variable
os.environ['AGTK_LOCATION'] = ''

# prepend ag install path to pythonpath env variable
if os.environ.has_key('PYTHONPATH'):
    os.environ['PYTHONPATH'] ='%s;%s '%(installpath, os.environ['PYTHONPATH'])

else:
    os.environ['PYTHONPATH'] = installpath

args = map(lambda x: '"' + x + '"', sys.argv[1:])
if sys.argv[1:]:
    os.spawnv(os.P_WAIT, sys.executable, [sys.executable]+args)

    
