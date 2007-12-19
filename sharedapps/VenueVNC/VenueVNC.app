[application]
name = VenueVNC
mimetype = application/x-ag-venuevnc
extension = venuevnc
files = VenueVNCClient.py, vncviewer.exe
startable = 0

[commands]
Open = %(python)s VenueVNCClient.py %(appUrl)s

