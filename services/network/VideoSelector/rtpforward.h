
struct participant {
  unsigned long ssrc;
  char* name;
};

static struct participant*
GetParticipants();

void
SetAllowedParticipant(unsigned long allowedParticipant);

//void start(char* fromAddr, int fport, char* toAddr, int tport);
void* start(void* test);
