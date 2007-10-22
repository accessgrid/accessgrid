#-----------------------------------------------------------------------------
# Name:        AuthorizationUI.py
# Purpose:     Roles Management UI
#
# Author:      Susanne Lefvert 
#
#
# Created:     2003/08/07
# RCS_ID:      $Id: AuthorizationUI.py,v 1.43 2007-10-22 20:51:43 turam Exp $ 
# Copyright:   (c) 2003
# Licence:     See COPYING.txt
#-----------------------------------------------------------------------------
"""
"""
__revision__ = "$Id: AuthorizationUI.py,v 1.43 2007-10-22 20:51:43 turam Exp $"
__docformat__ = "restructuredtext en"

import string
import copy
import xml.dom.minidom

import wx
from AccessGrid.UIUtilities import MessageDialog, ErrorDialog

from AccessGrid import Toolkit
from AccessGrid.Platform import IsWindows,IsOSX
from AccessGrid.ClientProfile import ClientProfileCache
from AccessGrid.interfaces.AuthorizationManager_client import AuthorizationManagerIW
from AccessGrid.Venue import VenueIW
from AccessGrid.Security.X509Subject import X509Subject    
from AccessGrid.Security.Role import Role, DefaultIdentityNotRemovable
from AccessGrid.Security.Action import Action 
from AccessGrid import icons

class AuthorizationUIPanel(wx.Panel):
    '''
    This class shows a tree of people structured in roles. When a user selects
    a role from the tree, available actions for the role are displayed. Actions to
    modify roles are available, such as Create/Remove Role and Add/Remove Person to role.
    '''
    ID_ROLE_ADDPERSON = wx.NewId()
    ID_ROLE_ADDROLE = wx.NewId()
    ID_ROLE_REMOVEROLE = wx.NewId()
    ID_PERSON_ADDPERSON = wx.NewId()
    ID_PERSON_DELETE = wx.NewId()
    #ID_PERSON_RENAME = wx.NewId()
    ID_PERSON_COPY = wx.NewId()
    ID_PERSON_PASTE = wx.NewId()
    ID_PERSON_PROPERTIES = wx.NewId()

    ID_WINDOW_LEFT = wx.NewId() 
         
    def __init__(self, parent, id, log, requireCertOption=0):
        wx.Panel.__init__(self, parent, id, wx.DefaultPosition)
        self.log = log
        self.requireCertOption = requireCertOption
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
        
        self.mainSizer = wx.BoxSizer(wx.VERTICAL)
        self.SetSizer(self.mainSizer)
        
        # Create ui componentes
        self.leftSashWindow = wx.SashLayoutWindow(self, self.ID_WINDOW_LEFT)
        self.leftSashWindow.SetDefaultSize((350, 1000))
        self.leftSashWindow.SetOrientation(wx.LAYOUT_VERTICAL)
        self.leftSashWindow.SetAlignment(wx.LAYOUT_LEFT)
        self.leftSashWindow.SetSashVisible(wx.SASH_RIGHT, True)

        self.rolePanel = wx.Panel(self.leftSashWindow ,  wx.NewId(),
                                 style = wx.SUNKEN_BORDER, 
                                 size = wx.Size(350, -1))
        self.roleTitle = wx.StaticText(self.rolePanel, -1, "Roles",
                      size=wx.Size(350,-1), style=wx.ALIGN_LEFT)
        
        if IsOSX():
            self.roleTitle.SetFont(wx.Font(12,wx.NORMAL,wx.NORMAL,wx.BOLD))
        else:
            self.roleTitle.SetFont(wx.Font(wx.DEFAULT,wx.NORMAL,wx.NORMAL,wx.BOLD))

        self.actionPanel = wx.Panel(self,  wx.NewId(),
                                   style = wx.SUNKEN_BORDER)
        self.actionTitle = wx.StaticText(self.actionPanel, -1, "Actions", 
                    size=wx.Size(100,-1), 
                    style=wx.ALIGN_LEFT)
        if IsOSX():
            self.actionTitle.SetFont(wx.Font(12,wx.NORMAL,wx.NORMAL,wx.BOLD))
        else:
            self.actionTitle.SetFont(wx.Font(wx.DEFAULT,wx.NORMAL,wx.NORMAL,wx.BOLD))

        self.tree = wx.TreeCtrl(self.rolePanel, wx.NewId(), wx.DefaultPosition, 
                               wx.DefaultSize, style = wx.TR_HAS_BUTTONS |
                               wx.TR_LINES_AT_ROOT | wx.TR_HIDE_ROOT)
        if IsOSX():
            self.actionList = wx.ListBox(self.actionPanel, wx.NewId(),style=wx.LB_MULTIPLE)
        else:
            self.actionList = wx.CheckListBox(self.actionPanel, wx.NewId())
               
        self.SetSize(wx.Size(800,800))

        if self.requireCertOption:
            self.requireCert = wx.CheckBox(self.rolePanel,-1,"Require user to present certificate")
        
        self.mainSizer.Add(self.leftSashWindow,0,wx.EXPAND)    


        self.__setMenus()
        self.__setEvents()
        self.__Layout()
        
    def ConnectToAuthManager(self, authManagerIW):
        '''
        Connects to the specified authorization manager. After a successful connect,
        roles and actions are displayed in the UI.

        '''
        self.authClient = authManagerIW

        roles = []

        # Is a certificate required?
        try:
            requireCertFlag = self.authClient.IsIdentificationRequired()
            if self.requireCertOption:
                self.requireCert.SetValue(requireCertFlag)
        except Exception,e:
            self.log.exception("Error calling IsIdentificationRequired; assume old server")
            requireCertFlag = 0

        # Get roles
        try:
            for r in self.authClient.ListRoles():
                self.allRoles.append(r)
        except:
            self.log.exception("AuthorizationUIPanel.ConnectToAuthManager:Failed to list roles.")


        # Add cached subjects.
        self.cacheRoleName = 'Registered People'
       
        # Check if we already have the Registered People role.
        #for r in self.allRoles:
        #    if r.GetName() == self.cacheRoleName:
        #        self.cacheRole = r
               
        # Add Registered People role.
        if not self.cacheRole:
            self.cacheRole = Role(self.cacheRoleName)
            self.allRoles.append(self.cacheRole)

        self.__AddCachedSubjects()
                        
        # Get Actions
        try:
           
            self.allActions = self.authClient.ListActions()
            self.allActions.sort()
            actions = []
            for action in self.allActions:
                actions.append(action.name)

            self.actionList.InsertItems(actions, 0)

        except:
            self.log.exception("AuthorizationUIPanel.ConnectToAuthManager: List actions failed.")
            self.allActions = []
            #MessageDialog(None, "Failed to load actions", "Error")

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
            
