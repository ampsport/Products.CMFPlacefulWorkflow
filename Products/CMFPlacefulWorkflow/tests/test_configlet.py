# -*- coding: utf-8 -*-
## CMFPlacefulWorkflow
## Copyright (C)2005 Ingeniweb

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
CMFPlacefulWorkflow Functional Test of the Through the Web Configuration
"""
__version__ = "$Revision: 61119 $"
__docformat__ = 'restructuredtext'

from Products.CMFCore.utils import getToolByName

from CMFPlacefulWorkflowTestCase import CMFPlacefulWorkflowFunctionalTestCase

from plone.testing.z2 import Browser
from plone.app import testing
from transaction import commit


class TestConfiglet(CMFPlacefulWorkflowFunctionalTestCase):

    def afterSetUp(self):
        """Init some shortcuts member variables."""
        self.ppw = getToolByName(self.portal, 'portal_placeful_workflow')

        self.createDummyPolicy()

    def getBrowser(self, logged_in=False):
        """ instantiate and return a testbrowser for convenience """
        browser = Browser(self.layer['app'])
        if logged_in:
            # Add an authorization header using the given or default
            # credentials """
            browser.addHeader('Authorization', 'Basic %s:%s' % (
                    testing.SITE_OWNER_NAME,
                    testing.SITE_OWNER_PASSWORD))
        return browser

    def createDummyPolicy(self):
        """Create a workflow policy named 'dummy_policy' for us to work with.
        """
        self.logout()
        self.loginAsPortalOwner()
        # Create a policy
        self.ppw.manage_addWorkflowPolicy(
            'dummy_policy', 'default_workflow_policy (Simple Policy)')
        self.ppw.dummy_policy.title = 'Dummy Policy'

    def setLocalChainForPortalType(self, pt, chain):
        gp = self.ppw.getWorkflowPolicyById('dummy_policy')
        gp.setChainForPortalTypes([pt, ], [chain, ])

    def test_local_mapping_select_acquisition_chain(self):
        """Test setting a local mapping to the special value 'acquisition'
        """
        self.setLocalChainForPortalType('Document', 'folder_workflow')
        commit()
        browser = self.getBrowser(logged_in=True)

        browser.open('http://nohost/plone/prefs_workflow_policy_mapping?'
                     'wfpid=dummy_policy')
        self.assertEqual(browser.getControl(name='wf.Document:record').value,
                         ['folder_workflow', ])

        browser.getControl(name='wf.Document:record').value = ['acquisition', ]
        browser.getControl(name='submit').click()

        self.assertEqual(browser.getControl(name='wf.Document:record').value,
                         ['acquisition', ])
