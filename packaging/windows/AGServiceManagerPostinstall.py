import os
import sys
import _winreg

if sys.platform == 'win32':
    AG20 = _winreg.OpenKey(_winreg.HKEY_LOCAL_MACHINE, "SOFTWARE\\Access Grid Toolkit\\2.0")
    ConfigDir, Type = _winreg.QueryValueEx(AG20, "ConfigPath")
    InstallDir, Type = _winreg.QueryValueEx(AG20, "InstallPath")
    AGServiceManagerFD = open(os.path.join(ConfigDir, "AGServiceManager.cfg"), "w")
    AGServiceManagerFD.write("[Service Manager]\n")
    AGServiceManagerFD.write("servicesDirectory = " + os.path.joing(InstallDir, "local_service\n"))
    AGServiceManagerFD.close()
