[application]
name = Shared Presentation
mimetype = application/x-ag-shared-presentation
extension = sharedpresentation
files = SharedPresentation.py, ImpressViewer.py

[commands]
Open = %(python)s SharedPresentation.py -v %(venueUrl)s -a %(appUrl)s -c %(connectionId)s

