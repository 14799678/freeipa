/*jsl:import ipa.js */
/*jsl:import search.js */

/*  Authors:
 *    Adam Young <ayoung@redhat.com>
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

/* REQUIRES: ipa.js, details.js, search.js, add.js, facet.js, entity.js, widget.js */

IPA.dns = {};

IPA.dns.zone_entity = function(spec) {

    var that = IPA.entity(spec);

    if (!IPA.dns_enabled) {
        var except = {
            expected: true
        };
        throw except;
    }

    that.init = function(params) {

        params.builder.facet_groups([ 'dnsrecord', 'settings' ]).
        search_facet({
            title: IPA.metadata.objects.dnszone.label,
            columns: [ 'idnsname' ]
        }).
        details_facet({
            factory: IPA.dnszone_details_facet,
            sections: [{
                name: 'identity',
                fields: [
                    'idnsname',
                    {
                        factory: IPA.radio_widget,
                        name: 'idnszoneactive',
                        options: [
                            { value: 'TRUE', label: IPA.get_message('true') },
                            { value: 'FALSE', label: IPA.get_message('false') }
                        ]
                    },
                    'idnssoamname',
                    'idnssoarname',
                    'idnssoaserial',
                    'idnssoarefresh',
                    'idnssoaretry',
                    'idnssoaexpire',
                    'idnssoaminimum',
                    'dnsttl',
                    {
                        factory: IPA.combobox_widget,
                        name: 'dnsclass',
                        options: [
                            'IN', 'CS', 'CH', 'HS'
                        ]
                    },
                    {
                        factory: IPA.radio_widget,
                        name: 'idnsallowdynupdate',
                        options: [
                            { value: 'TRUE', label: IPA.get_message('true') },
                            { value: 'FALSE', label: IPA.get_message('false') }
                        ]
                    },
                    {
                        factory: IPA.textarea_widget,
                        name: 'idnsupdatepolicy'
                    }
                ]
            }]
        }).
        nested_search_facet({
            facet_group: 'dnsrecord',
            nested_entity : 'dnsrecord',
            name: 'records',
            title: IPA.metadata.objects.dnszone.label_singular,
            label: IPA.metadata.objects.dnsrecord.label,
            load: IPA.dns_record_search_load,
            get_values: IPA.dnsrecord_get_delete_values,
            columns: [
                {
                    name: 'idnsname',
                    label: IPA.get_entity_param('dnsrecord', 'idnsname').label,
                    primary_key: true
                },
                {
                    name: 'type',
                    label: IPA.messages.objects.dnsrecord.type
                },
                {
                    name: 'data',
                    label: IPA.messages.objects.dnsrecord.data
                }
            ]
        }).
        standard_association_facets().
        adder_dialog({
            factory: IPA.dnszone_adder_dialog,
            height: 300,
            sections: [
                {
                    factory: IPA.dnszone_name_section,
                    name: 'name',
                    fields: [
                        {
                            name: 'idnsname',
                            required: false
                        },
                        'name_from_ip'
                    ]
                },
                {
                    name: 'other',
                    fields: [
                        'idnssoamname',
                        {
                            name: 'idnssoarname',
                            required: false
                        },
                        {
                            factory: IPA.force_dnszone_add_checkbox_widget,
                            name: 'force',
                            metadata: IPA.get_method_option('dnszone_add', 'force')
                        }
                    ]
                }
            ]
        });
    };

    return that;
};

