#-----------------------------------------------------------------------------
# Name:        NodeSetupWizard.py
# Purpose:     Roles Management UI
#
# Author:      Susanne Lefvert 
#
#
# Created:     2003/08/07
# RCS_ID:      $Id: AuthorizationUI.py,v 1.3 2004-02-26 14:50:37 judson Exp $ 
# Copyright:   (c) 2003
# Licence:     See COPYING.txt
#-----------------------------------------------------------------------------
"""
"""
__revision__ = "$Id: AuthorizationUI.py,v 1.3 2004-02-26 14:50:37 judson Exp $"
__docformat__ = "restructuredtext en"

from wxPython.wx import *
from AccessGrid.UIUtilities import MessageDialog, ErrorDialog
from wxPython.wizard import *

from AccessGrid import Toolkit
from AccessGrid.Platform import isWindows, isLinux
from AccessGrid.ClientProfile import ClientProfileCache
from AccessGrid.Security.AuthorizationManager import AuthorizationManagerIW
       
class AuthorizationUIPanel(wxPanel):
    '''
    This class shows a tree of people structured in roles.
    '''
    def __init__(self, parent, id, url):
        wxPanel.__init__(self, parent, id, wxDefaultPosition, \
			 size = wxSize(400,200), style = wxRAISED_BORDER)

        self.url = url
        self.authClient = AuthorizationManagerIW(self.url)

        # Stores all tree ids for roles (key = role, value = tree id)
        self.headingDict = dict()

        # Stores the tree structure
        for role in self.authClient.ListRoles():
            self.rolesDict[role] = self.authClient.ListSubjectInRole(role)
        
        # Adjust tree for different platforms 
        if isWindows():
            self.tree = wxTreeCtrl(self, wxNewId(), wxDefaultPosition, 
                                   wxDefaultSize, style = wxTR_HAS_BUTTONS |
                                   wxTR_NO_LINES|wxTR_EDIT_LABELS )
            
            
        elif isLinux():
            self.tree = wxTreeCtrl(self, wxNewId(), wxDefaultPosition, 
                                   wxDefaultSize, style = wxTR_HAS_BUTTONS |
                                   wxTR_NO_LINES | wxTR_HIDE_ROOT| wxTR_EDIT_LABELS )

        # Create ui componentes
        self.newRoleButton = wxButton(self, wxNewId(), "New Role")
        self.newRoleButton.Enable(false)
        self.newPersonButton = wxButton(self, wxNewId(), "Add People")
        self.deleteButton = wxButton(self, wxNewId(), "Delete")
        self.renameButton = wxButton(self, wxNewId(), "Rename")

        # default to localhost default venue 
        self.venueUri = "https://localhost:8000/Venues/default"

        self.dragItem = None
        self.copyItem = None

        self.__setMenus()
        self.__setEvents()
        self.__initTree()
        self.__layout()

    def __initTree(self):
        '''
        Adds items to the tree
        '''
        # Add items to the tree
        self.root = self.tree.AddRoot("", -1, -1)

        for role in self.rolesDict.keys():
            # Add role
            roleId = self.tree.AppendItem(self.root, role, -1, -1)
            self.headingDict[role] = roleId
            self.tree.SetItemBold(roleId)

            # For each role, add people/groups
            for person in self.rolesDict[role]:
                self.tree.AppendItem(roleId, person, -1, -1)

            # Sort the tree
            if self.tree.GetChildrenCount(roleId)> 0:
                self.tree.SortChildren(roleId)

        if self.tree.GetChildrenCount(self.root)> 0:
            self.tree.SortChildren(self.root)
            
    def __setEvents(self):
        '''
        Set events for this panel
        '''
        EVT_RIGHT_DOWN(self.tree, self.OnRightClick)
        EVT_BUTTON(self,self.newRoleButton.GetId(), self.NewRole)
        EVT_BUTTON(self,self.newPersonButton.GetId(), self.NewPerson)
        EVT_BUTTON(self, self.deleteButton.GetId(), self.Delete)
        EVT_BUTTON(self, self.renameButton.GetId(), self.Rename)
        EVT_TREE_END_LABEL_EDIT(self.tree, self.tree.GetId(), self.EndRename)
        EVT_TREE_BEGIN_DRAG(self.tree, self.tree.GetId(), self.BeginDrag)
        EVT_TREE_END_DRAG(self.tree, self.tree.GetId(), self.EndDrag)
                
        EVT_MENU(self, self.ID_ROLE_ADDPERSON, self.NewPerson)
        #EVT_MENU(self, self.ID_ROLE_ADDROLE, self.NewRole)
        #EVT_MENU(self, self.ID_ROLE_DELETE, self.Delete)
        #EVT_MENU(self,self.ID_ROLE_RENAME, self.Rename)
        #EVT_MENU(self, self.ID_ROLE_PASTE, self.Paste)

        EVT_MENU(self, self.ID_PERSON_ADDPERSON, self.NewPerson)
        EVT_MENU(self, self.ID_PERSON_ADDROLE, self.NewRole)
        EVT_MENU(self, self.ID_PERSON_DELETE, self.Delete)
        EVT_MENU(self,self.ID_PERSON_RENAME, self.Rename)
        EVT_MENU(self,self.ID_PERSON_COPY, self.Copy)
        EVT_MENU(self,self.ID_PERSON_PASTE, self.Paste)

    def __participantInRole(self, roleId, person):
        '''
        Check to see if person/group is added to a role already
        '''
        role = self.tree.GetItemText(roleId)
        list = self.rolesDict[role]
                       
        return person in list        
                   
    def __rmParticipantFromDict(self, role, person):
        '''
        Remove a participant from the role dictionary
        '''
        list = self.rolesDict[role]
        
        i = 0
        for item in list:
            if item == person:
                del list[i]
                return
            else:
                i = i + 1
                
        self.rolesDict[role] = list

    def __addParticipantToDict(self, role, person):
        '''
        Add a participant to the role dictionary
        '''
        list = self.rolesDict[role]
        list.append(person)
        self.rolesDict[role] = list

    def __isRole(self, treeId):
        '''
        Check to see if a tree id is a role
        '''
        return self.tree.GetItemText(treeId) in self.rolesDict.keys()
         
    def __setMenus(self):
        '''
        Initiate menues that are shown when user right-clicks a tree item
        '''
        self.ID_ROLE_ADDPERSON = wxNewId()
        #self.ID_ROLE_ADDROLE = wxNewId()
        #self.ID_ROLE_RENAME = wxNewId()
        #self.ID_ROLE_PASTE = wxNewId()
        #self.ID_ROLE_DELETE = wxNewId()

        self.ID_PERSON_ADDPERSON = wxNewId()
        self.ID_PERSON_ADDROLE = wxNewId()
        self.ID_PERSON_RENAME = wxNewId()
        self.ID_PERSON_COPY = wxNewId()
        self.ID_PERSON_PASTE = wxNewId()
        self.ID_PERSON_DELETE = wxNewId()
       

        # Menu when user clicks on a role item
        
        self.roleMenu = wxMenu()
        self.roleMenu.Append(self.ID_ROLE_ADDPERSON,"Add People...",
                                   "Add participant to this role")
        #self.roleMenu.Append(self.ID_ROLE_ADDROLE,"New Role...",
        #                           "Add new role")
        #self.roleMenu.AppendSeparator()
        #self.roleMenu.Append(self.ID_ROLE_RENAME,"Rename",
        #                           "Change name of this role")
        #self.roleMenu.Append(self.ID_ROLE_PASTE,"Paste",
        #                           "Paste copied participant to this role")
        #self.roleMenu.AppendSeparator()
        #self.roleMenu.Append(self.ID_ROLE_DELETE,"Delete",
        #                           "Remove this role from venue")
      

        # Menu when user clicks on a participant/group
        
        self.personMenu = wxMenu()
        self.personMenu.Append(self.ID_PERSON_ADDPERSON,"New Participant",
                                   "New participant")
        self.personMenu.Append(self.ID_PERSON_ADDROLE,"New Role",
                                   "Add new role")
        self.personMenu.AppendSeparator()
        self.personMenu.Append(self.ID_PERSON_RENAME,"Rename",
                                   "Rename this participant")
        self.personMenu.Append(self.ID_PERSON_COPY,"Copy",
                                   "Copy this participant")

        self.personMenu.Append(self.ID_PERSON_PASTE,"Paste",
                                   "Paste")
        self.personMenu.AppendSeparator()
        self.personMenu.Append(self.ID_PERSON_DELETE,"Delete",
                                   "Remove this role from venue")
       
    def __layout(self):
        '''
        Handles ui layout
        '''
        sizer = wxBoxSizer(wxVERTICAL)

        box = wxBoxSizer(wxHORIZONTAL)
        box.Add(self.newRoleButton, 1)
        box.Add(self.newPersonButton, 1)
        box.Add(self.deleteButton, 1)
        box.Add(self.renameButton, 1)

        sizer.Add(box, 0, wxEXPAND|wxLEFT|wxRIGHT, 5)
        sizer.Add(self.tree, 1, wxEXPAND| wxALL, 5)

        self.SetAutoLayout(1)
        self.SetSizer(sizer)
        self.Layout()

    def Copy(self, event):
        '''
        Is called when user selects to copy an item
        '''
        # Store the copied item so we can paste it
        self.copyItem = self.tree.GetSelection()
       
    def Paste(self, event):
        '''
        Paste last copied item
        '''
        if self.copyItem and self.copyItem.IsOk():
            text = self.tree.GetItemText(self.copyItem)
            selectedItem = self.tree.GetSelection()

            if self.__isRole(selectedItem):
                # If selected item is a role, paste the copied item
                # to that role
                parent = selectedItem
            else:
                # If selected item is a participant, paste copied item to
                # its parent (a role)
                parent = self.tree.GetItemParent(selectedItem)

            # Paste the item if it is not already added to the role
            if not self.__participantInRole(parent, text):
                self.tree.AppendItem(parent, text)

                # Add copied item to dictionary
                heading = self.tree.GetItemText(parent)
                self.__addParticipantToDict(heading, text)
            
            
    def BeginDrag(self, event):
        '''
        Is called when a user starts to drag a tree item
        '''
        self.dragItem = self.tree.GetSelection()
        
        # Need to call Allow to get an EVT_TREE_END_DRAG event
        event.Allow()
        
    def EndDrag(self, event):
        '''
        Is called when a user stops dragging a tree item
        '''
        selectedItem = event.GetItem()
        
        if self.dragItem.IsOk() and selectedItem.IsOk():
            text = self.tree.GetItemText(self.dragItem)
            oldHeading = None
            
            if self.__isRole(self.dragItem):
                # This is a role and we don't want to drag it
                return

            else:
                # We are dragging a participant/group
                oldHeadingId = self.tree.GetItemParent(self.dragItem)
                oldHeading = self.tree.GetItemText(oldHeadingId) 

            if self.__isRole(selectedItem):
                # If selected item is a role, add the dragged item
                # to that role
                parent = selectedItem

            else:
                # If selected item is a participant add it to the
                # same role as that participant
                parent = self.tree.GetItemParent(selectedItem)

            # Get the role we want to add the participant/group to
            heading = self.tree.GetItemText(parent)

            #If participant is not already present in the role, add it
            if not self.__participantInRole(parent, text):
                self.tree.Delete(self.dragItem)
                self.tree.AppendItem(parent, text)

                # Delete drag item
                self.__rmParticipantFromDict(oldHeading, text)

                # Add drag item
                self.__addParticipantToDict(heading, text)
                           
    def NewRole(self, event):
        print '---new role'
                
    def NewPerson(self, event):
        '''
        Adds a new person to the tree
        '''
        
        selectedItem = self.tree.GetSelection()
        activeRole = self.rolesDict.keys()[0]
        
        if selectedItem.IsOk() and selectedItem != self.root:
            
            if self.__isRole(selectedItem):
                # If selected item is a role
                activeRole = self.tree.GetItemText(selectedItem)
            else:
                # If selected item is a participant
                parent = self.tree.GetItemParent(selectedItem)
                activeRole = self.tree.GetItemText(parent)

        # Open the dialog with selected role in the combo box
        addPeopleDialog = AddPeopleDialog(self, -1, "Add People",
                                          self.venueUri,
                                          self.rolesDict,
                                          activeRole)

        if addPeopleDialog.ShowModal() == wxID_OK:
            # Get new role configuration
            self.rolesDict = addPeopleDialog.GetInfo()
            
            # Clear the tree
            for role in self.headingDict.keys():
                self.tree.DeleteChildren(self.headingDict[role])

            # Insert items in tree
            for role in self.rolesDict.keys():
                for item in self.rolesDict[role]:
                    self.tree.AppendItem(self.headingDict[role], item)    

            # Upload Roles
            for role in self.rolesDict.keys():
                self.authClient.SetSubjectInRole(role, roleDictionary[role])

    def Delete(self, event):
        '''
        Remove an item from the tree
        '''
        treeId = self.tree.GetSelection()
       
        if treeId.IsOk() and treeId != self.root:
            text = self.tree.GetItemText(treeId)

            if self.__isRole(treeId):
                MessageDialog(self, "Role can not be removed")
                return
            
            if treeId != self.root:
                message = wxMessageDialog(self, "Are you sure you want to delete '%s'?"%text,
                                          style = wxICON_QUESTION | wxYES_NO | wxNO_DEFAULT)
                
                if message.ShowModal() == wxID_YES:
                    # Remove participant
                    parentId = self.tree.GetItemParent(treeId)
                    heading = self.tree.GetItemText(parentId)
                    
                    # delete item from dictionary
                    self.__rmParticipantFromDict(heading, text)
                    
                    # delete item from tree
                    self.tree.Delete(treeId)
                        
                        
            else:
                MessageDialog(self, "Please select the participant you want to remove")

    def Rename(self, event):
        '''
        Is called when user wants to rename a participant/group
        '''
        treeId =  self.tree.GetSelection()

        if treeId.IsOk() and treeId != self.root:
           
            if self.__isRole(treeId):
                # Roles can not be modified yet
                MessageDialog(self, "Role can not be renamed")
                return
            
            self.tree.EditLabel(treeId)

        else:
            MessageDialog(self, "Please select the role or participant you want to rename")
            
    def EndRename(self, event):
        '''
        Is called when user finished renaming a participant/group
        '''
        treeId = self.tree.GetSelection()
        text = self.tree.GetItemText(treeId)
        roleId = self.tree.GetItemParent(treeId)
        role = self.tree.GetItemText(roleId)
        newText = event.GetLabel()

        # Remove the old participant/group from dictionary and add a new entry
        self.__rmParticipantFromDict(role, text)
        self.__addParticipantToDict(role, newText) 
            
    def OnRightClick(self, event):
        '''
        Is called when user right-clicks a tree item. Opens a menu.
        '''
        self.x = event.GetX()
        self.y = event.GetY()

        treeId, flag = self.tree.HitTest(wxPoint(self.x,self.y))
      
        if(treeId.IsOk()):
            self.tree.SelectItem(treeId)
            text = self.tree.GetItemText(treeId)

            if not self.__isRole(treeId):
                self.PopupMenu(self.personMenu,
                               wxPoint(self.x, self.y))
         
            else:
                self.PopupMenu(self.roleMenu,
                               wxPoint(self.x, self.y))
        
        
