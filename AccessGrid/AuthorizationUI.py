#-----------------------------------------------------------------------------
# Name:        AuthorizationUI.py
# Purpose:     Roles Management UI
# Created:     2003/08/07
# RCS_ID:      $Id: AuthorizationUI.py,v 1.6 2004-03-12 05:23:11 judson Exp $ 
# Copyright:   (c) 2003
# Licence:     See COPYING.txt
#-----------------------------------------------------------------------------
"""
"""
__revision__ = "$Id: AuthorizationUI.py,v 1.6 2004-03-12 05:23:11 judson Exp $"
__docformat__ = "restructuredtext en"

import string

from wxPython.wx import *
from AccessGrid.UIUtilities import MessageDialog, ErrorDialog
from wxPython.wizard import *

from AccessGrid import Toolkit
from AccessGrid.Platform import isWindows, isLinux
from AccessGrid.ClientProfile import ClientProfileCache
from AccessGrid.Security.AuthorizationManager import AuthorizationManagerIW
from AccessGrid.Security.X509Subject import X509Subject    
from AccessGrid.Security.Role import Role

class AuthorizationUIPanel(wxPanel):
    '''
    This class shows a tree of people structured in roles.
    '''
    def __init__(self, parent, id, log):
        wxPanel.__init__(self, parent, id, wxDefaultPosition, \
			 style = wxRAISED_BORDER)
        self.log = log
        self.cacheRole = 'Registered People'
        self.roleToTreeIdDict = dict()
        self.x = -1
        self.y = -1
        self.currentRole = None
        self.roleToSubjectDict = {}
        self.roleToActionDict = {}
        self.allActions = []
        self.dragItem = None
        self.copyItem = None
        self.authClient = None

        
        # Create ui componentes
        self.rolePanel = wxPanel(self, -1)
        self.actionPanel = wxPanel(self, -1)
        self.tree = wxTreeCtrl(self.rolePanel, wxNewId(), wxDefaultPosition, 
                               wxDefaultSize, style = wxTR_HAS_BUTTONS |
                               wxTR_NO_LINES | wxTR_HIDE_ROOT)

        
        self.staticBox = wxStaticBox(self.actionPanel, -1, "")
        self.createRoleButton = wxButton(self.rolePanel, wxNewId(), "Create Role")
        self.removeRoleButton = wxButton(self.rolePanel, wxNewId(), "Remove Role")

       
            
        self.actionList = wxCheckListBox(self.actionPanel, -1)
        self.createActionButton = wxButton(self.actionPanel, wxNewId(), "Create Action")
        self.removeActionButton = wxButton(self.actionPanel, wxNewId(), "Remove Action")

       
        self.__setMenus()
        self.__setEvents()
       
        self.__layout()
        
        self.SetSize(wxSize(800,800))
       
    def ConnectToAuthManager(self, url):
        authUrl = ''
        list =  string.split(url, '/')
        lastString = list[len(list)-1]
        if lastString == 'Authorization':
            # Authorization URL
            authUrl = url
        else:
            # Server URL
            for l in list:
                if authUrl == '':
                    authUrl = authUrl + l
                else:
                    authUrl = authUrl + '/'+l
        

            authUrl = authUrl + '/Authorization'
                            
        try:
            self.authClient = AuthorizationManagerIW(authUrl)
        except Exception, e:
            log.exception("VenueManagementTabs.__init__:Couldn't get authorization manager at\n%s. Shut down."%(authUrl))
            MessageDialog(None, "Can not connect.", "Error")
            return

        roles = []
        try:
            roles = self.authClient.ListRoles()
        except:
            log.exception("VenueManagementTabs.__init__: Failed to list roles.")

        # Get all subjects for each role.
        for role in roles:
            errorList = []
            try:
                self.roleToSubjectDict[role] = self.authClient.ListSubjects(role)
                
            except:
                self.log.exception("AuthorizationUIPanel.__init__: List subjects in role failed.")
                self.roleToSubjectDict[role] = []
                errorList.append(role.name)

            if errorList!=[]:
                MessageDialog(None, "Failed to laod people for roles:\n%s"%errorList, "Error")
        

        self.__AddCachedSubjects()
               
        # Get all actions for each role.
        for role in self.roleToSubjectDict.keys():
            errorList = []
            try:
                actions = self.authClient.ListActions(None, role)
                self.roleToActionDict[role] = actions
                
            except:
                self.log.exception("AuthorizationUIPanel.__init__: List actions for role failed.")
                self.roleToActionDict[role] = []
                errorList.append(role.name)

            if errorList != []:
                MessageDialog(None, "Failed to load actions for roles:\n %s" %errorList, "Error")

        try:
            self.allActions = self.authClient.ListActions()

            actions = []
            for action in self.allActions:
                actions.append(action.name)

            self.actionList.InsertItems(actions, 0)
            
        except:
            self.log.exception("AuthorizationUIPanel.__init__: List actions failed.")
            self.allActions = []
            MessageDialog(None, "Failed to load actions", "Error")

        self.__initTree()

    def __AddCachedSubjects(self):
        # Get subjects from our local cache
        c = ClientProfileCache()
        cachedDns = []
        cachedSubjects = []
        for p in c.loadAllProfiles():
            dn = p.GetDistinguishedName()
            if dn:
                cachedDns.append(dn)

        # Create role for cached subjects
        
        roleExists = 0
        
        for role in self.roleToSubjectDict.keys():
            if self.cacheRole == role.name:
                roleExists = 1
                self.cacheRole = role
                
        # If role is not already added; Create role.
        if not roleExists:
            try:
                self.cacheRole = self.authClient.AddRole(self.cacheRole)
                self.roleToSubjectDict[self.cacheRole] = []
                    
            except:
                self.log.exception("AuthorizationUIPanel.CreateRole: Failed to add role")
               
        # Create subjects.
        for dn in cachedDns:
            subject =  X509Subject(dn)
            cachedSubjects.append(subject)
       
        # Only add subjects that are new in the cache.
        subjects =  self.roleToSubjectDict[self.cacheRole]
                
        sList = []
                
        for subject in cachedSubjects:
            if not subject in subjects:
                sList.append(subject)

        if sList is not []:
            try:
                self.authClient.AddSubjectsToRole(sList, self.cacheRole)
                l = self.roleToSubjectDict[self.cacheRole]
                l = l + sList
                self.roleToSubjectDict[self.cacheRole] = l
            except:
                log.exception("AuthorizationUIPanel.__AddCachedSubjects: AddSubjectToRole failed")
              
    def __initTree(self):
        '''
        Adds items to the tree
        '''
        # Add items to the tree
        self.root = self.tree.AddRoot("", -1, -1)
        
        for role in self.roleToSubjectDict.keys():
            # Add role
            roleId = self.tree.AppendItem(self.root, role.name, -1, -1)
            self.roleToTreeIdDict[role] = roleId
            self.tree.SetItemBold(roleId)
            self.tree.SetItemData(roleId, wxTreeItemData(role))

            # For each role, add people.
            for person in self.roleToSubjectDict[role]:
                personId = self.tree.AppendItem(roleId, person.name, -1, -1)
                self.tree.SetItemData(personId, wxTreeItemData(person))

            # Sort the tree
            if self.tree.GetChildrenCount(roleId)> 0:
                self.tree.SortChildren(roleId)

        if self.tree.GetChildrenCount(self.root)> 0:
            self.tree.SortChildren(self.root)

        cookie = 1
        firstItem, stupidCookie = self.tree.GetFirstChild(self.root, cookie)
        self.tree.SelectItem(firstItem)

        currentItem = self.tree.GetSelection()
        self.staticBox.SetLabel("Actions for %s"%self.tree.GetItemText(currentItem))
            
    def __setEvents(self):
        '''
        Set events for this panel
        '''
        EVT_RIGHT_DOWN(self.tree, self.OnRightClick)
      
       
        EVT_BUTTON(self, self.removeRoleButton.GetId(), self.RemoveRole)
        EVT_BUTTON(self,self.createRoleButton.GetId(), self.CreateRole)
        EVT_BUTTON(self,self.createActionButton.GetId(), self.CreateAction)
        EVT_BUTTON(self,self.removeActionButton.GetId(), self.RemoveAction)

        #EVT_TREE_END_LABEL_EDIT(self.tree, self.tree.GetId(), self.EndRename)
        EVT_TREE_BEGIN_DRAG(self.tree, self.tree.GetId(), self.BeginDrag)
        EVT_TREE_END_DRAG(self.tree, self.tree.GetId(), self.EndDrag)
        EVT_TREE_SEL_CHANGED(self.tree, self.tree.GetId(), self.OnSelect)

        EVT_CHECKLISTBOX(self, self.actionList.GetId(), self.CheckAction)

        EVT_MENU(self, self.ID_PERSON_ADDPERSON, self.AddPerson)
        EVT_MENU(self, self.ID_PERSON_ADDROLE, self.CreateRole)
        EVT_MENU(self, self.ID_PERSON_DELETE, self.RemovePerson)
        #EVT_MENU(self, self.ID_PERSON_RENAME, self.Rename)
        EVT_MENU(self, self.ID_PERSON_COPY, self.Copy)
        EVT_MENU(self, self.ID_PERSON_PASTE, self.Paste)

        EVT_MENU(self, self.ID_ROLE_ADDPERSON, self.AddPerson)

    def __participantInRole(self, roleId, person):
        '''
        Check to see if person/group is added to a role already
        '''
        role = self.tree.GetItemData(roleId).GetData()
        list = self.roleToSubjectDict[role]

        for l in list:
            if l.name == person.name:
                return 1

        return 0
                   
    def __rmParticipantFromDict(self, role, person):
        '''
        Remove a participant from the role dictionary
        '''
        list = self.roleToSubjectDict[role]
        list.remove(person)

        index = 0
        for item in list:
            if item.name == person.name:
                del list[index]
                return
                
            index = index + 1

    def __addParticipantToDict(self, role, person):
        '''
        Add a participant to the role dictionary
        '''
        list = self.roleToSubjectDict[role]
        list.append(person)
        self.roleToSubjectDict[role] = list

    def __isRole(self, treeId):
        '''
        Check to see if a tree id is a role
        '''

        role = self.tree.GetItemData(treeId).GetData()

        for r in self.roleToSubjectDict.keys():
            if r.name == role.name:
                return 1
        return 0
            
    def __setMenus(self):
        '''
        Initiate menues that are shown when user right-clicks a tree item
        '''
        self.ID_ROLE_ADDPERSON = wxNewId()
      
        self.ID_PERSON_ADDPERSON = wxNewId()
        self.ID_PERSON_ADDROLE = wxNewId()
        #self.ID_PERSON_RENAME = wxNewId()
        self.ID_PERSON_COPY = wxNewId()
        self.ID_PERSON_PASTE = wxNewId()
        self.ID_PERSON_DELETE = wxNewId()
       

        # Menu when user clicks on a role item
        
        self.roleMenu = wxMenu()
        self.roleMenu.Append(self.ID_ROLE_ADDPERSON,"Add Person",
                             "Add participant to this role")
        #self.roleMenu.Append(self.ID_ROLE_ADDPERSON,"Create Role",
        #                     "Create new role")
     
        # Menu when user clicks on a participant/group
        
        self.personMenu = wxMenu()
        self.personMenu.Append(self.ID_PERSON_ADDPERSON,"Add Person",
                                   "New participant")
        self.personMenu.AppendSeparator()
        #self.personMenu.Append(self.ID_PERSON_RENAME,"Rename",
        #                           "Rename this participant")
        self.personMenu.Append(self.ID_PERSON_COPY,"Copy",
                                   "Copy this participant")

        self.personMenu.Append(self.ID_PERSON_PASTE,"Paste",
                                   "Paste")
        self.personMenu.AppendSeparator()
        self.personMenu.Append(self.ID_PERSON_DELETE,"Remove",
                                   "Remove this role from venue")
       
    def __layout(self):
        '''
        Handles ui layout
        '''
        # Role Panel
        staticBox = wxStaticBox(self.rolePanel, -1, "Roles")
        sizer  = wxStaticBoxSizer(staticBox,
                                  wxVERTICAL)
        sizer.Add(self.tree, 1, wxEXPAND|wxALL, 4)

        buttonSizer = wxBoxSizer(wxHORIZONTAL)
        buttonSizer.Add(self.createRoleButton, 1, wxEXPAND|wxALL, 4)
        buttonSizer.Add(self.removeRoleButton, 1, wxEXPAND|wxALL, 4)

        sizer.Add(buttonSizer, 0, wxEXPAND)

        self.rolePanel.SetSizer(sizer)

        # Action Panel
        sizer  = wxStaticBoxSizer(self.staticBox,
                                  wxVERTICAL)
        sizer.Add(self.actionList, 1, wxEXPAND|wxALL, 4)
              
        buttonSizer = wxBoxSizer(wxHORIZONTAL)
        buttonSizer.Add(self.createActionButton, 1, wxEXPAND|wxALL, 4)
        buttonSizer.Add(self.removeActionButton, 1, wxEXPAND|wxALL, 4)

        sizer.Add(buttonSizer, 0, wxEXPAND)

        self.actionPanel.SetSizer(sizer)

        # The frame
        sizer = wxBoxSizer(wxHORIZONTAL)
        
        sizer.Add(self.rolePanel, 5, wxEXPAND| wxALL, 5)
        sizer.Add(self.actionPanel, 3, wxEXPAND | wxALL, 5)
        
        self.SetAutoLayout(1)
        self.SetSizer(sizer)
        self.actionPanel.Layout()
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
            person = self.tree.GetItemData(self.copyItem).GetData()
            selectedItem = self.tree.GetSelection()

            if self.__isRole(selectedItem):
                
                # If selected item is a role, paste the copied item
                # to that role
                roleId = selectedItem
               
            else:
                # If selected item is a participant, paste copied item to
                # its parent (a role)
                roleId = self.tree.GetItemParent(selectedItem)

            # Paste the item if it is not already added to the role
            
            role = self.tree.GetItemData(roleId).GetData()

            if not self.__participantInRole(roleId, person):

                # Add the person to the new role.
                try:
                    self.authClient.AddSubjectToRole(person, role)
                except:
                    self.log.exception("AuthorizationUI.Paste: Add subject to role failed.")
                    MessageDialog(self, "Add %s to %s failed"%(person.name, role.name), "Error") 
                    return
                
                personId = self.tree.AppendItem(roleId, person.name)
                self.tree.SetItemData(personId, wxTreeItemData(person))

                # Add copied item to dictionary
                self.__addParticipantToDict(role, person)

            else:
                MessageDialog(self, "%s is already added to %s"%(person.name, role.name), "Error") 
            
    def BeginDrag(self, event):
        '''
        Is called when a user starts to drag a tree item
        '''
        self.dragItem = self.tree.GetSelection()
        
        # Need to call Allow to get an EVT_TREE_END_DRAG event
        event.Allow()

    def CheckAction(self, event):
        '''
        Is called when user checks an action.
        '''
        index = event.GetInt()
        actionName = self.actionList.GetString(index)
        checked = self.actionList.IsChecked(index)
        currentAction = None

        for action in self.allActions:
            if action.name == actionName:
                currentAction = action

        if currentAction:
            if checked:
                # Add action
                try:
                    self.authClient.AddRoleToAction(self.currentRole, currentAction)
                except:
                    self.log.exception("AuthorizationUIPanel.CheckAction: Add role to action failed.")
                    MessageDialog(self, "Add %s to %s failed"%(currentAction.name,
                                                               self.currentRole.name), "Error") 
                    # Uncheck list item
                    self.actionList.Check(index, 0)
                    return
                
                actions = self.roleToActionDict[self.currentRole]
                actions.append(currentAction)
                

            else:
                # Remove action
                try:
                    self.authClient.RemoveRoleFromAction(self.currentRole,
                                                         currentAction)
                except:
                    self.log.exception("AuthorizationUIPanel.CheckAction: Remoe role from action failed.")
                    MessageDialog(self, "Remove %s from %s failed"%(currentAction.name,
                                                               self.currentRole.name), "Error") 
                    
                    # Check list item
                    self.actionList.Check(index, 1)
                    return
                
                actions = self.roleToActionDict[self.currentRole]
                
                for action in actions:
                    if action.name == currentAction.name:
                        actions.remove(action)

    def OnSelect(self, event):
        '''
        Is called when user selects a new item in the tree.
        '''
        selectedItem = event.GetItem()
        if selectedItem.IsOk():
            role = self.tree.GetItemData(selectedItem).GetData()
            if not self.__isRole(selectedItem):
                # This is actually a person; Get parent onstead.
                selectedItem = self.tree.GetItemParent(selectedItem)
                role = self.tree.GetItemData(selectedItem).GetData()
                            
            # First, Uncheck all actions for this role.
            nrOfItems = self.actionList.GetCount()
            for index in range(nrOfItems):
                self.actionList.Check(index, 0)
                
            if self.__isRole(selectedItem):
                self.currentRole = role
                
                for action in self.roleToActionDict[role]:
                    index = self.actionList.FindString(action.name)
                
                    # Check correct actions for this role.
                    if index is not wxNOT_FOUND:
                        self.actionList.Check(index, 1)
                
            if self.staticBox:
                self.staticBox.SetLabel("Actions for %s"%self.currentRole.name)
            
    def EndDrag(self, event):
        '''
        Is called when a user stops dragging a tree item
        '''
        selectedItem = event.GetItem()
        
        if self.dragItem.IsOk() and selectedItem.IsOk():
            item = self.tree.GetItemData(self.dragItem).GetData()
            oldHeading = None
            
            if self.__isRole(self.dragItem):
                # This is a role and we don't want to drag it
                return

            else:
                # We are dragging a participant/group
                oldRoleId = self.tree.GetItemParent(self.dragItem)
                oldRole = self.tree.GetItemData(oldRoleId).GetData()

            if self.__isRole(selectedItem):
                # If selected item is a role, add the dragged item
                # to that role
                parent = selectedItem

            else:
                # If selected item is a participant add it to the
                # same role as that participant
                parent = self.tree.GetItemParent(selectedItem)

            # Get the role we want to add the participant/group to
            role = self.tree.GetItemData(parent).GetData()

            #If participant is not already present in the role, add it
            if not self.__participantInRole(parent,item):

                errorFlag = 0
                # Delete item from role
                try:
                    self.authClient.RemoveSubjectFromRole(item, oldRole)
                                       
                except:
                    self.log.exception("AuthorizationUI.EndDrag: Remove subject failed.")
                    errorFlag = 1
                    message = wxMessageDialog(self, "Failed to add %s to %s"%(item.name, role.name), "Error",  style = wxOK|wxICON_INFORMATION)
                    # Do not use modal; it hangs the dialog.
                    message.Show()
                    return
                                    
                # Add item to role
                    
                try:
                    # Only add if we could remove
                    if not errorFlag:
                        self.authClient.AddSubjectToRole(item, role)
                        
                except:
                    self.log.exception("AuthorizationUI.EndDrag: Add subject failed.")
                    # We might want to add subject to old role if this fails.
                    message = wxMessageDialog(self, "Failed to add %s to %s"%(item.name, role.name), "Error",  style = wxOK|wxICON_INFORMATION)
                    # Do not use modal; it hangs the dialog.
                    message.Show()
                    return
                    
                # Update tree
                self.tree.Delete(self.dragItem)
                itemId = self.tree.AppendItem(parent, item.name)
                self.tree.SetItemData(itemId, wxTreeItemData(item))
                self.__rmParticipantFromDict(oldRole, item)
                self.__addParticipantToDict(role, item)
                
            else:
                event.Skip()
                message = wxMessageDialog(self, "%s is already added to %s"%(item.name, role.name), "Error",  style = wxOK|wxICON_INFORMATION)
                # Do not use modal; it hangs the dialog.
                message.Show()
                           
    def CreateRole(self, event):
        '''
        Create new role
        '''

        # Open dialog for user input.
        createRoleDialog = CreateRoleDialog(self, -1, 'Create Role')
                
        if createRoleDialog.ShowModal() == wxID_OK:
            name =  createRoleDialog.GetName()
            # Add role

            for role in self.roleToSubjectDict.keys():
                if role.name == name:
                    MessageDialog(self, "A role named %s already exists."%(name), "Error") 
                    return None
            
            try:
                newRole = self.authClient.AddRole(name)
            except:
                self.log.exception("AuthorizationUIPanel.CreateRole: Failed to add role")
                MessageDialog(self, "Create new role %s failed"%(name), "Error") 
                return None
        
            roleId = self.tree.AppendItem(self.root, newRole.name, -1, -1)
            self.tree.SetItemBold(roleId)
            self.tree.SetItemData(roleId, wxTreeItemData(newRole))
            self.roleToSubjectDict[newRole] = []
            self.roleToActionDict[newRole] = []
            self.roleToTreeIdDict[newRole] = roleId
            
        return newRole
      
    def CreateAction(self, event):
        '''
        Create new action.
        '''
        # Open dialog for user input
        
        actionDialog = CreateActionDialog(self, -1, 'Create Action')

        if actionDialog.ShowModal() == wxID_OK:
            actionName = actionDialog.GetName()
            try:
                action = self.authClient.AddAction(actionName)
                self.allActions.append(action)
                self.actionList.InsertItems([action.name], 0)
            except:
                self.log.exception("AuthorizationUIPanel.CreateAction: Create action failed")
                MessageDialog(self, "Create action %s failed"%(actionName), "Error") 
                           
        actionDialog.Destroy()
        

    def RemoveAction(self, event):
        '''
        Remove action.
        '''
        itemToRemove = self.actionList.GetSelection()
        if itemToRemove is wxNOT_FOUND:
            MessageDialog(self, "Please select the action you want to remove",
                            style = wxICON_QUESTION)
            return
            
        # Make sure user want to remove this action
        text = self.actionList.GetString(itemToRemove)
        message = wxMessageDialog(self, "Are you sure you want to remove '%s'?"%text,
                                  style = wxICON_QUESTION | wxYES_NO | wxNO_DEFAULT)
        
        if message.ShowModal() == wxID_YES:
            for action in self.allActions:
                if action.name == text:
                    try:
                        self.authClient.RemoveAction(action.name)
                        self.actionList.Delete(itemToRemove)
                    except:
                        self.log.exception("AuthorizationUIPanel.RemoveAction: Remove action failed")
                        MessageDialog(self, "Remove action %s failed"%(action.name), "Error") 
                        return
                                               
    def AddPerson(self, event):
        '''
        Adds a new person to the tree
        '''
        
        selectedItem = self.tree.GetSelection()
               
        if selectedItem.IsOk() and selectedItem != self.root:
            
            if self.__isRole(selectedItem):
                # If selected item is a role
                activeRole = self.tree.GetItemData(selectedItem).GetData()
            else:
                # If selected item is a participant
                parent = self.tree.GetItemParent(selectedItem)
                activeRole = self.tree.GetItemData(parent).GetData()

        # Open the dialog
        addPersonDialog = AddPersonDialog(self, -1, 'Add Person', activeRole)
                
        if addPersonDialog.ShowModal() == wxID_OK:
            # Get subject
            subject =  X509Subject(addPersonDialog.GetName())
                        
            # Add subject to role
            try:
                self.authClient.AddSubjectToRole(subject, activeRole)
            except:
                self.log.exception("AuthorizationUIPanel.AddPerson: SetSubjectInRole failed.")
                MessageDialog(self, "Add %s to %s failed"%(subject.name,
                                                           activeRole.name), "Error") 
                return

            # Save subject in dictionary.
            subjects = self.roleToSubjectDict[activeRole]
            subjects.append(subject)
            self.roleToSubjectDict[activeRole] = subjects
            
            # Insert subject in tree
            subjectId = self.tree.AppendItem(self.roleToTreeIdDict[activeRole], subject.name)
            self.tree.SetItemData(subjectId, wxTreeItemData(subject))

        addPersonDialog.Destroy()  

    def RemovePerson(self, event):
        '''
        Remove person from role.
        '''
        treeId = self.tree.GetSelection()

        if treeId.IsOk() and treeId != self.root:
            item = self.tree.GetItemData(treeId).GetData()
            parentId = self.tree.GetItemParent(treeId)
            role = self.tree.GetItemData(parentId).GetData()

            message = wxMessageDialog(self, "Are you sure you want to remove '%s'?"%item.name,
                                      style = wxICON_QUESTION | wxYES_NO | wxNO_DEFAULT)
                
            if message.ShowModal() == wxID_YES:
                # Remove subject from role
                try:
                    self.authClient.RemoveSubjectFromRole(item, role)
                except:
                    self.log.exception("AuthorizationUIPanel.AddPerson: SetSubjectInRole failed.")
                    MessageDialog(self, "Remove %s from %s failed"%(item.name,
                                                                    role.name),
                                  "Error")
                    return

                # delete item from tree and dictionary
                self.tree.Delete(treeId)
                self.__rmParticipantFromDict(role, item)
            
        else:
            MessageDialog(self, "Please select the person you want to remove")
            
            
    def RemoveRole(self, event):
        '''
        Remove an item from the tree
        '''
        treeId = self.tree.GetSelection()
       
        if treeId.IsOk() and treeId != self.root:
            role = self.tree.GetItemData(treeId).GetData()

            if not self.roleToSubjectDict.has_key(role):
                MessageDialog(self, "Select the role you want to remove.", "Notification")
                return
            
            if treeId != self.root:
                message = wxMessageDialog(self, "Are you sure you want to remove '%s'?"%role.name,
                                          style = wxICON_QUESTION | wxYES_NO | wxNO_DEFAULT)
                
                if message.ShowModal() == wxID_YES:
                    try:
                        self.authClient.RemoveRole(role.name)
                    except:
                        log.exception("AuthorizationUIPanel.RemoveRole: Remove role failed.")
                        MessageDialog(self, "Failed to remove %s"%role.name, "Notification")
                        return
                    # delete item from tree and dictionary
                    self.tree.Delete(treeId)
                    del self.roleToSubjectDict[role]
                    del self.roleToTreeIdDict[role]
                        
            else:
                MessageDialog(self, "Please select the participant you want to remove")

    '''def Rename(self, event):
        """
        Is called when user wants to rename a participant/group
        """
        treeId =  self.tree.GetSelection()

        if treeId.IsOk() and treeId != self.root:
           
            if self.__isRole(treeId):
                # Roles can not be modified yet
                MessageDialog(self, "Role can not be renamed")
                return
            
            self.tree.EditLabel(treeId)
            role = self.tree.GetItemData(treeId).GetData()
            subjects = self.roleToSubjectDict[role]
            del self.roleToSubjectDict[role]
            self.roleToSubjectDict[role] = self.tree.GetLabel(treeId)

        else:
            MessageDialog(self, "Please select the role or participant you want to rename")
      
    def EndRename(self, event):
        """
        Is called when user finished renaming a participant/group
        """
        treeId = self.tree.GetSelection()
        person = self.tree.GetItemData(treeId).GetData()
        roleId = self.tree.GetItemParent(treeId)
        role = self.tree.GetItemData(roleId).GetData()
        newText = event.GetLabel()

        person.name = newText
        # Remove the old participant/group from dictionary and add a new entry
        self.__rmParticipantFromDict(role, person)
        self.__addParticipantToDict(role, person) 
        '''
        
    def OnRightClick(self, event):
        '''
        Is called when user right-clicks a tree item. Opens a menu.
        '''
        self.x = event.GetX()
        self.y = event.GetY()

        treeId, flag = self.tree.HitTest(wxPoint(self.x,self.y))
      
        if(treeId.IsOk()):
            self.tree.SelectItem(treeId)
         
            if not self.__isRole(treeId):
                self.PopupMenu(self.personMenu,
                               wxPoint(self.x, self.y))
         
            else:
                self.PopupMenu(self.roleMenu,
                               wxPoint(self.x, self.y))
        

