#include "windows.h"
#include "vfw.h"

int main(int argc, char *argv[]) {
  char deviceName[80];
  char deviceVersion[100];
  int index;

  for (index = 0 ; index < 9; index++) 
    {
      if (capGetDriverDescription(index,
				  (LPSTR)deviceName,
				  sizeof(deviceName),
				  (LPSTR)deviceVersion,
				  sizeof(deviceVersion)))
        printf("%s\n", deviceName);
    }

  return 0;
}
