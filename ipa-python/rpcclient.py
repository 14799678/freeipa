# Authors: Rob Crittenden <rcritten@redhat.com>
#
# Copyright (C) 2007  Red Hat
# see file 'COPYING' for use and warranty information
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation; version 2 only
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA 02111-1307 USA
#

import xmlrpclib
import socket
import config
import errno
from krbtransport import KerbTransport
from kerberos import GSSError
from ipa import ipaerror, ipautil
from ipa import config

# Some errors to catch
# http://cvs.fedora.redhat.com/viewcvs/ldapserver/ldap/servers/plugins/pam_passthru/README?root=dirsec&rev=1.6&view=auto

class RPCClient:

    def __init__(self, verbose=False):
        self.server = None
        self.verbose = verbose
        config.init_config()
    
    def server_url(self, server):
        """Build the XML-RPC server URL from our configuration"""
        url = "https://" + server + "/ipa/xml"
        if self.verbose:
            print "Connecting to IPA server: %s" % url
        return url
    
    def setup_server(self):
        """Create our XML-RPC server connection using kerberos
           authentication"""
        if not self.server:
            serverlist = config.config.get_server()

            # Try each server until we succeed or run out of servers to try
            # Guaranteed by ipa.config to have at least 1 in the list
            for s in serverlist:
                try:
                    self.server = s
                    remote = xmlrpclib.ServerProxy(self.server_url(s), KerbTransport())
                    result = remote.ping()
                    break
                except socket.error, e:
                    if (e[0] == errno.ECONNREFUSED) or (e[0] == errno.ECONNREFUSED) or (e[0] == errno.EHOSTDOWN) or (e[0] == errno.EHOSTUNREACH):
                        continue
                    else:
                        raise e

        return xmlrpclib.ServerProxy(self.server_url(self.server), KerbTransport(), verbose=self.verbose)
    
# Higher-level API

    def get_aci_entry(self, sattrs=None):
        """Returns the entry containing access control ACIs."""
        server = self.setup_server()
        if sattrs is None:
            sattrs = "__NONE__"
        try:
            result = server.get_aci_entry(sattrs)
        except xmlrpclib.Fault, fault:
            raise ipaerror.gen_exception(fault.faultCode, fault.faultString)
        except socket.error, (value, msg):
            raise xmlrpclib.Fault(value, msg)

        return ipautil.unwrap_binary_data(result)


# General searches

    def get_entry_by_dn(self,dn,sattrs=None):
        """Get a specific entry. If sattrs is not None then only those
           attributes will be returned, otherwise all available
           attributes are returned. The result is a dict."""
        server = self.setup_server()
        if sattrs is None:
            sattrs = "__NONE__"
        try:
            result = server.get_entry_by_dn(dn, sattrs)
        except xmlrpclib.Fault, fault:
            raise ipaerror.gen_exception(fault.faultCode, fault.faultString)
        except socket.error, (value, msg):
            raise xmlrpclib.Fault(value, msg)

        return ipautil.unwrap_binary_data(result)

    def get_entry_by_cn(self,cn,sattrs=None):
        """Get a specific entry by cn. If sattrs is not None then only those
           attributes will be returned, otherwise all available
           attributes are returned. The result is a dict."""
        server = self.setup_server()
        if sattrs is None:
            sattrs = "__NONE__"
        try:
            result = server.get_entry_by_cn(cn, sattrs)
        except xmlrpclib.Fault, fault:
            raise ipaerror.gen_exception(fault.faultCode, fault.faultString)
        except socket.error, (value, msg):
            raise xmlrpclib.Fault(value, msg)

        return ipautil.unwrap_binary_data(result)

    def update_entry(self,oldentry,newentry):
        """Update an existing entry. oldentry and newentry are dicts of attributes"""
        server = self.setup_server()

        try:
            result = server.update_entry(ipautil.wrap_binary_data(oldentry),
                    ipautil.wrap_binary_data(newentry))
        except xmlrpclib.Fault, fault:
            raise ipaerror.gen_exception(fault.faultCode, fault.faultString)
        except socket.error, (value, msg):
            raise xmlrpclib.Fault(value, msg)

        return ipautil.unwrap_binary_data(result)