class AddPeopleDialog(wxDialog):
    '''
    Dialog for adding people to roles
    '''
    def __init__(self, parent, id, title, authMIW, infoDict=None,
                 selectedRole=""):
        wxDialog.__init__(self, parent, id, title,
                          style=wxDEFAULT_DIALOG_STYLE|wxRESIZE_BORDER)
        self.SetSize(wxSize(500, 450))
        self.authClient = authMIW
        self.infoDict = dict()
        self.rolesDict = dict()
        self.selectedRole = selectedRole
        
        if infoDict:
            self.infoDict = infoDict
        else:
            for r in self.authClient.ListRoles():
                self.infoDict[r.name] = self.authClient.ListSubjectsInRole(r.name)

        for role in self.authClient.ListRoles():
            self.rolesDict[role] = self.authClient.ListSubjectsInRole(role)

        self.pList = []

        # Now from our local cache
        c = ClientProfileCache()
        for p in c.loadAllProfiles():
            if p.GetDistinguishedName():
                self.pList.append(p.GetDistinguishedName().split('=')[-1])
                
        self.gList = self.authClient.ListRoles()
        
        self.dnTextCtrl = wxTextCtrl(self,-1, "")
        self.addButton1 = wxButton(self, wxNewId(), "Add >>",
                                   style = wxBU_EXACTFIT )
        self.list = wxListCtrl(self, wxNewId(),
                               style = wxLC_REPORT | wxLC_SORT_ASCENDING |
                               wxSUNKEN_BORDER |wxHSCROLL | wxLC_NO_HEADER )
        self.list.InsertColumn(0, "People:")
       
        self.addButton2 = wxButton(self, wxNewId(), "Add >>",
                                   style = wxBU_EXACTFIT)

        self.addList = wxListCtrl(self, wxNewId(),
                                  style = wxLC_REPORT | wxLC_SORT_ASCENDING |
                                  wxHSCROLL |wxSUNKEN_BORDER |wxLC_NO_HEADER)
        self.addList.InsertColumn(0, "")
        self.removeUserButton = wxButton(self, wxNewId(), "Remove User",
                                   style = wxBU_EXACTFIT)

        self.selections = wxComboBox(self, wxNewId(),
                                     style = wxCB_DROPDOWN | wxCB_READONLY,
                                     choices = self.infoDict.keys())
        
        self.AddPeople(self.pList)
        self.dnText = wxStaticText(self, -1,
                                   "Add person by distinguished name ")
        self.peopleText = wxStaticText(self, -1, "Add people from list ")
        self.dnText.SetFont(wxFont(wxDEFAULT, wxNORMAL, wxNORMAL, wxBOLD))

        self.okButton = wxButton(self, wxID_OK, "Ok")
        self.cancelButton =  wxButton(self, wxID_CANCEL, "Cancel")

        self.peopleText.SetFont(wxFont(wxDEFAULT, wxNORMAL, wxNORMAL, wxBOLD))
        self.selectedPersonId = -1
        self.__setEvents()
        self.__layout()

        if len(self.selectedRole) > 0:
            self.selections.SetValue(self.selectedRole)
            self.SelectNewRole(self.selectedRole)
        else:
            if self.selections.Number():
                nv = self.selections.GetString(0)
                self.selections.SetValue(nv)
                self.SelectNewRole(nv)
        
    def __layout(self):
        box = wxBoxSizer(wxHORIZONTAL)
        sizer = wxBoxSizer(wxVERTICAL)

        sizer.Add(10,10)
        tempSizer =  wxBoxSizer(wxHORIZONTAL)
        tempSizer.Add(self.dnText)
        
        tempSizer.Add(wxStaticLine(self, -1), 1, wxALIGN_CENTER)
        sizer.Add(tempSizer, 0, wxEXPAND)
        sizer.Add(10,10)

        tempSizer = wxBoxSizer(wxHORIZONTAL)
        tempSizer.Add(wxStaticText(self, -1, "Name: "), 0, wxALIGN_CENTER)
        tempSizer.Add(self.dnTextCtrl, 1, wxRIGHT, 2)
        tempSizer.Add(self.addButton1, 0, wxALIGN_CENTER | wxLEFT, 5)
        sizer.Add(tempSizer, 0, wxEXPAND)

        sizer.Add(10,10)
        tempSizer =  wxBoxSizer(wxHORIZONTAL)
        tempSizer.Add(self.peopleText)
        tempSizer.Add(wxStaticLine(self, -1), 1, wxALIGN_CENTER)
        sizer.Add(tempSizer, 0, wxEXPAND)
        sizer.Add(10,10)

        tempSizer = wxBoxSizer(wxHORIZONTAL)
        tempSizer.Add(self.list, 1, wxEXPAND)
        tempSizer.Add(self.addButton2, 0, wxALIGN_CENTER | wxLEFT, 5)
        sizer.Add(tempSizer, 1, wxEXPAND)
            
        sizer.Add(10,10)
        box.Add(sizer, 3, wxEXPAND|wxLEFT|wxBOTTOM|wxTOP, 5)
        
        tempSizer = wxBoxSizer(wxVERTICAL)
        tempSizer.Add(10,10)
        tempSizer.Add(self.selections, 0, wxEXPAND|wxBOTTOM, 5)
        tempSizer.Add(self.addList, 1, wxEXPAND)
        tempSizer.Add(self.removeUserButton, 0, wxEXPAND|wxTOP, 5)
        box.Add(tempSizer, 2, wxEXPAND|wxALL, 5)

        mainSizer = wxBoxSizer(wxVERTICAL)
        mainSizer.Add(box, 1, wxEXPAND)
        mainSizer.Add(wxStaticLine(self,-1), 0, wxALL|wxEXPAND, 5)

        tempSizer = wxBoxSizer(wxHORIZONTAL)
        tempSizer.Add(self.okButton, 0, wxCENTER | wxALL, 5)
        tempSizer.Add(self.cancelButton, 0, wxCENTER| wxALL, 5)
        mainSizer.Add(tempSizer, 0, wxALIGN_CENTER)
        mainSizer.Add(10,10)
        
        self.SetAutoLayout(1)
        self.SetSizer(mainSizer)
        self.Layout()
        self.list.SetColumnWidth(0, wxLIST_AUTOSIZE)
        self.addList.SetColumnWidth(0, wxLIST_AUTOSIZE)

    def __setEvents(self):
        EVT_BUTTON(self.addButton1, self.addButton1.GetId(),
                   self.AddDistinguished)
        EVT_BUTTON(self.addButton2, self.addButton2.GetId(),
                   self.AddFromPeopleList) 
        EVT_COMBOBOX(self.selections, self.selections.GetId(),
                     self.ComboEvent)
        EVT_BUTTON(self.removeUserButton, self.removeUserButton.GetId(),
                   self.RemoveSelectedUsersFromList)

        EVT_LIST_ITEM_SELECTED(self.list, self.list.GetId(),
                               self.SelectPeople)

    def __addToList(self, item):
        list = self.infoDict[self.selections.GetValue()]
        
        if not item in list:
            list.append(item)
            self.infoDict[self.selections.GetValue()] = list
            self.addList.InsertStringItem(0, item)
            self.addList.SetColumnWidth(0, wxLIST_AUTOSIZE)
            return true

        return false

    def __removeFromList(self, index):
        if index == -1:
            return false
        item_name = self.addList.GetItemText(index)
        list = self.infoDict[self.selections.GetValue()]

        if item_name in list:
            list.remove(item_name)
            self.infoDict[self.selections.GetValue()] = list
            self.addList.DeleteItem(index)
            return true
 
        return false
        
    def SelectNewRole(self, role):
        self.selectedRole = role
        for item in self.infoDict[self.selectedRole]:
            self.addList.InsertStringItem(0, item.name.split('=')[-1])
            self.addList.SetColumnWidth(0, wxLIST_AUTOSIZE)
            
    def GetInfo(self):
        return self.infoDict
      
    def SelectPeople(self, event):
        self.selectedPersonId = event.m_itemIndex

    def AddDistinguished(self, event):
        item = self.dnTextCtrl.GetValue()
        if item != "":
            if not self.__addToList(item):
                MessageDialog(self, "A person with the same name is already added")
        
    def AddFromPeopleList(self, event):
        if self.selectedPersonId > -1:
            item = self.list.GetItemText(self.selectedPersonId)
            
            if not self.__addToList(item):
                MessageDialog(self, "A person with the same name is already added")

    def ComboEvent(self, event):
        role = event.GetEventObject()
        self.addList.DeleteAllItems()
        self.SelectNewRole(self.selections.GetValue())

    def RemoveSelectedUsersFromList(self, event):
        role = event.GetEventObject()

        i = self.addList.GetFirstSelected(None)
        while i != -1:
            if not self.__removeFromList(i):
                MessageDialog(self, "Unable to remove user from list.")
                i = -1 # Break out of loop
            else:
                i = self.addList.GetFirstSelected(None)
               
    def AddPeople(self, list):
        for item in list:
            self.list.InsertStringItem(0, item)

class AuthorizationUIFrame(wxFrame):
    def __init__(self, parent, id, title):
        wxFrame.__init__(self, parent, id, title)
        self.panel = AuthorizationUIPanel(self, -1)

if __name__ == "__main__":
    if len(sys.argv) == 2:
        uri = sys.argv[1]
    else:
        uri = "https://localhost:8000/VenueServer/Authorization"
        
    print "URI: ", uri
    try:
        am = AuthorizationManagerIW(uri)
    except Exception, e:
        print "Couldn't get authorization manager: ", e
        sys.exit(1)
        
    p1 = am.GetPolicy()
    am.TestImportExport(p1)
    p2 = am.GetPolicy()

    if p1 == p2:
        print "Policies the same!"
    else:
        print "Policies differ."
        import xml.dom.minidom
        from xml.dom.ext import PrettyPrint
        dp1 = xml.dom.minidom.parseString(p1)
        PrettyPrint(dp1)
        dp2 = xml.dom.minidom.parseString(p2)
        PrettyPrint(dp2)

    app = wxPySimpleApp()
    roles = AddPeopleDialog(None, -1, "Manage Roles", am)
    roles.ShowModal()
    roles.Destroy()
   
