import sys
import _winreg
import win32api

out = file(sys.argv[1], "w")

try:
    key = "SYSTEM\\ControlSet001\\Control\\MediaResources\\msvideo"
    videoKey = _winreg.OpenKey(_winreg.HKEY_LOCAL_MACHINE, key)
except Exception, e:
    print "Got an exception doing OpenKey: ", e
    out.close()
    sys.exit(-1)

try:
    (nSubKeys, nValues, lastModified) = _winreg.QueryInfoKey(videoKey)
except Exception, e:
    print "Got an exception doing QueryInfoKey: ", e
    out.close()
    sys.exit(-1)

try:
    sVal = _winreg.EnumKey(videoKey, 0)
    sKey = _winreg.OpenKey(videoKey, sVal)
except Exception, e:
    print "Got an exception retrieving: %s %d" % (videoKey, 0)
    out.close()
    sys.exit(-1)

try:
    (nSubKeys, nValues, lastModified) = _winreg.QueryInfoKey(sKey)
except Exception, e:
    print "Got an exception retrieving: %s %d" % (videoKey, 0)
    out.close()
    sys.exit(-1)

try:
    for i in range(0, nSubKeys):
        kName = _winreg.EnumKey(sKey, i)
except Exception, e:
    print "Got an exception retrieving: %s %d" % (sKey, i)
    out.close()
    sys.exit(-1)

try:
    for i in range(0, nValues):
        (vName, vData, vType) = _winreg.EnumValue(sKey, i)
        if vName == "FriendlyName":
            out.write("device: %s\n" % vData)
            out.write("portnames: external-in\n")
except Exception, e:
    print "Got an exception retrieving: %s %d" % (sKey, i)
    out.close()
    sys.exit(-1)

out.close()
