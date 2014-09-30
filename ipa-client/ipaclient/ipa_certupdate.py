# Authors: Jan Cholasta <jcholast@redhat.com>
#
# Copyright (C) 2014  Red Hat
# see file 'COPYING' for use and warranty information
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#

import os
import tempfile
import shutil

from ipapython import (admintool, ipautil, ipaldap, sysrestore, dogtag,
                       certmonger, certdb)
from ipaplatform import services
from ipaplatform.paths import paths
from ipaplatform.tasks import tasks
from ipalib import api, x509, certstore


class CertUpdate(admintool.AdminTool):
    command_name = 'ipa-certupdate'

    usage = "%prog [options]"

    description = ("Update local IPA certificate databases with certificates "
                   "from the server.")

    def validate_options(self):
        super(CertUpdate, self).validate_options(needs_root=True)

    def run(self):
        fstore = sysrestore.FileStore(paths.IPA_CLIENT_SYSRESTORE)
        if (not fstore.has_files() and
            not os.path.exists(paths.IPA_DEFAULT_CONF)):
            raise admintool.ScriptError(
                "IPA client is not configured on this system.")

        api.bootstrap(context='cli_installer')
        api.finalize()

        try:
            server = api.env.server
        except AttributeError:
            server = api.env.host
        ldap = ipaldap.IPAdmin(server)

        tmpdir = tempfile.mkdtemp(prefix="tmp-")
        try:
            principal = str('host/%s@%s' % (api.env.host, api.env.realm))
            ipautil.kinit_hostprincipal(paths.KRB5_KEYTAB, tmpdir, principal)

            ldap.do_sasl_gssapi_bind()

            certs = certstore.get_ca_certs(ldap, api.env.basedn,
                                           api.env.realm, api.env.enable_ra)
        finally:
            shutil.rmtree(tmpdir)

        server_fstore = sysrestore.FileStore(paths.SYSRESTORE)
        if server_fstore.has_files():
            self.update_server(certs)

        self.update_client(certs)

    def update_client(self, certs):
        self.update_file(paths.IPA_CA_CRT, certs)

        ipa_db = certdb.NSSDatabase(paths.IPA_NSSDB_DIR)
        sys_db = certdb.NSSDatabase(paths.NSS_DB_DIR)

        # Remove IPA certs from /etc/pki/nssdb
        for nickname, trust_flags in ipa_db.list_certs():
            while sys_db.has_nickname(nickname):
                try:
                    sys_db.delete_cert(nickname)
                except ipautil.CalledProcessError, e:
                    self.log.error("Failed to remove %s from %s: %s",
                                   nickname, sys_db.secdir, e)
                    break

        # Remove old IPA certs from /etc/ipa/nssdb
        for nickname in ('IPA CA', 'External CA cert'):
            while ipa_db.has_nickname(nickname):
                try:
                    ipa_db.delete_cert(nickname)
                except ipautil.CalledProcessError, e:
                    self.log.error("Failed to remove %s from %s: %s",
                                   nickname, ipa_db.secdir, e)
                    break

        self.update_db(ipa_db.secdir, certs)
        self.update_db(sys_db.secdir, certs)

        tasks.remove_ca_certs_from_systemwide_ca_store()
        tasks.insert_ca_certs_into_systemwide_ca_store(certs)

    def update_server(self, certs):
        instance = '-'.join(api.env.realm.split('.'))
        self.update_db(
            paths.ETC_DIRSRV_SLAPD_INSTANCE_TEMPLATE % instance, certs)
        if services.knownservices.dirsrv.is_running():
            services.knownservices.dirsrv.restart(instance)

        self.update_db(paths.HTTPD_ALIAS_DIR, certs)
        if services.knownservices.httpd.is_running():
            services.knownservices.httpd.restart()

        dogtag_constants = dogtag.configured_constants()
        nickname = 'caSigningCert cert-pki-ca'
        criteria = {
            'cert-database': dogtag_constants.ALIAS_DIR,
            'cert-nickname': nickname,
        }
        request_id = certmonger.get_request_id(criteria)
        if request_id is not None:
            timeout = api.env.startup_timeout + 60

            self.log.debug("resubmitting certmonger request '%s'", request_id)
            certmonger.resubmit_request(request_id, profile='ipaRetrieval')
            try:
                state = certmonger.wait_for_request(request_id, timeout)
            except RuntimeError:
                raise admintool.ScriptError(
                    "Resubmitting certmonger request '%s' timed out, "
                    "please check the request manually" % request_id)
            if state != 'MONITORING':
                raise admintool.ScriptError(
                    "Error resubmitting certmonger request '%s', "
                    "please check the request manually" % request_id)

            self.log.debug("modifying certmonger request '%s'", request_id)
            certmonger.modify(request_id, profile='ipaCACertRenewal')

        self.update_file(paths.CA_CRT, certs)

    def update_file(self, filename, certs, mode=0444):
        certs = (c[0] for c in certs if c[2] is not False)
        try:
            x509.write_certificate_list(certs, filename)
        except Exception, e:
            self.log.error("failed to update %s: %s", filename, e)

    def update_db(self, path, certs):
        db = certdb.NSSDatabase(path)
        for cert, nickname, trusted, eku in certs:
            trust_flags = certstore.key_policy_to_trust_flags(
                trusted, True, eku)
            try:
                db.add_cert(cert, nickname, trust_flags)
            except ipautil.CalledProcessError, e:
                self.log.error(
                    "failed to update %s in %s: %s", nickname, path, e)
