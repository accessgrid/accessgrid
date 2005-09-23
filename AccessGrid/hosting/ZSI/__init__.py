#-----------------------------------------------------------------------------
# Name:        __init__.py
# Created:     2003/08/02
# RCS-ID:      $Id: __init__.py,v 1.3 2005-09-23 22:03:06 eolson Exp $
# Copyright:   (c) 2003
# Licence:     See COPYING.txt
#-----------------------------------------------------------------------------
"""
ZSI hosting interface modules.
"""
__revision__ = "$Id: __init__.py,v 1.3 2005-09-23 22:03:06 eolson Exp $"

from ZSI import TC
from AccessGrid.interfaces.AccessGrid_Types import www_accessgrid_org_v3_0 as AGTypes
from AccessGrid.wsdl import SchemaToPyTypeMap

# Register our types with ZSI "any"
TC.RegisterGeneratedTypesWithMapping(generatedTypes = AGTypes, mapping=SchemaToPyTypeMap.mapping)


