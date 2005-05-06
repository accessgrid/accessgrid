
import os
import sys
from string import split, strip, find, lower
from random import seed, randint
from time import sleep

from AccessGrid import Log
from AccessGrid.Platform.Config import UserConfig
import jabber
import xmlstream
import threading

NS_P_MUC      = "http://jabber.org/protocol/muc" # JEP-0045
NS_IQ_MUC_OWNER = "http://jabber.org/protocol/muc#owner" 
NS_DATA = "jabber:x:data"

JABBER_CONNECTION = xmlstream.TCP_SSL

log = Log.GetLogger('JabberClient')
Log.SetDefaultLevel('JabberClient', Log.DEBUG)

# Generating random numbers between:
start = 100000000
end   = 999999999

class JabberClient:

    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.currentRoom = ''
        self.currentRoomId = ''
        # Initialize the default error codes and messgaes
        self.__init_error()
        # Set the seed for the random number generation
        seed()
        self._connect()

    def __init_error(self):
        self.errors = {'401':'Incorrect Jabber ID or password',
                       '409':'Jabber ID is already in use. Please choose another id'}
        self.errorCode = ''
        self.errorMsg  = ''

    def _connect(self):
        logDir = UserConfig.instance().GetLogDir()
        #logFile = os.path.join(logDir, "jabber.log")
        logFile = "c:\\jabber.log"

        self.host = "phosphorus.mcs.anl.gov"
        self.port = 5223

        print '=========== host:', self.host
        print '=========== port:', self.port
                
        self.con = jabber.Client(self.host, self.port, debug=[], log=logFile,
                                 connection = JABBER_CONNECTION)

        log.info("Connecting to Jabber Server '%s' ..." % self.host)
        #try:
        self.con.connect()
        #except Exception,E:
        #    log.exception("Connection failed: %s " % E)
        #else:
        #    log.info('Connected to Jabber Server Successfully')

        self.con.registerHandler('message',self.messageCB,makefirst=True)
        self.con.registerHandler('presence',self.presenceCB)
        self.con.registerHandler('iq',self.iqCB, makefirst=True)
        self.con.setDisconnectHandler(self.disconnectedCB)

        print '====================== connected to server!!!!!!!!'

    def setUserInfo(self, name, email, id, pwd, res):
        self.name = name
        self.jabberId = id
        self.password = pwd
        self.resource = res
        self.email = email

    def SetChatRoom(self, room):
        self.currentRoom = lower(room)
        self.currentRoomId = room + "@conference.phosphorus.mcs.anl.gov"
        self.to = self.currentRoomId + "/" + self.jabberId
        self.roomLocked = 0

    def GetChatRoom(self):
        return self.currentRoomId

    def SetPanel(self, panel):
        self.jabberPanel = panel

    def sendMessage(self, text):
        log.debug("currentRoom inside sendMessage(): '%s'" % self.currentRoomId)
        sent = 0
        if self.currentRoomId == '':
            log.error("No venue is selected")
        else:
            msg = jabber.Message(self.currentRoomId, strip(text))
            msg.setType('groupchat')
            try:
                log.debug("Sending message to jabber server ...")
                self.con.send(msg)
                sent = 1
            except Exception, E:
                print "Error:", E
                log.exception(E)
                sent = 0
        return sent
        
    def sendPresence(self, type='available'):
        log.debug("Sending the presence to '%s' of type '%s'..." % (self.to, type))
        p = jabber.Presence(self.to, type)
        if type == 'available':
            p.setX(NS_P_MUC)
        self.con.send(p)

    def messageCB(self, con, msg):
        message = msg.getBody()
        sender  = str(msg.getFrom())
        print msg.getFrom()
        
        if message:
            if self.roomLocked:
                print '----------- room is locked'
                if find(message,'This room is locked') > -1:
                    # Creating a room with default configuration
                    log.debug(message)
                    log.debug("Unlocking the chat room with default settings ...")
                    iq = jabber.Iq(to=sender, type='set')
                    iq.setID(self.__nextRand())
                    iq.setQuery(NS_IQ_MUC_OWNER)
                    iq.setQueryPayload("<x xmlns='%s' type='submit'/>" % NS_DATA)
                    self.con.send(iq)
                elif find(message, 'Configuration confirmed') > -1:
                    log.debug("Unlocked the chat room successfully.")
                    self.roomLocked = 0
                    pass
                elif message == self.currentRoom:
                    pass
                else:
                    self.roomLocked = 0
                    speaker = split(sender, '/')
                    print '***************', speaker
                    if len(speaker)<2:
                        log.debug(speaker[0] + ": " + message)
                    else:
                        self.jabberPanel.OutputText(speaker[1] + ": ", message)
            else:
                print '----------- room is not locked\n\n'
                print '\n\n============ this is sender', sender, '\n\n'
                speaker = split(str(sender), '/')
                print '\n\n------------- this is speaker ', speaker, '\n\n'
                if len(speaker)<2:
                    log.debug(speaker[0] + ": " + message)
                else:
                    self.jabberPanel.OutputText(speaker[1] + ": ", message)
                

    def presenceCB(self, con, prs):
        """Called when a presence is recieved"""
        who = str(prs.getFrom())
        type = prs.getType()
        if type == None: type = 'available'

        if type == 'available':
            log.debug("%s is available (%s / %s)" %
                      (who, prs.getShow(), prs.getStatus()))
        elif type == 'unavailable':
            log.debug("%s is unavailable (%s / %s)" %
                      (who, prs.getShow(), prs.getStatus()))

    def iqCB(self, con,iq):
        self.errorCode = ''
        if (iq.getType() == 'error'):
            self.errorCode = iq.getErrorCode()
            self.errorMsg  = iq.getError()
            log.error(self.errorCode + ": " + self.errorMsg)
        
    def disconnectedCB(self, con):
        print "Ouch, network error"
        sys.exit(1)

    def register(self):
        log.info("Registering the user '%s' in jabber server ..." % self.jabberId)
        regInfo = self.con.getRegInfo()
        regInfo[u'name'] = self.name
        regInfo[u'username'] = self.jabberId
        regInfo[u'password'] = self.password
        regInfo[u'email'] = self.email

        self.con.sendRegInfo()
        sleep(1)

    def login(self):
        log.info("Attempting to log in as %s ..." % self.jabberId)
        self.errorCode = ''
        if self.con.auth(self.jabberId,self.password,self.resource):
            log.info("Successfully logged in")

        ###################################
        ## Question ?
        ## Need user's roster information ?
        ###################################
        #self.con.requestRoster()
        #self.con.sendInitPresence()

        threading.Thread(target=self.__readIncoming).start()

    def disconnect(self):
        log.info("Disconnecting from the jabber server")
        try:
            self.con.disconnect()
        except Exception, e:
            log.debug("Error in disconnecting from the jabber server")
            log.exception(e)

    def __readIncoming(self):
        while 1:
            self.con.process(0.5)
        return

    def __nextRand(self):
        return randint(start, end)
