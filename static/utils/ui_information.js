/**
 *  This work is based on original code developed and copyrighted by TNO 2020.
 *  Subsequent contributions are licensed to you by the developers of such code and are
 *  made available to the Project under one or several contributor license agreements.
 *
 *  This work is licensed to you under the Apache License, Version 2.0.
 *  You may obtain a copy of the license at
 *
 *      http://www.apache.org/licenses/LICENSE-2.0
 *
 *  Contributors:
 *      TNO         - Initial implementation
 *  Manager:
 *      TNO
 */


// ------------------------------------------------------------------------------------------------------------
//  Get the tooltip format from markers and lines from the user settings
// ------------------------------------------------------------------------------------------------------------
function get_tooltip_format() {
    let marker_tt = '{name}';
    let line_tt = '{name}';
    if ('ui_settings' in user_settings) {
        if ('tooltips' in user_settings['ui_settings']) {
            if ('marker_tooltip_format' in user_settings['ui_settings']['tooltips'])
                marker_tt = user_settings['ui_settings']['tooltips']['marker_tooltip_format']
            if ('line_tooltip_format' in user_settings['ui_settings']['tooltips'])
                line_tt = user_settings['ui_settings']['tooltips']['line_tooltip_format']
       }
    }
    return {'marker': marker_tt, 'line': line_tt};
}

// ------------------------------------------------------------------------------------------------------------
//  Create tooltip text based on format and list of attributes (name is given as a separate parameter)
// ------------------------------------------------------------------------------------------------------------
function get_tooltip_text(tt_format, name, attrs) {
    console.log(attrs);
    let tt_text = tt_format;
    let attr_list = tt_format.match(/\(.*?\)/g);
    for (attr_idx in attr_list) {
        let attr_tmpl = attr_list[attr_idx];

        let attr_name_par = attr_tmpl.match(/{.*}/)[0];
        let attr_name = /{(.*)}/g.exec(attr_tmpl)[1];

        if (attr_name == 'name') {
            tt_text = tt_text.replace(attr_tmpl, name);
        } else {
            if (attr_name in attrs) {
                let attr_text = attr_tmpl;
                attr_text = attr_text.replace(attr_name_par, attrs[attr_name]);
                attr_text = /\((.*)\)/g.exec(attr_text)[1];
                tt_text = tt_text.replace(attr_tmpl, attr_text);
            } else {      // remove whole item
                tt_text = tt_text.replace(attr_tmpl, '');
            }
        }
    }
    return tt_text;
}

// ------------------------------------------------------------------------------------------------------------
//  Updates tooltip text after attribute changed
// ------------------------------------------------------------------------------------------------------------
function update_asset_tooltip(asset_id, attribute_name, value) {
    let asset_leaflet_obj = find_layer_by_id(active_layer_id, 'esdl_layer', asset_id);
    console.log(asset_leaflet_obj);

    if (attribute_name == 'name') {
        asset_leaflet_obj.name = value;
    }

    let tt_format = get_tooltip_format();
    let attrs = asset_leaflet_obj.attrs;
    for (const [k, v] of Object.entries(attrs)) {
        console.log(`${k}: ${v}`);
        if (k == attribute_name) attrs[k] = value;
    }

    if (asset_leaflet_obj instanceof L.Marker) {
        asset_leaflet_obj.setTooltipContent(get_tooltip_text(tt_format['marker'], asset_leaflet_obj.name, attrs));
    } else if (asset_leaflet_obj instanceof L.Polyline) {
        asset_leaflet_obj.setText(get_tooltip_text(tt_format['line'], asset_leaflet_obj.name, attrs)+'                   ',
            {repeat: true});
    }
}

// ------------------------------------------------------------------------------------------------------------
//  Updates asset state
// ------------------------------------------------------------------------------------------------------------
function update_asset_state(asset_id, new_state) {
    let asset_leaflet_obj = find_layer_by_id(active_layer_id, 'esdl_layer', asset_id);
    // if it's a joint, don't change appearance
    if (asset_leaflet_obj.type == 'Joint') return;

    let cll = asset_leaflet_obj.getElement().classList;

    // because old state is unknown, remove everything
    cll.remove('Optional');
    cll.remove(asset_leaflet_obj.capability);
    cll.remove(asset_leaflet_obj.capability + 'Disabled');

    // remove the disabled if applicable
    let html = asset_leaflet_obj.getIcon().options.html;
    html = html.replace('circle-img-disabled', 'circle-img');

    // add styling based on new state
    if (new_state == 'ENABLED') cll.add(asset_leaflet_obj.capability);
    if (new_state == 'OPTIONAL') {
        cll.add(asset_leaflet_obj.capability);
        cll.add('Optional');
    }
    if (new_state == 'DISABLED') {
        cll.add(asset_leaflet_obj.capability + 'Disabled');
        html = html.replace('circle-img', 'circle-img-disabled');
    }

    // assign DivIcon html again
    asset_leaflet_obj.getIcon().options.html = html;
}


$(document).ready(function() {
    window.PubSubManager.subscribe('ASSET_PROPERTIES', (name, message) => {
        // window.PubSubManager.broadcast('ASSET_PROPERTIES', { id: currentObjectID.value, name: name, value: new_value });
        update_asset_tooltip(message.id, message.name, message.value);
        if (message.name === 'state') {
            update_asset_state(message.id, message.value);
        }
    });
});