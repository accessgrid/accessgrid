#-----------------------------------------------------------------------------
# Name:        AGParameter.py
# Purpose:     
#
# Author:      Thomas D. Uram
#
# Created:     2003/08/02
# RCS-ID:      $Id: AGParameter.py,v 1.7 2003-02-28 17:20:43 turam Exp $
# Copyright:   (c) 2003
# Licence:     See COPYING.txt
#-----------------------------------------------------------------------------
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
        self.low = low
        self.high = high

    def SetValue( self, value ):

        value = int(value)

        if self.low > value or self.high < value:
            raise ValueError("RangeParameter.SetValue")

        self.value = value

class OptionSetParameter( ValueParameter ):

    TYPE = "OptionSetParameter"

    def __init__( self, name, value, options ):
        ValueParameter.__init__( self, name, value )
        self.options = options

    def SetValue( self, value ):

        if value not in self.options:
            raise ValueError("OptionSetParameter.SetValue")

        self.value = value

def CreateParameter( parmstruct ):
    """
    Object factory to create parameter instances from those moronic SOAPStructs,
    emphasizing that we should be using WSDL
    """
    if parmstruct.type == OptionSetParameter.TYPE:
        parameter = OptionSetParameter( parmstruct.name, parmstruct.value, parmstruct.options )
    elif parmstruct.type == RangeParameter.TYPE:
        parameter = RangeParameter( parmstruct.name, parmstruct.value, parmstruct.low, parmstruct.high )
    elif parmstruct.type == ValueParameter.TYPE:
        parameter = ValueParameter( parmstruct.name, parmstruct.value )
    elif parmstruct.type == TextParameter.TYPE:
        parameter = TextParameter( parmstruct.name, parmstruct.value )
    else:
        raise TypeError("Unknown parameter type:", parmstruct.type )

    return parameter
