#-----------------------------------------------------------------------------
# Name:        ImpressViewer.py
# Purpose:     This is part of the Shared Presentation Software. 
#
# Author:      Eric C. Olson
#
# Created:     2003/10
# Copyright:   (c) 2003
# Licence:     See COPYING.TXT
#-----------------------------------------------------------------------------    
import sys, os
import time
# bootstrap uno component context       
import uno
import unohelper

# a UNO struct later needed to create a document
from com.sun.star.text.ControlCharacter import PARAGRAPH_BREAK
from com.sun.star.text.TextContentAnchorType import AS_CHARACTER
from com.sun.star.awt import Size
from com.sun.star.beans import PropertyValue
from com.sun.star.util import URL

from AccessGrid import Platform

# local file to help find the OpenOffice directory
import GetPaths


#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#
# Viewer code
#
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

class ImpressViewer:
    """
    Here's a description of what we're keeping track of and why:

    seld.desktop -- Open Office desktop.  Files are loaded from here.
    self.doc -- the current presentation document.
    self.controller -- the current presentation controller.
    """
    def __init__(self):
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

        self.doc = None

    def Start(self):
        """
        This method actually fires up PowerPoint and if specified opens a
        file and starts viewing it.
        """
        localContext = uno.getComponentContext()
        resolver = localContext.ServiceManager.createInstanceWithContext(
            "com.sun.star.bridge.UnoUrlResolver", localContext )
        try:
            smgr = resolver.resolve( "uno:socket,host=localhost,port=2002;urp;StarOffice.ServiceManager" )
        except:
            print "Starting listening OpenOffice"

            if os.path.exists( os.path.join(GetPaths.GetOOHomeDir(), "soffice") ):
                # The single user installation provides binary "soffice".
                oo_bin = os.path.join(GetPaths.GetOOHomeDir(), "soffice")
            else:
                # The system wide installation provides binary "ooffice".
                #   (redhat/fedora tested, please notify us if other distributions vary)
                oo_bin = "ooffice"
            os.system( oo_bin + " \"-accept=socket,host=localhost,port=2002;urp;\" &")
            start = time.time()
            timeout = 40
            failed = 1
            print "Trying to connect",
            while time.time() - start < timeout and failed == 1:
                time.sleep(3)
                print ".",
                try:
                    failed = 0
                    smgr = resolver.resolve( "uno:socket,host=localhost,port=2002;urp;StarOffice.ServiceManager" )
                except:
                    failed = 1
            if failed:
                print "Could not start openoffice"
                sys.exit(2)
            else:
                print "Connected."
 
        remoteContext = smgr.getPropertyValue( "DefaultContext" )
        self.desktop = smgr.createInstanceWithContext( "com.sun.star.frame.Desktop",remoteContext)

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
        if self.doc:
            self.doc.close(1)

    def LoadPresentation(self, file):
        """
        This method opens a file and starts the viewing of it.
        """
        print "LoadPresentation:", file

        # Close existing presentation
        if self.doc:
            self.doc.close(1)

        if not file:
            print "Blank presentation"
            self.doc = self.desktop.loadComponentFromURL("private:factory/simpress","_blank", 0, ()  )
        if str.startswith(file, "http"):
            print "loading from http"
            self.doc = self.desktop.loadComponentFromURL(file,"_blank", 0, ()  )
        else: 
            self.doc = self.desktop.loadComponentFromURL("File:" + file,"_blank", 0, ()  )

        if not self.doc:
            self.doc = self.desktop.loadComponentFromURL("private:factory/simpress","_blank", 0, ()  )

        self.controller = self.doc.getCurrentController()
        self.numPages = self.doc.getDrawPages().getCount()
        self.openFile = file

        # Start viewing the slides in a window
        #self.presentation.SlideShowSettings.ShowType = win32com.client.constants.ppShowTypeWindow
        #self.win = self.presentation.SlideShowSettings.Run()

    def Next(self):
        """
        This method moves to the next slide.
        """
        # Move to the next slide
        current_page = self.controller.getCurrentPage()
        current_page_number = current_page.getPropertyValue("Number")
        print "next:", current_page_number, self.numPages
        if current_page_number + 1 <= self.numPages:
            pages = self.doc.getDrawPages()
            # getByIndex is zero based, so adding one and subtracting one = add 0
            new_page_index = current_page_number
            self.controller.setCurrentPage(pages.getByIndex(new_page_index))

    def Previous(self):
        """
        This method moves to the previous slide.
        """
        # Move to the previous slide
        current_page = self.controller.getCurrentPage()
        current_page_number = current_page.getPropertyValue("Number")
        if current_page_number - 1 >= 1:
            pages = self.doc.getDrawPages()
            new_page_number = current_page_number - 1
            # getByIndex is zero based, so subtract another 1
            new_page_index = new_page_number - 1
            self.controller.setCurrentPage(pages.getByIndex(new_page_index))

    def GoToSlide(self, slide):
        """
        This method moves to the specified slide.
        """
        # Move to the specified Slide
        if int(slide) >= 1 and int(slide) <= self.numPages:
            pages = self.doc.getDrawPages()
            # getByIndex is zero based, so subtract another 1
            goto_page_number = int(slide) - 1
            self.controller.setCurrentPage(pages.getByIndex(goto_page_number))

    def EndShow(self):
        """
        This method quits the viewing of the current set of slides.
        """
        # Quit the presentation
        if self.doc:
            self.doc.close(1)

    def GetLastSlide(self):
        """
        This method returns the index of the last slide (indexed from 1)
        """
        return self.numPages
        #if self.numPages > 0:
            #return self.numPages - 1
        #else:
            #return 0

    def GetSlideNum(self):
        """
        This method returns the index of the current slide
        """
        current_page = self.controller.getCurrentPage()
        return int(current_page.getPropertyValue("Number"))

    def GetStepNum(self):
        """
        This method returns the step of the current slide
        """
        print "Warning: GetStepNum not implemented yet."
        return 1

