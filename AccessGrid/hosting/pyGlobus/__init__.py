#-----------------------------------------------------------------------------
# Name:        __init__.py
# Purpose:     
#
# Author:      Robert D. Olson
#
# Created:     2003/08/02
# RCS-ID:      $Id: __init__.py,v 1.5 2003-08-12 20:56:41 olson Exp $
# Copyright:   (c) 2003
# Licence:     See COPYING.txt
#-----------------------------------------------------------------------------

import pyGlobus.io
import sys

IOException = pyGlobus.io.IOBaseException

if sys.platform == "win32":
    import ProxyGenProgrammatic
    ProxyGen = ProxyGenProgrammatic
    del ProxyGenProgrammatic
    
else:
    import ProxyGenGPI
    ProxyGen = ProxyGenProgrammatic
    del ProxyGenGPI


    
