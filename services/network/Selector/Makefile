OBJS = VideoSelectorGUI.o rtpforward.o
LDFLAGS = -I/usr/include -I/usr/X11R6/include -I/home/lefvert/common/src
CFLAGS = -L/usr/lib -L/usr/X11R6/lib -L/home/lefvert/common/src -lfltk -lm -lXext -lX11 -lsupc++ -luclmmbase -lpthread


all: Selector

Selector: SelectorGUI.o rtpforward.o
	gcc SelectorGUI.o rtpforward.o $(CFLAGS) -o Selector

SelectorGUI.o: SelectorGUI.cpp rtpforward.h
	gcc $(LDFLAGS) -c SelectorGUI.cpp

rtpforward.o: rtpforward.c rtpforward.h
	gcc $(LDFLAGS) -c rtpforward.c

clean:
	/bin/rm -f prog rtpforward.o SelectorGUI.o Selector