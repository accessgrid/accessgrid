
import sys
from AccessGrid.hosting.pyGlobus import Client
from AccessGrid.ClientProfile import ClientProfile


def BasicTest( appUrl ):
    print "App object url = ", appUrl
    appProxy = Client.Handle( appUrl ).get_proxy()

    print "-- Join application"
    profile = ClientProfile()
    privateToken = appProxy.Join( profile )

    print "-- Get data channel"
    (channelId, eventServiceLocation) = appProxy.GetDataChannel(privateToken)

    print "-- Set data"
    testKey = "test key"
    testValue = "test value"
    appProxy.SetData( privateToken, testKey, testValue )

    print "-- Get data"
    retVal = appProxy.GetData( privateToken, testKey )
    if not retVal == testValue:
        print "FAILURE: Get data returned different value than was set"

    print "-- Leave"
    appProxy.Leave(privateToken)



venueUrl = "https://localhost:8000/Venues/default"
if len(sys.argv) > 1:
   venueUrl = sys.argv[1]
venueProxy = Client.Handle( venueUrl ).get_proxy()


#
# Create an application
#
print "-- Create application"
appUrl = venueProxy.CreateApplication( 
            "test app name",
            "test app description",
            "test app mimeType" )
print "-- Test service reachability"
appUrlValid = Client.Handle( appUrl ).IsValid()
if not appUrlValid:
    print "Application service unreachable; exiting"
    os._exit(1)

# run the basic tests
BasicTest( appUrl )

# Destroy that application
#appId = Client.Handle( appUrl ).get_proxy().GetId()
#venueProxy.DestroyApplication( appId )


