import _winreg
import win32api

try:
    key = "SYSTEM\\ControlSet001\\Control\\MediaResources\\msvideo"
    videoKey = _winreg.OpenKey(_winreg.HKEY_LOCAL_MACHINE, key)
except Exception, e:
    print "Got an exception doing OpenKey: ", e
    
try:
    (nSubKeys, nValues, lastModified) = _winreg.QueryInfoKey(videoKey)
    print "NK: %d NV: %d LM: %d" % (nSubKeys, nValues, lastModified)
except Exception, e:
    print "Got an exception doing QueryInfoKey: ", e

try:
    sVal = _winreg.EnumKey(videoKey, 0)
    sKey = _winreg.OpenKey(videoKey, sVal)
    print "Subkey: ", sKey
except Exception, e:
    print "Got an exception retrieving: %s %d" % (videoKey, 0)

try:
    (nSubKeys, nValues, lastModified) = _winreg.QueryInfoKey(sKey)
    print "NK: %d NV: %d LM: %d" % (nSubKeys, nValues, lastModified)
except Exception, e:
    print "Got an exception retrieving: %s %d" % (videoKey, 0)

try:
    for i in range(0, nSubKeys):
        kName = _winreg.EnumKey(sKey, i)
        print "SubKey: %s" % kName
except Exception, e:
    print "Got an exception retrieving: %s %d" % (sKey, i)

try:
    for i in range(0, nValues):
        (vName, vData, vType) = _winreg.EnumValue(sKey, i)
        print "NV: %s VD: %s VT: %s" % (vName, vData, vType)
except Exception, e:
    print "Got an exception retrieving: %s %d" % (sKey, i)
