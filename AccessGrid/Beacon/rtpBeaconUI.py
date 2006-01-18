#!/usr/bin/python2
#----------------------------------------------------------------------------
# Name:        rtpBeaconUI.py
# Purpose:     User interface for the beacon 
#
# Author:      Thomas Uram, Susanne Lefvert
#
# Created:     2002/12/12
# RCS-ID:      $Id: rtpBeaconUI.py,v 1.6 2006-01-18 22:50:33 turam Exp $
# Copyright:   (c) 2003
# Licence:     See COPYING.TXT
#----------------------------------------------------------------------------

__revision__ = "$Id: rtpBeaconUI.py,v 1.6 2006-01-18 22:50:33 turam Exp $"

from wxPython.wx import *
from wxPython.grid import *
from wxPython.lib.mixins.grid import wxGridAutoEditMixin

from AccessGrid import icons

import copy
import threading
import time


class BeaconFrame(wxFrame):
    def __init__(self, parent, log, beacon):
        wxFrame.__init__(self, parent, -1, "RTP Beacon View", size=(400,300))
        self.log = log
        self.beacon = beacon
        
        self.SetIcon(icons.getAGIconIcon())
        self.running = 1
        self.updateThread = None
        
        
        # Build up the user interface
        self.SetLabel("Multicast Connectivity")

        # - sizer for pulldowns
        self.topsizer = wxBoxSizer(wxHORIZONTAL)
        
        # - pulldown for group to monitor (currently only beacon group, later audio/video)
        choices = ['Beacon']
        self.groupBox = wxChoice(self,-1,choices = choices)
        self.groupBox.SetSelection(0)
        
        # - pulldown for data to display (currently only fract.loss, later delay/jitter/cum.loss)
        choices = ['Fractional Loss']
        self.dataTypeBox = wxChoice(self,-1,choices = choices)
        self.dataTypeBox.SetSelection(0)
        
        self.topsizer.Add(self.groupBox,0)
        self.topsizer.Add(self.dataTypeBox,0)
        
        # Create the beacon grid
        self.grid = wxGrid(self,-1)
        self.grid.EnableEditing(false)
        self.grid.SetColLabelSize(0)
        self.grid.SetRowLabelAlignment(wxLEFT,wxBOTTOM)
        self.grid.DisableDragRowSize()
        self.grid.DisableDragColSize()
        self.grid.SetRowLabelSize(150)
        self.grid.SetDefaultColSize(40)
        self.grid.EnableScrolling(1,1)
        self.grid.CreateGrid(1,1)
        
        # Register event handlers
        EVT_CLOSE(self, self.OnExit)
       
        # Layout
        self.__Layout()
        self.Show(True)

        # Start update thread
        self.updateThread = threading.Thread(target=self.ChangeValuesThread)
        self.updateThread.start()

    def OnIdle(self, event):
        self.beacon.Update()

    def __Layout(self):
        '''
        Do ui layout.
        '''
        sizer = wxBoxSizer(wxVERTICAL)
        sizer.Add(self.topsizer,0, wxEXPAND)
        sizer.Add(self.grid, 1, wxEXPAND)

        self.SetSizer(sizer)
        self.SetAutoLayout(1)

    def OnExit(self, event):
        '''
        Invoked when window is closed.
        '''
        self.Hide()
        self.running = 0
        if self.updateThread:
            self.updateThread.join()
        self.Destroy()

    def ChangeValuesThread(self):
        '''
        Update UI based on beacon data.
        '''
        while self.running:
          try:
            YELLOW = wxColour(255,255,0)
            GRAY = wxColour(220,220,220)
       
            # Get snapshot of sources
            sources = copy.copy(self.beacon.GetSources()) 
            
            # Resize grid as needed
            numRows = self.grid.GetNumberRows()
            if numRows > len(sources):
                self.grid.DeleteCols(numRows - len(sources))
                self.grid.DeleteRows(numRows - len(sources))
            elif numRows < len(sources):
                self.grid.AppendCols(len(sources) - numRows )
                self.grid.AppendRows(len(sources) - numRows )
            

            # Sort the list of sources
            sources.sort()
            
            # Update the beacon grid
            rowNr = 0
            for s in sources:

                sdes = self.beacon.GetSdes(s)
                if sdes:
                    self.grid.SetRowLabelValue(rowNr,str(sdes))
                else:
                    self.grid.SetRowLabelValue(rowNr,str(s))

                # set cell values
                for o in sources:

                    # set black colour for same sender
                    if s == o:
                        wxCallAfter(self.grid.SetCellBackgroundColour, rowNr, rowNr, wxBLACK) 
                        continue

                    colNr = sources.index(o)

                    # get receiver report and add value to grid
                    rr = self.beacon.GetReport(o,s)

                    if rr:

                        # 1/4 packets lost, the loss fraction would be 1/4*256 = 64 
                        loss = (rr.fract_lost / 256.0) * 100.0

                        wxCallAfter(self.grid.SetCellValue, rowNr,colNr,'%d%%' % (loss))
                        if loss < 10:
                            wxCallAfter(self.grid.SetCellBackgroundColour,rowNr,colNr,wxGREEN)
                        elif loss < 30:
                            wxCallAfter(self.grid.SetCellBackgroundColour, rowNr,colNr,YELLOW)
                        else:
                            wxCallAfter(self.grid.SetCellBackgroundColour, rowNr,colNr,wxRED)
                    else:
                        wxCallAfter(self.grid.SetCellBackgroundColour, rowNr,colNr,GRAY)
                rowNr += 1

            wxCallAfter(self.Refresh)
            time.sleep(2)
          except Exception,e:
            self.log.exception('Exception updating beacon ui')
