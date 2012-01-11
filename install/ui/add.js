/*jsl:import ipa.js */

/*  Authors:
 *    Pavel Zuna <pzuna@redhat.com>
 *    Endi Sukma Dewata <edewata@redhat.com>
 *
 * Copyright (C) 2010 Red Hat
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

/* REQUIRES: ipa.js */

IPA.entity_adder_dialog = function(spec) {

    spec = spec || {};

    var that = IPA.dialog(spec);

    that.method = spec.method || 'add';
    that.pre_execute_hook = spec.pre_execute_hook;
    that.on_error = spec.on_error ;
    that.retry = typeof spec.retry !== 'undefined' ? spec.retry : true;
    that.command = null;

    that.show_edit_page = spec.show_edit_page || show_edit_page;

    var init = function() {
        that.create_button({
            name: 'add',
            label: IPA.messages.buttons.add,
            click: function() {
                that.hide_message();
                that.add(
                    function(data, text_status, xhr) {
                        var facet = IPA.current_entity.get_facet();
                        facet.refresh();
                        that.close();
                    },
                    that.on_error);
            }
        });

        that.create_button({
            name: 'add_and_add_another',
            label: IPA.messages.buttons.add_and_add_another,
            click: function() {
                that.hide_message();
                that.add(
                    function(data, text_status, xhr) {
                        var label = that.entity.metadata.label_singular;
                        var message = IPA.messages.dialogs.add_confirmation;
                        message = message.replace('${entity}', label);
                        that.show_message(message);

                        var facet = IPA.current_entity.get_facet();
                        facet.refresh();
                        that.reset();
                    },
                    that.on_error);
            }
        });

        that.create_button({
            name: 'add_and_edit',
            label: IPA.messages.buttons.add_and_edit,
            click: function() {
                that.hide_message();
                that.add(
                    function(data, text_status, xhr) {
                        that.close();
                        var result = data.result.result;
                        that.show_edit_page(that.entity, result);
                    },
                    that.on_error);
            }
        });

        that.create_button({
            name: 'cancel',
            label: IPA.messages.buttons.cancel,
            click: function() {
                that.hide_message();
                that.close();
            }
        });
    };

    function show_edit_page(entity,result) {
        var pkey_name = entity.metadata.primary_key;
        var pkey = result[pkey_name];
        if (pkey instanceof Array) {
            pkey = pkey[0];
        }
        IPA.nav.show_entity_page(that.entity, 'default', pkey);
    }

    that.add = function(on_success, on_error) {

        var pkey_name = that.entity.metadata.primary_key;

        var command = IPA.command({
            entity: that.entity.name,
            method: that.method,
            retry: that.retry,
            on_success: on_success,
            on_error: on_error
        });
        that.command = command;

        command.add_args(that.entity.get_primary_key_prefix());

        if (!that.validate()) return;

        var record = {};
        that.save(record);

        var sections = that.sections.values;
        for (var i=0; i<sections.length; i++) {
            var section = sections[i];

            var section_fields = section.fields.values;
            for (var j=0; j<section_fields.length; j++) {
                var field = section_fields[j];

                var values = record[field.name];
                if (!values) continue;

                // TODO: Handle multi-valued attributes like in detail facet's update()
                var value = values.join(',');
                if (!value) continue;

                if (field.name == pkey_name) {
                    command.add_arg(value);
                } else {
                    command.set_option(field.name, value);
                }
            }
        }

        //alert(JSON.stringify(command.to_json()));

        if (that.pre_execute_hook) {
            that.pre_execute_hook(command);
        }

        command.execute();
    };

    that.create = function() {
        that.dialog_create();

        var div = $('<div/>', {
        }).appendTo(that.container);

        $('<span/>', {
            'class': 'required-indicator',
            text: IPA.required_indicator
        }).appendTo(div);

        div.append(' ');

        $('<span/>', {
            text: IPA.messages.widget.validation.required
        }).appendTo(div);
    };

    // methods that should be invoked by subclasses
    that.entity_adder_dialog_create = that.create;

    init();

    return that;
};

