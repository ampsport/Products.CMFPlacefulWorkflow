# -*- coding: utf-8 -*-
## CMFPlacefulWorkflow
## A CMF/Plone product for locally changing the workflow of content types
## Copyright (C)2006 Ingeniweb

## This program is free software; you can redistribute it and/or modify
## it under the terms of the GNU General Public License as published by
## the Free Software Foundation; either version 2 of the License, or
## (at your option) any later version.

## This program is distributed in the hope that it will be useful,
## but WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
## GNU General Public License for more details.

## You should have received a copy of the GNU General Public License
## along with this program; see the file COPYING. If not, write to the
## Free Software Foundation, Inc., 675 Mass Ave, Cambridge, MA 02139, USA.
"""
PlacefulWorkflowTool main class
"""
__version__ = "$Revision$"
# $Source: /cvsroot/ingeniweb/CMFPlacefulWorkflow/PlacefulWorkflowTool.py,v $
# $Id$
__docformat__ = 'restructuredtext'

from Products.CMFCore.utils import UniqueObject
from OFS.Folder import Folder
from Globals import InitializeClass, PersistentMapping, DTMLFile
from Globals import InitializeClass
from AccessControl import ClassSecurityInfo
from Products.CMFCore.CMFCorePermissions import ManagePortal
#from Products.CMFCore.CMFCorePermissions import *
from Products.CMFCore.ActionProviderBase import ActionProviderBase
from Products.CMFPlone.migrations.migration_util import safeEditProperty
from os import path as os_path
from Globals import package_home
from Acquisition import aq_base, aq_parent, aq_inner

_dtmldir = os_path.join( package_home( globals() ), 'dtml' )

from global_symbols import *

from interfaces.portal_placeful_workflow import portal_workflow_policy

WorkflowPolicyConfig_id  = ".wf_policy_config"

def addPlacefulWorkflowTool(self,REQUEST={}):
    """
    Factory method for the Placeful Workflow Tool
    """
    id='portal_placeful_workflow'
    pwt=PlacefulWorkflowTool()
    self._setObject(id, pwt, set_owner=0)
    getattr(self, id)._post_init()
    if REQUEST:
        return REQUEST.RESPONSE.redirect(self.absolute_url() + '/manage_main')

class PlacefulWorkflowTool(UniqueObject, Folder, ActionProviderBase):
    """
    PlacefulWorkflow Tool
    """

    id = 'portal_placeful_workflow'
    meta_type = 'Placeful Workflow Tool'
    __implements__ = portal_workflow_policy
    _actions = []
    security = ClassSecurityInfo()


    manage_options=(
        ({
        'label': 'Content',
        'action': 'manage_main',
        },
         { 'label' : 'Overview'
           , 'action' : 'manage_overview'
           },) +
        ActionProviderBase.manage_options +
        Folder.manage_options
        )

    def __init__(self):
        # Properties to be edited by site manager
        safeEditProperty(self, 'max_chain_length', 1, data_type='int')

    _manage_addWorkflowPolicyForm = DTMLFile('addWorkflowPolicy', _dtmldir)

    security.declareProtected( ManagePortal, 'manage_addWorkflowPolicyForm')
    def manage_addWorkflowPolicyForm(self, REQUEST):

        """ Form for adding workflow policies.
        """
        wfpt = []
        for key in _workflow_policy_factories.keys():
            wfpt.append(key)
        wfpt.sort()
        return self._manage_addWorkflowPolicyForm(REQUEST, workflow_policy_types=wfpt)

    security.declareProtected( ManagePortal, 'manage_addWorkflowPolicy')
    def manage_addWorkflowPolicy(self, id, workflow_policy_type='default_workflow_policy (Simple Policy)', RESPONSE=None):
        """ Adds a workflow policies from the registered types.
        """
        factory = _workflow_policy_factories[workflow_policy_type]
        ob = factory(id)
        self._setObject(id, ob)
        if RESPONSE is not None:
            RESPONSE.redirect(self.absolute_url() +
                              '/manage_main?management_view=Contents')

    def all_meta_types(self):
        return (
            {'name': 'WorkflowPolicy',
             'action': 'manage_addWorkflowPolicyForm',
             'permission': ManagePortal },)

    security.declareProtected( ManagePortal, 'getWorkflowPolicyById')
    def getWorkflowPolicyById(self, wfp_id):

        """ Retrieve a given workflow policy.
        """
        policy=None
        if wfp_id != None:
            wfp = getattr(self, wfp_id, None)
            if wfp !=None:
                if getattr(wfp, '_isAWorkflowPolicy', 0):
                    policy = wfp
        return policy

    security.declareProtected( ManagePortal, 'getWorkflowPolicyIds')
    def getWorkflowPolicies(self):
        """ Return the list of workflow policies.
        """
        wfps = []
        for obj_name, obj in self.objectItems():
            if getattr(obj, '_isAWorkflowPolicy', 0):
                wfps.append(obj)
        return tuple(wfps)

    security.declareProtected( ManagePortal, 'getWorkflowPolicyIds')
    def getWorkflowPolicyIds(self):

        """ Return the list of workflow policy ids.
        """
        wfp_ids = []

        for obj_name, obj in self.objectItems():
            if getattr(obj, '_isAWorkflowPolicy', 0):
                wfp_ids.append(obj_name)

        return tuple(wfp_ids)


    security.declareProtected( ManagePortal, 'getWorkflowPolicyConfig')
    def getWorkflowPolicyConfig(self, ob):
        local_config = None
        some_config = getattr(ob, WorkflowPolicyConfig_id, None)
        if some_config is not None:
            # Was it here or did we acquire?
             if hasattr(aq_base(ob), WorkflowPolicyConfig_id):
                 local_config = some_config
        return local_config

    def _post_init(self):
        """
        _post_init(self) => called from manage_add method, acquired within ZODB (__init__ is not)
        """
        pass

    #
    #   portal_workflow_policy implementation.
    #

    def getMaxChainLength(self):
        """Return the max workflow chain length"""
        max_chain_length = self.getProperty('max_chain_length')
        return max_chain_length

    def setMaxChainLength(self, max_chain_length):
        """Set the max workflow chain length"""
        safeEditProperty(self, 'max_chain_length', max_chain_length, data_type='int')

_workflow_policy_factories = {}

def _makeWorkflowPolicyFactoryKey(factory, id=None, title=None):
    # The factory should take one argument, id.
    if id is None:
        id = getattr(factory, 'id', '') or getattr(factory, 'meta_type', '')
    if title is None:
        title = getattr(factory, 'title', '')
    key = id
    if title:
        key = key + ' (%s)' % title
    return key

def addWorkflowPolicyFactory(factory, id=None, title=None):
    key = _makeWorkflowPolicyFactoryKey( factory, id, title )
    _workflow_policy_factories[key] = factory

def _removeWorkflowPolicyFactory( factory, id=None, title=None ):
    """ Make teardown in unitcase cleaner. """
    key = _makeWorkflowPolicyFactoryKey( factory, id, title )
    try:
        del _workflow_policy_factories[key]
    except KeyError:
        pass

InitializeClass(PlacefulWorkflowTool)
