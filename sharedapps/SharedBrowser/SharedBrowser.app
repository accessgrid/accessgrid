[application]
name = Shared Browser
mimetype = application/x-ag-shared-browser
extension = sharedbrowser
files = SharedBrowser.py

[commands]
Join = %(python)s SharedBrowser.py -a %(appUrl)s
 
