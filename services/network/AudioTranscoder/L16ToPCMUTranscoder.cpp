/*
 An audio transcoder that can translate L16-8K-Mono to u-law-8K-Mono. The code
 uses the live.com streaming media library (www.live.com/liveMedia)
*/

#include "liveMedia.hh"
#include "GroupsockHelper.hh"
#include "BasicUsageEnvironment.hh"

void afterPlaying(void* clientData); // forward

// A structure to hold the state of the current session.
// It is used in the "afterPlaying()" function to clean up the session.
struct sessionState_t {
  FramedSource* source;
  //RTPSource* source;
  RTPSink* sink;
  Groupsock* rtpGroupsock;
  Groupsock* rtcpGroupsock;
  RTCPInstance* rtcpInstance;
  RTSPServer* rtspServer;
} sessionState;

UsageEnvironment* env;

int main(int argc, char** argv) {
  
  // Begin by setting up our usage environment:
  TaskScheduler* scheduler = BasicTaskScheduler::createNew();
  env = BasicUsageEnvironment::createNew(*scheduler);
  
  if (argc != 5){
    *env << "\n      Usage: L16ToPCMUTranscoder.cpp fromAddress fromPort toAddress toPort\n\n      fromAddress/fromPort transmits L16-8K-Mono audio \n      toAddress/toPort receives PCMu-8K-Mono\n\n";
    exit(1);
  }

  unsigned const samplingFrequency = 8000; 
  unsigned char const numChannels = 1; 
  unsigned char const bitsPerSample = 16;
  unsigned bitsPerSecond = samplingFrequency*bitsPerSample*numChannels;
  
  // *********** SOURCE ****************
 
  // Create 'groupsocks' for RTP and RTCP:
  char* fromAddr = argv[1];
  const unsigned short fromPort = atoi(argv[2]);
  const unsigned short rtcpPortNumSource = fromPort+1;
  const unsigned char ttlSource = 255;
  char* mimeType = "PCM";
  unsigned char rtpPayloadFormat = 122;  //Receive L16-8K-Mono
   
  struct in_addr sessionAddress;
  sessionAddress.s_addr = our_inet_addr(fromAddr);
  const Port rtpPortSource(fromPort);
  const Port rtcpPortSource(rtcpPortNumSource);
  Groupsock rtpGroupsock(*env, sessionAddress, rtpPortSource, ttlSource);
  Groupsock rtcpGroupsock(*env, sessionAddress, rtcpPortSource, ttlSource);
  
  RTPSource* rtpSource
    = SimpleRTPSource::createNew(*env, &rtpGroupsock, rtpPayloadFormat,
				 samplingFrequency, mimeType, 1, true);

  // Create (and start) a 'RTCP instance' for the RTP source:
  const unsigned estimatedSessionBandwidth = 130; // in kbps; for RTCP b/w share
  const unsigned maxCNAMElen = 100;
  unsigned char CNAME[maxCNAMElen+1];
  gethostname((char*)CNAME, maxCNAMElen);
  CNAME[maxCNAMElen] = '\0'; // just in case
  sessionState.rtcpInstance
    = RTCPInstance::createNew(*env, &rtcpGroupsock,
			      estimatedSessionBandwidth, CNAME,
			      NULL /* we're a client */, rtpSource);
  // Note: This starts RTCP running automatically

  // ************** FILTER ****************

  // Add a filter that converts from raw 16-bit PCM audio (in little-endian order)
  // to 8-bit u-law audio:
  sessionState.source = uLawFromPCMAudioSource::createNew(*env, rtpSource, 1/*little-endian*/);
  if (sessionState.source == NULL) {
    *env << "Unable to create a u-law filter from the PCM audio source: "
	 << env->getResultMsg() << "\n";
    exit(1);
  }
  bitsPerSecond /= 2;
  mimeType = "PCMU";
  if (samplingFrequency == 8000 && numChannels == 1) {
    *env << "Convert to u-law 8kHz with payloadformat 0";
    rtpPayloadFormat = 0; // a static RTP payload type
    
  } else {
    *env << "dynamic payload format\n";
    rtpPayloadFormat = 96; // a dynamic RTP payload type
  }
    
  // ********** SINK ********************
  
  // Get attributes of the audio source:
 
  if (bitsPerSample != 8 && bitsPerSample !=  16) {
    *env << "The input file contains " << bitsPerSample
  	 << " bit-per-sample audio, which we don't handle\n";
    exit(1);
  }
     
  char* toAddr = argv[3];
  const unsigned short toPort = atoi(argv[4]);
  const unsigned short rtcpPortNumSink = toPort+1;
  const unsigned char ttlSink = 255;
  const Port rtpPortSink(toPort);
  const Port rtcpPortSink(rtcpPortNumSink);
  
  // Create 'groupsocks' for RTP and RTCP:
  struct in_addr destinationAddress;
  destinationAddress.s_addr = our_inet_addr(toAddr);
    
  sessionState.rtpGroupsock
    = new Groupsock(*env, destinationAddress, toPort, ttlSink);
  sessionState.rtpGroupsock->multicastSendOnly(); // we're a SSM source
  sessionState.rtcpGroupsock
    = new Groupsock(*env, destinationAddress, toPort, ttlSink);
  sessionState.rtcpGroupsock->multicastSendOnly(); // we're a SSM source
  
  // Create an appropriate audio RTP sink (using "SimpleRTPSink")
  // from the RTP 'groupsock':
  sessionState.sink
    = SimpleRTPSink::createNew(*env, sessionState.rtpGroupsock,
			       rtpPayloadFormat, samplingFrequency,
			       "audio", mimeType, 1);
  
  // Create (and start) a 'RTCP instance' for this RTP sink:
  gethostname((char*)CNAME, maxCNAMElen);
  CNAME[maxCNAMElen] = '\0'; // just in case
  sessionState.rtcpInstance
    = RTCPInstance::createNew(*env, sessionState.rtcpGroupsock,
			      estimatedSessionBandwidth, CNAME,
			      sessionState.sink, NULL /* we're a server */,
			      True /* we're a SSM source*/);
  // Note: This starts RTCP running automatically

  // Create and start a RTSP server to serve this stream:
  sessionState.rtspServer = RTSPServer::createNew(*env, 7070);
  if (sessionState.rtspServer == NULL) {
    *env << "Failed to create RTSP server: " << env->getResultMsg() << "\n";
    exit(1);
  }
  
  ServerMediaSession* sms
    = ServerMediaSession::createNew(*env, "Transcoder", "L16-8K-Mono -> PCMu-8K-Mono",
				    "Session streamed by \"L16ToPCMUTranscoder\"", True/*SSM*/);
  sms->addSubsession(PassiveServerMediaSubsession::createNew(*sessionState.sink, sessionState.rtcpInstance));
  sessionState.rtspServer->addServerMediaSession(sms);
  
  // ************ START RECEIVING AND SENDING *******************

  // Finally, start receiving the multicast stream:
  *env << "\nBegin receiving multicast stream at address "<< fromAddr << " port "<< fromPort<<"\n";
  sessionState.sink->startPlaying(*sessionState.source, afterPlaying, NULL);
  
  // Start streaming received rtp packets 
  char* url = sessionState.rtspServer->rtspURL(sms);
  *env << "Play this stream using the URL \"" << url << "\"\n";
  *env << "Or tune in via multicast address " <<toAddr<<"/"<<toPort<<"\n";
  delete[] url;
  
  env->taskScheduler().doEventLoop(); // does not return
  
  return 0; // only to prevent compiler warning
}

void afterPlaying(void* /*clientData*/) {
  *env << "...done receiving\n";

  // End by closing the media:
  Medium::close(sessionState.rtcpInstance); // Note: Sends a RTCP BYE
  Medium::close(sessionState.sink);
  Medium::close(sessionState.source);
}
