#!/usr/bin/python2
#----------------------------------------------------------------------------
# Name:        rtpBeaconUI.py
# Purpose:     User interface for the beacon 
#
# Author:      Thomas Uram, Susanne Lefvert
#
# Created:     2002/12/12
# RCS-ID:      $Id: rtpBeaconUI.py,v 1.1 2005-06-22 22:40:19 lefvert Exp $
# Copyright:   (c) 2003
# Licence:     See COPYING.TXT
#----------------------------------------------------------------------------

__revision__ = "$Id: rtpBeaconUI.py,v 1.1 2005-06-22 22:40:19 lefvert Exp $"

from wxPython.wx import *
from wxPython.grid import *
from wxPython.lib.mixins.grid import wxGridAutoEditMixin

import copy

class BeaconFrame(wxFrame):
    def __init__(self, parent, log, beacon):
        wxFrame.__init__(self, parent, -1, "RTP Beacon View", size=(910,310))

        self.beacon = beacon
        self.grid = wxGrid(self,-1)

        if not self.beacon:
            self.OnExit(None)
            return
            
        address = self.beacon.GetConfigData('groupAddress')
        port = self.beacon.GetConfigData('groupPort')
        self.SetLabel("Multicast Connectivity (Beacon Address: %s/%s)"%(address, port))
        num = 10
        self.grid.CreateGrid(num,num)
        
        self.grid.DisableDragRowSize()
        self.grid.DisableDragColSize()
        
        for i in range(num):
            self.grid.SetColLabelValue(i,"")
            self.grid.SetRowLabelValue(i,"")

        EVT_IDLE(self,self.OnIdle)
        self.Show(True)
        self.Layout()
        
    def OnIdle(self, event):
        YELLOW = wxColour(255,255,0)
        GRAY = wxColour(220,220,220)
       
        # Get snapshot of sources
        sources = copy.copy(self.beacon.GetSources()) 
       
        colNr = 0
        
        # for each ssrc
        for s in sources:
            
            # set row and column headings
            rowhead = self.beacon.GetSdes(s)
          
            if not rowhead:
                rowhead = str(s)
             
            self.grid.SetRowLabelValue(colNr, rowhead)
            self.grid.SetColLabelValue(colNr, rowhead)

            rowNr = 0

            # set cell values
            for o in sources:
                rr = self.beacon.GetReport(s, o)
                                
                if rr:
                    loss = rr.fract_lost
                    self.grid.SetCellValue(rowNr,colNr,'%d%%' % (loss))

                    # set black colour between same sender
                    if s == o:
                        self.grid.SetCellBackgroundColour(colNr, colNr, wxBLACK) 
                    elif loss < 10:
                        self.grid.SetCellBackgroundColour(rowNr,colNr,wxGREEN)
                    elif loss < 30:
                        self.grid.SetCellBackgroundColour(rowNr,colNr,YELLOW)
                    else:
                        self.grid.SetCellBackgroundColour(rowNr,colNr,wxRED)

                else:
                    if s == o:
                        self.grid.SetCellBackgroundColour(colNr, colNr, wxBLACK)
                                            
                rowNr = rowNr + 1

            colNr = colNr + 1

        self.Refresh()
