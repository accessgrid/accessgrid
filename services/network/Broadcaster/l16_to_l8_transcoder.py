import array
import time
import sys
import struct
from common.RTPSensor import RTPSensor
from common import common

class L16_to_L8(RTPSensor):
    def __init__(self, from_address, from_port, to_address, to_port):
        RTPSensor.__init__(self, from_address, from_port)
        self.handlerDict[0] = self.do_RTP
        self.destination = common.Rtp(to_address, to_port, to_port, 127,
                                      64000.0, None)
        dest_ssrc = self.destination.my_ssrc()
        tool = "audiotest.py"
        name = "RTP Messer"
        self.destination.set_sdes(dest_ssrc, common.RTCP_SDES_TOOL,
                                  tool, len(tool))
        self.destination.set_sdes(dest_ssrc, common.RTCP_SDES_NAME,
                                  name, len(name))
        self.destination.send_ctrl(0, None)
        self.last_ts = 0
        self.buffer = ""
        
    def do_RTP(self, session, event):
    
        packet = common.make_rtp_packet(event.data)
        data = common.rtp_packet_getdata(packet)
        
        # require l16-16k mono as input
        if packet.pt != 112:
            common.free_rtp_packet(packet)
            return
        
        args = []
        fmt = '%dh' % (len(data)/4)
        s = struct.unpack('%dh' % (len(data)/2) , data)
        args.append(fmt)
        for i in range(0, len(s), 2):
            args.append(s[i])
            
        sdata = apply(struct.pack,args)
        
        if self.buffer:
            self.buffer = self.buffer + sdata
            sdata = self.buffer
            self.buffer = None
        else:
            self.buffer = sdata
            common.free_rtp_packet(event.data)
            return
        
        pt = 122

        try:
            self.destination.send_data(self.last_ts, pt, packet.m,
                                       packet.cc, packet.csrc,
                                       sdata, len(sdata),
                                       packet.extn, packet.extn_len,
                                       packet.extn_type)
            self.last_ts = self.last_ts + 160
        except Exception, e:
            print "Exception sending data, ", e
            
        self.destination.send_ctrl(packet.ts, None)
        self.destination.update()

        common.free_rtp_packet(event.data)
        

if __name__ == "__main__":
    import sys
    
    from_addr = sys.argv[1]
    from_port = int(sys.argv[2])
    to_addr = sys.argv[3]
    to_port = int(sys.argv[4])

    tcoder = L16_to_L8(from_addr, from_port, to_addr, to_port)
    tcoder.Start()
    
