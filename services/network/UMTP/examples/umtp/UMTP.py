#-----------------------------------------------------------------------------
# Name:        UMTP.py
# Purpose:     Class implementing interface for communicating with UMTP Agent
# Created:     2005/08/16
# RCS-ID:      $Id: UMTP.py,v 1.1 2006/06/28 08:47:47 ngkim Exp $
# Copyright:   (c) 2005
# Licence:     See COPYING.TXT
#-----------------------------------------------------------------------------

"""
"""
__revision__ = "$Id: UMTP.py,v 1.1 2006/06/28 08:47:47 ngkim Exp $"

import socket, threading, string, struct, select

from wxPython.wx import *

from AccessGrid.Venue import *
from AccessGrid.Platform import IsWindows, IsLinux, IsOSX
from AccessGrid.Platform.Config import AGTkConfig
from AccessGrid.Platform.ProcessManager import ProcessManager
from AccessGrid.NetworkAddressAllocator import NetworkAddressAllocator

class UMTPAgent:

    def __init__(self, log):
        self.log        = log

	umtp_agent  = ( "127.0.0.1"       , 8011)
	umtp_server = ( "umtp.mcs.anl.gov", "8010")
		
	self.apm = AgentProcessManager(self.log)	
	self.gmt = GroupManagementThread(self.log, self)

	self.SetAgent(umtp_agent)
	self.SetServer(umtp_server)

    def SetExitCB(self, ExitCB):
        self.Exit = ExitCB

    def Start(self):
        try:
	    self.apm.Start()
	    self.gmt.start()

    	    """
	     Set UMTP is now running
	    """
	    self.umtp_running = 1
	except AssertionError, e:
	    self.RestartThread()	    
	    self.log.debug("UMTP: Thread already started. Restart thread")
	    self.log.exception(e)
	    
    def RestartThread(self):
        try:
	    self.gmt = GroupManagementThread(self.log, self)
	    self.gmt.SetStreamList(self.streamList)
	    self.gmt.SetAgent(self.umtp_agent)
	    self.gmt.start()

    	    """
	     Set UMTP is now running
	    """
	    self.umtp_running = 1
	except Exception, e:
	    self.log.exception(e)

    def Stop(self, transport = 'multicast'): # default is 'multicast'    
	try:
	    if self.umtp_running :
	        self.umtp_running = 0	        
	        if self.gmt.IsRunning(): self.gmt.StopThread()
		if self.apm.IsRunning(): self.apm.Stop()
	        self.Exit(transport)	        
	except AttributeError, e:
	    """
	     If Exit Callback is not set, make a log
	    """
	    self.log.exception(e)
    
    def SetStreamList(self, streamList):
        self.streamList = streamList
	self.gmt.SetStreamList(streamList)

    def GetStreamList(self):
        return self.streamList

    def SetAgent(self, umtp_agent):
        self.umtp_agent = umtp_agent
	self.gmt.SetAgent(umtp_agent)

    def GetAgent(self):
        return self.umtp_agent

    def SetServer(self, umtp_server):
        self.umtp_server = umtp_server
	self.apm.SetOptions(self.umtp_server)

    def GetServer(self):
        return self.umtp_server   