class CreateActionDialog(wxDialog):
    '''
    Dialog for adding actions to roles.
    '''
    def __init__(self, parent, id, title):
        wxDialog.__init__(self, parent, id, title,
                          style=wxDEFAULT_DIALOG_STYLE|wxRESIZE_BORDER)
        self.SetSize(wxSize(300, 150))
        self.infoText = wxStaticText(self, -1,
                                     "Name the action.")
        self.actionTextCtrl = wxTextCtrl(self,-1, "")
        self.okButton = wxButton(self, wxID_OK, "Ok")
        self.cancelButton =  wxButton(self, wxID_CANCEL, "Cancel")

        self.__layout()

    def GetName(self):
        return self.actionTextCtrl.GetValue()

    def __layout(self):
        mainSizer = wxBoxSizer(wxHORIZONTAL)
        box = wxBoxSizer(wxVERTICAL)
        sizer = wxBoxSizer(wxHORIZONTAL)

        box.Add(10,10)
        box.Add(self.infoText, 0, wxEXPAND|wxALL, 5)
        
        sizer = wxBoxSizer(wxHORIZONTAL)
        sizer.Add(wxStaticText(self, -1, "Name: "), 0, wxALIGN_CENTER)
        sizer.Add(self.actionTextCtrl, 1, wxALIGN_CENTER, 2)
        box.Add(sizer, 1, wxEXPAND|wxALL, 5)

        box.Add(wxStaticLine(self, -1), 0, wxEXPAND|wxALL, 5)
        sizer2 = wxBoxSizer(wxHORIZONTAL)
        sizer2.Add(self.okButton, 0, wxCENTER | wxRIGHT, 10)
        sizer2.Add(self.cancelButton, 0, wxCENTER)
        box.Add(sizer2, 0, wxCENTER|wxALL, 5)

        mainSizer.Add(box, 1, wxALL | wxEXPAND, 10)
        
        self.SetAutoLayout(1)
        self.SetSizer(mainSizer)
        self.Layout()