#             for profile in self.venue.GetCachedProfiles():
#                 dn = profile.GetDistinguishedName()
#                 if dn:
#                     cachedDns.append(dn)
        except:
            self.log.exception("AuthorizationUI.__AddCachedSubjects: Failed to load remote profiles. Only venues have profile caches so this may be the case when connecting to an application. Not critical.")

        # Create subjects.
        for dn in cachedDns:
            subject =  X509Subject(dn)
            cachedSubjects.append(subject)
       
        # Only add subjects that are new in the cache.
        if self.cacheRole != None:
            subjects = self.cacheRole.GetSubjects()
                
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
        imageList = wx.ImageList(22,22)
        self.bulletId = imageList.Add(icons.getBulletBitmap())
        self.participantId = imageList.Add(icons.getDefaultParticipantBitmap())
        self.tree.AssignImageList(imageList)
        
        # Add items to the tree
        self.root = self.tree.AddRoot("", -1, -1)
        
        for role in self.allRoles:
            # Add role
            roleId = self.tree.AppendItem(self.root, role.name, self.bulletId, self.bulletId)
            self.roleToTreeIdDict[role.name] = roleId
            self.tree.SetItemBold(roleId)
            self.tree.SetItemData(roleId, wx.TreeItemData(role))

            # For each role, add people.
            for person in role.subjects:
                personId = self.tree.AppendItem(roleId, person.GetCN(),  self.participantId ,  self.participantId)
                self.tree.SetItemData(personId, wx.TreeItemData(person))

            # Sort the tree
            if self.tree.GetChildrenCount(roleId)> 0:
                self.tree.SortChildren(roleId)

        if self.tree.GetChildrenCount(self.root)> 0:
            self.tree.SortChildren(self.root)

        cookie = 0
        if wx.VERSION[0] <= 2 and wx.VERSION[1] <= 4:
            firstItem, cookie = self.tree.GetFirstChild(self.root, cookie)
        else:
            firstItem, cookie = self.tree.GetFirstChild(self.root)
        self.tree.SelectItem(firstItem)

        currentItem = self.tree.GetSelection()
        self.actionTitle.SetLabel("Actions for %s"%self.tree.GetItemText(currentItem))
            
    def __setEvents(self):
        '''
        Set events.
        '''
        wx.EVT_RIGHT_DOWN(self.tree, self.OnRightClick)

        #wx.EVT_TREE_END_LABEL_EDIT(self.tree, self.tree.GetId(), self.EndRename)
        wx.EVT_TREE_BEGIN_DRAG(self.tree, self.tree.GetId(), self.BeginDrag)
        wx.EVT_TREE_END_DRAG(self.tree, self.tree.GetId(), self.EndDrag)
        wx.EVT_TREE_SEL_CHANGED(self.tree, self.tree.GetId(), self.OnSelect)

        wx.EVT_CHECKLISTBOX(self.actionList, self.actionList.GetId(),
                         self.CheckAction)
        wx.EVT_LISTBOX(self, self.actionList.GetId(), self.SelectAction)
             
        wx.EVT_MENU(self, self.ID_PERSON_ADDPERSON, self.AddPerson)
        #wx.EVT_MENU(self, self.ID_PERSON_ADDROLE, self.CreateRole)
        wx.EVT_MENU(self, self.ID_PERSON_DELETE, self.RemovePerson)
        #wx.EVT_MENU(self, self.ID_PERSON_RENAME, self.Rename)
        wx.EVT_MENU(self, self.ID_PERSON_COPY, self.Copy)
        wx.EVT_MENU(self, self.ID_PERSON_PASTE, self.Paste)
        wx.EVT_MENU(self, self.ID_PERSON_PROPERTIES, self.OpenPersonProperties)

        wx.EVT_MENU(self, self.ID_ROLE_ADDPERSON, self.AddPerson)
        wx.EVT_MENU(self, self.ID_ROLE_ADDROLE, self.CreateRole)
        wx.EVT_MENU(self, self.ID_ROLE_REMOVEROLE, self.RemoveRole)
        
        wx.EVT_SASH_DRAGGED(self, self.ID_WINDOW_LEFT, self.__OnSashDrag)
        wx.EVT_SIZE(self, self.__OnSize)

    def __OnSashDrag(self, event):
        '''
        Called when a user drags the sash window.
        '''
        eID = event.GetId()
        
        if eID == self.ID_WINDOW_LEFT:
            width = event.GetDragRect().width
            self.leftSashWindow.SetDefaultSize(wx.Size(width, -1))
         
        wx.LayoutAlgorithm().LayoutWindow(self, self.actionPanel)
        self.actionPanel.Refresh()
        s = self.leftSashWindow.GetSize()
        self.rolePanel.SetSize(wx.Size(s.width-5, s.height))
                                                
    def __OnSize(self, event = None):
        '''
        Called when a user resizes the window.
        '''
        wx.LayoutAlgorithm().LayoutWindow(self, self.actionPanel)
        s = self.leftSashWindow.GetSize()
        self.rolePanel.SetSize(wx.Size(s.width-5, s.height))
              
    def __participantInRole(self, roleId, person):
        '''
        Check to see if a person is added to a role.

        @param roleId: tree id for a role.
        @type name: wx.TreeId.

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
        @type name: wx.TreeId.

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
                    actions.append(a)
        return actions
            
    def __setMenus(self):
        '''
        Initiate menus that are shown when user right-clicks a tree item
        '''
        # Menu when user clicks the tree.
        self.treeMenu = wx.Menu()
        self.treeMenu.Append(self.ID_ROLE_ADDROLE,"Create Role",
                             "Create a new role")

        # Menu when user clicks on a role item
        self.roleMenu = wx.Menu()
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
        self.personMenu = wx.Menu()
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
       
    def __Layout(self):
        '''
        Handles UI layout,
        '''
        # Role Panel
        mainSizer = wx.BoxSizer(wx.VERTICAL)
        mainSizer.Add(self.roleTitle,0,wx.EXPAND|wx.ALL,10)
        mainSizer.Add(self.tree,1,wx.EXPAND|wx.LEFT|wx.RIGHT|wx.BOTTOM,10)
        if self.requireCertOption:
            mainSizer.Add(self.requireCert,0,wx.EXPAND,10)
        self.rolePanel.SetSizer(mainSizer)
        mainSizer.Fit(self.rolePanel)
        self.rolePanel.SetAutoLayout(1)
       
        # Action Panel
        mainSizer2 = wx.BoxSizer(wx.VERTICAL)
        mainSizer2.Add(self.actionTitle,0,wx.EXPAND|wx.ALL,10)
        mainSizer2.Add(self.actionList,1,wx.EXPAND|wx.LEFT|wx.RIGHT|wx.BOTTOM,10)
        self.actionPanel.SetSizer(mainSizer2)
        mainSizer2.Fit(self.actionPanel)
        self.actionPanel.SetAutoLayout(1)
        
        sizer = wx.BoxSizer(wx.HORIZONTAL)
        sizer.Add(self.rolePanel, 1, wx.EXPAND)
        self.leftSashWindow.SetSizer(sizer)
        sizer.Fit(self.leftSashWindow)
        
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
                self.tree.SetItemData(personId, wx.TreeItemData(person))
                role.AddSubject(person)

                if self.tree.GetChildrenCount(roleId)> 0:
                    self.tree.SortChildren(roleId)

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
        if IsOSX():
            index = event.GetInt()
            self.__SetAction(index)
        else:
            index = event.GetInt()
            checked = self.actionList.IsChecked(index)
            if checked:
                self.actionList.Check(index, 0)
            else:
                self.actionList.Check(index, 1)

            self.__SetAction(index)


    def __SetAction(self, index):
        actionName = self.actionList.GetString(index)
        if IsOSX():
            checked = self.actionList.IsSelected(index)
        else:
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
        if IsOSX():
            checked = self.actionList.IsSelected(index)
        else:
            checked = self.actionList.IsChecked(index)

        # Make select action work as check action for usability reasons.
        # Thus, ignore check action events.
        if not IsOSX():
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
                if IsOSX():
                    self.actionList.Deselect(index)
                else:
                    self.actionList.Check(index, 0)
                               
            if self.__isRole(selectedItem):
                self.currentRole = role

                actions = self.__listActions(role)
                for action in actions:
                    index = self.actionList.FindString(action.name)
                    
                    # Check correct actions for this role.
                    if index is not wx.NOT_FOUND:
                        if IsOSX():
                            self.actionList.SetSelection(index)
                        else:
                            self.actionList.Check(index, 1)
            
            if self.currentRole:
                self.actionTitle.SetLabel("Actions for %s"%self.currentRole.name)

    def BeginDrag(self, event):
        '''
        Is called when a user starts to drag a tree item.
        '''
        self.dragItem = event.GetItem()
       
        # Need to call Allow to get an wx.EVT_TREE_END_DRAG event
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
                    message = wx.MessageDialog(self, 'You can not remove yourself from role %s.'%(role.name), 'Error',  style = wx.OK|wx.ICON_INFORMATION)
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
                self.tree.SetItemData(itemId, wx.TreeItemData(item))

                if self.tree.GetChildrenCount(parent)> 0:
                    self.tree.SortChildren(parent)
                                
            else:
                # This message doesn't show up under Windows. Weird.
                message = wx.MessageDialog(self, '%s is already added to %s'%(item.name, role.name), 'Error',  style = wx.OK|wx.ICON_INFORMATION)
                # Do not use modal; it hangs the dialog.
                message.Show()

    def CreateRole(self, event ):
        '''
        Create new role
        '''
        # Open dialog for user input.
        createRoleDialog = CreateRoleDialog(self, -1, 'Create Role')
        newRole = None
                
        if createRoleDialog.ShowModal() == wx.ID_OK:
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
            self.tree.SetItemData(roleId, wx.TreeItemData(newRole))
            self.allRoles.append(newRole)
            self.roleToTreeIdDict[newRole] = roleId
            
        return newRole
      
    def CreateAction(self, event):
        '''
        Create new action.
        '''
        actionDialog = CreateActionDialog(self, -1, 'Create Action')

        if actionDialog.ShowModal() == wx.ID_OK:
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
        if itemToRemove is wx.NOT_FOUND:
            MessageDialog(self, "Please select the action you want to remove",
                            style = wx.ICON_QUESTION)
            return
            
        # Make sure user want to remove this action
        text = self.actionList.GetString(itemToRemove)
        message = wx.MessageDialog(self, "Are you sure you want to remove '%s'?"%text,
                                  style = wx.ICON_QUESTION | wx.YES_NO | wx.NO_DEFAULT)
        
        if message.ShowModal() == wx.ID_YES:
            for action in self.allActions:
                if action.name == text:
                    self.actionList.Delete(itemToRemove)
                    self.changed = 1
            
    def Apply(self, event = None):
        '''
        Set current security configuration of roles and actions in the
        authorization manager.
        '''
        # - update certificate requirement
        if self.requireCertOption:
            try:
                self.authClient.RequireIdentification(self.requireCert.GetValue())
            except Exception,e:
                self.log.exception("Error calling RequireIdentification; assume old server")

        if not self.changed:
            # Ignore if user didn't change anything 
            return
            
        domImpl = xml.dom.minidom.getDOMImplementation()
        authDoc = domImpl.createDocument(xml.dom.minidom.EMPTY_NAMESPACE,
                                         "AuthorizationPolicy", None)
        authP = authDoc.documentElement

        for role in self.allRoles:
            if self.cacheRoleName != role.name:
                authP.appendChild(role.ToXML(authDoc))
        
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
                
        if addPersonDialog.ShowModal() == wx.ID_OK:
            # Get subject
            subject =  X509Subject(addPersonDialog.GetName())
            self.changed = 1
            
            # Save subject
            if self.__participantInRole(selectedItem, subject):
                MessageDialog(self, "%s is already added to %s"%(subject.name, activeRole.name), "Error") 
                return
            
            try:
                activeRole.AddSubject(subject)

            except:
                self.log.exception("Error adding person to role")
                MessageDialog(self, "Can not add person to this role.", "Notification")
                
                
            # Insert subject in tree
            index = self.roleToTreeIdDict[activeRole.GetName()]
            subjectId = self.tree.AppendItem(index, subject.GetCN(),
                                             self.participantId, self.participantId)
            self.tree.SetItemData(subjectId, wx.TreeItemData(subject))

            if self.tree.GetChildrenCount(index)> 0:
                    self.tree.SortChildren(index)

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

            message = wx.MessageDialog(self, "Are you sure you want to remove '%s'?"%item.name,
                                      style = wx.ICON_QUESTION | wx.YES_NO | wx.NO_DEFAULT)
                
            if message.ShowModal() == wx.ID_YES:
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
                message = wx.MessageDialog(self, "Are you sure you want to remove '%s'?"%role.name,
                                          style = wx.ICON_QUESTION | wx.YES_NO | wx.NO_DEFAULT)
                
                if message.ShowModal() == wx.ID_YES:
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

        treeId, flag = self.tree.HitTest(wx.Point(self.x,self.y))
      
        if(treeId.IsOk()):
            self.tree.SelectItem(treeId)
         
            if not self.__isRole(treeId):
                self.PopupMenu(self.personMenu,
                               wx.Point(self.x, self.y))
         
            else:
                self.PopupMenu(self.roleMenu,
                               wx.Point(self.x, self.y))

        else:
            self.PopupMenu(self.treeMenu,
                           wx.Point(self.x, self.y))


class CreateActionDialog(wx.Dialog):
    '''
    Dialog for adding actions to roles.
    '''
    def __init__(self, parent, id, title):
        wx.Dialog.__init__(self, parent, id, title,
                          style=wx.DEFAULT_DIALOG_STYLE|wx.RESIZE_BORDER)
        self.SetSize(wx.Size(300, 150))
        self.infoText = wx.StaticText(self, -1,
                                     "Name the action.")
        self.actionTextCtrl = wx.TextCtrl(self,-1, "")
        self.okButton = wx.Button(self, wx.ID_OK, "Ok")
        self.cancelButton =  wx.Button(self, wx.ID_CANCEL, "Cancel")

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
        mainSizer = wx.BoxSizer(wx.HORIZONTAL)
        box = wx.BoxSizer(wx.VERTICAL)
        sizer = wx.BoxSizer(wx.HORIZONTAL)

        box.Add(wx.Size(10,10))
        box.Add(self.infoText, 0, wx.EXPAND|wx.ALL, 5)
        
        sizer = wx.BoxSizer(wx.HORIZONTAL)
        sizer.Add(wx.StaticText(self, -1, "Name: "), 0, wx.ALIGN_CENTER)
        sizer.Add(self.actionTextCtrl, 1, wx.ALIGN_CENTER, 2)
        box.Add(sizer, 1, wx.EXPAND|wx.ALL, 5)

        box.Add(wx.StaticLine(self, -1), 0, wx.EXPAND|wx.ALL, 5)
        sizer2 = wx.BoxSizer(wx.HORIZONTAL)
        sizer2.Add(self.okButton, 0, wx.CENTER | wx.RIGHT, 10)
        sizer2.Add(self.cancelButton, 0, wx.CENTER)
        box.Add(sizer2, 0, wx.CENTER|wx.ALL, 5)

        mainSizer.Add(box, 1, wx.ALL | wx.EXPAND, 10)
        
        self.SetAutoLayout(1)
        self.SetSizer(mainSizer)
        self.Layout()

class AddPersonDialog(wx.Dialog):
    '''
    Dialog for adding actions to roles.
    '''
    def __init__(self, parent, id, title, role):
        wx.Dialog.__init__(self, parent, id, title,
                          style=wx.DEFAULT_DIALOG_STYLE|wx.RESIZE_BORDER)
        self.infoText = wx.StaticText(self, -1,
                                     "Enter the distinguished name of the person you want to add to '%s' role" %role.name)
        self.dnTextCtrl = wx.TextCtrl(self,-1, "", size = wx.Size(450, 20))
        self.okButton = wx.Button(self, wx.ID_OK, "Ok")
        self.cancelButton =  wx.Button(self, wx.ID_CANCEL, "Cancel")

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
        mainSizer = wx.BoxSizer(wx.HORIZONTAL)
        box = wx.BoxSizer(wx.VERTICAL)
        sizer = wx.BoxSizer(wx.HORIZONTAL)
        
        box.Add(wx.Size(5,5))
        box.Add(self.infoText, 0, wx.EXPAND|wx.ALL, 5)
        
        sizer = wx.BoxSizer(wx.HORIZONTAL)
        sizer.Add(wx.StaticText(self, -1, "Distinguished Name: "), 0, wx.ALIGN_CENTER)
        sizer.Add(self.dnTextCtrl, 1, wx.ALIGN_CENTER, 2)
        box.Add(sizer, 1, wx.EXPAND|wx.ALL, 5)

        box.Add(wx.StaticLine(self, -1), 0, wx.EXPAND|wx.ALL, 5)
        sizer2 = wx.BoxSizer(wx.HORIZONTAL)
        sizer2.Add(self.okButton, 0, wx.CENTER | wx.RIGHT, 10)
        sizer2.Add(self.cancelButton, 0, wx.CENTER)
        box.Add(sizer2, 0, wx.CENTER)

        mainSizer.Add(box, 1, wx.ALL | wx.EXPAND, 10)
        
        self.SetAutoLayout(1)
        self.SetSizer(mainSizer)
        mainSizer.Fit(self)
        self.Layout()

class CreateRoleDialog(wx.Dialog):
    '''
    Dialog for adding actions to roles.
    '''
    def __init__(self, parent, id, title):
        wx.Dialog.__init__(self, parent, id, title,
                          style=wx.OK|wx.RESIZE_BORDER|wx.CAPTION)
        self.SetSize(wx.Size(300, 150))
        self.infoText = wx.StaticText(self, -1,
                                     "Enter the name of the new role.")
        self.dnTextCtrl = wx.TextCtrl(self,-1, "")
        self.okButton = wx.Button(self, wx.ID_OK, "Ok")
        self.cancelButton =  wx.Button(self, wx.ID_CANCEL, "Cancel")

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
        mainSizer = wx.BoxSizer(wx.HORIZONTAL)
        box = wx.BoxSizer(wx.VERTICAL)
        sizer = wx.BoxSizer(wx.HORIZONTAL)

        box.Add(wx.Size(5,5))
        box.Add(self.infoText, 0, wx.EXPAND|wx.ALL, 5)
        
        sizer = wx.BoxSizer(wx.HORIZONTAL)
        sizer.Add(wx.StaticText(self, -1, "Name: "), 0, wx.ALIGN_CENTER)
        sizer.Add(self.dnTextCtrl, 1, wx.ALIGN_CENTER, 2)
        box.Add(sizer, 1, wx.EXPAND|wx.ALL, 5)

        box.Add(wx.StaticLine(self, -1), 0, wx.EXPAND|wx.ALL, 5)
        sizer2 = wx.BoxSizer(wx.HORIZONTAL)
        sizer2.Add(self.okButton, 0, wx.CENTER | wx.RIGHT, 10)
        sizer2.Add(self.cancelButton, 0, wx.CENTER)
        box.Add(sizer2, 0, wx.CENTER|wx.TOP, 5)

        mainSizer.Add(box, 1, wx.ALL | wx.EXPAND, 10)
        
        self.SetAutoLayout(1)
        self.SetSizer(mainSizer)
        self.Layout()

class PersonPropertiesDialog(wx.Dialog):
    '''
    Dialog showing a persons properties.
    '''
    def __init__(self, parent, id, title, person):
        wx.Dialog.__init__(self, parent, id, title,
                          style=wx.RESIZE_BORDER|wx.DEFAULT_DIALOG_STYLE)
        self.dnText = wx.StaticText(self, -1, 'Distinguished Name: ')
        self.dnCtrl = wx.TextCtrl(self, -1, person.name, size = wx.Size(450, 20),
                                 style =  wx.TE_READONLY)
        self.okButton = wx.Button(self, wx.ID_OK, "Ok")
        self.__layout()
        
    def __layout(self):
        sizer = wx.BoxSizer(wx.VERTICAL)
        s2 = wx.BoxSizer(wx.HORIZONTAL)
        s2.Add(self.dnText, 0, wx.EXPAND)
        s2.Add(self.dnCtrl, 1, wx.EXPAND)
        sizer.Add(s2, 0, wx.EXPAND|wx.ALL, 10)

        sizer.Add(wx.StaticLine(self, -1), 0, wx.EXPAND|wx.LEFT|wx.RIGHT, 5)
        sizer.Add(self.okButton, 0, wx.CENTER|wx.ALL, 10)

        self.SetAutoLayout(1)
        self.SetSizer(sizer)
        sizer.Fit(self)
        self.Layout()

                      
class AddPeopleDialog(wx.Dialog):
    '''
    Dialog for adding people to roles
    '''
    def __init__(self, parent, id, title, authMIW, infoDict=None,
                 selectedRole=""):
        wx.Dialog.__init__(self, parent, id, title,
                          style=wx.DEFAULT_DIALOG_STYLE|wx.RESIZE_BORDER)
        self.SetSize(wx.Size(500, 450))
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
        
        self.dnTextCtrl = wx.TextCtrl(self,-1, "")
        self.addButton1 = wx.Button(self, wx.NewId(), "Add >>",
                                   style = wx.BU_EXACTFIT )
        self.list = wx.ListCtrl(self, wx.NewId(),
                               style = wx.LC_REPORT | wx.LC_SORT_ASCENDING |
                               wx.SUNKEN_BORDER |wx.HSCROLL | wx.LC_NO_HEADER )
        self.list.InsertColumn(0, "People:")
       
        self.addButton2 = wx.Button(self, wx.NewId(), "Add >>",
                                   style = wx.BU_EXACTFIT)

        self.addList = wx.ListCtrl(self, wx.NewId(),
                                  style = wx.LC_REPORT | wx.LC_SORT_ASCENDING |
                                  wx.HSCROLL |wx.SUNKEN_BORDER |wx.LC_NO_HEADER)
        self.addList.InsertColumn(0, "")
        self.removeUserButton = wx.Button(self, wx.NewId(), "Remove User",
                                   style = wx.BU_EXACTFIT)

        self.selections = wx.ComboBox(self, wx.NewId(),
                                     style = wx.CB_DROPDOWN | wx.CB_READONLY,
                                     choices = self.infoDict.keys())
        
        self.AddPeople(self.pList)
        self.dnText = wx.StaticText(self, -1,
                                   "Add person by distinguished name ")
        self.peopleText = wx.StaticText(self, -1, "Add people from list ")
        self.dnText.SetFont(wx.Font(wx.DEFAULT, wx.NORMAL, wx.NORMAL, wx.BOLD))

        self.okButton = wx.Button(self, wx.ID_OK, "Ok")
        self.cancelButton =  wx.Button(self, wx.ID_CANCEL, "Cancel")

        self.peopleText.SetFont(wx.Font(wx.DEFAULT, wx.NORMAL, wx.NORMAL, wx.BOLD))
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
        box = wx.BoxSizer(wx.HORIZONTAL)
        sizer = wx.BoxSizer(wx.VERTICAL)

        sizer.Add(wx.Size(10,10))
        tempSizer =  wx.BoxSizer(wx.HORIZONTAL)
        tempSizer.Add(self.dnText)
        
        tempSizer.Add(wx.StaticLine(self, -1), 1, wx.ALIGN_CENTER)
        sizer.Add(tempSizer, 0, wx.EXPAND)
        sizer.Add(wx.Size(10,10))

        tempSizer = wx.BoxSizer(wx.HORIZONTAL)
        tempSizer.Add(wx.StaticText(self, -1, "Name: "), 0, wx.ALIGN_CENTER)
        tempSizer.Add(self.dnTextCtrl, 1, wx.RIGHT, 2)
        tempSizer.Add(self.addButton1, 0, wx.ALIGN_CENTER | wx.LEFT, 5)
        sizer.Add(tempSizer, 0, wx.EXPAND)

        sizer.Add(wx.Size(10,10))
        tempSizer =  wx.BoxSizer(wx.HORIZONTAL)
        tempSizer.Add(self.peopleText)
        tempSizer.Add(wx.StaticLine(self, -1), 1, wx.ALIGN_CENTER)
        sizer.Add(tempSizer, 0, wx.EXPAND)
        sizer.Add(wx.Size(10,10))

        tempSizer = wx.BoxSizer(wx.HORIZONTAL)
        tempSizer.Add(self.list, 1, wx.EXPAND)
        tempSizer.Add(self.addButton2, 0, wx.ALIGN_CENTER | wx.LEFT, 5)
        sizer.Add(tempSizer, 1, wx.EXPAND)
            
        sizer.Add(wx.Size(10,10))
        box.Add(sizer, 3, wx.EXPAND|wx.LEFT|wx.BOTTOM|wx.TOP, 5)
        
        tempSizer = wx.BoxSizer(wx.VERTICAL)
        tempSizer.Add(wx.Size(10,10))
        tempSizer.Add(self.selections, 0, wx.EXPAND|wx.BOTTOM, 5)
        tempSizer.Add(self.addList, 1, wx.EXPAND)
        tempSizer.Add(self.removeUserButton, 0, wx.EXPAND|wx.TOP, 5)
        box.Add(tempSizer, 2, wx.EXPAND|wx.ALL, 5)

        mainSizer = wx.BoxSizer(wx.VERTICAL)
        mainSizer.Add(box, 1, wx.EXPAND)
        mainSizer.Add(wx.StaticLine(self,-1), 0, wx.ALL|wx.EXPAND, 5)

        tempSizer = wx.BoxSizer(wx.HORIZONTAL)
        tempSizer.Add(self.okButton, 0, wx.CENTER | wx.ALL, 5)
        tempSizer.Add(self.cancelButton, 0, wx.CENTER| wx.ALL, 5)
        mainSizer.Add(tempSizer, 0, wx.ALIGN_CENTER)
        mainSizer.Add(wx.Size(10,10))
        
        self.SetAutoLayout(1)
        self.SetSizer(mainSizer)
        self.Layout()
        self.list.SetColumnWidth(0, wx.LIST_AUTOSIZE)
        self.addList.SetColumnWidth(0, wx.LIST_AUTOSIZE)

    def __setEvents(self):
        wx.EVT_BUTTON(self.addButton1, self.addButton1.GetId(),
                   self.AddDistinguished)
        wx.EVT_BUTTON(self.addButton2, self.addButton2.GetId(),
                   self.AddFromPeopleList) 
        wx.EVT_COMBOBOX(self.selections, self.selections.GetId(),
                     self.ComboEvent)
        wx.EVT_BUTTON(self.removeUserButton, self.removeUserButton.GetId(),
                   self.RemoveSelectedUsersFromList)

        wx.EVT_LIST_ITEM_SELECTED(self.list, self.list.GetId(),
                               self.SelectPeople)

    def __addToList(self, item):
        list = self.infoDict[self.selections.GetValue()]
        
        if not item in list:
            list.append(item)
            self.infoDict[self.selections.GetValue()] = list
            self.addList.InsertStringItem(0, item)
            self.addList.SetColumnWidth(0, wx.LIST_AUTOSIZE)
            return True

        return False

    def __removeFromList(self, index):
        if index == -1:
            return False
        item_name = self.addList.GetItemText(index)
        list = self.infoDict[self.selections.GetValue()]

        if item_name in list:
            list.remove(item_name)
            self.infoDict[self.selections.GetValue()] = list
            self.addList.DeleteItem(index)
            return True
 
        return False
        
    def SelectNewRole(self, role):
        self.selectedRole = role
        for item in self.infoDict[self.selectedRole]:
            self.addList.InsertStringItem(0, item.name.split('=')[-1])
            self.addList.SetColumnWidth(0, wx.LIST_AUTOSIZE)
            
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

class AuthorizationUIDialog(wx.Dialog):
    def __init__(self, parent, id, title, log, requireCertOption=0):
        '''
        Encapsulates an AuthorizationUIPanel object in a dialog. 
        '''
        wx.Dialog.__init__(self, parent, id, title,
                          size = wx.Size(800,300),
                          style=wx.DEFAULT_DIALOG_STYLE|wx.RESIZE_BORDER)
        self.panel = AuthorizationUIPanel(self, -1, log,requireCertOption)
        self.okButton = wx.Button(self, wx.ID_OK, "Ok")
        self.cancelButton = wx.Button(self, wx.ID_CANCEL, "Cancel")

        self.__layout()
               
    def ConnectToAuthManager(self, authManagerIW):
        '''
        Connect to specified authorization manager.
        '''
        self.panel.ConnectToAuthManager(authManagerIW)

    def Apply(self):
        '''
        Update authorization manager with current roles and actions.
        '''
        self.panel.Apply()

    def __layout(self):
        '''
        Handle UI layout.
        '''
        mainSizer = wx.BoxSizer(wx.VERTICAL)
        mainSizer.Add(self.panel, 1, wx.EXPAND|wx.BOTTOM, 5)

        buttonSizer = wx.BoxSizer(wx.HORIZONTAL)
        buttonSizer.Add(self.okButton, 0, wx.ALL, 5)
        buttonSizer.Add(self.cancelButton, 0, wx.ALL, 5)
        mainSizer.Add(buttonSizer, 0, wx.CENTER)

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
    import sys
    
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

    wxapp = wx.PySimpleApp()
    log = InitLogging()

    #actionDialog = AddPersonDialog(None, -1, 'Add Person', Role('test'))
    #print 'before show modal'
    #if actionDialog.ShowModal() == wx.ID_OK:
    #    print 'add action'
    #   
    #actionDialog.Destroy()
    
    
    f = AuthorizationUIDialog(None, -1, "Manage Roles", log)
    f.ConnectToAuthManager(uri)
    if f.ShowModal() == wx.ID_OK:
        f.panel.Apply()
    f.Destroy()
    wxapp.SetTopWindow(f)
    wxapp.MainLoop()

    #roles = AddPeopleDialog(None, -1, "Manage Roles", am)
    #roles.ShowModal()
    #roles.Destroy()
   