IPA.dnszone_details_facet = function(spec) {

    spec = spec || {};

    var that = IPA.details_facet(spec);

    that.update = function(on_success, on_error) {

        var args = that.get_primary_key();

        var modify_operation = {
            execute: false,
            command: IPA.command({
                entity: that.entity.name,
                method: 'mod',
                args: args,
                options: { all: true, rights: true }
            })
        };

        var enable_operation = {
            execute: false,
            command: IPA.command({
                entity: that.entity.name,
                method: 'enable',
                args: args,
                options: { all: true, rights: true }
            })
        };

        var record = {};
        that.save(record);

        var sections = that.sections.values;
        for (var i=0; i<sections.length; i++) {
            var section = sections[i];

            var section_fields = section.fields.values;
            for (var j=0; j<section_fields.length; j++) {
                var field = section_fields[j];
                if (!field.is_dirty()) continue;

                var values = record[field.name];
                if (!values) continue;

                var metadata = field.metadata;

                // skip primary key
                if (metadata && metadata.primary_key) continue;

                // check enable/disable
                if (field.name == 'idnszoneactive') {
                    if (values[0] == 'FALSE') enable_operation.command.method = 'disable';
                    enable_operation.execute = true;
                    continue;
                }

                if (metadata) {
                    if (values.length == 1) {
                        modify_operation.command.set_option(field.name, values[0]);
                    } else if (field.join) {
                        modify_operation.command.set_option(field.name, values.join(','));
                    } else {
                        modify_operation.command.set_option(field.name, values);
                    }

                } else {
                    if (values.length) {
                        modify_operation.command.set_option('setattr', field.name+'='+values[0]);
                    } else {
                        modify_operation.command.set_option('setattr', field.name+'=');
                    }
                    for (var l=1; l<values.length; l++) {
                        modify_operation.command.set_option('addattr', field.name+'='+values[l]);
                    }
                }

                modify_operation.execute = true;
            }
        }

        var batch = IPA.batch_command({
            name: 'dnszone_details_update',
            on_success: function(data, text_status, xhr) {
                that.refresh();
                if (on_success) on_success.call(this, data, text_status, xhr);
            },
            on_error: function(xhr, text_status, error_thrown) {
                that.refresh();
                if (on_error) on_error.call(this, xhr, text_status, error_thrown);
            }
        });

        if (modify_operation.execute) batch.add_command(modify_operation.command);
        if (enable_operation.execute) batch.add_command(enable_operation.command);

        if (!batch.commands.length) {
            that.refresh();
            return;
        }

        batch.execute();
    };

    return that;
};

IPA.dnszone_name_section = function(spec) {

    spec = spec || {};

    var that = IPA.details_table_section(spec);

    that.create = function(container) {
        that.container = container;

        that.message_container = $('<div/>', {
            style: 'display: none',
            'class': 'dialog-message ui-state-highlight ui-corner-all'
        }).appendTo(that.container);

        var table = $('<table/>', {
            'class': 'section-table'
        }).appendTo(that.container);

        var idnsname = that.get_field('idnsname');

        var tr = $('<tr/>').appendTo(table);

        var td = $('<td/>', {
            'class': 'section-cell-label',
            title: idnsname.label
        }).appendTo(tr);

        var label = $('<label/>', {
            name: 'idnsname',
            'class': 'field-label',
            'for': 'dnszone-adder-dialog-idnsname-radio'
        }).appendTo(td);

        idnsname.radio = $('<input/>', {
            type: 'radio',
            id: 'dnszone-adder-dialog-idnsname-radio',
            name: 'type',
            value: idnsname.name
        }).appendTo(label);

        label.append(idnsname.label+':');

        idnsname.create_required(td);

        td = $('<td/>', {
            'class': 'section-cell-field',
            title: idnsname.label
        }).appendTo(tr);

        var span = $('<span/>', {
            name: 'idnsname',
            'class': 'field'
        }).appendTo(td);

        idnsname.create(span);

        var idnsname_input = $('input', span);

        var name_from_ip = that.get_field('name_from_ip');

        tr = $('<tr/>').appendTo(table);

        td = $('<td/>', {
            'class': 'section-cell-label',
            title: name_from_ip.label
        }).appendTo(tr);

        label = $('<label/>', {
            name: 'name_from_ip',
            'class': 'field-label',
            'for': 'dnszone-adder-dialog-name_from_ip-radio'
        }).appendTo(td);

        name_from_ip.radio = $('<input/>', {
            type: 'radio',
            id: 'dnszone-adder-dialog-name_from_ip-radio',
            name: 'type',
            value: name_from_ip.name
        }).appendTo(label);

        label.append(name_from_ip.label+':');

        name_from_ip.create_required(td);

        td = $('<td/>', {
            'class': 'section-cell-field',
            title: name_from_ip.label
        }).appendTo(tr);

        span = $('<span/>', {
            name: 'name_from_ip',
            'class': 'field'
        }).appendTo(td);

        name_from_ip.create(span);

        var name_from_ip_input = $('input', span);

        idnsname.radio.click(function() {
            idnsname_input.attr('disabled', false);
            name_from_ip_input.attr('disabled', true);

            idnsname.set_required(true);
            name_from_ip.set_required(false);

            name_from_ip.reset();
        });

        name_from_ip.radio.click(function() {
            idnsname_input.attr('disabled', true);
            name_from_ip_input.attr('disabled', false);

            idnsname.set_required(false);
            name_from_ip.set_required(true);

            idnsname.reset();
        });

        idnsname.radio.click();
    };

    that.save = function(record) {

        var idnsname = that.get_field('idnsname');
        var name_from_ip = that.get_field('name_from_ip');

        if (idnsname.radio.is(':checked')) {
            record.idnsname = idnsname.save();

        } else {
            record.name_from_ip = name_from_ip.save();
        }
    };

    return that;
};

