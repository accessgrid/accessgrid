"""
Docstring to fill in later.
"""

__revision__ = ""

from AccessGrid import Log
from AccessGrid.AsyncService import AsyncService
from AccessGrid.Events import ConnectEvent, DisconnectEvent

class TextService(AsyncService):
    def __init__(self, address):
        AsyncService.__init__(self, address)
        
    def HandleEvent(self, event, connObj):
        """
        Docstring to fill in later.
        """
        connChannel = self.findConnectionChannel(connObj.GetId())

        if connChannel is None:
            self.HandleEventForDisconnectedChannel(event, connObj)
        else:
            connChannel.HandleEvent(event, connObj)
        
        if event.eventType == ConnectEvent.CONNECT:
            return
        
        if event.eventType == DisconnectEvent.DISCONNECT:
            return
        
        payload = event.data
        payload.sender = connObj.sender
        self.Distribute(connChannel.GetId(), event)
    
if __name__ == "__main__":
  import string, traceback
  from optparse import Option
  from AccessGrid import Toolkit

  app = Toolkit.CmdlineApplication()
  portOption = Option("-p", "--port", dest="port", type="int", default=6600,
                      help="Specify a port to run the event service on.")
  app.AddCmdLineOption(portOption)
  
  try:
      app.Initialize("TextService-Main")
  except:
      print "Exception initializing toolkit: ", traceback.print_exc()
      sys.exit(-1)

  port = app.GetOption("port")
  print "Creating new TextService at %d." % port
  textService = TextService(('', port))
  textService.AddChannel("Test")
  textService.start()

