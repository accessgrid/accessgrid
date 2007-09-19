#!/usr/bin/python
#----------------------------------------------------------------------------
# Name:        rtpBeaconUI.py
# Purpose:     User interface for the beacon 
#
# Author:      Thomas Uram, Susanne Lefvert
#
# Created:     2002/12/12
# RCS-ID:      $Id: rtpBeaconUI.py,v 1.15 2007-09-19 16:51:22 turam Exp $
# Copyright:   (c) 2003
# Licence:     See COPYING.TXT
#----------------------------------------------------------------------------

__revision__ = "$Id: rtpBeaconUI.py,v 1.15 2007-09-19 16:51:22 turam Exp $"

import wx
import wx.grid

from AccessGrid import icons

import copy
import threading
import time


class BeaconFrame(wx.Frame):
    def __init__(self, parent, log, beacon, **args):
        wx.Frame.__init__(self, parent, -1, "RTP Beacon View", size=(400,300), **args)
        self.log = log
        self.beacon = beacon
        
        self.SetIcon(icons.getAGIconIcon())
        self.running = 1
        self.updateThread = None

        self.panel = wx.Panel(self, -1)
        
        # Build up the user interface
        self.SetLabel("Multicast Connectivity")

        # - sizer for pulldowns
        self.topsizer = wx.BoxSizer(wx.HORIZONTAL)
        
        # - pulldown for group to monitor (currently only beacon group, later audio/video)
        choices = ['Beacon']
        self.groupBox = wx.Choice(self.panel,-1,choices = choices)
        self.groupBox.SetSelection(0)
        
        # - pulldown for data to display (currently only fract.loss, later delay/jitter/cum.loss)
        choices = ['Fractional Loss']
        self.dataTypeBox = wx.Choice(self.panel,-1,choices = choices)
        self.dataTypeBox.SetSelection(0)

        self.label = wx.StaticText(self.panel, -1, "")
        
        self.topsizer.Add(self.groupBox,0, wx.ALL, 2)
        self.topsizer.Add(self.dataTypeBox,0, wx.ALL, 2)
        self.topsizer.Add(self.label,1, wx.EXPAND|wx.ALL, 2)
        
        # Create the beacon grid
        self.grid = wx.grid.Grid(self.panel,-1)
        self.grid.SetToolTip(wx.ToolTip("test"))
        self.grid.EnableEditing(False)
        self.grid.SetColLabelSize(0)
        self.grid.SetRowLabelAlignment(wx.LEFT,wx.BOTTOM)
        self.grid.DisableDragRowSize()
        self.grid.DisableDragColSize()
        self.grid.SetRowLabelSize(150)
        self.grid.SetDefaultColSize(40)
        self.grid.EnableScrolling(1,1)
        self.grid.CreateGrid(1,1)
        
        # Register event handlers
        wx.EVT_CLOSE(self, self.OnExit)
        wx.grid.EVT_GRID_CELL_LEFT_CLICK(self.grid, self.OnLeftClick) 
        
        # Layout
        self.__Layout()

        # Start update thread
        self.updateThread = threading.Thread(target=self.ChangeValuesThread)
        self.updateThread.start()

    def OnIdle(self, event):
        self.beacon.Update()

    def __Layout(self):
        '''
        Do ui layout.
        '''
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.topsizer,0, wx.EXPAND)
        sizer.Add(self.grid, 1, wx.EXPAND|wx.ALL, 2)

        self.panel.SetSizer(sizer)
        self.panel.SetAutoLayout(1)

    def OnExit(self, event):
        '''
        Invoked when window is closed.
        '''
        self.Hide()
        self.running = 0
        if self.updateThread:
            self.updateThread.join()
        self.Destroy()

    def OnLeftClick(self, event):
        row = event.GetRow()
        col = event.GetCol()
        sender = self.sources[col]
        receiver = self.sources[row]
        self.label.SetLabel("From "+str(self.beacon.GetSdes(sender))+" to "+str(self.beacon.GetSdes(receiver)))
        
    def ChangeValuesThread(self):
        '''
        Update UI based on beacon data.
        '''
        while self.running:
          try:
            YELLOW = wx.Colour(255,255,0)
            GRAY = wx.Colour(220,220,220)
       
            # Get snapshot of sources
            self.sources = copy.copy(self.beacon.GetSources()) 
            
            # Resize grid as needed
            numRows = self.grid.GetNumberRows()
            if numRows > len(self.sources) and numRows > 1:
                wx.CallAfter(self.grid.DeleteCols,numRows - len(self.sources))
                wx.CallAfter(self.grid.DeleteRows,numRows - len(self.sources))
            elif numRows < len(self.sources):
                wx.CallAfter(self.grid.AppendCols,len(self.sources) - numRows )
                wx.CallAfter(self.grid.AppendRows,len(self.sources) - numRows )
            
            # Sort the list of sources
            self.sources.sort()
            
            # Update the beacon grid
            rowNr = 0
            for s in self.sources:

                sdes = self.beacon.GetSdes(s)
                if sdes:
                    wx.CallAfter(self.grid.SetRowLabelValue,rowNr,str(sdes))
                else:
                    wx.CallAfter(self.grid.SetRowLabelValue,rowNr,str(s))

                # set cell values
                for o in self.sources:

                    # set black colour for same sender
                    if s == o:
                        wx.CallAfter(self.grid.SetCellBackgroundColour, rowNr, rowNr, wx.BLACK) 
                        continue

                    colNr = self.sources.index(o)

                    # get receiver report and add value to grid
                    rr = self.beacon.GetReport(o,s)

                    if rr:

                        # 1/4 packets lost, the loss fraction would be 1/4*256 = 64 
                        loss = (rr.fract_lost / 256.0) * 100.0

                        wx.CallAfter(self.grid.SetCellValue, rowNr,colNr,'%d%%' % (loss))
                        if loss < 10:
                            wx.CallAfter(self.grid.SetCellBackgroundColour,rowNr,colNr,wx.GREEN)
                        elif loss < 30:
                            wx.CallAfter(self.grid.SetCellBackgroundColour, rowNr,colNr,YELLOW)
                        else:
                            wx.CallAfter(self.grid.SetCellBackgroundColour, rowNr,colNr,wx.RED)
                    else:
                        wx.CallAfter(self.grid.SetCellBackgroundColour, rowNr,colNr,GRAY)
                rowNr += 1

            wx.CallAfter(self.Refresh)
          except Exception,e:
            self.log.exception('Exception updating beacon ui')
          time.sleep(2)
