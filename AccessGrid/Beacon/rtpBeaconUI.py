#!/usr/bin/python2
#----------------------------------------------------------------------------
# Name:        rtpBeaconUI.py
# Purpose:     User interface for the beacon 
#
# Author:      Thomas Uram, Susanne Lefvert
#
# Created:     2002/12/12
# RCS-ID:      $Id: rtpBeaconUI.py,v 1.2 2005-06-28 15:29:57 lefvert Exp $
# Copyright:   (c) 2003
# Licence:     See COPYING.TXT
#----------------------------------------------------------------------------

__revision__ = "$Id: rtpBeaconUI.py,v 1.2 2005-06-28 15:29:57 lefvert Exp $"

from wxPython.wx import *
from wxPython.grid import *
from wxPython.lib.mixins.grid import wxGridAutoEditMixin

from AccessGrid import icons

import copy
import threading
import time


class BeaconFrame(wxFrame):
    def __init__(self, parent, log, beacon):
        wxFrame.__init__(self, parent, -1, "RTP Beacon View", size=(820,250))
        self.SetIcon(icons.getAGIconIcon())
        self.running = 1
        self.updateThread = None
        self.beacon = beacon
        self.grid = wxGrid(self,-1)
               
        if not self.beacon:
            messageDialog = wxMessageDialog(self, "You have to be connected to a venue to see multicast connectivity to other participants.",
                                            "Not Connected",
                                            style = wxOK|wxICON_INFORMATION)
            messageDialog.ShowModal()
            messageDialog.Destroy()

            self.OnExit(None)
            return
            
        address = self.beacon.GetConfigData('groupAddress')
        port = self.beacon.GetConfigData('groupPort')
        self.SetLabel("Multicast Connectivity (Beacon Address: %s/%s)"%(address, port))
        num = 9
        self.grid.CreateGrid(num,num)
        self.grid.EnableScrolling(1,1)
        
        self.grid.DisableDragRowSize()
        self.grid.DisableDragColSize()
        
        for i in range(num):
            self.grid.SetColLabelValue(i,"")
            self.grid.SetRowLabelValue(i,"")

        EVT_CLOSE(self, self.OnExit)
       
        self.__Layout()
        self.Show(True)

        self.updateThread = threading.Thread(target=self.ChangeValuesThread)
        self.updateThread.setDaemon(1)
        self.updateThread.start()

    def __Layout(self):
        '''
        Do ui layout.
        '''
        sizer = wxBoxSizer(wxHORIZONTAL)
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
            YELLOW = wxColour(255,255,0)
            GRAY = wxColour(220,220,220)
       
            # Get snapshot of sources
            sources = copy.copy(self.beacon.GetSources()) 
            colNr = 0
        
            # for each ssrc
            for s in sources:
            
                # set column heading
                colhead = self.beacon.GetSdes(s)
                
                if not colhead:
                    colhead = str(s)

                if colNr >= self.grid.GetNumberCols():
                    self.grid.AppendCols(1)
                    self.grid.SetColLabelValue(colNr, colhead)

                elif self.grid.GetColLabelValue(colNr) != colhead:
                    self.grid.SetColLabelValue(colNr, colhead)
                
                rowNr = 0

                # set cell values
                for o in sources:

                    row = s
                    col = o

                    # set row heading
                    rowhead = self.beacon.GetSdes(o)
                    if not rowhead:
                        rowhead = str(o)

                    if rowNr >= self.grid.GetNumberRows():
                        self.grid.AppendRows(1)
                        self.grid.SetRowLabelValue(rowNr, rowhead)
                    elif self.grid.GetRowLabelValue(rowNr) != rowhead:
                        self.grid.SetRowLabelValue(rowNr, rowhead)

                    if self.beacon.GetSdes(s):
                        row = self.beacon.GetSdes(s)
                    if self.beacon.GetSdes(o):
                        col = self.beacon.GetSdes(o)

                    # get receiver report and add value to grid
                    rr = self.beacon.GetReport(s, o)
                                
                    if rr:
                        loss = rr.fract_lost
                        self.grid.SetCellValue(rowNr,colNr,'%d%%' % (loss))

                        # set black colour for same sender
                        if s == o:
                            self.grid.SetCellBackgroundColour(rowNr, colNr, wxBLACK) 
                        elif loss < 10:
                            self.grid.SetCellBackgroundColour(rowNr,colNr,wxGREEN)
                        elif loss < 30:
                            self.grid.SetCellBackgroundColour(rowNr,colNr,YELLOW)
                        else:
                            self.grid.SetCellBackgroundColour(rowNr,colNr,wxRED)
                    else:
                        if s == o:
                            # set black colour for same sender
                            self.grid.SetCellBackgroundColour(rowNr, colNr, wxBLACK)
                                            
                    rowNr = rowNr + 1
                colNr = colNr + 1
            self.Refresh()