class AddPersonDialog(wxDialog):
    '''
    Dialog for adding actions to roles.
    '''
    def __init__(self, parent, id, title, role):
        wxDialog.__init__(self, parent, id, title,
                          style=wxDEFAULT_DIALOG_STYLE|wxRESIZE_BORDER)
        self.SetSize(wxSize(450, 150))
        self.infoText = wxStaticText(self, -1,
                                     "Enter the distinguished name of the person you want to add to %s. role" %role.name)
        self.dnTextCtrl = wxTextCtrl(self,-1, "")
        self.okButton = wxButton(self, wxID_OK, "Ok")
        self.cancelButton =  wxButton(self, wxID_CANCEL, "Cancel")

        self.__layout()

    def GetName(self):
        return self.dnTextCtrl.GetValue()

    def __layout(self):
        mainSizer = wxBoxSizer(wxHORIZONTAL)
        box = wxBoxSizer(wxVERTICAL)
        sizer = wxBoxSizer(wxHORIZONTAL)

        box.Add(10,10)
        box.Add(self.infoText, 0, wxEXPAND|wxALL, 5)
        
        sizer = wxBoxSizer(wxHORIZONTAL)
        sizer.Add(wxStaticText(self, -1, "Distinguished Name: "), 0, wxALIGN_CENTER)
        sizer.Add(self.dnTextCtrl, 1, wxALIGN_CENTER, 2)
        box.Add(sizer, 1, wxEXPAND|wxALL, 5)

        box.Add(wxStaticLine(self, -1), 0, wxEXPAND|wxALL, 5)
        sizer2 = wxBoxSizer(wxHORIZONTAL)
        sizer2.Add(self.okButton, 0, wxCENTER | wxRIGHT, 10)
        sizer2.Add(self.cancelButton, 0, wxCENTER)
        box.Add(sizer2, 0, wxCENTER|wxALL, 5)

        mainSizer.Add(box, 1, wxALL | wxEXPAND, 10)
        
        self.SetAutoLayout(1)
        self.SetSizer(mainSizer)
        self.Layout()

