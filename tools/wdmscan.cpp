
#include <strmif.h>
#include <uuids.h>
#include <stdio.h>
#include <atlconv.h>
#include <dshow.h>   // DirectShow
#include <atlbase.h> // DirectShow



static int NUM_DEVS = 20;
int debug=0;

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



class DirectShowScanner {
   public:      
      DirectShowScanner();
      ~DirectShowScanner();
};

DirectShowScanner::DirectShowScanner() {
   ICreateDevEnum *pDevEnum      = 0;
   int             hr;
   
   // Initialize the COM subsystem
   CoInitialize(NULL);

   // Create a helper object to find the capture device.
   hr = CoCreateInstance(CLSID_SystemDeviceEnum, NULL, CLSCTX_INPROC_SERVER, IID_ICreateDevEnum, (LPVOID*)&pDevEnum);
   if( pDevEnum == 0 )
	   return;

   IEnumMoniker						*pEnum    = 0;
   IMoniker							*pMoniker = 0;
   IPropertyBag						*pPropBag = 0;
   VARIANT							varName;
   CLSID							clsid;
   IAMCrossbar						*pXBar    = NULL;
   long								input     = -1;
   long								output    = -1;
   long								related;
   long								pinType;    
   char								*ports[10];
   int								numports = 0;
   int								devNum;
   char								nameBuf[80];
   CComPtr<IGraphBuilder>			pGraph_;
   CComPtr<ICaptureGraphBuilder2>   pBuild_;


   // Set up filter graph builder and filter graph
   CoCreateInstance(CLSID_CaptureGraphBuilder2, NULL, CLSCTX_INPROC_SERVER,
                         IID_ICaptureGraphBuilder2, (void **)&pBuild_);
   hr = CoCreateInstance(CLSID_FilterGraph, NULL, CLSCTX_INPROC_SERVER,
                         IID_IGraphBuilder, (void **)&pGraph_);
   hr = pBuild_->SetFiltergraph(pGraph_);

   // Get an enumerator over video capture filters
   hr = pDevEnum->CreateClassEnumerator(CLSID_VideoInputDeviceCategory, &pEnum, 0);
   if(debug==2) printf("post CreateClassEnumerator\n");


   if( pEnum == 0 )
	   return;
 
   // Get the capture filter for each device installed, up to NUM_DEVS devices
   for( devNum=0; devNum < NUM_DEVS; ++devNum) {
      if ( pEnum->Next(1, &pMoniker, NULL) == S_OK ) {

         hr = pMoniker->BindToStorage(0, 0, IID_IPropertyBag, (void **)&pPropBag);
		 if(debug==2) printf("post BindToStorage\n");
         VariantInit(&varName);
         hr = pPropBag->Read(L"FriendlyName", &varName, 0);

		 // Need this macro in atlconv.h to go from bStr to char* - msp
         USES_CONVERSION;
         strcpy(nameBuf, W2A(varName.bstrVal));

		 IBaseFilter *pCap = NULL;
		 hr = pMoniker->BindToObject(0, 0, IID_IBaseFilter, (void**)&pCap);
		 hr = pGraph_->AddFilter(pCap, L"VicCaptureFilter");
		 pCap->GetClassID(&clsid);
		 if (IsEqualGUID(clsid,CLSID_VfwCapture)) {
            //fprintf(stderr,"discarding an apparent VFW device= %s\n", nameBuf);
			continue;
         }

		 if(debug==2) printf("pre FindInterface\n");

		 // Find ports on this device
		 numports = 0;
		 pXBar = 0;
         hr = pBuild_->FindInterface(&LOOK_UPSTREAM_ONLY, NULL, pCap, IID_IAMCrossbar, 
                                     (void**)&pXBar);
		 if(debug==2) printf("post FindInterface: pXBar=%x\n", pXBar);
		 if(pXBar) {

			 hr = pXBar->get_PinCounts(&output, &input);
			 if(debug==2) printf("post get_PinCounts: output=%d input=%d\n", output,input);

			 if (debug)  printf("inputs %d\n", input);
			 for( int i = 0; i < input; ++i ) {
				 pXBar->get_CrossbarPinInfo(TRUE, i, &related, &pinType);
				 if (debug)  printf("input %d pintype %d\n", i, pinType);
				 if( pinType == PhysConn_Video_SVideo ) {
					ports[numports] = "S-Video";  numports++;
				 }
				 if( pinType == PhysConn_Video_Composite ) {
					 ports[numports] = "Composite"; numports++;
				 }
			 }
		 }
		 else {
			 ports[numports] = "external-in"; numports++;
		 }

		 // Print the list of ports
		 printf("%s",nameBuf);
		 for(int i=0; i<numports; i++ )
			 printf(",%s", ports[i]);
	     printf("\n");

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

int main(int argc, char **argv)
{
  for(int i=0; i<argc; i++) {
	  if(!strcmp(argv[i],"-d"))
		  debug++;
  }

  DirectShowScanner();

}
