[application]
name = Shared Question Tool
mimetype = application/x-ag-question-tool
extension = sqtool
files = SharedQuestionTool.py, ObserverPattern.py

[commands] 
Open = %(python)s SharedQuestionTool.py -a %(appUrl)s
Open for All Participants = %(python)s SharedQuestionTool.py -a %(appUrl)s
