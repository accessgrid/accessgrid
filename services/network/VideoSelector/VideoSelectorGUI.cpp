
#include <stdlib.h>
#include <stdio.h>
#include <FL/Fl.H>
#include <FL/Fl_Window.H>
#include <FL/Fl_Button.H>
#include <FL/Fl_Return_Button.H>
#include <FL/Fl_Repeat_Button.H>
#include <FL/Fl_Check_Button.H>
#include <FL/Fl_Light_Button.H>
#include <FL/Fl_Round_Button.H>
#include <FL/Fl_Tooltip.H>
#include <FL/Fl_Input.H>
#include <FL/Fl_Scroll.H>

extern "C"{
#include "rtpforward.h"
}

#include "pthread.h"

//extern void start(char* fromAddr, int fport, char* toAddr, int tport);
extern void* start(void* test);

extern void
SetAllowedParticipant(unsigned long allowedParticipant);

int participants = 20;

Fl_Window *window;

class VideoSelector{
private:
  
public:
  char* test;
  void create(int argc, char** argv);
  void applyCB(Fl_Widget* w);
  void closeCB(Fl_Widget* w);
  static void static_applyCB(Fl_Widget *w, void* v){((VideoSelector*)v)->applyCB(w);}
  static void static_closeCB(Fl_Widget *w, void* v){((VideoSelector*)v)->closeCB(w);}
};

void VideoSelector::create(int argc, char** argv){
  Fl_Window *window = new Fl_Window(400,460);
  int x = 80;
  int y = 10;
  char* participantList[100];
  test = "this is a member";
  
  if (argc != 5) {
    printf("Usage: rtpforward address port address port\n");
    exit(-1);
  }

  // Actually get the participant info.
  //participants = GetParticipants()

  window->size_range(400, 400, 600, 600);
    
  // Sending multicast address.
  new Fl_Input(x + 40, y, 120, 30, "Receive Address:");
  x = x + 220;
  new Fl_Input(x, y, 50, 30, " Port:");
  y = y + 40;
  x = 80;
  
  // Receiving multicast address.
  new Fl_Input(x + 40, y, 120, 30, "Send Address:");
  x = x + 220;
  new Fl_Input(x, y, 50, 30, " Port:");
  
  // Participant buttons.
  y = y + 40;
  x = 10;
  int dx = 20; 
  int i = 0;
  
  // Scroll window containing participants
  Fl_Scroll *swindow = new Fl_Scroll(0, y, 400, 300);
  
  for(i; i < participants; i ++){
    new Fl_Check_Button(x, y, 130, 30, "Susanne L Lefvert");
    y = y + dx;
  }

  swindow->end();

  // Apply and close button.
  y = 400;
  x = 150; 
  Fl_Button *applyButton = new Fl_Button(150, y, 60, 40, "Apply");
  Fl_Button *closeButton = new Fl_Button(x + 70, y, 60, 40, "Close");
  
  // Callbacks.
  applyButton->callback(static_applyCB, this);
  closeButton->callback(static_closeCB, this);

  window->end();
  window->show(argc,argv);

  pthread_t t;

  // Maybe start this in a thread....then call it from callbacks.
  // pthread_create(&t, NULL, start, argv[1], atoi(argv[2]), argv[3], atoi(argv[4]));
  pthread_create(&t, NULL, start, (void*)1);
}



/*
------------------------------------------------
  Callbacks
------------------------------------------------
*/

/*
  Called when you press the apply button.
  Sets allowed participant in video selector service.
*/ 
void VideoSelector::applyCB(Fl_Widget *w){
  printf("apply\n");
  SetAllowedParticipant(1097459989l);
}
/*
  Called when you press the apply button.
  Closes the window.
*/
void VideoSelector::closeCB(Fl_Widget *w){
  exit(0);
}

/*
  ------------------------------------------------
*/

int main(int argc, char ** argv) {
  VideoSelector v;
  v.create(argc, argv);
  return Fl::run();
  pthread_exit(NULL);
}

