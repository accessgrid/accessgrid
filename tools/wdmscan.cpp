
#include <strmif.h>
#include <uuids.h>
#include <stdio.h>
#include <atlconv.h>


static int NUM_DEVS = 20;


class DirectShowScanner {
   public:      
      DirectShowScanner();
      ~DirectShowScanner();
};


DirectShowScanner::DirectShowScanner() {
   ICreateDevEnum *pDevEnum      = 0;
   int             hr;
   int             devNum;
   char            nameBuf[80];
   
   // Initialize the COM subsystem
   CoInitialize(NULL);

   // Create a helper object to find the capture device.
   hr = CoCreateInstance(CLSID_SystemDeviceEnum, NULL, CLSCTX_INPROC_SERVER, IID_ICreateDevEnum, (LPVOID*)&pDevEnum);

   IEnumMoniker *pEnum    = 0;
   IMoniker     *pMoniker = 0;
   IPropertyBag *pPropBag = 0;
   VARIANT      varName;
   CLSID		clsid;

   if( pDevEnum == 0 )
	   return;
   
   // Get an enumerator over video capture filters
   hr = pDevEnum->CreateClassEnumerator(CLSID_VideoInputDeviceCategory, &pEnum, 0);
   //showErrorMessage(hr);

   if( pEnum == 0 )
	   return;
 
   // Get the capture filter for each device installed, up to NUM_DEVS devices
   for( devNum=0; devNum < NUM_DEVS; ++devNum) {
      if ( pEnum->Next(1, &pMoniker, NULL) == S_OK ) {

         hr = pMoniker->BindToStorage(0, 0, IID_IPropertyBag, (void **)&pPropBag);
         //showErrorMessage(hr);
         //debug_msg("propbag bound to storage ok= %d\n", hr);

         VariantInit(&varName);
         hr = pPropBag->Read(L"FriendlyName", &varName, 0);
         //showErrorMessage(hr);
         //debug_msg("friendly name read ok= %d\n", hr);

         // Need this macro in atlconv.h to go from bStr to char* - msp
         USES_CONVERSION;
         strcpy(nameBuf, W2A(varName.bstrVal));

         //debug_msg("DirectShowScanner::DirectShowScanner():  found nameBuf/FriendlyName=%s\n", nameBuf);

		 IBaseFilter *pCap = NULL;
		 hr = pMoniker->BindToObject(0, 0, IID_IBaseFilter, (void**)&pCap);
		 pCap->GetClassID(&clsid);
		 if (!IsEqualGUID(clsid,CLSID_VfwCapture))
		 {
			printf("%s\n", nameBuf);
         } else {
            //fprintf(stderr,"discarding an apparent VFW device= %s\n", nameBuf);
         }

         VariantClear(&varName);
         pPropBag->Release();
      }
   }

   // Release these objects so COM can release their memory
   pMoniker->Release();
   pEnum->Release();
   pDevEnum->Release();
}

DirectShowScanner::~DirectShowScanner()
{

}

int main(char **argv, int argc)
{
  DirectShowScanner();

}