# User support

    def get_user_by_uid(self,uid,sattrs=None):
        """Get a specific user. If sattrs is not None then only those
           attributes will be returned, otherwise all available
           attributes are returned. The result is a dict."""
        server = self.setup_server()
        if sattrs is None:
            sattrs = "__NONE__"
        try:
            result = server.get_user_by_uid(uid, sattrs)
        except xmlrpclib.Fault, fault:
            raise ipaerror.gen_exception(fault.faultCode, fault.faultString)
        except socket.error, (value, msg):
            raise xmlrpclib.Fault(value, msg)

        return ipautil.unwrap_binary_data(result)

    def get_user_by_principal(self,principal,sattrs=None):
        """Get a specific user. If sattrs is not None then only those
           attributes will be returned, otherwise all available
           attributes are returned. The result is a dict."""
        server = self.setup_server()
        if sattrs is None:
            sattrs = "__NONE__"
        try:
            result = server.get_user_by_principal(principal, sattrs)
        except xmlrpclib.Fault, fault:
            raise ipaerror.gen_exception(fault.faultCode, fault.faultString)
        except socket.error, (value, msg):
            raise xmlrpclib.Fault(value, msg)

        return ipautil.unwrap_binary_data(result)

    def get_user_by_email(self,email,sattrs=None):
        """Get a specific user's entry. Return as a dict of values.
           Multi-valued fields are represented as lists. The result is a
           dict.
        """
        server = self.setup_server()
        if sattrs is None:
            sattrs = "__NONE__"
        try:
            result = server.get_user_by_email(email, sattrs)
        except xmlrpclib.Fault, fault:
            raise ipaerror.gen_exception(fault.faultCode, fault.faultString)
        except socket.error, (value, msg):
            raise xmlrpclib.Fault(value, msg)

        return ipautil.unwrap_binary_data(result)

    def get_users_by_manager(self,manager_dn,sattrs=None):
        """Gets the users that report to a manager.
           If sattrs is not None then only those
           attributes will be returned, otherwise all available
           attributes are returned. The result is a list of dicts."""
        server = self.setup_server()
        if sattrs is None:
            sattrs = "__NONE__"
        try:
            result = server.get_users_by_manager(manager_dn, sattrs)
        except xmlrpclib.Fault, fault:
            raise ipaerror.gen_exception(fault.faultCode, fault.faultString)
        except socket.error, (value, msg):
            raise xmlrpclib.Fault(value, msg)

        return ipautil.unwrap_binary_data(result)

    def add_user(self,user,user_container=None):
        """Add a new user. Takes as input a dict where the key is the
           attribute name and the value is either a string or in the case
           of a multi-valued field a list of values"""
        server = self.setup_server()

        if user_container is None:
            user_container = "__NONE__"
    
        try:
            result = server.add_user(ipautil.wrap_binary_data(user),
                    user_container)
        except xmlrpclib.Fault, fault:
            raise ipaerror.gen_exception(fault.faultCode, fault.faultString)
        except socket.error, (value, msg):
            raise xmlrpclib.Fault(value, msg)

        return ipautil.unwrap_binary_data(result)
        
    def get_custom_fields(self):
        """Get custom user fields."""
        server = self.setup_server()
        
        try:
            result = server.get_custom_fields()
        except xmlrpclib.Fault, fault:
            raise ipaerror.gen_exception(fault.faultCode, fault.faultString)
        except socket.error, (value, msg):
            raise xmlrpclib.Fault(value, msg)
      
        return ipautil.unwrap_binary_data(result)

    def set_custom_fields(self, schema):
        """Set custom user fields."""
        server = self.setup_server()
        
        try:
            result = server.set_custom_fields(schema)
        except xmlrpclib.Fault, fault:
            raise ipaerror.gen_exception(fault.faultCode, fault.faultString)
        except socket.error, (value, msg):
            raise xmlrpclib.Fault(value, msg)

        return ipautil.unwrap_binary_data(result)
      
    def get_all_users (self):
        """Return a list containing a dict for each existing user."""
    
        server = self.setup_server()
        try:
            result = server.get_all_users()
        except xmlrpclib.Fault, fault:
            raise ipaerror.gen_exception(fault.faultCode, fault.faultString)
        except socket.error, (value, msg):
            raise xmlrpclib.Fault(value, msg)
    
        return ipautil.unwrap_binary_data(result)

    def find_users (self, criteria, sattrs=None, sizelimit=-1, timelimit=-1):
        """Return a list: counter followed by a dict for each user that
           matches the criteria. If the results are truncated, counter will
           be set to -1"""
    
        server = self.setup_server()
        try:
            # None values are not allowed in XML-RPC
            if sattrs is None:
                sattrs = "__NONE__"
            result = server.find_users(criteria, sattrs, sizelimit, timelimit)
        except xmlrpclib.Fault, fault:
            raise ipaerror.gen_exception(fault.faultCode, fault.faultString)
        except socket.error, (value, msg):
            raise xmlrpclib.Fault(value, msg)
    
        return ipautil.unwrap_binary_data(result)

    def update_user(self,olduser,newuser):
        """Update an existing user. olduser and newuser are dicts of attributes"""
        server = self.setup_server()
    
        try:
            result = server.update_user(ipautil.wrap_binary_data(olduser),
                    ipautil.wrap_binary_data(newuser))
        except xmlrpclib.Fault, fault:
            raise ipaerror.gen_exception(fault.faultCode, fault.faultString)
        except socket.error, (value, msg):
            raise xmlrpclib.Fault(value, msg)

        return ipautil.unwrap_binary_data(result)

    def delete_user(self,uid):
        """Delete a user. uid is the uid of the user to delete."""
        server = self.setup_server()
    
        try:
            result = server.delete_user(uid)
        except xmlrpclib.Fault, fault:
            raise ipaerror.gen_exception(fault.faultCode, fault.faultString)
        except socket.error, (value, msg):
            raise xmlrpclib.Fault(value, msg)

        return result

    def modifyPassword(self,principal,oldpass,newpass):
        """Modify a user's password"""
        server = self.setup_server()

        if oldpass is None:
            oldpass = "__NONE__"
    
        try:
            result = server.modifyPassword(principal,oldpass,newpass)
        except xmlrpclib.Fault, fault:
            raise ipaerror.gen_exception(fault.faultCode, fault.faultString)
        except socket.error, (value, msg):
            raise xmlrpclib.Fault(value, msg)

        return result

    def mark_user_active(self,uid):
        """Mark a user as active"""
        server = self.setup_server()
    
        try:
            result = server.mark_user_active(uid)
        except xmlrpclib.Fault, fault:
            raise ipaerror.gen_exception(fault.faultCode, fault.faultString)
        except socket.error, (value, msg):
            raise xmlrpclib.Fault(value, msg)

        return ipautil.unwrap_binary_data(result)

    def mark_user_inactive(self,uid):
        """Mark a user as inactive"""
        server = self.setup_server()
    
        try:
            result = server.mark_user_inactive(uid)
        except xmlrpclib.Fault, fault:
            raise ipaerror.gen_exception(fault.faultCode, fault.faultString)
        except socket.error, (value, msg):
            raise xmlrpclib.Fault(value, msg)

        return ipautil.unwrap_binary_data(result)