class CreateRoleDialog(wxDialog):
    '''
    Dialog for adding actions to roles.
    '''
    def __init__(self, parent, id, title):
        wxDialog.__init__(self, parent, id, title,
                          style=wxDEFAULT_DIALOG_STYLE|wxRESIZE_BORDER)
        self.SetSize(wxSize(450, 150))
        self.infoText = wxStaticText(self, -1,
                                     "Enter the name of the new role.")
        self.dnTextCtrl = wxTextCtrl(self,-1, "")
        self.okButton = wxButton(self, wxID_OK, "Ok")
        self.cancelButton =  wxButton(self, wxID_CANCEL, "Cancel")

        self.__layout()

    def GetName(self):
        return self.dnTextCtrl.GetValue()

    def __layout(self):
        mainSizer = wxBoxSizer(wxHORIZONTAL)
        box = wxBoxSizer(wxVERTICAL)
        sizer = wxBoxSizer(wxHORIZONTAL)

        box.Add(10,10)
        box.Add(self.infoText, 0, wxEXPAND|wxALL, 5)
        
        sizer = wxBoxSizer(wxHORIZONTAL)
        sizer.Add(wxStaticText(self, -1, "Name: "), 0, wxALIGN_CENTER)
        sizer.Add(self.dnTextCtrl, 1, wxALIGN_CENTER, 2)
        box.Add(sizer, 1, wxEXPAND|wxALL, 5)

        box.Add(wxStaticLine(self, -1), 0, wxEXPAND|wxALL, 5)
        sizer2 = wxBoxSizer(wxHORIZONTAL)
        sizer2.Add(self.okButton, 0, wxCENTER | wxRIGHT, 10)
        sizer2.Add(self.cancelButton, 0, wxCENTER)
        box.Add(sizer2, 0, wxCENTER|wxALL, 5)

        mainSizer.Add(box, 1, wxALL | wxEXPAND, 10)
        
        self.SetAutoLayout(1)
        self.SetSizer(mainSizer)
        self.Layout()
            
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
        self.roleToSubjectDict = dict()
        self.selectedRole = selectedRole
        
        if infoDict:
            self.infoDict = infoDict
        else:
            for r in self.authClient.ListRoles():
                self.infoDict[r.name] = self.authClient.ListSubjects(r.name)

        for role in self.authClient.ListRoles():
            self.roleToSubjectDict[role] = self.authClient.ListSubjects(role)

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
    def __init__(self, parent, id, title, am, log):
        wxFrame.__init__(self, parent, id, title, size = wxSize(1000,400))
        self.panel = AuthorizationUIPanel(self, -1, log)
        self.panel.ConnectToAuthManager("https://localhost:8880/VenueServer/Authorization")
        


