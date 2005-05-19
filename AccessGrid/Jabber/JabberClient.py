from gov.lbl.dsd.bajjer import *
import string, random
import time
import string

from AccessGrid import Log
#from AccessGrid.Platform.Config import UserConfig

log = Log.GetLogger('JabberClient')
Log.SetDefaultLevel('JabberClient', Log.DEBUG)

# Generating random numbers between:
start = 100000000
end   = 999999999 

class JabberClient:

    def __init__(self, host, port):
        log.info("Connecting to Jabber Server '%s' ..." % host)
        self._stream = stream.JabberClientStream(host, port=port, use_ssl=True)
        self.currentRoom = ''
        self.currentRoomId = ''
        self._auth_info = None
        self.email = None
        self.jid = None
        self.name = None
        self.resource = None
        self.roomLocked = 0

    def setUserInfo(self, name, id, pwd, res):
        self.name = name
        self.jid = auth.Jid(id) 
        self.auth_info = auth.AuthInfo(self.jid) 
        self.auth_info.password = pwd
        self.resource = res
        #email isn't passed in
        #self.email = email

    def SetChatRoom(self, room):
        self.currentRoom = string.lower(room)
        self.currentRoomId = room + "@conference.phosphorus.mcs.anl.gov"
        self.to = self.currentRoomId + "/" + self.name

    def SetPanel(self, panel):
        self.jabberPanel = panel

    def sendMessage(self, text):
        log.debug("currentRoom inside sendMessage(): '%s'" %self.currentRoomId)
        sent = 0
        if self.currentRoomId == '':
            log.error("No venue is selected")
            return sent
      
        try:
            log.debug("Sending message to jabber server ...")
            self._stream.message(self.currentRoomId, string.strip(text), msg_type="groupchat") 
            sent = 1
        except Exception, E:
            print "Error:", E
            log.exception(E)
            sent = 0
        return sent

    def sendPresence(self, type='available'):
        log.debug("Sending the presence to '%s' of type '%s'..." % (self.to, type))
        req = stanza.Presence()
        if type == 'available': 
            req.to_ = self.to
            req.type_ = type
            req.x_ = (stanza.External(),)
            #req.x_ = (stanza.External(util.Namespaces.Muc.muc),)

        self._stream.write(req)

    def messageCB(self, msg_stanza):
        message = msg_stanza.body_
        sender  = msg_stanza.from_ 
   
        if not message == '':
            if self.roomLocked:
                if string.find(message,'This room is locked') > -1:
                    # Creating a room with default configuration
                    log.debug(message)
                    log.debug("Unlocking the chat room with default settings ...")
                    iq = stanza.Iq()
                    iq.to_ = sender
                    iq.type_ = 'set' 
                    iq.id_ = self.__nextRand()
                    iq.query_e = (stanza.External(),)
                    #iq.query_e = stanza.Query(util.Namespaces.Muc.owner)  
                    iq.query_e.x_e = stanza.External(util.Namespaces.x_form)
                    iq.query_e.x_e.type_= 'submit' 
                    self._stream.write(iq)
                elif string.find(message, 'Configuration confirmed') > -1:
                    log.debug("Unlocked the chat room successfully.")
                    self.roomLocked = 0
                    pass
                elif message == self.currentRoom:
                    pass
                else:
                    self.roomLocked = 0
                    speaker = string.split(sender, '/')
                    
                    if len(speaker)<2:
                        log.debug(speaker[0] + ": " + message)
                    else:
                        self.jabberPanel.OutputText(speaker[1] + ": ", message)
            else:
                speaker = string.split(str(sender), '/')
                if len(speaker)<2:
                    log.debug(speaker[0] + ": " + message)
                else:
                    self.jabberPanel.OutputText(speaker[1] + ": ", message)

    def presenceCB(self, prs_stanza):
        """Called when a presence is recieved"""
        who = prs_stanza.from_
        prs_type = prs_stanza.type_
        if prs_type == None: 
            prs_type = 'available'

        if prs_type == 'available':
            log.debug("%s is available (%s / %s)" %
                      (who, prs_stanza.show_ , prs_stanza.status_ ))
        elif prs_type == 'unavailable':
            log.debug("%s is unavailable (%s / %s)" %
                      (who, prs_stanza.show_ , prs_stanza.status_ ))
    
    def iqCB(self, iq_stanza):
        self.errorCode = ''
        if (iq_stanza.type_ == 'error'):
            self.errorCode = iq_stanza.error_e.code_ 
            self.errorMsg  = iq_stanza.error_e.getText()
            log.error(self.errorCode + ": " + self.errorMsg)

    def register(self):
        """
        TODO: user name and email, when registering a user
        """
        log.info("Registering the user '%s' in jabber server ..." % self.jid) 
        if self.auth_info is None:
            raise RuntimeError("setUserInfo must be called before register")

        self._stream.register(self.auth_info)
        #msg = self._stream.read(expected=stanza.Message)
        time.sleep(1)

    def login(self):
        log.info("Attempting to log in as %s ..." % self.jid)
        self.errorCode = ''

        if self._stream.authorize(self.auth_info):
            log.info("Successfully logged in")
        self._stream.setMessageHandler(self.messageCB)
        self._stream.setPresenceHandler(self.presenceCB)
        self._stream.setIqHandler(self.iqCB)

       

    def __nextRand(self):
        return random.randint(start, end)
