
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

#include "pthread.h"
#include <string.h>

extern "C"{
#include "rtpforward.h"
}

/*
  functions from rtpforward.h
*/
extern void* start(void* addr);
extern void SetAllowedParticipant(unsigned long allowedParticipant);
int GetParticipants(struct participant* participantList);


/*
------------------------------------------------
   SelectorGUI
------------------------------------------------
*/
class  SelectorGUI{
private:
  
public:
  char* ssrcList[100];
  struct participant pList[100];
  int x;
  int y;
  Fl_Scroll *swindow;
  char* test;
  void update();
  void create();
  void applyCB(Fl_Widget* w);
  void selectCB(Fl_Widget* w, void* data);
  void closeCB(Fl_Widget* w);
  void idleCB();
  static void static_applyCB(Fl_Widget *w, void* v){(( SelectorGUI*)v)->applyCB(w);}
  static void static_selectCB(Fl_Widget *w, void* v){(( SelectorGUI*)v)->selectCB(w, v);}
  static void static_closeCB(Fl_Widget *w, void* v){(( SelectorGUI*)v)->closeCB(w);}
  static void static_idleCB(void* v){(( SelectorGUI*)v)->idleCB();}
};

/*
  Called everytime we click the refresh button. This will request all participants
  and update the UI.
 */ 
void SelectorGUI::update(){
  int x = 40;
  int y = 10;
  int dy = 20; 
  int i = 0;
  int len = 0;
  
  swindow->clear();
  swindow->redraw();
  swindow->begin();
  
  len = GetParticipants(pList);
  
  for(i; i < len; i ++){
    ssrcList[i] = (char*)pList[i].ssrc;
    Fl_Check_Button* b = new Fl_Check_Button(x, y, 300, 30, pList[i].name);
    b->callback(static_selectCB, (void*) pList[i].ssrc);
    b->type(102);
    y = y + dy;
  }
  swindow->end();
  swindow->redraw();
}

/*
  Initial creation of ui components.
*/
void SelectorGUI::create(){
  Fl_Window *window = new Fl_Window(400,460,"Stream Selector");
  x = 80;
  y = 10;
  char* participantList[100];
  test = "this is a member";
   
  window->size_range(400, 400, 600, 600);

  // Scroll window containing participants
  swindow = new Fl_Scroll(0, y, 400, 380);
  Fl_Group* o = new Fl_Group(x, y, 380, 280);
  o->box(FL_THIN_UP_FRAME);
  
  // Add buttons to scroll window
  update();
  
  // Apply and close button.
  y = 400;
  x = 150; 
  Fl_Button *applyButton = new Fl_Button(150, y, 60, 40, "Refresh");
  Fl_Button *closeButton = new Fl_Button(x + 70, y, 60, 40, "Close");
  
  // Callbacks.
  applyButton->callback(static_applyCB, this);
  closeButton->callback(static_closeCB, this);
  
  window->end();
  window->show();
    
 
  // For some reason, the idle callback causes a segfault.
  //Fl::add_idle(static_idleCB);
}

/*
------------------------------------------------
  Callbacks
------------------------------------------------
*/

/*
  Called when you press the refresh button.
  Sets allowed participant in selector service.
*/ 
void SelectorGUI::applyCB(Fl_Widget *w){
  update();
}

/*
  Called whey you select a participant. Participants
  stream will be forwarded to new multicast address.
*/
void SelectorGUI::selectCB(Fl_Widget *w, void* data){
  unsigned int d = (unsigned int) data;
  SetAllowedParticipant(d);
}

/*
  Called when you press the apply button.
  Closes the window.
*/
void SelectorGUI::closeCB(Fl_Widget *w){
  exit(0);
}

void SelectorGUI::idleCB(){
  update();
}

/*
  ------------------------------------------------
  Main 
  ------------------------------------------------
*/

int main(int argc, char ** argv) {
  // Parse arguments
  if (argc != 5) {
    printf("Usage: ./Selector from_address from_port to_address to_port\n");
    exit(-1);
  }

  struct address a;
  a.fromAddr = argv[1];
  a.fport = atoi(argv[2]);
  a.toAddr = argv[3];
  a.tport = atoi(argv[4]);
  
  // Start packet forwarding.
  pthread_t t;
  pthread_create(&t, NULL, start, (void*)&a);
  
  // Start the program
  SelectorGUI v;
  v.create();
    
  return Fl::run();
  pthread_exit(NULL);
}

