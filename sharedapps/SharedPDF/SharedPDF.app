[application]
name = Shared PDF
mimetype = application/x-ag-shared-pdf
extension = sharedpdf
files = SharedPDF.py

[commands]
Open = %(python)s SharedPDF.py -v %(venueUrl)s -a %(appUrl)s

