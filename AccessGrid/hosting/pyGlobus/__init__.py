#-----------------------------------------------------------------------------
# Name:        __init__.py
# Purpose:     
#
# Author:      Robert D. Olson
#
# Created:     2003/08/02
# RCS-ID:      $Id: __init__.py,v 1.7 2003-09-16 07:20:56 judson Exp $
# Copyright:   (c) 2003
# Licence:     See COPYING.txt
#-----------------------------------------------------------------------------
"""
"""
__revision__ = "$Id: __init__.py,v 1.7 2003-09-16 07:20:56 judson Exp $"
__docformat__ = "restructuredtext en"

import pyGlobus.io
import sys

IOException = pyGlobus.io.IOBaseException

if sys.platform == "win32":
    import ProxyGenProgrammatic
    ProxyGen = ProxyGenProgrammatic
    del ProxyGenProgrammatic
    
else:
    import ProxyGenGPI
    ProxyGen = ProxyGenGPI
    del ProxyGenGPI


    
