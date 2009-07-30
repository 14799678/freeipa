# Copyright (C) 2007    Red Hat
# see file 'COPYING' for use and warranty information
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation; version 2 only
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.    See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA 02111-1307 USA
#

import exceptions
import types

class IPAError(exceptions.Exception):
    """Base error class for IPA Code"""

    def __init__(self, code, message="", detail=None):
        """code is the IPA error code.
           message is a human viewable error message.
           detail is an optional exception that provides more detail about the
           error."""
        self.code = code
        self.msg = message
        # Fill this in as an empty LDAP error message so we don't have a lot
        # of "if e.detail ..." everywhere
        if detail is None:
             detail = []
             detail.append({'desc':'','info':''})
        self.detail = detail

    def __str__(self):
        return self.msg

    def __repr__(self):
        repr = "%d: %s" % (self.code, self.msg)
        if self.detail:
            repr += "\n%s" % str(self.detail)
        return repr


###############
# Error codes #
###############

code_map_dict = {}

def gen_exception(code, message=None, nested_exception=None):
    """This should be used by IPA code to translate error codes into the
       correct exception/message to throw.

       message is an optional argument which overrides the default message.

       nested_exception is an optional argument providing more details
       about the error."""
    (default_message, exception) = code_map_dict.get(code, ("unknown", IPAError))
    if not message:
        message = default_message
    return exception(code, message, nested_exception)

def exception_for(code):
    """Used to look up the corresponding exception for an error code.
       Will usually be used for an except block."""
    (default_message, exception) = code_map_dict.get(code, ("unknown", IPAError))
    return exception

def gen_error_code(category, detail, message):
    """Private method used to generate exception codes.
       category is one of the 16 bit error code category constants.
       detail is a 16 bit code within the category.
       message is a human readable description on the error.
       exception is the exception to throw for this error code."""
    code = (category << 16) + detail
    exception = types.ClassType("IPAError%d" % code,
                      (IPAError,),
                      {})
    code_map_dict[code] = (message, exception)

    return code

#
# Error codes are broken into two 16-bit values: category and detail
#

#
# LDAP Errors:   0x0001
#
LDAP_CATEGORY = 0x0001

LDAP_DATABASE_ERROR = gen_error_code(
        LDAP_CATEGORY,
        0x0001,
        "A database error occurred")

LDAP_MIDAIR_COLLISION = gen_error_code(
        LDAP_CATEGORY,
        0x0002,
        "Change collided with another change")

LDAP_NOT_FOUND = gen_error_code(
        LDAP_CATEGORY,
        0x0003,
        "Entry not found")

LDAP_DUPLICATE = gen_error_code(
        LDAP_CATEGORY,
        0x0004,
        "This entry already exists")

LDAP_MISSING_DN = gen_error_code(
        LDAP_CATEGORY,
        0x0005,
        "Entry missing dn")

LDAP_EMPTY_MODLIST = gen_error_code(
        LDAP_CATEGORY,
        0x0006,
        "No modifications to be performed")

LDAP_NO_CONFIG = gen_error_code(
        LDAP_CATEGORY,
        0x0007,
        "IPA configuration not found")

#
# Function input errors
#
INPUT_CATEGORY = 0x0002

INPUT_INVALID_PARAMETER = gen_error_code(
        INPUT_CATEGORY,
        0x0001,
        "Invalid parameter(s)")

INPUT_SAME_GROUP = gen_error_code(
        INPUT_CATEGORY,
        0x0002,
        "You can't add a group to itself")

INPUT_NOT_DNS_A_RECORD = gen_error_code(
        INPUT_CATEGORY,
        0x0003,
        "The requested hostname is not a DNS A record. This is required by Kerberos.")

INPUT_ADMINS_IMMUTABLE = gen_error_code(
        INPUT_CATEGORY,
        0x0004,
        "The admins group cannot be renamed.")

INPUT_MALFORMED_SERVICE_PRINCIPAL = gen_error_code(
        INPUT_CATEGORY,
        0x0005,
        "The requested service principal is not of the form: service/fully-qualified host name")

INPUT_REALM_MISMATCH = gen_error_code(
        INPUT_CATEGORY,
        0x0006,
        "The realm for the principal does not match the realm for this IPA server.")

INPUT_ADMIN_REQUIRED = gen_error_code(
        INPUT_CATEGORY,
        0x0007,
        "The admin user cannot be deleted.")

INPUT_CANT_INACTIVATE = gen_error_code(
        INPUT_CATEGORY,
        0x0008,
        "This entry cannot be inactivated.")

INPUT_ADMIN_REQUIRED_IN_ADMINS = gen_error_code(
        INPUT_CATEGORY,
        0x0009,
        "The admin user cannot be removed from the admins group.")

INPUT_SERVICE_PRINCIPAL_REQUIRED = gen_error_code(
        INPUT_CATEGORY,
        0x000A,
        "You cannot remove IPA server service principals.")

INPUT_UID_TOO_LONG = gen_error_code(
        INPUT_CATEGORY,
        0x0009,
        "The requested username is too long.")

#
# Connection errors
#
CONNECTION_CATEGORY = 0x0003

CONNECTION_NO_CONN = gen_error_code(
        CONNECTION_CATEGORY,
        0x0001,
        "Connection to database failed")

CONNECTION_NO_CCACHE = gen_error_code(
        CONNECTION_CATEGORY,
        0x0002,
        "No Kerberos credentials cache is available. Connection cannot be made.")

CONNECTION_GSSAPI_CREDENTIALS = gen_error_code(
        CONNECTION_CATEGORY,
        0x0003,
        "GSSAPI Authorization error")

CONNECTION_UNWILLING = gen_error_code(
        CONNECTION_CATEGORY,
        0x0004,
        "Account inactivated. Server is unwilling to perform.")

#
# Configuration errors
#
CONFIGURATION_CATEGORY = 0x0004

CONFIG_REQUIRED_GROUPS = gen_error_code(
        CONFIGURATION_CATEGORY,
        0x0001,
        "The admins and editors groups are required.")

CONFIG_DEFAULT_GROUP = gen_error_code(
        CONFIGURATION_CATEGORY,
        0x0002,
        "You cannot remove the default users group.")

CONFIG_INVALID_OC = gen_error_code(
        CONFIGURATION_CATEGORY,
        0x0003,
        "Invalid object class.")

#
# Entry status errors
#
STATUS_CATEGORY = 0x0005

STATUS_ALREADY_ACTIVE = gen_error_code(
        STATUS_CATEGORY,
        0x0001,
        "This entry is already active.")

STATUS_ALREADY_INACTIVE = gen_error_code(
        STATUS_CATEGORY,
        0x0002,
        "This entry is already inactive.")

STATUS_HAS_NSACCOUNTLOCK = gen_error_code(
        STATUS_CATEGORY,
        0x0003,
        "This entry appears to have the nsAccountLock attribute in it so the Class of Service activation/inactivation will not work. You will need to remove the attribute nsAccountLock for this to work.")

STATUS_NOT_GROUP_MEMBER = gen_error_code(
        STATUS_CATEGORY,
        0x0004,
        "This entry is not a member of the group.")
