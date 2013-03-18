/*  Authors:
 *    Ana Krivokapic <akrivoka@redhat.com>
 *
 * Copyright (C) 2013 Red Hat
 * see file 'COPYING' for use and warranty information
 *
 * This program is free software; you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation, either version 3 of the License, or
 * (at your option) any later version.
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with this program.  If not, see <http://www.gnu.org/licenses/>.
 */

define(['./ipa', './jquery', './details', './entity'], function (IPA, $) {

    IPA.realmdomains = {};

    IPA.realmdomains.entity = function (spec) {

        var that = IPA.entity(spec);

        that.init = function () {
            that.entity_init();

            that.builder.details_facet({
                factory: IPA.realmdomains_details_facet,
                title: IPA.metadata.objects.realmdomains.label,
                sections: [
                    {
                        name: 'identity',
                        label: IPA.messages.objects.realmdomains.identity,
                        fields: [
                            {
                                name: 'associateddomain',
                                type: 'multivalued'
                            }
                        ]
                    }
                ],
                needs_update: true
            });
        };
        return that;
    };

    IPA.realmdomains_details_facet = function (spec) {
        spec = spec || {};
        var that = IPA.details_facet(spec);

        that.update = function (on_success, on_error) {
            var command = that.create_update_command();

            command.on_success = function (data, text_status, xhr) {
                that.update_on_success(data, text_status, xhr);
                if (on_success) on_success.call(this, data, text_status, xhr);
            };

            command.on_error = function (xhr, text_status, error_thrown) {
                that.update_on_error(xhr, text_status, error_thrown);
                if (on_error) on_error.call(this, xhr, text_status, error_thrown);
            };

            var dialog = IPA.confirm_dialog({
                title: IPA.messages.objects.realmdomains.check_dns,
                message: IPA.messages.objects.realmdomains.check_dns_confirmation,
                ok_label: IPA.messages.objects.realmdomains.check_dns,
                on_ok: function () {
                    command.execute();
                }
            });

            var cancel_button = dialog.get_button('cancel');
            dialog.buttons.remove('cancel');

            dialog.create_button({
                name: 'force',
                label: IPA.messages.objects.realmdomains.force_update,
                visible: true,
                click: function () {
                    command.set_option('force', true);
                    command.execute();
                    dialog.close();
                }
            });

            dialog.add_button(cancel_button);
            dialog.open();
        };

        return that;
    };

    IPA.register('realmdomains', IPA.realmdomains.entity);

    return {};
});