# Group support

    def get_groups_by_member(self,member_dn,sattrs=None):
        """Gets the groups that member_dn belongs to.
           If sattrs is not None then only those
           attributes will be returned, otherwise all available
           attributes are returned. The result is a list of dicts."""
        server = self.setup_server()
        if sattrs is None:
            sattrs = "__NONE__"
        try:
            result = server.get_groups_by_member(member_dn, sattrs)
        except xmlrpclib.Fault, fault:
            raise ipaerror.gen_exception(fault.faultCode, fault.faultString)
        except socket.error, (value, msg):
            raise xmlrpclib.Fault(value, msg)

        return ipautil.unwrap_binary_data(result)

    def add_group(self,group,group_container=None):
        """Add a new group. Takes as input a dict where the key is the
           attribute name and the value is either a string or in the case
           of a multi-valued field a list of values"""
        server = self.setup_server()

        if group_container is None:
            group_container = "__NONE__"
    
        try:
            result = server.add_group(ipautil.wrap_binary_data(group),
                    group_container)
        except xmlrpclib.Fault, fault:
            raise ipaerror.gen_exception(fault.faultCode, fault.faultString)
        except socket.error, (value, msg):
            raise xmlrpclib.Fault(value, msg)

        return ipautil.unwrap_binary_data(result)

    def find_groups (self, criteria, sattrs=None, sizelimit=-1, timelimit=-1):
        """Return a list containing a Group object for each group that matches
           the criteria."""
    
        server = self.setup_server()
        try:
            # None values are not allowed in XML-RPC
            if sattrs is None:
                sattrs = "__NONE__"
            result = server.find_groups(criteria, sattrs, sizelimit, timelimit)
        except xmlrpclib.Fault, fault:
            raise ipaerror.gen_exception(fault.faultCode, fault.faultString)
        except socket.error, (value, msg):
            raise xmlrpclib.Fault(value, msg)
    
        return ipautil.unwrap_binary_data(result)

    def add_member_to_group(self, member_dn, group_dn):
        """Add a new member to an existing group.
        """
        server = self.setup_server()
        try:
            result = server.add_member_to_group(member_dn, group_dn)
        except xmlrpclib.Fault, fault:
            raise ipaerror.gen_exception(fault.faultCode, fault.faultString)
        except socket.error, (value, msg):
            raise xmlrpclib.Fault(value, msg)

        return ipautil.unwrap_binary_data(result)

    def add_members_to_group(self, member_dns, group_dn):
        """Add several members to an existing group.
           member_dns is a list of the dns to add

           Returns a list of the dns that were not added.
        """
        server = self.setup_server()
        try:
            result = server.add_members_to_group(member_dns, group_dn)
        except xmlrpclib.Fault, fault:
            raise ipaerror.gen_exception(fault.faultCode, fault.faultString)
        except socket.error, (value, msg):
            raise xmlrpclib.Fault(value, msg)

        return ipautil.unwrap_binary_data(result)

    def remove_member_from_group(self, member_dn, group_dn):
        """Remove a member from an existing group.
        """
        server = self.setup_server()
        try:
            result = server.remove_member_from_group(member_dn, group_dn)
        except xmlrpclib.Fault, fault:
            raise ipaerror.gen_exception(fault.faultCode, fault.faultString)
        except socket.error, (value, msg):
            raise xmlrpclib.Fault(value, msg)

        return ipautil.unwrap_binary_data(result)

    def remove_members_from_group(self, member_dns, group_dn):
        """Remove several members from an existing group.

           Returns a list of the dns that were not removed.
        """
        server = self.setup_server()
        try:
            result = server.remove_members_from_group(member_dns, group_dn)
        except xmlrpclib.Fault, fault:
            raise ipaerror.gen_exception(fault.faultCode, fault.faultString)
        except socket.error, (value, msg):
            raise xmlrpclib.Fault(value, msg)

        return ipautil.unwrap_binary_data(result)

    def add_user_to_group(self, user_uid, group_dn):
        """Add a user to an existing group.
        """
        server = self.setup_server()
        try:
            result = server.add_user_to_group(user_uid, group_dn)
        except xmlrpclib.Fault, fault:
            raise ipaerror.gen_exception(fault.faultCode, fault.faultString)
        except socket.error, (value, msg):
            raise xmlrpclib.Fault(value, msg)

        return ipautil.unwrap_binary_data(result)

    def add_users_to_group(self, user_uids, group_dn):
        """Add several users to an existing group.
           user_uids is a list of the uids of the users to add

           Returns a list of the user uids that were not added.
        """
        server = self.setup_server()
        try:
            result = server.add_users_to_group(user_uids, group_dn)
        except xmlrpclib.Fault, fault:
            raise ipaerror.gen_exception(fault.faultCode, fault.faultString)
        except socket.error, (value, msg):
            raise xmlrpclib.Fault(value, msg)

        return ipautil.unwrap_binary_data(result)

    def remove_user_from_group(self, user_uid, group_dn):
        """Remove a user from an existing group.
        """
        server = self.setup_server()
        try:
            result = server.remove_user_from_group(user_uid, group_dn)
        except xmlrpclib.Fault, fault:
            raise ipaerror.gen_exception(fault.faultCode, fault.faultString)
        except socket.error, (value, msg):
            raise xmlrpclib.Fault(value, msg)
    
        return ipautil.unwrap_binary_data(result)

    def remove_users_from_group(self, user_uids, group_dn):
        """Remove several users from an existing group.
           user_uids is a list of the uids of the users to remove

           Returns a list of the user uids that were not removed.
        """
        server = self.setup_server()
        try:
            result = server.remove_users_from_group(user_uids, group_dn)
        except xmlrpclib.Fault, fault:
            raise ipaerror.gen_exception(fault.faultCode, fault.faultString)
        except socket.error, (value, msg):
            raise xmlrpclib.Fault(value, msg)
    
        return ipautil.unwrap_binary_data(result)

    def add_groups_to_user(self, group_dns, user_dn):
        """Given a list of group dn's add them to the user.

           Returns a list of the group dns that were not added.
        """
        server = self.setup_server()
        try:
            result = server.add_groups_to_user(group_dns, user_dn)
        except xmlrpclib.Fault, fault:
            raise ipaerror.gen_exception(fault.faultCode, fault.faultString)
        except socket.error, (value, msg):
            raise xmlrpclib.Fault(value, msg)

        return ipautil.unwrap_binary_data(result)

    def remove_groups_from_user(self, group_dns, user_dn):
        """Given a list of group dn's remove them from the user.

           Returns a list of the group dns that were not removed.
        """
        server = self.setup_server()
        try:
            result = server.remove_groups_from_user(group_dns, user_dn)
        except xmlrpclib.Fault, fault:
            raise ipaerror.gen_exception(fault.faultCode, fault.faultString)
        except socket.error, (value, msg):
            raise xmlrpclib.Fault(value, msg)

        return ipautil.unwrap_binary_data(result)

    def update_group(self,oldgroup,newgroup):
        """Update an existing group. oldgroup and newgroup are dicts of attributes"""
        server = self.setup_server()
    
        try:
            result = server.update_group(ipautil.wrap_binary_data(oldgroup),
                    ipautil.wrap_binary_data(newgroup))
        except xmlrpclib.Fault, fault:
            raise ipaerror.gen_exception(fault.faultCode, fault.faultString)
        except socket.error, (value, msg):
            raise xmlrpclib.Fault(value, msg)

        return ipautil.unwrap_binary_data(result)

    def delete_group(self,group_dn):
        """Delete a group. group_dn is the dn of the group to be deleted."""
        server = self.setup_server()
    
        try:
            result = server.delete_group(group_dn)
        except xmlrpclib.Fault, fault:
            raise ipaerror.gen_exception(fault.faultCode, fault.faultString)
        except socket.error, (value, msg):
            raise xmlrpclib.Fault(value, msg)

        return ipautil.unwrap_binary_data(result)

    def add_group_to_group(self, group_cn, tgroup_cn):
        """Add a group to an existing group.
           group_cn is a cn of the group to add
           tgroup_cn is the cn of the group to be added to
        """
        server = self.setup_server()
        try:
            result = server.add_group_to_group(group_cn, tgroup_cn)
        except xmlrpclib.Fault, fault:
            raise ipaerror.gen_exception(fault.faultCode, fault.faultString)
        except socket.error, (value, msg):
            raise xmlrpclib.Fault(value, msg)
    
        return ipautil.unwrap_binary_data(result)

    def attrs_to_labels(self,attrs):
        """Convert a list of LDAP attributes into a more readable form."""

        server = self.setup_server()
        try:
            result = server.attrs_to_labels(attrs)
        except xmlrpclib.Fault, fault:
            raise ipaerror.gen_exception(fault.faultCode, fault.faultString)
        except socket.error, (value, msg):
            raise xmlrpclib.Fault(value, msg)

        return ipautil.unwrap_binary_data(result)

    def get_all_attrs(self):
        """We have a list of hardcoded attributes -> readable labels. Return
           that complete list if someone wants it.
        """

        server = self.setup_server()
        try:
            result = server.get_all_attrs()
        except xmlrpclib.Fault, fault:
            raise ipaerror.gen_exception(fault.faultCode, fault.faultString)
        except socket.error, (value, msg):
            raise xmlrpclib.Fault(value, msg)

        return ipautil.unwrap_binary_data(result)

    def group_members(self, groupdn, attr_list=None, memberstype=0):
        """Do a memberOf search of groupdn and return the attributes in
           attr_list (an empty list returns everything)."""

        if attr_list is None:
            attr_list = "__NONE__"

        server = self.setup_server()
        try:
            result = server.group_members(groupdn, attr_list, memberstype)
        except xmlrpclib.Fault, fault:
            raise ipaerror.gen_exception(fault.faultCode, fault.faultString)
        except socket.error, (value, msg):
            raise xmlrpclib.Fault(value, msg)

        return ipautil.unwrap_binary_data(result)

    def mark_group_active(self,cn):
        """Mark a group as active"""
        server = self.setup_server()
    
        try:
            result = server.mark_group_active(cn)
        except xmlrpclib.Fault, fault:
            raise ipaerror.gen_exception(fault.faultCode, fault.faultString)
        except socket.error, (value, msg):
            raise xmlrpclib.Fault(value, msg)

        return ipautil.unwrap_binary_data(result)

    def mark_group_inactive(self,cn):
        """Mark a group as inactive"""
        server = self.setup_server()
    
        try:
            result = server.mark_group_inactive(cn)
        except xmlrpclib.Fault, fault:
            raise ipaerror.gen_exception(fault.faultCode, fault.faultString)
        except socket.error, (value, msg):
            raise xmlrpclib.Fault(value, msg)

        return ipautil.unwrap_binary_data(result)

