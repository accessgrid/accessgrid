#-----------------------------------------------------------------------------
# Name:        AuthorizationUI.py
# Purpose:     Roles Management UI
#
# Author:      Susanne Lefvert 
#
#
# Created:     2003/08/07
# RCS_ID:      $Id: AuthorizationUI.py,v 1.18 2004-06-02 00:18:51 eolson Exp $ 
# Copyright:   (c) 2003
# Licence:     See COPYING.txt
#-----------------------------------------------------------------------------
"""
"""
__revision__ = "$Id: AuthorizationUI.py,v 1.18 2004-06-02 00:18:51 eolson Exp $"
__docformat__ = "restructuredtext en"

import string
import copy
import xml.dom.minidom

from wxPython.wx import *
from AccessGrid.UIUtilities import MessageDialog, ErrorDialog
from wxPython.wizard import *

from AccessGrid import Toolkit
from AccessGrid.Platform import IsWindows
from AccessGrid.ClientProfile import ClientProfileCache
from AccessGrid.Security.AuthorizationManager import AuthorizationManagerIW
from AccessGrid.Venue import VenueIW
from AccessGrid.Descriptions import CreateClientProfile
from AccessGrid.Security.X509Subject import X509Subject    
from AccessGrid.Security.Role import Role, DefaultIdentityNotRemovable
from AccessGrid.Security.Action import Action 
from AccessGrid import icons
from AccessGrid.Security.Utilities import GetCNFromX509Subject

