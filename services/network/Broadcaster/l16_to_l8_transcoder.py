import array
import time
import sys
import struct

from common.RTPSensor import RTPSensor
from common import common


class L16_to_L8(RTPSensor):
    '''
    Class for down-sampling L16-16kHz to L16-8kHz audio. 
    '''
    def __init__(self, from_address, from_port, to_address, to_port):
        RTPSensor.__init__(self, from_address, from_port)
        self.handlerDict[0] = self.do_RTP
        self.buffers = {} 
        self.sources = {}
        self.timeStamps = {}
        self.to_address = to_address
        self.to_port = to_port
                                
    def do_RTP(self, session, event):
        '''
        Method called when an rtp data packet arrives.
        '''
        packet = common.make_rtp_packet(event.data)
        data = common.rtp_packet_getdata(packet)

        # require l16-16k mono as input
        if packet.pt != 112:
            common.free_rtp_packet(packet)
            return

        # down sample the data
        args = []
        fmt = '%dh' % (len(data)/4)
        s = struct.unpack('%dh' % (len(data)/2) , data)
        args.append(fmt)
        for i in range(0, len(s), 2):
            args.append(s[i])
            
        sdata = apply(struct.pack,args)

        # buffer the data
        if self.buffers.has_key(packet.ssrc) and self.buffers[packet.ssrc]:
            packets = self.buffers[packet.ssrc]
            packets = self.buffers[packet.ssrc] + sdata
            self.buffers[packet.ssrc] = packets
            
        else:
            self.buffers[packet.ssrc] = sdata
            common.free_rtp_packet(event.data)
            return

        # L16 - 8kHz
        pt = 122

        destination = None

        try:
            data = self.buffers[packet.ssrc]
            
            # Create a new source for each stream to send
            # to the multicast address. Each new source is
            # keeping track of its own timestamp.
            
            if self.sources.has_key(packet.ssrc):
                destination = self.sources[packet.ssrc]

            else:
                destination = common.Rtp(self.to_address, self.to_port,
                                         self.to_port, 127,
                                         64000.0, None)
                dest_ssrc = destination.my_ssrc()
                tool = "audiotest.py"
                name = "RTP Messer"
                destination.set_sdes(dest_ssrc, common.RTCP_SDES_TOOL,
                                          tool, len(tool))
                destination.set_sdes(dest_ssrc, common.RTCP_SDES_NAME,
                                          name, len(name))
                destination.send_ctrl(0, None)
                self.sources[packet.ssrc] = destination


            # Each source keeps track of its own timestamp.
            if self.timeStamps.has_key(packet.ssrc):
                ts = self.timeStamps[packet.ssrc]
            else:
                self.timeStamps[packet.ssrc] = 0
                ts = 0

            # Send data
            destination.send_data(ts, pt, packet.m,
                                  packet.cc, packet.csrc,
                                  data, len(data),
                                  packet.extn, packet.extn_len,
                                  packet.extn_type)

            # Increment timestamp
            self.timeStamps[packet.ssrc] = ts + 160

           
        except Exception, e:
            print "Exception sending data, ", e

        common.free_rtp_packet(event.data)

        # Clear the buffer
        self.buffers[packet.ssrc] = None
      
        # Send control packets for each source
        for destination in self.sources.values():
            destination.send_ctrl(self.timeStamps[packet.ssrc], None)
            destination.update()
                   
    def StartSignalLoop(self):
        '''
        Start loop that can get interrupted from signals and
        shut down service properly.
        '''
        
        self.flag = 1
        while self.flag:
            try:
                time.sleep(0.5)
            except:
                self.flag = 0
                self.log.debug("l16_to_18_transcoder.StartSignalLoop: Signal loop interrupted, exiting.")
                self.Stop()

                                                         
if __name__ == "__main__":
    import sys
        
    from_addr = sys.argv[1]
    from_port = int(sys.argv[2])
    to_addr = sys.argv[3]
    to_port = int(sys.argv[4])

    tcoder = L16_to_L8(from_addr, from_port, to_addr, to_port)
    tcoder.Start()

    tcoder.StartSignalLoop()
      
    tcoder.Stop()