class GroupManagementThread( threading.Thread ):

    def __init__(self, log, parent):
        threading.Thread.__init__ ( self )

        self.log	  = log
	self.parent       = parent

        self.ac           = AgentCommunication(log)
	self.ae		  = AgentError(log)	

	self.ae.SetJoinCB(self.ac.SendJoin)
	self.ae.SetHoldCB(self.HoldThread)
	self.ae.SetStopCB(self.StopThread)
	self.ae.SetUpdateAgentCB(self.parent.SetAgent)	

        """
	 Timing variables, send join message every join_interval seconds
	"""	
	self.join_interval = 0
	self.max_interval  = 60
	self.lastJoin      = time.time()
	
	"""
	 Condition variables for running thread
	"""
	self.hold_thread  = 0
        self.cond         = threading.Condition()
	self.running      = threading.Event()
 
    def run(self):
        self.cond.acquire()
	self.running.set()

	while self.running.isSet():            
	    try:
	        if self.ac.Select():
		    ((command, u_addr, u_port), src_addr) = self.ac.Receive()
                    self.ae.ProcessAgentError(command, u_addr, u_port, src_addr)
                else:		    	    
		    if time.time() - self.lastJoin > self.join_interval:
		        self.ac.SendJoin()
			self.lastJoin = time.time()
		    """
		     Increase join_interval upto max_interval
		    """	
		    if self.join_interval <= self.max_interval: 
		        self.join_interval += 2
	    except Exception, e:
	        self.log.exception(e)
		self.ae.Message("No connection with UMTP Agent!!!\n"
		                "Check if UMTP Agent process is running")		
		self.StopThread()
	self.log.debug("UMTP Thread stops")
	
    def SetStreamList(self, streamList):
        self.streamList = streamList
	self.ac.SetStreamList(streamList)

    def SetAgent(self, umtp_agent):
        self.umtp_agent = umtp_agent
        self.ac.SetAgent(umtp_agent)
	self.ae.SetAgent(umtp_agent)

    def IsRunning(self):
        return self.running.isSet()

    def HoldThread(self):
        self.hold_thread = 1
        self.cond.wait()

    def StopThread(self):
	self.running.clear()
	self.WakeUpThread()
	self.ac.SendLeave()
	self.parent.Stop()

    def WakeUpThread(self):
        if self.hold_thread :
	    self.cond.acquire()
	    self.cond.notify()
	    self.cond.release()
	    self.hold_thread = 0
    
class AgentCommunication:

    MSGSIZE = 5192
    JOIN    = 0
    LEAVE   = 1

    def __init__(self, log):
        self.timeout = 5

	self.log     = log
	self.UDPSock = self.OpenSocket()
	self.gmp     = GroupManagementProtocol()	

    def OpenSocket(self):        
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

	port = NetworkAddressAllocator().AllocatePort()
        s.bind(('', port))
	return s

    """
     Receive error information from Agent
    """
    def Select(self):
        try:
	    fdList = select.select([self.UDPSock.fileno()],[],[],self.timeout)		
            if fdList[0] and self.UDPSock.fileno() in fdList[0]:
	        return 1
	    else:
	        return 0	
	except Exception, e:
	    self.log.exception(e)
	    raise
    
    def Receive(self):
        try:
	    (msg, src_addr) = self.Recv()
	except Exception, e:
	    raise
	return (self.gmp.Disassemble(msg), src_addr)
    
    """
     Send JOIN and LEAVE message to Agent
    """
    def SendJoin(self):	
	if not self.streamList:
            return

	for s in self.streamList:
	    for netLoc in s.networkLocations:
	        if netLoc.type == 'multicast' and s.capability[0].type in ("audio", "video"):
		    self.log.debug("UMTP: join %s", netLoc.host)
	            g_addr = self.Aton(netLoc.host)
	            g_port = netLoc.port
	            self.Send(self.gmp.Assemble(self.JOIN, g_addr, g_port), self.umtp_agent)
		    
	            if g_port % 2 == 0: g_port = g_port + 1
	            else:		g_port = g_port - 1
	            self.Send(self.gmp.Assemble(self.JOIN, g_addr, g_port), self.umtp_agent)

    def SendLeave(self):	
        if not self.streamList:
            return

        for stream in self.streamList:
	    for netLoc in stream.networkLocations:
	        if netLoc.type == 'multicast':
	            g_addr = self.Aton(netLoc.host)
	            g_port = netLoc.port
	            self.Send(self.gmp.Assemble(self.LEAVE, g_addr, g_port), self.umtp_agent)
	    
	            if g_port % 2 == 0: g_port = g_port + 1
	            else:		g_port = g_port - 1
	            self.Send(self.gmp.Assemble(self.LEAVE, g_addr, g_port), self.umtp_agent)

    """
     Basic Socket operations
    """
    def Send(self, msg, dst):
        self.UDPSock.sendto(msg, dst)

    def Recv(self):
        data,src_addr = self.UDPSock.recvfrom(self.MSGSIZE)
	return (data, src_addr)    

    """
     Set Agent and Stream information
    """
    def SetAgent(self, umtp_agent):
        self.umtp_agent = umtp_agent

    def SetStreamList(self, streamList):
        self.streamList = streamList
    
    def Aton(self, host):
        # Construct binary group address
        bytes = map(int, string.split(host, "."))
        addr = long(0)
        for byte in bytes:
            addr = (addr << 8) | byte
	return addr

    def Close(self):
        self.UDPSock.close()
	del self.UDPSock

