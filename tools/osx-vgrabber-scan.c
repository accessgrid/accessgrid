/*
 * Uses Quicktime's SGGetChannelDeviceList() to list the video capture devices
 * and corresponding inputs to stdout.
 * Each output line is in the following CSV format:
 * devicename,input1,input2,...,inputn
 */

#include <Carbon/Carbon.h>
#include <QuickTime/QuickTime.h>

#include <stdio.h>
#include <stdlib.h>

/*
 * Prints a string in the same way Excel does for CSV fields
 */
void printcsv(const char *str) {
	if (strchr(str, ',')) {
		if (strchr(str, '"')) {
			printf("\"\"%s\"\"", str);
		} else {
			printf("\"%s\"", str);
		}
	} else {
		if (strchr(str, '"')) {
			printf("\"%s\"", str);
		} else {
			printf("%s", str);
		}
	}
}

int main(int argc, char* argv[])
{
	SeqGrabComponent seqGrab;
	SGChannel sgchanVideo;
	SGDeviceList sgdeviceList;
	OSErr err = noErr;
	int i, j;

	seqGrab = OpenDefaultComponent(SeqGrabComponentType, 0);
	if (seqGrab != NULL)
		err = SGInitialize(seqGrab);
	if (err == noErr)
		err = SGSetDataRef(seqGrab, 0, 0, seqGrabDontMakeMovie);
	err = SGNewChannel(seqGrab, VideoMediaType, &sgchanVideo);
	if (err != noErr) {
		// clean up on failure
		SGDisposeChannel(seqGrab, sgchanVideo);
		return -1;
	}
	if (err == noErr) {
		SGGetChannelDeviceList(sgchanVideo, sgDeviceListIncludeInputs, &sgdeviceList);
		char dev_str[64];
		char port_str[64];
		for (i = 0; i <(*sgdeviceList)->count; i++) {
			// ignore devices that are currently unavailable
			if ((sgDeviceNameFlagDeviceUnavailable &(*sgdeviceList)->entry[i].flags) == 0) {
				p2cstrcpy(dev_str, (*sgdeviceList)->entry[i].name);
				// print capture device's name
				printcsv(dev_str);
				if ((*sgdeviceList)->entry[i].inputs != NULL) {
					// print inputs
					for(j = 0; j <(*(((*sgdeviceList)->entry[i]).inputs))->count; j++) {
						p2cstrcpy(port_str,(*(((*sgdeviceList)->entry[i]).inputs))->entry[j].name);
						printf(",");
						printcsv(port_str);
					}
				}
				printf("\n");
			}
		}
	}

	SGDisposeDeviceList(seqGrab, sgdeviceList);
	SGDisposeChannel(seqGrab, sgchanVideo);
	CloseComponent(seqGrab);

	return 0;
}

