import os
import sys
import _winreg

if sys.platform == 'win32':
    AG20 = _winreg.OpenKey(_winreg.HKEY_LOCAL_MACHINE, "SOFTWARE\\Access Grid Toolkit\\2.0")
    ConfigDir, Type = _winreg.QueryValueEx(AG20, "ConfigPath")
    InstallDir, Type = _winreg.QueryValueEx(AG20, "InstallPath")
    AGNodeServiceFD = open(os.path.join(ConfigDir, "AGNodeService.cfg"), "w")
    AGNodeServiceFD.write("[Node Configuration]\n")
    AGNodeServiceFD.write("servicesDirectory = " + os.path.join(InstallDir, "services\n"))
    AGNodeServiceFD.write("configDirectory = " + ConfigDir + "\n")
    AGNodeServiceFD.write("defaultNodeConfiguration = defaultWindows\n")
    AGNodeServiceFD.close()
