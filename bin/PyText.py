#-----------------------------------------------------------------------------
# Name:        PyText.py
# Purpose:
#
# Author:      Ivan R. Judson
#
# Created:     2003/01/02
# RCS-ID:      $Id: PyText.py,v 1.2 2003-02-06 20:45:47 judson Exp $
# Copyright:   (c) 2002
# Licence:     See COPYING.TXT
#-----------------------------------------------------------------------------

import sys
from wxPython.wx import wxPySimpleApp, wxInitAllImageHandlers

from AccessGrid.TextClientUI import TextClientUI

if __name__ == "__main__":
    pyText = wxPySimpleApp()
    wxInitAllImageHandlers()
    TextFrame = TextClientUI(None, -1, "", location = (sys.argv[1],
                              int(sys.argv[2])))
    pyText.SetTopWindow(TextFrame)
    TextFrame.Show(1)
    pyText.MainLoop()
