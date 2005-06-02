#-----------------------------------------------------------------------------
# Name:        __init__.py
# Created:     2003/08/02
# RCS-ID:      $Id: __init__.py,v 1.2 2005-06-02 19:19:42 eolson Exp $
# Copyright:   (c) 2003
# Licence:     See COPYING.txt
#-----------------------------------------------------------------------------
"""
ZSI hosting interface modules.
"""
__revision__ = "$Id: __init__.py,v 1.2 2005-06-02 19:19:42 eolson Exp $"

from ZSI import TC
from AccessGrid.interfaces.AccessGrid_Types import www_accessgrid_org_v3_0 as AGTypes

def dynamicImport(moduleName, className):
    mod = __import__(moduleName)
    components = moduleName.split('.')
    for comp in components[1:]:
        mod = getattr(mod, comp)
    return getattr(mod, className)
    
def RegisterType(schemaTypeName, classModuleName, className):
    # Doing this
    # sd_instance = AGTypes.StreamDescription_(pname="StreamDescription")
    # TC.Any.serialmap[Descriptions.StreamDescription] = sd_instance
    # TC.Any.parsemap[(None,'StreamDescription')] = sd_instance
    classDef = dynamicImport(classModuleName, className)
    interfaceDef = getattr(AGTypes, schemaTypeName + "_")

    instance = interfaceDef(pname=className)
    TC.Any.serialmap[classDef] = instance
    TC.Any.parsemap[(None,schemaTypeName)] = instance


