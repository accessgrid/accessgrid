# GUI related imports
from wxPython.wx import wxPySimpleApp

# Our imports
from AccessGrid.Toolkit import WXGUIApplication
from AccessGrid import Log
from AccessGrid.Platform.Config import UserConfig
from AccessGrid.VenueClientUI import VenueClientUI
from AccessGrid.VenueClientController import VenueClientController
from AccessGrid.VenueClient import VenueClient
from AccessGrid.UIUtilities import ErrorDialog
from AccessGrid.UIUtilities import ProgressDialog
from AccessGrid.Descriptions import ServiceDescription, ApplicationDescription
from AccessGrid.VenueClientObserver import VenueClientObserver

# General imports
from optparse import Option
import sys
import signal, time, os, time

class SystemTest:
    def __init__(self):

        # Init the toolkit with the standard environment.
        self.app = WXGUIApplication()
        
        # Try to initialize
        args = self.app.Initialize("VenueClient", sys.argv[:1])

        # Handle command line options
        self.__buildOptions()
              
        if not self.port:
            self.port = 8000

        if not self.url:
            self.url = 'https://localhost:8000/Venues/default'

        # Create venue client components
        self.vc = VenueClient(pnode=self.pnode, port=self.port)
        self.vcc = VenueClientController()
        self.vcc.gui = Gui()
        self.vcc.SetVenueClient(self.vc)
        self.observer = Observer()
        self.vc.AddObserver(self.observer)
                
        # Start tests
        self.__StartTests()
        
        # Exit
        self.vc.Shutdown()
        sys.exit(0)
        
    def __StartTests(self):
        # -------------------------------------
        # EnterVenue
        # -------------------------------------
        
        self.__testMethod(self.vc.EnterVenue, "EnterVenue", args = [self.url])
                
        # -------------------------------------
        # Services
        # -------------------------------------
        
        # AddService
        service = ServiceDescription("test", "test", "test", "test")
        service.SetId(5)
        self.__testMethod(self.vc.AddService, "AddService", args = [service])

        s = self.observer.lastService
        
        if not s.id == service.id:
            print 'Add Service FAILED; service does not exist'
        
        # UpdateService
        service.SetName("Updated Service")
        self.__testMethod(self.vc.UpdateService, "UpdateService", args = [service])
        
        # RemoveService
        self.__testMethod(self.vc.RemoveService, "RemoveService", args = [service])

        # -------------------------------------
        # Data
        # -------------------------------------

        # AddData
        file1 = os.path.join(os.getcwd(), 'unittest_all.py')
        file2 = os.path.join(os.getcwd(), 'unittest_ClientProfile.py')
        self.__testMethod(self.vcc.UploadVenueFiles, "UploadVenueFiles", args = [[file1,file2]])

        time.sleep(20)
        d = self.observer.lastData
        
        d.SetName("Updated Name")
        # ModifyData
        self.__testMethod(self.vc.ModifyData, "ModifyData", args = [d])

        # RemoveData

        
        # -------------------------------------
        # Applications
        # -------------------------------------
        
        # CreateApplication
        name = 'Test App'
        self.__testMethod(self.vc.CreateApplication, "CreateApplication", args = ['Test App', "my_desc", 'my_mime'])
        
        app = self.observer.lastApplication
        
        if not app.name == name:
            print 'Create Application Failed; app does not exist'
            
        # UpdateApplication
        app.SetName("Updated Application")
        self.__testMethod(self.vc.UpdateApplication, "UpdateApplication", args = [app])
        
        # DestroyApplication
        self.__testMethod(self.vc.DestroyApplication, "DestroyApplication", args = [app.id])

        # --------------------------------------
        # ExitVenue
        # --------------------------------------
        self.__testMethod(self.vc.ExitVenue, 'ExitVenue')

                  
    def __testMethod(self, method, text, args = None):

        print '******************************************'
        
        try:
            if args:
                return apply(method, args)
            else:
                return apply(method)
            print '%s SUCCEEDED'%text
        except:
            print '%s FAILED'%text
        
        print '******************************************'
        
                
    def __buildOptions(self):
        # build options for this application
        
        portOption = Option("-p", "--port", type="int", dest="port",
                                        default=0, metavar="PORT",
                                        help="Set the port the venueclient control interface\
                                        should listen on.")
        self.app.AddCmdLineOption(portOption)
        pnodeOption = Option("--personalNode", action="store_true", dest="pnode",
                             default=0,
                             help="Run NodeService and ServiceManager with the client.")
        self.app.AddCmdLineOption(pnodeOption)
        urlOption = Option("--url", type="string", dest="url",
                           default="", metavar="URL",
                           help="URL of venue to enter on startup.")
        self.app.AddCmdLineOption(urlOption)
                        
        self.log = self.app.GetLog()
        self.pnode = self.app.GetOption("pnode")
        self.url = self.app.GetOption("url")
        self.port = self.app.GetOption("port")

class Gui:
    def __init__(self):
        pass

    def OpenUploadFilesDialog(self):
        pass

    def Notify(self, t1, t2):
        pass
    

class Observer(VenueClientObserver):
    def __init__(self):
        print 'observer'
        self.lastService = None
        self.lastApplication = None
        self.lastData = None
        
    def EnterVenue(self, url, warning = None, success = None):
        pass

    def ExitVenue(self):
        pass

    def Exception(self):
        pass

    def AddService(self, s):
        print '-------- ADD SERVICE EVENT', s.name
        self.lastService = s

    def UpdateService(self, s):
        print '-------- UPDATE SERVICE EVENT', s.name
        self.lastService = s

    def RemoveService(self, s):
        print '-------- REMOVE SERVICE EVENT', s.name
        self.lastService = s

    def AddApplication(self, a):
        print '-------- ADD APPLICATION EVENT', a.name
        self.lastApplication = a
        
    def UpdateApplication(self, a):
        print '-------- UPDATE APPLICATION EVENT', a.name
        self.lastApplication = a
        
    def RemoveApplication(self, a):
        print '-------- REMOVE APPLICATION EVENT', a.name
        self.lastApplication = a

    def AddData(self, d):
        print '-------- ADD DATA EVENT', d.name
        self.lastData = d

    def UpdateData(self, d):
        print '-------- UPDATE DATA EVENT', d.name
        self.lastData = d

    def RemoveData(self, d):
        print '-------- REMOVE DATA EVENT', d.name
        self.lastData = d
        
        
# The main block
if __name__ == "__main__":
    s = SystemTest()

