#!/usr/bin/python

import os
import sys

from AccessGrid.Platform import IsOSX, IsWindows
from AccessGrid.Platform.ProcessManager import ProcessManager
from AccessGrid.Toolkit import WXGUIApplication
from wxPython.wx import *
import webbrowser

class LauncherFrame(wxFrame):
    BUTTON_MAIN_ID = 1000   # Main binaries
    BUTTON_VC_ID = 1001       # Venue Client
    BUTTON_DOCS_ID = 2000   # Documentation
    BUTTON_README_ID = 2001   # ReadMe
    BUTTON_VCM_ID = 2002      # Venue Client Manual
    BUTTON_VMCM_ID = 2003     # Venue Management Client Manual
    BUTTON_LIC_ID = 2004      # License
    BUTTON_CONFIG_ID = 3000 # Configuration
    BUTTON_NM_ID = 3001       # Node Management
    BUTTON_VM_ID = 3002       # Venue Management
    BUTTON_NSW_ID = 3003      # Node Setup Wizard
    BUTTON_CM_ID = 3004       # Certificate Management
    #BUTTON_CRW_ID = 3004	  # Certificate Request Wizard
    BUTTON_SERVICE_ID = 4000 # Configuration
    BUTTON_NS_ID = 4001       # Node Service
    BUTTON_SM_ID = 4002       # Service Manager
    BUTTON_VS_ID = 4003       # Venue Server
    BUTTON_DEBUG_ID = 5000  # Debug form of main binaries
    BUTTON_VCD_ID = 5001      # Venue Client Debug
    BUTTON_CMD_ID = 5002       # Certificate Management
    BUTTON_NSD_ID = 5003	  # Node Service Debug
    BUTTON_SMD_ID = 5004      # Service Manager Debug
    BUTTON_VSD_ID = 5005      # Venue Server Debug
	
    def __init__(self, parent=None, id=-1, title="Access Grid Launcher",agtk_location=None):
        wxFrame.__init__(self,parent,id,title,size=wxSize(400,125),style=wxDEFAULT_FRAME_STYLE&(~wxMAXIMIZE_BOX))

	self.processManager=ProcessManager();
	self.browser=None;
        
        if IsOSX():
            self.mainButton=wxRadioButton(self,self.BUTTON_MAIN_ID,"Main",style=wxRB_GROUP);
            EVT_RADIOBUTTON(self,self.BUTTON_MAIN_ID,self.OnToggle);
        else:
            self.mainButton=wxToggleButton(self,self.BUTTON_MAIN_ID,"Main");
            EVT_TOGGLEBUTTON(self,self.BUTTON_MAIN_ID,self.OnToggle);
        self.mainButton.SetValue(true);

        if IsOSX():
            self.docButton=wxRadioButton(self,self.BUTTON_DOCS_ID,"Documentation");
            EVT_RADIOBUTTON(self,self.BUTTON_DOCS_ID,self.OnToggle);
        else:
            self.docButton=wxToggleButton(self,self.BUTTON_DOCS_ID,"Documentation");
            EVT_TOGGLEBUTTON(self,self.BUTTON_DOCS_ID,self.OnToggle);
        self.docButton.SetValue(false);
        
        if IsOSX():
            self.confButton=wxRadioButton(self,self.BUTTON_CONFIG_ID,"Configuration");
            EVT_RADIOBUTTON(self,self.BUTTON_CONFIG_ID,self.OnToggle);
        else:
            self.confButton=wxToggleButton(self,self.BUTTON_CONFIG_ID,"Configuration");
            EVT_TOGGLEBUTTON(self,self.BUTTON_CONFIG_ID,self.OnToggle);
        self.confButton.SetValue(false);

        if IsOSX():
            self.servButton=wxRadioButton(self,self.BUTTON_SERVICE_ID,"Services");
            EVT_RADIOBUTTON(self,self.BUTTON_SERVICE_ID,self.OnToggle);
        else:
            self.servButton=wxToggleButton(self,self.BUTTON_CONFIG_ID,"Services");
            EVT_TOGGLEBUTTON(self,self.BUTTON_SERVICE_ID,self.OnToggle);
        self.servButton.SetValue(false);
        
        
        if IsOSX():
            self.debugButton=wxRadioButton(self,self.BUTTON_DEBUG_ID,"Debug");
            EVT_RADIOBUTTON(self,self.BUTTON_DEBUG_ID,self.OnToggle);
        else:
            self.debugButton=wxToggleButton(self,self.BUTTON_DEBUG_ID,"Debug");
            EVT_TOGGLEBUTTON(self,self.BUTTON_DEBUG_ID,self.OnToggle);
        self.debugButton.SetValue(false)
	self.debugButton.Disable()
	self.debugButton.Show(false)
        
        if not agtk_location:
            agtk_location=".."
            
        self.mainButtonList=[];
        self.mainButtonActions=[];
        self.mainButtonList.append(wxButton(self,self.BUTTON_VC_ID,"Venue Client"));
        self.mainButtonActions.append([self.RunPython,"%s/bin/VenueClient.py"%(agtk_location),[]]);
        for button in self.mainButtonList:
            button.Show(false);
        
        self.docsButtonList=[];
        self.docsButtonActions=[];
        self.docsButtonList.append(wxButton(self,self.BUTTON_README_ID,"Read Me"));
        self.docsButtonActions.append([self.LoadURL,"file://%s/doc/README"%(agtk_location),[]]);
        self.docsButtonList.append(wxButton(self,self.BUTTON_VCM_ID,"Venue Client Manual"));
        self.docsButtonActions.append([self.LoadURL,"http://www.mcs.anl.gov/fl/research/accessgrid/documentation/manuals/VenueClient/3_0",[]]);
        self.docsButtonList.append(wxButton(self,self.BUTTON_VMCM_ID,"Venue Management Manual"));
        self.docsButtonActions.append([self.LoadURL,"http://www.mcs.anl.gov/fl/research/accessgrid/documentation/manuals/VenueManagement/3_0",[]]);
        self.docsButtonList.append(wxButton(self,self.BUTTON_LIC_ID,"License"));
        self.docsButtonActions.append([self.LoadURL,"file://%s/COPYING.txt"%(agtk_location),[]]);
        for button in self.docsButtonList:
            button.Show(false);
        
        self.configButtonList=[];
        self.configButtonActions=[];
        self.configButtonList.append(wxButton(self,self.BUTTON_NM_ID,"Node Management"));
        self.configButtonActions.append([self.RunPython,"%s/bin/NodeManagement.py"%(agtk_location),[]]);
        self.configButtonList.append(wxButton(self,self.BUTTON_VM_ID,"Venue Management"));
        self.configButtonActions.append([self.RunPython,"%s/bin/VenueManagement.py"%(agtk_location),[]]);
        self.configButtonList.append(wxButton(self,self.BUTTON_NSW_ID,"Node Setup Wizard"));
        self.configButtonActions.append([self.RunPython,"%s/bin/NodeSetupWizard.py"%(agtk_location),[]]);
        #self.configButtonList.append(wxButton(self,self.BUTTON_CRW_ID,"Certificate Request Wizard"));
        #self.configButtonActions.append([self.RunPython,"%s/bin/CertificateRequestTool.py"%(agtk_location),[]]);
        self.configButtonList.append(wxButton(self,self.BUTTON_CM_ID,"Certificate Management"));
        self.configButtonActions.append([self.RunPython,"%s/bin/CertificateManager.py"%(agtk_location),[]]);
        for button in self.configButtonList:
            button.Show(false);

        self.serviceButtonList=[];
        self.serviceButtonActions=[];
        self.serviceButtonList.append(wxButton(self,self.BUTTON_NS_ID,"Node Service"));
        if IsOSX():
            self.serviceButtonActions.append([self.RunCommandline,"/Applications/Utilities/Terminal.app/Contents/MacOS/Terminal", ["-ps", "-e", "/Applications/AccessGridToolkit3.app/Contents/MacOS/runns.sh"]]);
        else:
            self.serviceButtonActions.append([self.RunPython,"%s/bin/AGServiceManager.py"%(agtk_location),["-n"]]);
        self.serviceButtonList.append(wxButton(self,self.BUTTON_SM_ID,"Service Manager"));
        if IsOSX():
            self.serviceButtonActions.append([self.RunCommandline,"/Applications/Utilities/Terminal.app/Contents/MacOS/Terminal", ["-ps", "-e", "/Applications/AccessGridToolkit3.app/Contents/MacOS/runsm.sh"]]);
        else:
            self.serviceButtonActions.append([self.RunPython,"%s/bin/AGServiceManager.py"%(agtk_location),[]]);
        self.serviceButtonList.append(wxButton(self,self.BUTTON_VS_ID,"Venue Server"));
        if IsOSX():
            self.serviceButtonActions.append([self.RunCommandline,"/Applications/Utilities/Terminal.app/Contents/MacOS/Terminal", ["-ps", "-e", "/Applications/AccessGridToolkit3.app/Contents/MacOS/runvs.sh"]]);
        else:
            self.serviceButtonActions.append([self.RunPython,"%s/bin/VenueServer.py"%(agtk_location),[]]);
        for button in self.serviceButtonList:
            button.Show(false);
        
        self.debugButtonList=[];
        self.debugButtonActions=[];
        self.debugButtonList.append(wxButton(self,self.BUTTON_VCD_ID,"Venue Client (Debug)"));
        self.debugButtonActions.append([self.RunPythonDebug,"%s/bin/VenueClient.py"%(agtk_location),["-d"]]);
        self.debugButtonList.append(wxButton(self,self.BUTTON_CMD_ID,"Certificate Management (Debug)"));
        self.debugButtonActions.append([self.RunPythonDebug,"%s/bin/CertificateManager.py"%(agtk_location),["-d"]]);
        self.debugButtonList.append(wxButton(self,self.BUTTON_NSD_ID,"Node Service (Debug)"));
        self.debugButtonActions.append([self.RunPythonDebug,"%s/bin/AGNodeService.py"%(agtk_location),["-d"]]);
        self.debugButtonList.append(wxButton(self,self.BUTTON_SMD_ID,"Service Manager (Debug)"));
        self.debugButtonActions.append([self.RunPythonDebug,"%s/bin/AGServiceManager.py"%(agtk_location),["-d"]]);
        self.debugButtonList.append(wxButton(self,self.BUTTON_VSD_ID,"Venue Server (Debug)"));
        self.debugButtonActions.append([self.RunPythonDebug,"%s/bin/VenueServer.py"%(agtk_location),["-d"]]);
        for button in self.debugButtonList:
            button.Show(false);
        
        EVT_BUTTON(self,self.BUTTON_VC_ID,self.OnButton);
        EVT_BUTTON(self,self.BUTTON_CM_ID,self.OnButton);
        EVT_BUTTON(self,self.BUTTON_NS_ID,self.OnButton);
        EVT_BUTTON(self,self.BUTTON_SM_ID,self.OnButton);
        EVT_BUTTON(self,self.BUTTON_VS_ID,self.OnButton);
        EVT_BUTTON(self,self.BUTTON_README_ID,self.OnButton);
        EVT_BUTTON(self,self.BUTTON_VCM_ID,self.OnButton);
        EVT_BUTTON(self,self.BUTTON_VMCM_ID,self.OnButton);
        EVT_BUTTON(self,self.BUTTON_LIC_ID,self.OnButton);
        EVT_BUTTON(self,self.BUTTON_NM_ID,self.OnButton);
        EVT_BUTTON(self,self.BUTTON_VM_ID,self.OnButton);
        EVT_BUTTON(self,self.BUTTON_NSW_ID,self.OnButton);
        #EVT_BUTTON(self,self.BUTTON_CRW_ID,self.OnButton);
        EVT_BUTTON(self,self.BUTTON_VCD_ID,self.OnButton);
        EVT_BUTTON(self,self.BUTTON_CMD_ID,self.OnButton);
        EVT_BUTTON(self,self.BUTTON_NSD_ID,self.OnButton);
        EVT_BUTTON(self,self.BUTTON_SMD_ID,self.OnButton);
        EVT_BUTTON(self,self.BUTTON_VSD_ID,self.OnButton);
        
        self.myLine=wxStaticLine(self,-1,style=wxLI_VERTICAL);
        
        self.__doLayout();
        
    def OnToggle(self,evt):
        self.mainButton.SetValue(false);
        self.docButton.SetValue(false);
        self.confButton.SetValue(false);
        self.servButton.SetValue(false);
        self.debugButton.SetValue(false);
       
        if evt.GetId() == self.BUTTON_DOCS_ID:
            self.docButton.SetValue(true);
        elif evt.GetId() == self.BUTTON_CONFIG_ID:
            self.confButton.SetValue(true);
        elif evt.GetId() == self.BUTTON_SERVICE_ID:
            self.servButton.SetValue(true);
        elif evt.GetId() == self.BUTTON_DEBUG_ID:
            self.debugButton.SetValue(true);
        else:
            self.mainButton.SetValue(true);
        self.__doLayout();
    
    def OnButton(self,evt):
        # Figure out which button set is active
        if self.mainButton.GetValue():
            buttonBase=self.BUTTON_MAIN_ID;
            actionSet=self.mainButtonActions;
        elif self.docButton.GetValue():
            buttonBase=self.BUTTON_DOCS_ID;
            actionSet=self.docsButtonActions;
        elif self.confButton.GetValue():
            buttonBase=self.BUTTON_CONFIG_ID;
            actionSet=self.configButtonActions;
        elif self.servButton.GetValue():
            buttonBase=self.BUTTON_SERVICE_ID;
            actionSet=self.serviceButtonActions;
        elif self.debugButton.GetValue():
            buttonBase=self.BUTTON_DEBUG_ID;
            actionSet=self.debugButtonActions;
        else:
            return # No active button set?
        
        buttonVal=evt.GetId()-buttonBase
        if (buttonVal < 0) or (buttonVal > len(actionSet)):
            return;  # Our button isn't one of the active ones!

        buttonVal=buttonVal-1; # Adjust to make a proper array index
        actionSet[buttonVal][0](actionSet[buttonVal][1],actionSet[buttonVal][2]); # Call encoded action with encoded argument.

    def RunCommandline(self,cmd,args):
        print "Run: %s"%(cmd);
        print "args: ",
        print args;
        self.processManager.StartProcess(cmd,args);
    
    def RunPython(self,cmd,args):
        if IsOSX() or IsWindows():
            command="pythonw";
        else:
            command="python";
        
        print "Run: %s"%(cmd);
	print "args: ",
	print args;
        self.processManager.StartProcess(command,[cmd]+args);
    
    def RunPythonDebug(self,cmd,args):
        if IsOSX():
	    pass;
            #command="/Applications/Utilities/Terminal.app/Contents/MacOS/Terminal";
        elif IsWindows():
            command="start";
        else:
            command="python";
        
        if IsOSX() or IsWindows():
            command2="pythonw";
        else:
            command2="";

        print "DEBUG: %s"%(cmd);
	print "args: ",
	print args;
        if command2:
            self.processManager.StartProcess(command,[command2,cmd]+args);
        else:
            self.processManager.StartProcess(command,[cmd]+args);
    
    def LoadURL(self,url,args):
        print "URL: %s"%(url);
        needNewWindow = 0
        if not self.browser:
            self.browser = webbrowser.get()
            needNewWindow = 1
        self.browser.open(url, needNewWindow)
    
    def __doLayout(self):
        for button in self.mainButtonList:
            button.Show(false);
        for button in self.docsButtonList:
            button.Show(false);
        for button in self.configButtonList:
            button.Show(false);
        for button in self.serviceButtonList:
            button.Show(false);
        for button in self.debugButtonList:
            button.Show(false);

        # Figure out which button set is active
        if self.mainButton.GetValue():
            buttonSet=self.mainButtonList;
        elif self.docButton.GetValue():
            buttonSet=self.docsButtonList;
        elif self.confButton.GetValue():
            buttonSet=self.configButtonList;
        elif self.servButton.GetValue():
            buttonSet=self.serviceButtonList;
        elif self.debugButton.GetValue():
            buttonSet=self.debugButtonList;
        else:
            buttonSet=[];
        
        menuButtonSizer=wxBoxSizer(wxVERTICAL);
	menuButtonSizer.Add(wxSize(0,0),1);
        menuButtonSizer.Add(self.mainButton,0,wxEXPAND);
	menuButtonSizer.Add(wxSize(0,0),1);
        menuButtonSizer.Add(self.docButton,0,wxEXPAND);
	menuButtonSizer.Add(wxSize(0,0),1);
        menuButtonSizer.Add(self.confButton,0,wxEXPAND);
	menuButtonSizer.Add(wxSize(0,0),1);
        menuButtonSizer.Add(self.servButton,0,wxEXPAND);
	menuButtonSizer.Add(wxSize(0,0),1);
        menuButtonSizer.Add(self.debugButton,0,wxEXPAND);
	menuButtonSizer.Add(wxSize(0,0),1);
        
        submenuButtonSizer=wxBoxSizer(wxVERTICAL);
        submenuButtonSizer.Add(wxSize(0,0),1);
        if len(buttonSet):
            for button in buttonSet:
                button.Show(true);
                submenuButtonSizer.Add(button,0,wxEXPAND);
                submenuButtonSizer.Add(wxSize(0,0),1);
        
        mainSizer=wxBoxSizer(wxHORIZONTAL);
        mainSizer.Add(menuButtonSizer,0,wxEXPAND|wxALL,10);
        mainSizer.Add(self.myLine,0,wxEXPAND);
        mainSizer.Add(submenuButtonSizer,1,wxEXPAND|wxALL,10);
        
        self.SetSizer(mainSizer);
        self.Layout()
    