# Configuration support

    def get_ipa_config(self):
        """Get the IPA configuration"""
        server = self.setup_server()
        try:
            result = server.get_ipa_config()
        except xmlrpclib.Fault, fault:
            raise ipaerror.gen_exception(fault.faultCode, fault.faultString)
        except socket.error, (value, msg):
            raise xmlrpclib.Fault(value, msg)

        return ipautil.unwrap_binary_data(result)

    def update_ipa_config(self, oldconfig, newconfig):
        """Update the IPA configuration"""
        server = self.setup_server()
        try:
            result = server.update_ipa_config(oldconfig, newconfig)
        except xmlrpclib.Fault, fault:
            raise ipaerror.gen_exception(fault.faultCode, fault.faultString)
        except socket.error, (value, msg):
            raise xmlrpclib.Fault(value, msg)

        return ipautil.unwrap_binary_data(result)

    def get_password_policy(self):
        """Get the IPA password policy"""
        server = self.setup_server()
        try:
            result = server.get_password_policy()
        except xmlrpclib.Fault, fault:
            raise ipaerror.gen_exception(fault.faultCode, fault.faultString)
        except socket.error, (value, msg):
            raise xmlrpclib.Fault(value, msg)

        return ipautil.unwrap_binary_data(result)

    def update_password_policy(self, oldpolicy, newpolicy):
        """Update the IPA password policy"""
        server = self.setup_server()
        try:
            result = server.update_password_policy(ipautil.wrap_binary_data(oldpolicy), ipautil.wrap_binary_data(newpolicy))
        except xmlrpclib.Fault, fault:
            raise ipaerror.gen_exception(fault.faultCode, fault.faultString)
        except socket.error, (value, msg):
            raise xmlrpclib.Fault(value, msg)

        return ipautil.unwrap_binary_data(result)

    def add_service_principal(self, princ_name, force):
        server = self.setup_server()
    
        try:
            result = server.add_service_principal(princ_name, force)
        except xmlrpclib.Fault, fault:
            raise ipaerror.gen_exception(fault.faultCode, fault.faultString)
        except socket.error, (value, msg):
            raise xmlrpclib.Fault(value, msg)

        return ipautil.unwrap_binary_data(result)

    def delete_service_principal(self, principal_dn):
        server = self.setup_server()
    
        try:
            result = server.delete_service_principal(principal_dn)
        except xmlrpclib.Fault, fault:
            raise ipaerror.gen_exception(fault.faultCode, fault.faultString)
        except socket.error, (value, msg):
            raise xmlrpclib.Fault(value, msg)

        return ipautil.unwrap_binary_data(result)

    def find_service_principal (self, criteria, sattrs=None, sizelimit=-1, timelimit=-1):
        """Return a list: counter followed by a Entity object for each host that
           matches the criteria. If the results are truncated, counter will
           be set to -1"""
    
        server = self.setup_server()
        try:
            # None values are not allowed in XML-RPC
            if sattrs is None:
                sattrs = "__NONE__"
            result = server.find_service_principal(criteria, sattrs, sizelimit, timelimit)
        except xmlrpclib.Fault, fault:
            raise ipaerror.gen_exception(fault.faultCode, fault.faultString)
        except socket.error, (value, msg):
            raise xmlrpclib.Fault(value, msg)
    
        return ipautil.unwrap_binary_data(result)

    def get_keytab(self, princ_name):
        server = self.setup_server()
    
        try:
            result = server.get_keytab(princ_name)
        except xmlrpclib.Fault, fault:
            raise ipaerror.gen_exception(fault.faultCode, fault.faultString)
        except socket.error, (value, msg):
            raise xmlrpclib.Fault(value, msg)

        return ipautil.unwrap_binary_data(result)