def InitLogging(debug = 1, l = None):
        """
        This method sets up logging that prints debug and error messages.
        
        **Arguments**
        
        *debug* If debug is set to 1, log messages will be printed to file
        and command window
 
        *log* Name of log file. If set to None, <appName>.log is used
        """

        logFormat = "%(name)-17s %(asctime)s %(levelname)-5s %(message)s"
        log = Log.GetLogger(Log.AuthorizationUI)
        
        # Log to file
        if l == None:
            logFile = 'AuthorizationUI.log'
        else:
            logFile = l
      
        fileHandler = Log.FileHandler(logFile)
        fileHandler.setFormatter(Log.Formatter(logFormat))
        fileHandler.setLevel(Log.DEBUG)
        Log.HandleLoggers(fileHandler, Log.GetDefaultLoggers())

        # If debug mode is on, log to command window too
        if debug:
            hdlr = Log.StreamHandler()
            hdlr.setFormatter(Log.Formatter(logFormat))
            Log.HandleLoggers(hdlr, Log.GetDefaultLoggers())

        return log
    

if __name__ == "__main__":
    import logging
        
    if len(sys.argv) == 2:
        uri = sys.argv[1]
    else:
        uri = "https://localhost:8880/VenueServer/Authorization"
        
    try:
        am = AuthorizationManagerIW(uri)
    except Exception, e:
        print "Couldn't get authorization manager: ", e
        sys.exit(1)

   
    #p1 = am.GetPolicy()
    #am.TestImportExport(p1)
    #p2 = am.GetPolicy()

    #if p1 == p2:
    #    print "Policies the same!"
    #else:
    #    print "Policies differ."
    #    import xml.dom.minidom
    #    from xml.dom.ext import PrettyPrint
    #    dp1 = xml.dom.minidom.parseString(p1)
    #    PrettyPrint(dp1)
    #    dp2 = xml.dom.minidom.parseString(p2)
    #    PrettyPrint(dp2)

    wxapp = wxPySimpleApp()
    log = InitLogging()

    #actionDialog = AddPersonDialog(None, -1, 'Add Person', Role('test'))
    #print 'before show modal'
    #if actionDialog.ShowModal() == wxID_OK:
    #    print 'add action'
    #   
    #actionDialog.Destroy()
    
    
    f = AuthorizationUIFrame(None, -1, "Manage Roles", am, log)
    f.Show()
    wxapp.SetTopWindow(f)
    wxapp.MainLoop()

    #roles = AddPeopleDialog(None, -1, "Manage Roles", am)
    #roles.ShowModal()
    #roles.Destroy()
   
