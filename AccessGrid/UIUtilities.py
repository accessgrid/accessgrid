#-----------------------------------------------------------------------------
# Name:        UIUtilities.py
# Purpose:     
#
# Author:      Everyone
#
# Created:     2003/06/02
# RCS-ID:      $Id: UIUtilities.py,v 1.1 2003-02-06 14:48:36 judson Exp $
# Copyright:   (c) 2002-2003
# Licence:     See COPYING.TXT
#-----------------------------------------------------------------------------
from wxPython.wx import *
from wxPython.lib.imagebrowser import *

from AccessGrid.Utilities import formatExceptionInfo

class ErrorDialog:
    def __init__(self, frame, text):
        (name, args, traceback_string_list) = formatExceptionInfo()
#        for x in traceback_string_list:
#            print(x)       
        noServerDialog = wxMessageDialog(frame, text, '', wxOK)
        noServerDialog.ShowModal()
        noServerDialog.Destroy()
        
class BugReportDialog:
    def __init__(self, frame, profile):
        reportDialog = wxMessageDialog(frame, 'BUG REPORT', '', wxOK)
        reportDialog.ShowModal()
        reportDialog.Destroy()