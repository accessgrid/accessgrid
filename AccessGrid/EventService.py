"""
Docstring to fill in later.
"""

__revision__ = ""

from AccessGrid import Log
from AccessGrid.AsyncService import AsyncService
from AccessGrid.Events import Event, AddDataEvent, RemoveDataEvent
from AccessGrid.Events import UpdateDataEvent

log = Log.GetLogger(Log.EventService)
Log.SetDefaultLevel(Log.EventService, Log.DEBUG)

class EventService(AsyncService):
    def __init__(self, address):
        log.debug("Event Service Created with Address: %s %d", address[0],
                  address[1])
        AsyncService.__init__(self, address)
        
    def HandleEvent(self, event, connObj):
        """
        Docstring to fill in later.
        """
        log.debug("EventService Handle Event for connection %s", connObj)
        
        connChannel = self.findConnectionChannel(connObj.GetId())
        
        if connChannel is None:
            self.HandleEventForDisconnectedChannel(event, connObj)
        else:
            if event.eventType == AddDataEvent.ADD_DATA:
                self.Distribute(event.venue,
                                Event( Event.ADD_DATA,
                                       event.venue,
                                       event.data))
            elif event.eventType == UpdateDataEvent.UPDATE_DATA:
                self.Distribute(event.venue,
                                Event( Event.UPDATE_DATA,
                                       event.venue,
                                       event.data))
            elif event.eventType == RemoveDataEvent.REMOVE_DATA:
                self.Distribute(event.venue,
                                Event( Event.REMOVE_DATA,
                                       event.venue,
                                       event.data))
            connChannel.HandleEvent(event, connObj)

if __name__ == "__main__":
  import string, traceback
  from optparse import Option
  from AccessGrid import Toolkit

  app = Toolkit.CmdlineApplication()
  portOption = Option("-p", "--port", dest="port", type="int", default=6500,
                      help="Specify a port to run the event service on.")
  app.AddCmdLineOption(portOption)
  
  try:
      app.Initialize("EventService-Main")
  except:
      print "Exception initializing toolkit: ", traceback.print_exc()
      sys.exit(-1)

  port = app.GetOption("port")
  print "Creating new EventService at %d." % port
  eventService = EventService(('', port))
  eventService.AddChannel('Test')
  eventService.start()
