#-----------------------------------------------------------------------------
# Name:        AGParameter.py
# Purpose:     
#
# Author:      Thomas D. Uram
#
# Created:     2003/08/02
# RCS-ID:      $Id: AGParameter.py,v 1.9 2004-05-12 17:09:09 turam Exp $
# Copyright:   (c) 2003
# Licence:     See COPYING.txt
#-----------------------------------------------------------------------------
"""
"""

__revision__ = "$Id: AGParameter.py,v 1.9 2004-05-12 17:09:09 turam Exp $"
__docformat__ = "restructuredtext en"

class ValueParameter:

    TYPE = "ValueParameter"

    def __init__( self, name, value=None ):
        self.name = name
        self.value = value
        self.type = self.TYPE

    def SetValue( self, value ):
        self.value = int(value)

class TextParameter:

    TYPE = "TextParameter"

    def __init__( self, name, value=None ):
        self.name = name
        self.value = value
        self.type = self.TYPE

    def SetValue( self, value ):
        self.value = value

class RangeParameter( ValueParameter ):

    TYPE = "RangeParameter"

    def __init__( self, name, value, low, high ):

        ValueParameter.__init__( self, name, value )
        self.low = int(low)
        self.high = int(high)

    def SetValue( self, value ):

        value = int(value)

        if self.low > value or self.high < value:
            raise ValueError("RangeParameter: Value %d not in range [%d:%d]",
                             value,self.low,self.high)

        self.value = value

class OptionSetParameter( ValueParameter ):

    TYPE = "OptionSetParameter"

    def __init__( self, name, value, options ):
        ValueParameter.__init__( self, name, value )
        self.options = options

    def SetValue( self, value ):

        if value not in self.options:
            raise KeyError("Option not in option set: %s", value)

        self.value = value