class AuthorizationUIPanel(wxPanel):
    '''
    This class shows a tree of people structured in roles. When a user selects
    a role from the tree, available actions for the role are displayed. Actions to
    modify roles are available, such as Create/Remove Role and Add/Remove Person to role.
    '''
    ID_ROLE_ADDPERSON = wxNewId()
    ID_ROLE_ADDROLE = wxNewId()
    ID_ROLE_REMOVEROLE = wxNewId()
    ID_PERSON_ADDPERSON = wxNewId()
    ID_PERSON_DELETE = wxNewId()
    #ID_PERSON_RENAME = wxNewId()
    ID_PERSON_COPY = wxNewId()
    ID_PERSON_PASTE = wxNewId()
    ID_PERSON_PROPERTIES = wxNewId()

    ID_WINDOW_LEFT = wxNewId() 
         
    def __init__(self, parent, id, log):
        wxPanel.__init__(self, parent, id, wxDefaultPosition)
        self.log = log
        self.cacheRoleName = 'Registered People'
        self.cacheRole = None
        self.roleToTreeIdDict = dict()
        self.x = -1
        self.y = -1
        self.currentRole = None
        self.allActions = []
        self.allRoles = []
        self.dragItem = None
        self.copyItem = None
        self.authClient = None
        self.changed = 0
        
        # Create ui componentes
        self.leftSashWindow = wxSashLayoutWindow(self, self.ID_WINDOW_LEFT,
                                                 size = wxSize(400,10))
        self.rolePanel = wxPanel(self.leftSashWindow ,  wxNewId(),
                                 style = wxSUNKEN_BORDER)
        self.actionPanel = wxPanel(self,  wxNewId(),
                                   style = wxSUNKEN_BORDER)
        self.tree = wxTreeCtrl(self.rolePanel, wxNewId(), wxDefaultPosition, 
                               wxDefaultSize, style = wxTR_HAS_BUTTONS |
                               wxTR_LINES_AT_ROOT | wxTR_HIDE_ROOT)
        self.staticBox = None
        self.actionList = wxCheckListBox(self.actionPanel, wxNewId())
               
        self.__setMenus()
        self.__setEvents()
        self.__layout()
        
        self.SetSize(wxSize(800,800))
       
    def ConnectToAuthManager(self, url):
        '''
        Connects to an authorization manager running at url. After a successful connect,
        roles and actions are displayed in the UI.

        @param url: location of authorization manager SOAP service.
        @type name: string.
        '''
        authUrl = ''
        self.baseUrl = url
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
            self.log.exception("AuthorizationUIPanel.ConnectToAuthManager:Couldn't get authorization manager at\n%s. Shut down."%(authUrl))
            MessageDialog(None, "Can not connect.", "Error")
            return

        roles = []

        # Get roles
        try:
            self.allRoles = self.authClient.ListRoles()
        except:
            self.log.exception("AuthorizationUIPanel.ConnectToAuthManager:Failed to list roles. %s"%(authUrl))
        
        # Get Actions
        try:
           
            self.allActions = self.authClient.ListActions()
            actions = []
            for action in self.allActions:
                actions.append(action.name)

            self.actionList.InsertItems(actions, 0)
                      
        except:
            self.log.exception("AuthorizationUIPanel.ConnectToAuthManager: List actions failed. %s"%(authUrl))
            self.allActions = []
            MessageDialog(None, "Failed to load actions", "Error")

        self.__AddCachedSubjects()
        self.__initTree()

    def __AddCachedSubjects(self):
        '''
        Retreive and add subjects available in user cache.
        '''
        # Get subjects from our local cache
        c = ClientProfileCache()
        cachedDns = []
        cachedSubjects = []
        for p in c.loadAllProfiles():
            dn = p.GetDistinguishedName()
            if dn:
                cachedDns.append(dn)

        # Get subjects from remote cache
        try:
            # Test if self.baseUrl really is a venue url...for now use try except.
            self.venue = VenueIW(self.baseUrl)
            
            for p in self.venue.GetCachedProfiles():
                profile = CreateClientProfile(p)
                dn = profile.GetDistinguishedName()
                if dn:
                    cachedDns.append(dn)
        except:
            self.log.exception("AuthorizationUI.__AddCachedSubjects: Failed to load remote profiles. Only venues have profile caches so this may be the case when connecting to an application. Not critical.")

        # Create role for cached subjects
        roleExists = 0
        
        for role in self.allRoles:
            if self.cacheRoleName == role.name:
                roleExists = 1
                self.cacheRole = role
                
        # If role is not already added; Create role.
        if not roleExists:
            try:
                self.cacheRole = Role(self.cacheRoleName)
                self.allRoles.append(self.cacheRole)
                self.changed = 1   
            except:
                self.log.exception("AuthorizationUIPanel.CreateRole: Failed to add role")
               
        # Create subjects.
        for dn in cachedDns:
            subject =  X509Subject(dn)
            cachedSubjects.append(subject)
       
        # Only add subjects that are new in the cache.
        if self.cacheRole != None:
            subjects = self.cacheRole.subjects
                
            sList = []
                
            for subject in cachedSubjects:
                if not subject in subjects:
                    try:
                        self.cacheRole.AddSubject(subject)
                        self.changed = 1
                    except:
                        self.log.exception("AuthorizationUIPanel.__AddCachedSubjects: AddSubjectToRole failed")
                     
    def __initTree(self):
        '''
        Add roles and people to tree.
        '''
        imageList = wxImageList(18,18)
        self.bulletId = imageList.Add(icons.getBulletBitmap())
        self.participantId = imageList.Add(icons.getDefaultParticipantBitmap())
        self.tree.AssignImageList(imageList)
        
        # Add items to the tree
        self.root = self.tree.AddRoot("", -1, -1)
        
        for role in self.allRoles:
            # Add role
            roleId = self.tree.AppendItem(self.root, role.name, self.bulletId, self.bulletId)
            self.roleToTreeIdDict[role] = roleId
            self.tree.SetItemBold(roleId)
            self.tree.SetItemData(roleId, wxTreeItemData(role))

            # For each role, add people.
            for person in role.subjects:
                personId = self.tree.AppendItem(roleId, person.GetCN(),  self.participantId ,  self.participantId)
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
        if self.staticBox:
            self.staticBox.SetLabel("Actions for %s"%self.tree.GetItemText(currentItem))
            
    def __setEvents(self):
        '''
        Set events.
        '''
        EVT_RIGHT_DOWN(self.tree, self.OnRightClick)
       
       
        #EVT_TREE_END_LABEL_EDIT(self.tree, self.tree.GetId(), self.EndRename)
        EVT_TREE_BEGIN_DRAG(self.tree, self.tree.GetId(), self.BeginDrag)
        EVT_TREE_END_DRAG(self.tree, self.tree.GetId(), self.EndDrag)
        EVT_TREE_SEL_CHANGED(self.tree, self.tree.GetId(), self.OnSelect)

        EVT_CHECKLISTBOX(self.actionList, self.actionList.GetId(), self.CheckAction)
        EVT_LISTBOX(self, self.actionList.GetId(), self.SelectAction)
             
        EVT_MENU(self, self.ID_PERSON_ADDPERSON, self.AddPerson)
        #EVT_MENU(self, self.ID_PERSON_ADDROLE, self.CreateRole)
        EVT_MENU(self, self.ID_PERSON_DELETE, self.RemovePerson)
        #EVT_MENU(self, self.ID_PERSON_RENAME, self.Rename)
        EVT_MENU(self, self.ID_PERSON_COPY, self.Copy)
        EVT_MENU(self, self.ID_PERSON_PASTE, self.Paste)
        EVT_MENU(self, self.ID_PERSON_PROPERTIES, self.OpenPersonProperties)

        EVT_MENU(self, self.ID_ROLE_ADDPERSON, self.AddPerson)
        EVT_MENU(self, self.ID_ROLE_ADDROLE, self.CreateRole)
        EVT_MENU(self, self.ID_ROLE_REMOVEROLE, self.RemoveRole)
        
        EVT_SASH_DRAGGED(self, self.ID_WINDOW_LEFT, self.__OnSashDrag)
        EVT_SIZE(self, self.__OnSize)

    def __OnSashDrag(self, event):
        '''
        Called when a user drags the sash window.
        '''
        if event.GetDragStatus() == wxSASH_STATUS_OUT_OF_RANGE:
            # out of range
            return

        eID = event.GetId()
        
        if eID == self.ID_WINDOW_LEFT:
            width = event.GetDragRect().width
            self.leftSashWindow.SetDefaultSize(wxSize(width, 1000))
                                           
        wxLayoutAlgorithm().LayoutWindow(self, self.actionPanel)
        self.actionPanel.Refresh()
                                                
    def __OnSize(self, event = None):
        '''
        Called when a user resizes the window.
        '''
        wxLayoutAlgorithm().LayoutWindow(self, self.actionPanel)
              
    def __participantInRole(self, roleId, person):
        '''
        Check to see if a person is added to a role.

        @param roleId: tree id for a role.
        @type name: wxTreeId.

        @param person: person to check.
        @type name: Subject.

        @return: I if person is in role, otherwise 0.
        '''
        role = self.tree.GetItemData(roleId).GetData()
        list = role.subjects

        for l in list:
            if l.name == person.name:
                return 1
        return 0
    
    def __isRole(self, treeId):
        '''
        Check to see if a tree id is a role

        @param treeId: tree id for item to check.
        @type name: wxTreeId.

        @return: I if the tree id is a role, otherwise 0.
        '''
        role = self.tree.GetItemData(treeId).GetData()

        return role in self.allRoles
    
    def __listActions(self, role):
        '''
        List actions for a role.

        @param role: role object.
        @type name: Role.

        @return: a list of actions for the role.
        '''
        actions = []
        
        for a in self.allActions:
            for r in a.GetRoles():
                if r.name == role.name:
                    #if isinstance(r, SOAPpy.Types.structType):
                        #a.RemoveRole(r)
                        #a.AddRole(CreateRoleFromStruct(r))
                    actions.append(a)
        return actions
            
    def __setMenus(self):
        '''
        Initiate menus that are shown when user right-clicks a tree item
        '''
        # Menu when user clicks the tree.
        self.treeMenu = wxMenu()
        self.treeMenu.Append(self.ID_ROLE_ADDROLE,"Create Role",
                             "Create a new role")

        # Menu when user clicks on a role item
        self.roleMenu = wxMenu()
        self.roleMenu.Append(self.ID_ROLE_ADDPERSON,"Add Person",
                             "Add participant to selected role")
        self.roleMenu.AppendSeparator()
        self.roleMenu.Append(self.ID_ROLE_ADDROLE,"Create Role",
                             "Create a new role")
        self.roleMenu.Append(self.ID_ROLE_REMOVEROLE,"Remove Role",
                             "Remove selected role")
        self.roleMenu.AppendSeparator()
        self.roleMenu.Append(self.ID_PERSON_PASTE,"Paste",
                             "Paste")
        
        #self.roleMenu.Append(self.ID_ROLE_ADDPERSON,"Create Role",
        #                     "Create new role")
     
        # Menu when user clicks on a participant/group
        self.personMenu = wxMenu()
        self.personMenu.Append(self.ID_PERSON_ADDPERSON,"Add Person",
                                   "New participant")
        self.personMenu.Append(self.ID_PERSON_DELETE,"Remove Person",
                                   "Remove this role from venue")
        self.personMenu.AppendSeparator()
        #self.personMenu.Append(self.ID_PERSON_RENAME,"Rename",
        #                           "Rename this participant")
        self.personMenu.Append(self.ID_PERSON_COPY,"Copy",
                                   "Copy this participant")

        self.personMenu.Append(self.ID_PERSON_PASTE,"Paste",
                                   "Paste")
        self.personMenu.AppendSeparator()
        self.personMenu.Append(self.ID_PERSON_PROPERTIES,"Properties",
                               "View distinguished name")
       
    def __layout(self):
        '''
        Handles UI layout,
        '''
        # Role Panel
        mainSizer = wxBoxSizer(wxHORIZONTAL)
        staticBox = wxStaticBox(self.rolePanel, -1, "Roles")
        staticBox.SetFont(wxFont(wxDEFAULT, wxNORMAL, wxNORMAL, wxBOLD))
        sizer  = wxStaticBoxSizer(staticBox,
                                  wxVERTICAL)
        sizer.Add(self.tree, 1, wxEXPAND|wxALL, 10)
        mainSizer.Add(sizer, 1, wxEXPAND|wxALL, 10) 
        self.rolePanel.SetSizer(mainSizer)

        # Action Panel
        mainSizer = wxBoxSizer(wxHORIZONTAL)
        self.staticBox = wxStaticBox(self.actionPanel, -1, "Actions")
        self.staticBox.SetFont(wxFont(wxDEFAULT, wxNORMAL, wxNORMAL, wxBOLD))
        sizer  = wxStaticBoxSizer(self.staticBox,
                                  wxVERTICAL)
        sizer.Add(self.actionList, 1, wxEXPAND|wxALL, 10)
        mainSizer.Add(sizer, 1, wxEXPAND|wxALL, 10) 
        self.actionPanel.SetSizer(mainSizer)

        # Sash windows
        self.leftSashWindow.SetDefaultSize(wxSize(400, 60))
        self.leftSashWindow.SetOrientation(wxLAYOUT_VERTICAL)
        self.leftSashWindow.SetAlignment(wxLAYOUT_LEFT)
        self.leftSashWindow.SetSashVisible(wxSASH_RIGHT, TRUE)
        
    def Copy(self, event):
        '''
        Is called when user selects to copy a tree item.
        '''
        # Store the copied item so we can paste it
        self.copyItem = self.tree.GetSelection()
       
    def Paste(self, event):
        '''
        Paste last copied tree item.
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
                self.changed = 1
                personId = self.tree.AppendItem(roleId, person.GetCN(),
                                                self.participantId,
                                                self.participantId)
                self.tree.SetItemData(personId, wxTreeItemData(person))
                role.AddSubject(person)

            else:
                MessageDialog(self, "%s is already added to %s"%(person.name, role.name), "Error") 

    def OpenPersonProperties(self, event):
        '''
        Show profile dialog for a subject.
        '''
        selectedItem = self.tree.GetSelection()
        if not selectedItem.IsOk():
            return

        person = self.tree.GetItemData(selectedItem).GetData()
        
        dialog = PersonPropertiesDialog(self, -1, "Properties for %s"%person.GetCN(), person)
        dialog.ShowModal()
        dialog.Destroy()
        
    def SelectAction(self, event):
        '''
        Called when a user selects a checklistbox item and
        makes the list behave as if the user checked a the list
        box of that item.
        '''
        index = event.GetInt()
        checked = self.actionList.IsChecked(index)
        if checked:
            self.actionList.Check(index, 0)
        else:
            self.actionList.Check(index, 1)

        self.__SetAction(index)


    def __SetAction(self, index):
        actionName = self.actionList.GetString(index)
        checked = self.actionList.IsChecked(index)

        # Get current action object
        currentAction = None

        for action in self.allActions:
            if action.name == actionName:
                currentAction = action

        # Check correct action and add/remove current role to the action.
        if not checked:
            self.changed = 1
            if currentAction:
                # Remove action
                currentAction.RemoveRole(self.currentRole)
        else:
            self.changed = 1
            if currentAction:
                # Add action
                currentAction.AddRole(self.currentRole)
                    
    def CheckAction(self, event):
        '''
        Is called when user checks an action.
        '''
        if IsWindows():
            
            self.__SetAction(event.GetInt())
            return
       
        index = event.GetInt()
        actionName = self.actionList.GetString(index)
        checked = self.actionList.IsChecked(index)

        # Make select action work as check action for usability reasons.
        # Thus, ignore check action events.
        if checked:
            self.actionList.Check(index, 0)
        else:
            self.actionList.Check(index, 1)

      
    def OnSelect(self, event):
        '''
        Is called when user selects a new item in the tree.
        '''
        selectedItem = event.GetItem()
     
        if selectedItem.IsOk():
            role = self.tree.GetItemData(selectedItem).GetData()
            if not self.__isRole(selectedItem):
                # This is actually a person; Get parent instead.
                selectedItem = self.tree.GetItemParent(selectedItem)
                role = self.tree.GetItemData(selectedItem).GetData()
                            
            # First, uncheck all actions for this role.
            nrOfItems = self.actionList.GetCount()
            
            for index in range(nrOfItems):
                self.actionList.Check(index, 0)
                               
            if self.__isRole(selectedItem):
                self.currentRole = role

                actions = self.__listActions(role)
                for action in actions:
                    index = self.actionList.FindString(action.name)
                    
                    # Check correct actions for this role.
                    if index is not wxNOT_FOUND:
                        self.actionList.Check(index, 1)
                                       
            if self.staticBox:
                self.staticBox.SetLabel("Actions for %s"%self.currentRole.name)

    def BeginDrag(self, event):
        '''
        Is called when a user starts to drag a tree item.
        '''
        self.dragItem = event.GetItem()
       
        # Need to call Allow to get an EVT_TREE_END_DRAG event
        event.Allow()

   
    def EndDrag(self, event):
        '''
        Is called when a user stops dragging a tree item.
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

                # Remove subject from role
                try:
                    oldRole.RemoveSubject(item)
                except DefaultIdentityNotRemovable:
                    message = wxMessageDialog(self, 'You can not remove yourself from role %s.'%(role.name), 'Error',  style = wxOK|wxICON_INFORMATION)
                    # Do not use modal; it hangs the dialog.
                    message.Show()
                    return
                    
                # Add subject to role
                role.AddSubject(item)
                                    
                # Update tree
                self.changed = 1
                self.tree.Delete(self.dragItem)
                itemId = self.tree.AppendItem(parent, item.GetCN(), self.participantId,
                                              self.participantId)
                self.tree.SetItemData(itemId, wxTreeItemData(item))
                                
            else:
                # This message doesn't show up under Windows. Weird.
                message = wxMessageDialog(self, '%s is already added to %s'%(item.name, role.name), 'Error',  style = wxOK|wxICON_INFORMATION)
                # Do not use modal; it hangs the dialog.
                message.Show()

    def CreateRole(self, event ):
        '''
        Create new role
        '''
        # Open dialog for user input.
        createRoleDialog = CreateRoleDialog(self, -1, 'Create Role')
        newRole = None
                
        if createRoleDialog.ShowModal() == wxID_OK:
            name =  createRoleDialog.GetName()
            # Add role

            for role in self.allRoles:
                if role.name == name:
                    MessageDialog(self, "A role named %s already exists."%(name), "Error") 
                    return None
                        
            self.changed = 1
            newRole = Role(name)
            roleId = self.tree.AppendItem(self.root, newRole.name, self.bulletId,
                                          self.bulletId)
            self.tree.SetItemBold(roleId)
            self.tree.SetItemData(roleId, wxTreeItemData(newRole))
            self.allRoles.append(newRole)
            self.roleToTreeIdDict[newRole] = roleId
            
        return newRole
      
    def CreateAction(self, event):
        '''
        Create new action.
        '''
        actionDialog = CreateActionDialog(self, -1, 'Create Action')

        if actionDialog.ShowModal() == wxID_OK:
            actionName = actionDialog.GetName()
            action = Action(name)
            self.allActions.append(action)
            self.actionList.InsertItems([action.name], 0)
            self.changed = 1
            
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
                    self.actionList.Delete(itemToRemove)
                    self.changed = 1
            
    def Apply(self, event = None):
        '''
        Set current security configuration of roles and actions in the
        authorization manager.
        '''
        if not self.changed:
            # Ignore if user didn't change anything 
            return
            
        domImpl = xml.dom.minidom.getDOMImplementation()
        authDoc = domImpl.createDocument(xml.dom.minidom.EMPTY_NAMESPACE,
                                         "AuthorizationPolicy", None)
        authP = authDoc.documentElement

        for r in self.allRoles:
            if r.name is not self.cacheRoleName:
                authP.appendChild(r.ToXML(authDoc))
        
        for a in self.allActions:
            authP.appendChild(a.ToXML(authDoc, 1))

        rval = authDoc.toxml()

        # Update authorization manager
        try:
            if self.changed:
                self.authClient.ImportPolicy(rval)
        except:
            self.log.exception("AuthorizationUIPanel.Apply:Couldn't update authorization manager.")
            MessageDialog(None, "Set authorizaton failed", "Error")
           
    def AddPerson(self, event):
        '''
        Adds a new person to a role.
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
            self.changed = 1
            
            # Save subject
            activeRole.AddSubject(subject)
                        
            # Insert subject in tree
            index = self.roleToTreeIdDict[activeRole]
            subjectId = self.tree.AppendItem(index, subject.GetCN(),
                                             self.participantId, self.participantId)
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
                self.changed = 1

                try:
                    role.RemoveSubject(item)

                    # delete item from tree and dictionary
                    self.tree.Delete(treeId)

                except DefaultIdentityNotRemovable:
                    MessageDialog(self, "You are not allowed to remove yourself from role %s"%role.name)
        else:
            MessageDialog(self, "Please select the person you want to remove")
            
    def RemoveRole(self, event):
        '''
        Remove a role from the tree.
        '''
        treeId = self.tree.GetSelection()
       
        if treeId.IsOk() and treeId != self.root:
            role = self.tree.GetItemData(treeId).GetData()

            if not role in self.allRoles:
                MessageDialog(self, "Select the role you want to remove.", "Notification")
                return
            
            if treeId != self.root:
                message = wxMessageDialog(self, "Are you sure you want to remove '%s'?"%role.name,
                                          style = wxICON_QUESTION | wxYES_NO | wxNO_DEFAULT)
                
                if message.ShowModal() == wxID_YES:
                    self.changed = 1
                    
                    # delete item from tree and dictionary
                    self.tree.Delete(treeId)
                    self.allRoles.remove(role)
                                            
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
        Opens a menu when user right-clicks a tree item. 
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

        else:
            self.PopupMenu(self.treeMenu,
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
        '''
        Get name of the new action to create.

        @return: name string of the new action.
        '''
        return self.actionTextCtrl.GetValue()

    def __layout(self):
        '''
        Handle UI layout.
        '''
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
                                     "Enter the distinguished name of the person you want to add to '%s' role" %role.name)
        self.dnTextCtrl = wxTextCtrl(self,-1, "")
        self.okButton = wxButton(self, wxID_OK, "Ok")
        self.cancelButton =  wxButton(self, wxID_CANCEL, "Cancel")

        self.__layout()

    def GetName(self):
        '''
        Get distinguished name of the person to add.

        @return: name string of the new subject.
        '''
        return self.dnTextCtrl.GetValue()

    def __layout(self):
        '''
        Hanle UI layout.
        '''
        mainSizer = wxBoxSizer(wxHORIZONTAL)
        box = wxBoxSizer(wxVERTICAL)
        sizer = wxBoxSizer(wxHORIZONTAL)
        
        box.Add(5,5)
        box.Add(self.infoText, 0, wxEXPAND|wxALL, 5)
        
        sizer = wxBoxSizer(wxHORIZONTAL)
        sizer.Add(wxStaticText(self, -1, "Distinguished Name: "), 0, wxALIGN_CENTER)
        sizer.Add(self.dnTextCtrl, 1, wxALIGN_CENTER, 2)
        box.Add(sizer, 1, wxEXPAND|wxALL, 5)

        box.Add(wxStaticLine(self, -1), 0, wxEXPAND|wxALL, 5)
        sizer2 = wxBoxSizer(wxHORIZONTAL)
        sizer2.Add(self.okButton, 0, wxCENTER | wxRIGHT, 10)
        sizer2.Add(self.cancelButton, 0, wxCENTER)
        box.Add(sizer2, 0, wxCENTER)

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
                          style=wxOK|wxRESIZE_BORDER|wxCAPTION)
        self.SetSize(wxSize(300, 150))
        self.infoText = wxStaticText(self, -1,
                                     "Enter the name of the new role.")
        self.dnTextCtrl = wxTextCtrl(self,-1, "")
        self.okButton = wxButton(self, wxID_OK, "Ok")
        self.cancelButton =  wxButton(self, wxID_CANCEL, "Cancel")

        self.__layout()

    def GetName(self):
        '''
        Get name of the role to create.

        @return: name string of the new role.
        '''
        return self.dnTextCtrl.GetValue()

    def __layout(self):
        '''
        Handle UI layout.
        '''
        mainSizer = wxBoxSizer(wxHORIZONTAL)
        box = wxBoxSizer(wxVERTICAL)
        sizer = wxBoxSizer(wxHORIZONTAL)

        box.Add(5,5)
        box.Add(self.infoText, 0, wxEXPAND|wxALL, 5)
        
        sizer = wxBoxSizer(wxHORIZONTAL)
        sizer.Add(wxStaticText(self, -1, "Name: "), 0, wxALIGN_CENTER)
        sizer.Add(self.dnTextCtrl, 1, wxALIGN_CENTER, 2)
        box.Add(sizer, 1, wxEXPAND|wxALL, 5)

        box.Add(wxStaticLine(self, -1), 0, wxEXPAND|wxALL, 5)
        sizer2 = wxBoxSizer(wxHORIZONTAL)
        sizer2.Add(self.okButton, 0, wxCENTER | wxRIGHT, 10)
        sizer2.Add(self.cancelButton, 0, wxCENTER)
        box.Add(sizer2, 0, wxCENTER|wxTOP, 5)

        mainSizer.Add(box, 1, wxALL | wxEXPAND, 10)
        
        self.SetAutoLayout(1)
        self.SetSizer(mainSizer)
        self.Layout()

class PersonPropertiesDialog(wxDialog):
    '''
    Dialog showing a persons properties.
    '''
    def __init__(self, parent, id, title, person):
        wxDialog.__init__(self, parent, id, title,
                          style=wxRESIZE_BORDER|wxDEFAULT_DIALOG_STYLE)
        self.dnText = wxStaticText(self, -1, 'Distinguished Name: ')
        self.dnCtrl = wxTextCtrl(self, -1, person.name, size = wxSize(450, 20),
                                 style =  wxTE_READONLY)
        self.okButton = wxButton(self, wxID_OK, "Ok")
        self.__layout()
        
    def __layout(self):
        sizer = wxBoxSizer(wxVERTICAL)
        s2 = wxBoxSizer(wxHORIZONTAL)
        s2.Add(self.dnText, 0, wxEXPAND)
        s2.Add(self.dnCtrl, 1, wxEXPAND)
        sizer.Add(s2, 0, wxEXPAND|wxALL, 10)

        sizer.Add(wxStaticLine(self, -1), 0, wxEXPAND|wxLEFT|wxRIGHT, 5)
        sizer.Add(self.okButton, 0, wxCENTER|wxALL, 10)

        self.SetAutoLayout(1)
        self.SetSizer(sizer)
        sizer.Fit(self)
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

class AuthorizationUIDialog(wxDialog):
    def __init__(self, parent, id, title, log):
        '''
        Encapsulates an AuthorizationUIPanel object in a dialog. 
        '''
        wxDialog.__init__(self, parent, id, title,
                          size = wxSize(800,300),
                          style=wxDEFAULT_DIALOG_STYLE|wxRESIZE_BORDER)
        self.panel = AuthorizationUIPanel(self, -1, log)
        self.okButton = wxButton(self, wxID_OK, "Ok")
        self.cancelButton = wxButton(self, wxID_CANCEL, "Cancel")

        self.__layout()
               
    def ConnectToAuthManager(self, url):
        '''
        Connect to authorization manager located at url.
        '''
        self.panel.ConnectToAuthManager(url)

    def Apply(self):
        '''
        Update authorization manager with current roles and actions.
        '''
        self.panel.Apply()

    def __layout(self):
        '''
        Handle UI layout.
        '''
        mainSizer = wxBoxSizer(wxVERTICAL)
        mainSizer.Add(self.panel, 1, wxEXPAND|wxBOTTOM, 5)

        buttonSizer = wxBoxSizer(wxHORIZONTAL)
        buttonSizer.Add(self.okButton, 0, wxALL, 5)
        buttonSizer.Add(self.cancelButton, 0, wxALL, 5)
        mainSizer.Add(buttonSizer, 0, wxCENTER)

        self.SetAutoLayout(1)
        self.SetSizer(mainSizer)
        self.Layout()


def InitLogging(debug = 1, l = None):
        """
        This method sets up logging that prints debug and error messages.
        
        **Arguments**
        
        *debug* If debug is set to 1, log messages will be printed to file
        and command window
 
        *log* Name of log file. If set to None, <appName>.log is used
        """

        logFormat = "%(name)-17s %(asctime)s %(levelname)-5s %(message)s"
        log = logging.getLogger('AuthorizationUI')
        log.setLevel(logging.DEBUG)
        
        # Log to file
        if l == None:
            logFile = 'AuthorizationUI.log'
        else:
            logFile = l
      
        fileHandler = logging.FileHandler(logFile)
        fileHandler.setFormatter(logging.Formatter(logFormat))
        log.addHandler(fileHandler)

        # If debug mode is on, log to command window too
        if debug:
            hdlr = logging.StreamHandler()
            hdlr.setFormatter(logging.Formatter(logFormat))
            log.addHandler(hdlr)

        return log
    

if __name__ == "__main__":
    import logging

    app = Toolkit.WXGUIApplication()
    app.Initialize()
        
    if len(sys.argv) == 2:
        uri = sys.argv[1]
    else:
        uri = "https://localhost:8000/VenueServer"
        
    try:
        am = AuthorizationManagerIW(uri)
    except Exception, e:
        print "Couldn't get authorization manager: ", e
        sys.exit(1)

    #am.TestImportExport(p1)
    #p2 = am.GetPolicy()
    #am.ImportPolicy(p2)
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
    
    
    f = AuthorizationUIDialog(None, -1, "Manage Roles", log)
    f.ConnectToAuthManager(uri)
    if f.ShowModal() == wxID_OK:
        f.panel.Apply()
    f.Destroy()
    wxapp.SetTopWindow(f)
    wxapp.MainLoop()

    #roles = AddPeopleDialog(None, -1, "Manage Roles", am)
    #roles.ShowModal()
    #roles.Destroy()
   