class AgentProcessManager:

    def __init__(self, log):
        self.processManager = ProcessManager()
	self.log     = log
	self.started = 0
	self.options = []

	executable = None
	if   IsWindows() : executable = "umtp_win32"
	elif IsLinux()   : 
	    executable = "umtp_linux"
	    os.chmod(executable, 0755) # make umtp_linux file executable 
	elif IsOSX()     : executable = "umtp_darwin"

	self.SetExecutable(AGTkConfig.instance().GetBinDir(), executable)

    def SetExecutable(self, directory, command):
        self.executable = os.path.join(directory, command)

    def SetOptions(self, umtp_server):
        self.options = []
	self.options.append("-m")
	self.options.append(umtp_server[0])
	self.options.append(umtp_server[1])  
	
    def IsRunning(self):
        return self.started

    def Start( self ):
        """ if started, stop """
        if self.started == 1:
           self.Stop()

        self.pid = self.processManager.StartProcess( self.executable, self.options )
	self.started = 1
	
    
    def Stop( self ):
        """ Stop the service """
        try:
            self.started = 0	    
            self.processManager.TerminateAllProcesses()	    
        except Exception, e:
            self.log.exception("Exception in AGService.Stop")
            raise e

class GroupManagementProtocol:
    
    def __init__(self):
        self.command = 0
	self.g_addr  = 0
	self.g_port  = 0

    def Assemble(self, command, g_addr, g_port):
        msg = struct.pack('HHI', command, g_port, socket.htonl(g_addr) )
	return msg

    def Disassemble(self, msg):      	
	( command, g_port, g_addr ) = struct.unpack('HHI', msg)
	return (command, g_addr, g_port)

class AgentError:
    NO_PROBE_ACK     = 3
    FIND_NEIGHBOR    = 4
    SERVER_REACHABLE = 5
    RECV_SIGTERM     = 6
    
    def __init__(self, log):
        self.log      = log
	self.msg      = None

    def IsMyAgent(self, addr):
        return (self.agent_ip == addr)

    def SetAgent(self, umtp_agent):
	self.agent_ip   = struct.unpack('I', socket.inet_aton(umtp_agent[0]))

    def ProcessAgentError(self, command, addr, port, src_addr):	  
        """
	 If sender is not my agent, then ignore
	"""
	agent = struct.unpack('I', socket.inet_aton(src_addr[0]))
	if not self.IsMyAgent(agent):
	    return

	if command == self.FIND_NEIGHBOR:
	    self.FindNeighbor(addr, port)
	elif command == self.NO_PROBE_ACK:
	    self.msg = "Failed to connect Server! Try other Server."
	    self.StopUMTP()
	else:
	    if command == self.SERVER_REACHABLE:
	        self.msg = "You are multicast-reachable from Server."
	    elif command == self.RECV_SIGTERM:
	        self.msg = "UMTP Agent catches SIGTERM event"
	    self.StopUMTP()
    
    def FindNeighbor(self, new_agent_ip, new_agent_port):
        """
	 Change agent, only if it's new agent
	"""
        if not self.IsMyAgent(new_agent_ip):
            self.agent_ip  = new_agent_ip
            new_agent_addr = socket.inet_ntoa(struct.pack('I', new_agent_ip))
            self.UpdateAgent((new_agent_addr, new_agent_port))
	        
	    self.msg = "Move to new Agent. [%s/%d]" % (new_agent_addr, new_agent_port)
            self.Message(self.msg)

	    """
	     Immediately send JOIN to new agent
	    """
	    self.Join()
    
    def HoldUMTP(self):
        self.Message(self.msg)
	self.Hold()

    def StopUMTP(self):
        self.Message(self.msg)
	self.Stop()

    """
     Set Callback methods
    """
    def SetHoldCB(self, HoldCB):
        self.Hold = HoldCB

    def SetStopCB(self, StopCB):
        self.Stop = StopCB

    def SetJoinCB(self, JoinCB):
        self.Join = JoinCB

    def SetUpdateAgentCB(self, UpdateAgentCB):
        self.UpdateAgent = UpdateAgentCB

    def Message(self, message, style = wxOK|wxICON_INFORMATION):
        messageDialog = None
        try:
	    messageDialog = wxMessageDialog(None, message, "Error Dialog", style)
    	    messageDialog.ShowModal()
	    messageDialog.Destroy()
	except:
	    if messageDialog:
	        messageDialog.Destroy()