IPA.dnszone_adder_dialog = function(spec) {

    spec = spec || {};

    var that = IPA.entity_adder_dialog(spec);

    that.create = function() {
        that.entity_adder_dialog_create();
        that.container.addClass('dnszone-adder-dialog');
    };

    return that;
};

IPA.dns_record_search_load = function (result) {
    this.table.empty();
    var normalized_record;
    var dns_record_types = IPA.dns_record_types();
    for (var i = 0; i<result.length; i++) {
        var record = result[i];
        for (var j =0; j < dns_record_types.length; j += 1){
            var record_type = dns_record_types[j].value;
            if (record[record_type]){
                var record_of_type = record[record_type];
                for (var k =0;
                     k < record_of_type.length;
                     k+=1)
                {
                    normalized_record = {
                        idnsname:record.idnsname,
                        type:record_type,
                        data:record_of_type[k]
                    };
                    this.table.add_record(normalized_record);

                }
            }
        }
    }
};

IPA.dns.record_entity = function(spec) {

    var that = IPA.entity(spec);

    if (!IPA.dns_enabled) {
        var except = {
            expected: true
        };
        throw except;
    }

    that.init = function(params) {

        params.builder.containing_entity('dnszone').
        details_facet({
            post_update_hook:function(data){
                var result = data.result.result;
                 if (result.idnsname) {
                    this.load(result);
                } else {
                    this.reset();
                    var dialog = IPA.dnsrecord_redirection_dialog();
                    dialog.open(this.container);
                }
            },
            disable_breadcrumb: false,
            sections:[
               {
                   name:'identity',
                   label: IPA.messages.details.identity,
                   fields:[
                       {
                           factory:IPA.dnsrecord_host_link_widget,
                           name: 'idnsname',
                           other_entity:'host',
                           label:IPA.get_entity_param(
                               'dnsrecord', 'idnsname').label
                       }
                   ]
               },
                {
                    name:'standard',
                    label:IPA.messages.objects.dnsrecord.standard,
                    fields:[
                        { factory: IPA.multivalued_text_widget,
                          name: 'arecord',
                          metadata: {primary_key: false},
                          label:'A'
                        },
                        { factory: IPA.multivalued_text_widget,
                          name: 'aaaarecord',
                          metadata: {primary_key: false},
                          label:'AAAA'
                        },
                        { factory: IPA.multivalued_text_widget,
                          name: 'ptrrecord',
                          metadata: {primary_key: false},
                          label:'PTR'
                        },
                        { factory: IPA.multivalued_text_widget,
                          name: 'srvrecord',
                          metadata: {primary_key: false},
                          label:'SRV'
                        },
                        { factory: IPA.multivalued_text_widget,
                          name: 'txtrecord',
                          metadata: {primary_key: false},
                          label:'TXT'
                        },
                        { factory: IPA.multivalued_text_widget,
                          name: 'cnamerecord',
                          metadata: {primary_key: false},
                          label:'CNAME'
                        },
                        { factory: IPA.multivalued_text_widget,
                          label:'MX',
                          metadata: {primary_key: false},
                          name:"mxrecord"
                        },
                        { factory: IPA.multivalued_text_widget,
                          label:'NS',
                          metadata: {primary_key: false},
                          name:"nsrecord"
                        }

                    ]
                },
                {
                    name:'unusual',
                    label:IPA.messages.objects.dnsrecord.other,
                    fields:[
                        { factory: IPA.multivalued_text_widget,
                          label:'AFSDB',
                          metadata: {primary_key: false},
                          name: "afsdbrecord"
                        },
                        { factory: IPA.multivalued_text_widget,
                          label:'CERT',
                          metadata: {primary_key: false},
                          name:"certrecord"
                        },
                        { factory: IPA.multivalued_text_widget,
                          label:'DNAME',
                          metadata: {primary_key: false},
                          name:"dnamerecord"
                        },
                        { factory: IPA.multivalued_text_widget,
                          label:'DSRECORD',
                          metadata: {primary_key: false},
                          name:"dsrecord"
                        },
                        { factory: IPA.multivalued_text_widget,
                          label:'KEY',
                          metadata: {primary_key: false},
                          name:"keyrecord"
                        },
                        { factory: IPA.multivalued_text_widget,
                          label:'KX',
                          metadata: {primary_key: false},
                          name:"kxrecord"
                        },
                        { factory: IPA.multivalued_text_widget,
                          label:'LOC',
                          metadata: {primary_key: false},
                          name:"locrecord"
                        },
                        { factory: IPA.multivalued_text_widget,
                          label:'NAPTR',
                          name:"naptrrecord"
                        },
                        { factory: IPA.multivalued_text_widget,
                          label:'NSEC',
                          metadata: {primary_key: false},
                          name:"nsecrecord"
                        },
                        { factory: IPA.multivalued_text_widget,
                          label:'RRSIG',
                          metadata: {primary_key: false},
                          name:"rrsigrecord"
                        },
                        { factory: IPA.multivalued_text_widget,
                          label:'SIG',
                          metadata: {primary_key: false},
                          name:"sigrecord"
                        },
                        { factory: IPA.multivalued_text_widget,
                          label:'SSHFP',
                          metadata: {primary_key: false},
                          name:"sshfprecord"
                        }
                    ]
                }
            ]
        }).
        adder_dialog({
            pre_execute_hook: function(command) {
                var record_type = command.options.record_type;
                var record_data = command.options.record_data;

                delete command.options.record_type;
                delete command.options.record_data;
                command.options[record_type] = record_data;
            },
            fields: [
                'idnsname',
                {
                    name: 'record_type',
                    label: IPA.messages.objects.dnsrecord.type,
                    factory: IPA.dnsrecord_type_widget
                },
                {
                    name: 'record_data',
                    label: IPA.messages.objects.dnsrecord.data,
                    factory: IPA.text_widget,
                    required: true
                }
            ]
        });
    };

    return that;
};