class MyApp(wxApp):
    def OnInit(self):
        self.frame=LauncherFrame(None,-1,"Access Grid Launcher","/Applications/Access Grid Toolkit.app");
        self.frame.Show();
        self.SetTopWindow(self.frame);
        return True;
    
if __name__ == '__main__':
    if len(sys.argv) < 2:
        print "Missing argument for the base path of the Access Grid Toolkit."
    basePath = sys.argv[1]

    if sys.platform == "darwin":
        from argvemulator import ArgvCollector
        ArgvCollector().mainloop()

    # Check to see if this was launched to handle an agpkg file.
    if ".agpkg" in str(sys.argv).lower():
        pp = wxPySimpleApp();
        for arg in sys.argv:
            if ".agpkg" in str(arg).lower():
                # Register an agpkg
                pkgFile = arg
                cmd = os.path.join(basePath, "bin", "agpm.py") + " --package %s" % str(pkgFile)
                os.system(cmd)
    else:

        #app=MyApp();
        #app.MainLoop();

        import sys

        pp = wxPySimpleApp();
    
        app=WXGUIApplication();
        #try:
            #args = app.Initialize('AGLauncher')
        #except:
            #pass

        frame=LauncherFrame(None,-1,"Access Grid Launcher",sys.argv[1]);
        frame.Show();
        pp.SetTopWindow(frame);
        pp.MainLoop();

    
