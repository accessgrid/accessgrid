#-----------------------------------------------------------------------------
# Name:        __init__.py
# Created:     2003/08/02
# RCS-ID:      $Id: __init__.py,v 1.5 2006-01-19 20:46:41 eolson Exp $
# Copyright:   (c) 2003
# Licence:     See COPYING.txt
#-----------------------------------------------------------------------------
"""
ZSI hosting interface modules.
"""
__revision__ = "$Id: __init__.py,v 1.5 2006-01-19 20:46:41 eolson Exp $"

def SetupParser():
    from ZSI.parse import ParsedSoap
    from xml.dom import expatbuilder
    class ExpatReaderClass:
        fromString = staticmethod(expatbuilder.parseString)
        fromStream = staticmethod(expatbuilder.parse)
    ParsedSoap.defaultReaderClass = ExpatReaderClass

SetupParser()

from ZSI import TC
from AccessGrid.interfaces.AccessGrid_Types import www_accessgrid_org_v3_0 as AGTypes
from AccessGrid.wsdl import SchemaToPyTypeMap

# Register our types with ZSI "any"
TC.RegisterGeneratedTypesWithMapping(generatedTypes = AGTypes, mapping=SchemaToPyTypeMap.mapping)

from ZSI import ZSIException as HostingException
from ZSI.TC import _DynamicImport

class NotAuthorized(Exception): pass
class NoSuchService(Exception): pass

def GetHostingExceptionModuleAndClassName(exc):
    try:
        if exc.fault.string.startswith("Processing Failure"):
            exceptionInfo = str(exc).split('\n')[1] # 0 line is the type of zsi fault
                                                    # 1 line is the exception class information
            moduleName, className = exceptionInfo.split(":")
            # Remap zsi defined exceptions to AG.hosting module so AG code doesn't need to know about zsi.
            if str(moduleName).lower().startswith("zsi"):
                lowerClassName = str(className).lower()
                if lowerClassName == "nosuchservice":
                    moduleName = "AccessGrid.hosting"
                    className = "NoSuchService"
                # --- Add elifs for other zsi exceptions here ---
        elif exc.fault.string.startswith( "Not authorized"):
            moduleName, className = "AccessGrid.hosting", "NotAuthorized"
        else:
            moduleName, className = None, exc.fault.string
    except Exception,e:
        raise Exception("Unable to extract module and class name from remote Exception: ", exc)
    return moduleName, className

def GetHostingException(exc):
    moduleName, className = None,None
    try:
        moduleName, className = GetHostingExceptionModuleAndClassName(exc)
        remoteExceptionClass = _DynamicImport(moduleName, className)
        exceptionDetailStr = str(exc).split('\n')[1:]
        remoteException = apply(remoteExceptionClass, [exceptionDetailStr])
    except Exception, e:
        remoteException = Exception("Unable to extract a Hosting Exception: ", exc, str(exc), moduleName, className, e)
    return remoteException

def ReraiseHostingException(exc):
    raise GetHostingException(exc)