IPA.dnsrecord_redirection_dialog = function(spec) {
    spec = spec || {};
    spec.title = spec.title || IPA.messages.dialogs.redirection;

    var that = IPA.dialog(spec);

    that.create = function() {
        $('<p/>', {
            'text': IPA.messages.objects.dnsrecord.deleted_no_data
        }).appendTo(that.container);
        $('<p/>', {
            'text': IPA.messages.objects.dnsrecord.redirection_dnszone
        }).appendTo(that.container);
    };

    that.create_button({
        name: 'ok',
        label: IPA.messages.buttons.ok,
        click: function() {
            that.close();
            IPA.nav.show_page('dnszone','default');
        }
    });
    return that;
};

IPA.dnsrecord_host_link_widget = function(spec) {
    var that = IPA.entity_link_widget(spec);
    that.other_pkeys = function() {
        var pkey = that.entity.get_primary_key();
        return [pkey[0]+'.'+pkey[1]];
    };
    return that;
};

IPA.dns_record_types = function() {
    var attrs = IPA.metadata.objects.dnsrecord.default_attributes;
    var record_types = [];
    for (var i=0; i<attrs.length; i++) {
        var attr = attrs[i];
        var index = attr.search('record$');
        if (index > -1) {
            var rec_type = {
                label: attr.substring(0, index).toUpperCase(),
                value: attr
            };
            record_types.push(rec_type);
        }
    }
    return record_types;
};

IPA.dnsrecord_type_widget = function(spec) {

    spec.options = IPA.dns_record_types();
    var that = IPA.select_widget(spec);
    return that;
};

IPA.force_dnszone_add_checkbox_widget = function(spec) {
    var metadata = IPA.get_method_option('dnszone_add', spec.name);
    spec.label = metadata.label;
    spec.tooltip = metadata.doc;
    return IPA.checkbox_widget(spec);
};


IPA.dnsrecord_get_delete_values = function() {

    var records = {};
    var value;
    var record_type;
    $('input[name="select"]:checked', this.table.tbody).each(function() {

        $('span',$(this).parent().parent()).each(function(){
            var name = this.attributes['name'].value;

            if (name === 'idnsname'){
                value = records[$(this).text()];
                if (!value){
                    value = {pkey:$(this).text()};
                    records[$(this).text()] = value;
                }
            }else if (name === 'type'){
                record_type = $(this).text();
            }else if (name === 'data'){
                if (!value[record_type]){
                    value[record_type] = $(this).text();
                }else{
                     value[record_type] += "," + $(this).text();
                }
            }
        });
    });

    var value_array = [];
    for (var key in records){
        value_array.push(records[key]);
    }

    return value_array;
};

IPA.register('dnszone', IPA.dns.zone_entity);
IPA.register('dnsrecord', IPA.dns.record_entity);
