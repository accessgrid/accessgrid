#-----------------------------------------------------------------------------
# Name:        MacPPTView.py
# Purpose:     This is part of the Shared Presentation Software. 
#
# Author:      Wenjun Wu
#
# Created:     2007/01
# Copyright:   (c) 2003
# Licence:     See COPYING.TXT
#-----------------------------------------------------------------------------    

from appscript import *
import mactypes

class MacPPTViewer:
    """
    The Mac PowerPoint Viewer is meant to be a single instance of a Presentation
    viewer. It only works on Mac.
    Appscript (http://appscript.sourceforge.net/), an open source Apple event bridge, needs
    to be installed on your MacOSX.
    Here's a description of what we're keeping track of and why:

    self.ppt -- Appscript Interface to an instance of the PowerPoint Application
    self.presentation -- The current presentation.
    self.win -- The window showing a slideshow of the current presentation.
    """

    def __init__(self, log):
        """
        We aren't doing anything in here because we really don't need
        anything yet. Once things get started up externally, this gets fired
        up through the other methods.
        """
        self.ppt = None
        self.presentation = None
        self.win = None

        self.pptAlreadyOpen = 0
        # The filename of the currently open file.
        self.openFile = ""
        self.lastSlide = None
        self.log = log
    
    def Start(self):
        """
        This method actually fires up PowerPoint and if specified opens a
        file and starts viewing it.
        """
        # Instantiate the powerpoint application via appscript
        self.ppt = app('Microsoft PowerPoint')
        self.ppt.start_up_dialog.set(False)
        if len(self.ppt.presentations.get()) > 0:
            self.pptAlreadyOpen = 1

        # Make it active (visible)
        self.ppt.activate()

    def Stop(self):
        """
        This method shuts the powerpoint application down.
        """
        # Turn the slide show off
        self.EndShow()
        
        
    def Quit(self):
        """
        This method quits the powerpoint application.
        """
        # Close the presentation
        try:
            if self.presentation:
                self.ppt.close(self.presentation)
        except:
            print 'can not close presentation....continue anyway'
            self.log.exception('can not close presentation....continue anyway')
                
        # Exit the powerpoint application, but only if 
        # it was opened by the viewer
        if not self.pptAlreadyOpen:
            self.ppt.quit(k.no)
        
    def LoadPresentation(self, file):
        """
        This method opens a file and starts the viewing of it.
        """

        print '---------- load presentation'
        # Close existing presentation
        try:
            if self.presentation:
                self.ppt.close(self.presentation)
        except:
            print 'can not close previous presentation...continue anyway'
            self.log.exception('can not close presentation....continue anyway')
        # Open a new presentation and keep a reference to it in self.presentation
        
        file.replace("%20", " ")
        self.ppt.open(mactypes.Alias(file))
        self.presentation = self.ppt.active_presentation
        self.lastSlide = len(self.presentation.slides.get())
        print '================== set open file to ', file
        self.openFile = file
        
        # Start viewing the slides in a window
        self.presentation.slide_show_settings.show_type.set(k.slide_show_type_window)
        self.ppt.run_slide_show(self.presentation.slide_show_settings)
        self.win = self.ppt.slide_show_windows[1]
        
       
    def Next(self):
        """
        This method moves to the next slide.
        """
        # Move to the next slide
        self.ppt.go_to_next_slide(self.win.slideshow_view)

    def Previous(self):
        """
        This method moves to the previous slide.
        """
        # Move to the previous slide
        self.ppt.go_to_previous_slide(self.win.slideshow_view)

    def GoToSlide(self, slide):
        """
        This method moves to the specified slide.
        """
        # Move to the specified Slide
        # self.ppt.go_to_slide(self.win.slideshow_view, number=int(slide))
        self.ppt.go_to_slide(self.ppt.document_windows[1].view, number=int(slide))
        # a ugly  way to do goto slide in the slide show  because microsoft applescript interface doesn't offer go-to-slide command for the slide show 
        curPos = self.win.slideshow_view.current_show_position.get()
        wantPos = int(slide)
        if wantPos == 1:
           self.ppt.go_to_first_slide(self.win.slideshow_view)
        elif wantPos == self.GetLastSlide():
           self.ppt.go_to_last_slide(self.win.slideshow_view)
        else: # neither the first slide nor the last slide, go here
         step = curPos - wantPos
         while curPos != wantPos:
           if step < 0:
             self.Next()
           else:
             self.Previous()
           curPos = self.win.slideshow_view.current_show_position.get()

    def EndShow(self):
        """
        This method quits the viewing of the current set of slides.
        """
        # Quit the presentation
      
        if self.win:
            self.ppt.exit_slide_show(self.ppt.slide_show_windows[1].slideshow_view)
            self.win = None

    def GetLastSlide(self):
        """
        This method returns the index of the last slide (indexed from 1)
        """
        if self.lastSlide is None:
          self.presentation = self.ppt.active_presentation
          self.lastSlide = len(self.presentation.slides.get())
        return self.lastSlide

    def GetSlideNum(self):
        """
        This method returns the index of the current slide
        """
        curPos = self.win.slideshow_view.current_show_position.get()
        return curPos

    def GetStepNum(self):
        """
        This method returns the step of the current slide
        """
        curPos = self.win.slideshow_view.current_show_position.get()
        slide = self.presentation.slides[curPos]
        stepNum = slide.print_steps.get()
        return stepNum
