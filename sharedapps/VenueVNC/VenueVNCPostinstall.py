import os
import sys
import time
import win32api

sys.stdout.write("Generating runvnc.bat file.... ")
InstallDir = win32api.GetShortPathName(sys.argv[1])
print(InstallDir)
runvncFD = open(os.path.join(InstallDir, "runvnc.bat"), "w")
runvncFD.write("cd " + InstallDir + "\n")
runvncFD.write("VenueVNCClient %1\n")
runvncFD.close()
    
sys.stdout.write("Done\n")
