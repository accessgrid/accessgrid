OBJS = VideoSelectorGUI.o rtpforward.o
LDFLAGS = -I/usr/include -I/usr/X11R6/include -I/home/lefvert/common/src 
CFLAGS = -L/usr/lib -L/usr/X11R6/lib -L/home/lefvert/common/src -lfltk -lm -lXext -lX11 -lsupc++ -luclmmbase -lpthread


all: Selector

Selector: VideoSelectorGUI.o rtpforward.o
	gcc VideoSelectorGUI.o rtpforward.o $(CFLAGS) -o Selector

VideoSelectorGUI.o: VideoSelectorGUI.cpp rtpforward.h
	gcc $(LDFLAGS) -c VideoSelectorGUI.cpp

rtpforward.o: rtpforward.c rtpforward.h
	gcc $(LDFLAGS) -c rtpforward.c

clean:
	/bin/rm -f prog rtpforward.o VideoSelectorGUI.o