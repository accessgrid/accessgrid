import VenueServer
import socket
import SOAP

venueServer = VenueServer.VenueServer()
soapServer = SOAP.SOAPServer((venueServer.serverHost, venueServer.serverPort))
venueServer.SetServerInstance(soapServer)
# soapServer.registerObject(venueServer, venueServer.serverURL)

print "Test Server running on: %s %s %s" % (venueServer.serverHost, 
                                            venueServer.serverPort,
                                            venueServer.serverURL)

soapServer.serve_forever()