# radius support

    def get_radius_client_by_ip_addr(self, ip_addr, container, sattrs=None):
        server = self.setup_server()
        if container is None: container = "__NONE__"
        if sattrs is None: sattrs = "__NONE__"
        try:
            result = server.get_radius_client_by_ip_addr(ip_addr, container, sattrs)
        except xmlrpclib.Fault, fault:
            raise ipaerror.gen_exception(fault.faultCode, fault.faultString)
        except socket.error, (value, msg):
            raise xmlrpclib.Fault(value, msg)

        return ipautil.unwrap_binary_data(result)

    def add_radius_client(self, client, container=None):
        server = self.setup_server()

        if container is None: container = "__NONE__"

        try:
            result = server.add_radius_client(ipautil.wrap_binary_data(client), container)
        except xmlrpclib.Fault, fault:
            raise ipaerror.gen_exception(fault.faultCode, fault.faultString)
        except socket.error, (value, msg):
            raise xmlrpclib.Fault(value, msg)

        return ipautil.unwrap_binary_data(result)

    def update_radius_client(self, oldclient, newclient):
        server = self.setup_server()
    
        try:
            result = server.update_radius_client(ipautil.wrap_binary_data(oldclient),
                                                 ipautil.wrap_binary_data(newclient))
        except xmlrpclib.Fault, fault:
            raise ipaerror.gen_exception(fault.faultCode, fault.faultString)
        except socket.error, (value, msg):
            raise xmlrpclib.Fault(value, msg)

        return ipautil.unwrap_binary_data(result)

        
    def delete_radius_client(self, ip_addr, container=None):
        server = self.setup_server()
        if container is None: container = "__NONE__"
    
        try:
            result = server.delete_radius_client(ip_addr, container)
        except xmlrpclib.Fault, fault:
            raise ipaerror.gen_exception(fault.faultCode, fault.faultString)
        except socket.error, (value, msg):
            raise xmlrpclib.Fault(value, msg)

        return ipautil.unwrap_binary_data(result)

    def find_radius_clients(self, criteria, container=None, sattrs=None, sizelimit=-1, timelimit=-1):
        server = self.setup_server()
        if container is None: container = "__NONE__"
        try:
            # None values are not allowed in XML-RPC
            if sattrs is None:
                sattrs = "__NONE__"
            result = server.find_radius_clients(criteria, container, sattrs, sizelimit, timelimit)
        except xmlrpclib.Fault, fault:
            raise ipaerror.gen_exception(fault.faultCode, fault.faultString)
        except socket.error, (value, msg):
            raise xmlrpclib.Fault(value, msg)
    
        return ipautil.unwrap_binary_data(result)

    def get_radius_profile_by_uid(self, ip_addr, user_profile, sattrs=None):
        server = self.setup_server()
        if user_profile is None: user_profile = "__NONE__"
        if sattrs is None: sattrs = "__NONE__"
        try:
            result = server.get_radius_profile_by_uid(ip_addr, user_profile, sattrs)
        except xmlrpclib.Fault, fault:
            raise ipaerror.gen_exception(fault.faultCode, fault.faultString)
        except socket.error, (value, msg):
            raise xmlrpclib.Fault(value, msg)

        return ipautil.unwrap_binary_data(result)

    def add_radius_profile(self, profile, user_profile=None):
        server = self.setup_server()

        if user_profile is None: user_profile = "__NONE__"

        try:
            result = server.add_radius_profile(ipautil.wrap_binary_data(profile), user_profile)
        except xmlrpclib.Fault, fault:
            raise ipaerror.gen_exception(fault.faultCode, fault.faultString)
        except socket.error, (value, msg):
            raise xmlrpclib.Fault(value, msg)

        return ipautil.unwrap_binary_data(result)

    def update_radius_profile(self, oldprofile, newprofile):
        server = self.setup_server()
    
        try:
            result = server.update_radius_profile(ipautil.wrap_binary_data(oldprofile),
                                                 ipautil.wrap_binary_data(newprofile))
        except xmlrpclib.Fault, fault:
            raise ipaerror.gen_exception(fault.faultCode, fault.faultString)
        except socket.error, (value, msg):
            raise xmlrpclib.Fault(value, msg)

        return ipautil.unwrap_binary_data(result)

        
    def delete_radius_profile(self, ip_addr, user_profile=None):
        server = self.setup_server()
        if user_profile is None: user_profile = "__NONE__"
    
        try:
            result = server.delete_radius_profile(ip_addr, user_profile)
        except xmlrpclib.Fault, fault:
            raise ipaerror.gen_exception(fault.faultCode, fault.faultString)
        except socket.error, (value, msg):
            raise xmlrpclib.Fault(value, msg)

        return ipautil.unwrap_binary_data(result)

    def find_radius_profiles(self, criteria, user_profile=None, sattrs=None, sizelimit=-1, timelimit=-1):
        server = self.setup_server()
        if user_profile is None: user_profile = "__NONE__"
        try:
            # None values are not allowed in XML-RPC
            if sattrs is None:
                sattrs = "__NONE__"
            result = server.find_radius_profiles(criteria, user_profile, sattrs, sizelimit, timelimit)
        except xmlrpclib.Fault, fault:
            raise ipaerror.gen_exception(fault.faultCode, fault.faultString)
        except socket.error, (value, msg):
            raise xmlrpclib.Fault(value, msg)
    
        return ipautil.unwrap_binary_data(result)

