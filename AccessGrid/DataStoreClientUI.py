from AccessGrid import DataStoreClient

from wxPython.wx import *

class DataStoreFileChooser:
    def __init__(self, datastoreClient, pattern = "*", message = "", caption = ""):

        self.datastoreClient = datastoreClient
        
        filenames = self.datastoreClient.QueryMatchingFiles(pattern)
        print "Got filenames ", filenames
        self.dlg = wxSingleChoiceDialog(None, message, caption, filenames)

    def run(self):
        ret = self.dlg.ShowModal()

        print "Returned ", ret

        file = None

        if ret == wxID_OK:
            file = self.dlg.GetStringSelection()

        self.dlg.Destroy()
        return file

if __name__ == "__main__":

    app = wxPySimpleApp()

    url = "https://lorax.mcs.anl.gov:8000/Venues/default"
    dsc = DataStoreClient.GetVenueDataStore(url)

    dlg = DataStoreFileChooser(dsc, "*.ppt", "Choose a powerpoint file")

    file = dlg.run()
    print "You chose ", file

    dlg = DataStoreFileChooser(dsc, "*", "Choose any file", "Pick one")

    file = dlg.run()
    print "You chose ", file
