if (!window.app) {
    window.app = {};
}
var app = window.app;

app.featureInfoControl = function (opt_options) {
    var options = opt_options || {};

    this.generateID = function () {

        var s4 = function() {
            return Math.floor((1 + Math.random()) * 0x10000)
                       .toString(16)
                       .substring(1);
        }

        return s4() + s4() + s4() + s4() + s4() + s4() + s4() + s4();
    }

    /* Info Formats */
    //'application/vnd.ogc.gml/3.1.1';
    //'text/html';
    //'application/json';
    //'application/vnd.ogc.gml';
    options['infoFormat'] = options['infoFormat'] || 'application/json';

    var buttonFeatureInfo = document.createElement('button');
    buttonFeatureInfo.innerHTML = '<i class="fa fa-info-circle title="Informação"><i>';
    buttonFeatureInfo.title = "Informação";

    var this_ = this;

    this_.containment = options.containment || null;

    this_.rootLayer = options.rootLayer || null;
    this_.queryLayers = options.queryLayers || null;
    this_.layer = options.layer || null;
    this_.features = [];

    this_.config = options.config || null;

    this.showLoading = options.showLoading || null;
    this.hideLoading = options.hideLoading ||null;

    this.showDirectory = options.showDirectory || null;
    this.executeAction = options.executeAction || null;
    this.showEditor = options.showEditor || null;
    this.addWMSLayer = options.addWMSLayer || null;

    this_.panelWindow = null;

    // Hold last CSV data
    var csvData = {};

    this_.panelonclosed = function (evt) {
        if (this_.disableControl) {
            this_.disableControl();
        }

        if (this_.layer) {
            this_.layer.getSource().clear();
        }
        if (this_.features) {
            this_.features = [];
        }

        this_.panelWindow = null;
        $(this).remove();
    };

    var _encodeUrl = function (url) {
        var urlParts = url.split("?");

        var newUrl = encodeURIComponent(urlParts[0] + "?" + urlParts[1]);

        return newUrl;
    };

    function removeFeatureInfoInteraction() {
        $(this_.get('button')).removeClass('active');
        this_.set('active', false);
    }

    function addFeatureInfoInteraction() {
        if (!this_.panelWindow) {
            var html = '<div class="msg">';
            html += '<p>Clique no mapa para obter informação sobre os elementos</p>';
            html += '</div>';

            var panelpos = function panelpos() {
                return {
                    my: 'right-top',
                    at: 'right-top',
                    offsetY: $('#map-navbar-container').position().top + $('#map-navbar-container').outerHeight() + 8,
                    offsetX: -55
                };
            }

            var getPanelWidth = function (config) {
                var width = 275;
                if (config && config.width) {
                    if (config.width.endsWith('%')) {
                        width = function() {return ($(window).width() * parseInt(config.width)) / 100};
                    } else {
                        width = config.width;
                    }
                }
                return width;
            }

            var getPanelHeight = function (config) {
                var height = 275;
                if (config && config.height) {
                    if (config.height.endsWith('%')) {
                        height = function() {return ($(window).height() * parseInt(config.height)) / 100};
                    } else {
                        height = config.height;
                    }
                }
                return height;
            }

            this_.panelWindow = $.jsPanel({
                id: 'feature-info-panel',
                headerTitle: 'Informação',
                panelSize: {
                    width:  getPanelWidth(this_.config),
                    height: getPanelHeight(this_.config)
                },
                position: panelpos,
                dragit: {
                    containment: 'window',
                },
                contentOverflow: { horizontal: 'hidden', vertical: 'auto' },
                headerControls: {
                    controls:  'closeonly'
                },
                content: '<div class="msg"><p>Clique no mapa para obter informação sobre os elementos</p></div>',
                onclosed: this_.panelonclosed,
                onwindowresize: function(event, panel) {
                    panel.reposition(panelpos());
                }
            });

            this_.panelWindow.on( "click", ".layer-title", function() {
                if ($('span.icon', this).hasClass('expanded-icon')) {
                    $('span.icon', this).removeClass('expanded-icon').addClass('expand-icon');
                    $(this).next('div').hide('fast');
                } else {
                    $('span.icon', this).removeClass('expand-icon').addClass('expanded-icon');
                    $(this).next('div').show('fast');
                }
            });
        } else {
            this_.panelWindow.normalize();
        }
    }

    var handleMapClick = function (evt) {

        var map = this_.getMap();

        var ints = map.getInteractions().getArray();
        var drawing = false;
        csvData = {};

        for (var i = 0; i < ints.length; i++) {
            if (map.getInteractions().getArray()[i] instanceof ol.interaction.Draw) {
                drawing = true;
                break;
            }
        }

        if (!drawing) {
            var coordinate = evt.coordinate;
            var layers = [];
            var wmsSource;

            if (this_.layer) {
                this_.layer.getSource().clear();
            }
            if (this_.features) {
                this_.features = [];
            }

            if (this_.rootLayer) {
                layers = this_.rootLayer.getLayers().getArray();
            } else {
                layers = map.getLayers().getArray();
            }

            var query_layers = [];

            var getLayer = function (layer) {
                if (layer.get('visible')) {
                    if (layer instanceof ol.layer.Group) {
                        var ls = layer.getLayers();
                        ls.forEach(function(lll) {
                            getLayer(lll);
                        });
                    } else if (layer.getSource) {
                        var source = layer.getSource();

                        if ((source instanceof ol.source.TileWMS || source instanceof ol.source.ImageWMS) && layer.get('queryable')) {
                            query_layers.push(layer);
                        }
                    }
                }
            }

            layers.forEach(function (ll) {
                getLayer(ll);
            });

            if (this_.queryLayers && this_.queryLayers.length > 0) {
                for (var qi = 0; qi < this_.queryLayers.length; qi++) {
                    var qlayer = this_.queryLayers[qi];
                    var source = qlayer.getSource();

                    if ((source instanceof ol.source.TileWMS || source instanceof ol.source.ImageWMS)) {
                        query_layers.push(qlayer);
                    }
                }
            }

            if (query_layers && query_layers.length >0) {
                this_.panelWindow.content.empty();
                if (this_.showLoading) { this_.showLoading('#' + this_.panelWindow.attr('id') + ' .jsPanel-content'); }
            } else {
                var html = '<div class="msg msg-alert">';
                html += '<p>Não existem temas a inquirir</p>';
                html += '</div>';

                this_.panelWindow.content.empty().append(html);

                return false;
            }

            var def = $.Deferred();
            var deferreds = [];

            for (var i = query_layers.length - 1; i >= 0; i--) {
                var l = query_layers[i];
                var s = l.getSource();

                var infoFormat = l.get('infoFormat');
                if (!infoFormat && l.get('capability') && l.get('capability').infoFormats) {
                    for (var j=0; j<l.get('capability').infoFormats.length;j++) {
                        if (l.get('capability').infoFormats[j].toLowerCase().indexOf('json') > 0) {
                            infoFormat = l.get('capability').infoFormats[j];
                            break;
                        }
                    }
                    if (!infoFormat) {
                        for (var j=0; j<l.get('capability').infoFormats.length;j++) {
                            if (l.get('capability').infoFormats[j].toLowerCase().indexOf('gml') > 0) {
                                infoFormat = l.get('capability').infoFormats[j];
                                break;
                            }
                        }
                    }
                    if (!infoFormat) {
                        for (var j=0; j<l.get('capability').infoFormats.length;j++) {
                            if (l.get('capability').infoFormats[j].toLowerCase().indexOf('html') > 0) {
                                infoFormat = l.get('capability').infoFormats[j];
                                break;
                            }
                        }
                    }
                    if (!infoFormat) {
                        for (var j=0; j<l.get('capability').infoFormats.length;j++) {
                            if (l.get('capability').infoFormats[j].toLowerCase().indexOf('plain') > 0) {
                                infoFormat = l.get('capability').infoFormats[j];
                                break;
                            }
                        }
                    }
                }
                if (!infoFormat) {
                    infoFormat = options.infoFormat;
                }
                l.set('infoFormat', infoFormat);

                var featureCount = l.get('featureCount') || options.featureCount || 10;

                var url = s.getGetFeatureInfoUrl(
                        evt.coordinate, map.getView().getResolution(), map.getView().getProjection(),
                        { 'INFO_FORMAT': infoFormat, 'FEATURE_COUNT': featureCount });

                var ajax = null;
                var opts = {
                    url: options.proxy + '?url=' + _encodeUrl(url),
                    method: 'get',
                    parametersData: { 'layer': l, 'format': infoFormat }
                };

                if (infoFormat == 'application/json' || infoFormat == 'application/geojson') {
                    opts['dataType'] = 'json';
                }

                ajax = $.ajax(opts).then(function(res){
                    return { result: res, request: this};
                }).fail(function(res){
                    return { result: res};
                });

                if (ajax) {
                    // Push promise to 'deferreds' array
                    deferreds.push(ajax);
                }
            };

            // get a hook on when all of the promises resolve, some fulfill
            // this is reusable, you can use this whenever you need to hook on some promises
            // fulfilling but all resolving.
            function execute_requests(promises){
                var d = $.Deferred(), results = [];
                var remaining = promises.length;
                for(var i = 0; i < promises.length; i++){
                    promises[i].then(function(res){
                        results.push({ status: 'success', result: res.result, request: res.request, format: res.request.parametersData.format }); // on success, add to results
                    }).fail(function(res) {
                        results.push({ status: 'error', result: res, request: this, format: this.parametersData.format }); // on fail, add to results
                    }).always(function(res){
                        remaining--; // always mark as finished
                        if(!remaining) d.resolve(results);
                    });
                }
                return d.promise(); // return a promise on the remaining values
            }

            var getFeaturesResultsJSON = function (layer, data) {
                var json_features = data.features;

                if (!json_features || json_features.length == 0) {
                    return [];
                }

                var source = new ol.source.Vector({
                    features: (new ol.format.GeoJSON()).readFeatures(data)
                });
                var fts = source.getFeatures();

                if (data.crs && data.crs.properties && ol.proj.get(data.crs.properties.name)) {
                    var proj = ol.proj.get(data.crs.properties.name);
                    var transform = ol.proj.getTransform(proj, this_.getMap().getView().getProjection());

                    for (var i=0; i < fts.length; i++) {
                        var f = fts[i];
                        f.getGeometry().applyTransform(transform);
                    }
                } else if (data.crs && data.crs.properties) {
                    var crs = data.crs.properties.name.split(':');
                    var code = crs[crs.length-1];

                    for (var i=0; i < fts.length; i++) {
                        var f = fts[i];
                        f.set('proj_code', code);
                    }
                }

                return fts;
            };

            var getFeaturesResultsGML = function (layer, data) {
                var parser = new ol.format.WMSGetFeatureInfo();
                var gml_features = parser.readFeatures(data);

                if (!gml_features || gml_features.length == 0) {
                    return [];
                }

                if (ol.proj.get(layer.get('projection'))) {
                    var proj = ol.proj.get(layer.get('projection'));
                    var transform = ol.proj.getTransform(proj, this_.getMap().getView().getProjection());

                    for (var i=0; i < gml_features.length; i++) {
                        var f = gml_features[i];
                        f.getGeometry().applyTransform(transform);
                    }

                    return gml_features;

                } else if (layer.get('projection')) {
                    var crs = layer.get('projection').split(':');
                    var code = crs[crs.length-1];

                    for (var i=0; i < gml_features.length; i++) {
                        var f = gml_features[i];
                        f.set('proj_code', code);
                    }

                    return gml_features;
                } else {
                    return gml_features;
                }
            }

            var outputLayerResults = function (layer, data, format) {
                var features = [];
                var template = null;

                var hasContent = false;

                if (layer) {
                    template = layer.get('template');
                }

                // Collect layer data
                var layerProps = layer.getProperties();
                var layerTitle = layer.get('title') || 'Sem título';
                if (typeof csvData[layerProps['layer-id']] === 'undefined') csvData[layerProps['layer-id']] = { title: layerTitle, results: []};

                var html = '<div class="layer-title"><span class="icon expanded-icon" /><span>' + layerTitle + '</span></div>';
                html += '<div>';

                if (format == 'text/html' || format == 'text/plain') {
                    html += data; //'<a href="#">Ver dados</a>';
                    hasContent = true;
                } else if (format == 'application/json') {
                    features = getFeaturesResultsJSON(layer, data);
                } else if (format == 'application/geojson') {
                    features = getFeaturesResultsJSON(layer, data)
                } else if (format == 'application/vnd.ogc.gml' || infoFormat == 'application/vnd.ogc.gml/3.1.1') {
                    features =  getFeaturesResultsGML(layer, data, format);
                }

                if (features && features.length > 0) {
                    for (var h = 0; h < features.length; h++) {
                        var feature = features[h];
                        var values = feature.properties || feature.getProperties();

                        feature.set('feature_id', this_.generateID());

                        var tbl = '<table class="table table-striped table-bordered table-condensed">';

                        var geom_key = null;

                        for (var key in values) {
                            var val = values[key];
                            if (val instanceof ol.geom.Geometry) {
                                geom_key = key;
                                break;
                            }
                        }

                        if (geom_key) {
                            if (feature.get('proj_code') && feature.get('proj_code').length > 0) {
                                tbl += '<tr><td colspan="2"><a href="#" data-feature-id="' + feature.get('feature_id') + '" title="Sistema de coordenadas não suportado"><i class="fa fa-exclamation-circle" aria-hidden="true"></i> </td></tr>';
                            } else {
                                tbl += '<tr><td colspan="2"><a href="#" class="zoom-feature" data-feature-id="' + feature.get('feature_id') + '"><i class="fa fa-search-plus" aria-hidden="true"></i> Ver</td></tr>';
                            }
                        }

                        if (template && template.fields && template.fields.length > 0) {
                            var fields = template.fields;

                            for (var j=0; j<fields.length; j++) {
                                var value = fields[j].value;

                                if (fields[j].field != null && fields[j].field in values) {
                                    value = values[fields[j].field];
                                }

                                var content = value;

                                if (fields[j].type == 'hyperlink') {
                                    var url = null;
                                    var val = value;
                                    if (fields[j].field != null) {
                                        url = String.format(fields[j].url, value);
                                        if (fields[j].field instanceof Array) {
                                            url = fields[j].url;
                                            for (var x=0; x<fields[j].field.length; x++ ){
                                                if (fields[j].field[x] in values) {
                                                    url = url.replace('{' + x + '}', values[fields[j].field[x]]);
                                                }
                                            }
                                        }
                                    } else {
                                        url = fields[j].url;
                                    }
                                    if (fields[j].value != null) {
                                        val = fields[j].value;
                                        if (fields[j].field instanceof Array) {
                                            for (var x=0; x<fields[j].field.length; x++ ){
                                                if (fields[j].field[x] in values) {
                                                    val = val.replace('{' + x + '}', values[fields[j].field[x]]);
                                                }
                                            }
                                        }
                                    }
                                    content = '<a href="' + url + '" target="_blank">' + val + '</a>';
                                } else if (fields[j].type == 'html') {
                                    if (fields[j].field != null) {
                                        if (fields[j].field instanceof Array) {
                                            content = fields[j].value;
                                            for (var x=0; x<fields[j].field.length; x++ ){
                                                if (fields[j].field[x] in values) {
                                                    content = content.replace('{' + x + '}', values[fields[j].field[x]]);
                                                }
                                            }
                                        } else {
                                            content = String.format(fields[j].value, value);
                                        }
                                    } else {
                                        content = fields[j].value;
                                    }
                                } else if (fields[j].type == 'directory') {
                                    //TODO
                                    var url = null;
                                    var val = value;
                                    var window_title = null;
                                    var recursive = true;
                                    if (fields[j].field != null) {
                                        url = String.format(fields[j].url, value);
                                        if (fields[j].field instanceof Array) {
                                            url = fields[j].url;
                                            for (var x=0; x<fields[j].field.length; x++ ){
                                                if (fields[j].field[x] in values) {
                                                    url = url.replace('{' + x + '}', values[fields[j].field[x]]);
                                                }
                                            }
                                        }
                                    } else {
                                        url = fields[j].url;
                                    }
                                    if (fields[j].value != null) {
                                        val = fields[j].value;
                                        if (fields[j].field instanceof Array) {
                                            for (var x=0; x<fields[j].field.length; x++ ){
                                                if (fields[j].field[x] in values) {
                                                    val = val.replace('{' + x + '}', values[fields[j].field[x]]);
                                                }
                                            }
                                        }
                                    }
                                    if (fields[j].window && fields[j].window.title) {
                                        window_title = fields[j].window.title;
                                        if (fields[j].field instanceof Array) {
                                            for (var x=0; x<fields[j].field.length; x++ ){
                                                if (fields[j].field[x] in values) {
                                                    window_title = window_title.replace('{' + x + '}', values[fields[j].field[x]]);
                                                }
                                            }
                                        }
                                    }

                                    if (fields[j].recursive != undefined) {
                                        recursive = fields[j].recursive;
                                    }

                                    content = '<a href="#" class="feature-info-link-dir" data-action="' + url + '" data-title="' + window_title + '" data-filter="' + fields[j].filter  + '" data-recursive=' + recursive + '>' + val + '</a>';
                                } else if (fields[j].type == 'wms_layer') {
                                    var url = null;
                                    var val = value;
                                    var layer = '';
                                    var layer_title = '';
                                    var target_layer = fields[j].target;
                                    if (fields[j].field != null) {
                                        url = String.format(fields[j].url, value);
                                        if (fields[j].field instanceof Array) {
                                            url = fields[j].url;
                                            for (var x=0; x<fields[j].field.length; x++ ){
                                                if (fields[j].field[x] in values) {
                                                    url = url.replace('{' + x + '}', values[fields[j].field[x]]);
                                                }
                                            }
                                        }
                                    } else {
                                        url = fields[j].url;
                                    }
                                    if (fields[j].value != null) {
                                        val = fields[j].value;
                                        if (fields[j].field instanceof Array) {
                                            for (var x=0; x<fields[j].field.length; x++ ){
                                                if (fields[j].field[x] in values) {
                                                    val = val.replace('{' + x + '}', values[fields[j].field[x]]);
                                                }
                                            }
                                        }
                                    }
                                    if (fields[j].value != null) {
                                        layer = fields[j].parameters.layer;
                                        if (fields[j].field instanceof Array) {
                                            for (var x=0; x<fields[j].field.length; x++ ){
                                                if (fields[j].field[x] in values) {
                                                    layer = layer.replace('{' + x + '}', values[fields[j].field[x]]);
                                                }
                                            }
                                        }
                                    }
                                    if (fields[j].value != null) {
                                        layer_title = fields[j].parameters.title;
                                        if (fields[j].field instanceof Array) {
                                            for (var x=0; x<fields[j].field.length; x++ ){
                                                if (fields[j].field[x] in values) {
                                                    layer_title = layer_title.replace('{' + x + '}', values[fields[j].field[x]]);
                                                }
                                            }
                                        }
                                    }

                                    content = '<a href="#" class="feature-info-wms-layer" data-url="' + url + '" data-layer-name="' + layer + '" data-layer-title="' + layer_title + (target_layer ? '" data-target-layer="' + target_layer : '') + '">' + val + '</a>';
                                } else if (fields[j].type == 'action') {
                                    //TODO
                                    var action = null;
                                    var val = value;
                                    if (fields[j].field != null) {
                                        action = String.format(fields[j].action, value);
                                        if (fields[j].field instanceof Array) {
                                            action = fields[j].action;
                                            for (var x=0; x<fields[j].field.length; x++ ){
                                                if (fields[j].field[x] in values) {
                                                    action = action.replace('{' + x + '}', values[fields[j].field[x]]);
                                                }
                                            }
                                        }
                                    } else {
                                        action = fields[j].action;
                                    }
                                    if (fields[j].value != null) {
                                        val = fields[j].value;
                                        if (fields[j].field instanceof Array) {
                                            for (var x=0; x<fields[j].field.length; x++ ){
                                                if (fields[j].field[x] in values) {
                                                    val = val.replace('{' + x + '}', values[fields[j].field[x]]);
                                                }
                                            }
                                        }
                                    }

                                    content = '<a href="#" class="feature-info-link-action" data-layer-title="' + layer.get('title') + '" data-action="' + action +  '">' + val + '</a>';
                                } else if (fields[j].type == 'editor') {
                                    //TODO
                                    var url = null;
                                    var val = value;
                                    if (fields[j].field != null) {
                                        url = String.format(fields[j].url, value);
                                        if (fields[j].field instanceof Array) {
                                            url = fields[j].url;
                                            for (var x=0; x<fields[j].field.length; x++ ){
                                                if (fields[j].field[x] in values) {
                                                    url = url.replace('{' + x + '}', values[fields[j].field[x]]);
                                                }
                                            }
                                        }
                                    } else {
                                        url = fields[j].url;
                                    }
                                    if (fields[j].value != null) {
                                        val = fields[j].value;
                                        if (fields[j].field instanceof Array) {
                                            for (var x=0; x<fields[j].field.length; x++ ){
                                                if (fields[j].field[x] in values) {
                                                    val = val.replace('{' + x + '}', values[fields[j].field[x]]);
                                                }
                                            }
                                        }
                                    }

                                    content = '<a href="#" class="feature-info-link-editor" data-layer-title="' + layer.get('title') + '" data-action="' + url +  '">' + val + '</a>';
                                }

                                hasContent = true;

                                if (content === 0) {
                                    content = String(content);
                                }

                                tbl += '<tr><td>' + fields[j].title + '</td><td>' + (content || '') + '</td></tr>';

                                // Add to CSV data
                                csvData[layerProps['layer-id']].results.push([fields[j].title, (content || '')]);
                            }
                        } else {
                            for (var key in values) {
                                var value = values[key];
                                if (!(value instanceof ol.geom.Geometry)) {
                                    tbl += '<tr><td>' + key + '</td><td>' + (value || '') + '</td></tr>';

                                    // Add to CSV data
                                    csvData[layerProps['layer-id']].results.push([key, (value || '')]);
                                }
                                hasContent = true;
                            }
                        }

                        tbl += '</table>';

                        if (hasContent === true) {
                            html += tbl;
                        }

                        /*
                        if (this_.layer) {
                            this_.layer.getSource().addFeature(feature);
                        }
                        */
                    }
                }
                if (!hasContent) {
                    html += '<div>SEM DADOS</div>';
                }
                html += '</div>';

                if (features && features.length > 0) {
                    this_.features = features.concat([].concat(this_.features));
                }

                /*
                var vectorSource = new ol.source.Vector({
                    features: (new ol.format.GeoJSON()).readFeatures(data)
                });

                var ps = new ol.style.Style({
                  image: new ol.style.Circle({
                        radius: 5,
                        fill: null,
                        stroke: new ol.style.Stroke({color: 'red', width: 1})
                      })
                });

                var vectorLayer = new ol.layer.Vector({
                    source: vectorSource,
                    style: ps
                });
                map.addLayer(vectorLayer);
                */


                return html;
            };

            var outputLayerError = function (layer, data) {
                var html = '<div class="layer-title"><span class="icon expanded-icon" /><span>' + (layer.get('title') || 'Sem título') + '</span></div>';
                html += '<div>Erro ao inquirir serviço</div>';

                return html;
            };

            execute_requests(deferreds).then(function(results){
                var html = '';

                for(var i = 0; i < results.length; i++) {
                    var r = results[i];
                    var layer = r.request.parametersData.layer;

                    if (r.status == 'success') {
                        html += outputLayerResults(layer, r.result, r.format);
                    } else if (r.status == 'error') {
                        html += outputLayerError(layer, r.result);
                    }
                }

                // Add export CSV link
                html = '<a class="btn btn-primary btn-xs feature-info-export">Exportar Resultados</a><br />' + html;

                this_.panelWindow.content.empty().append(html);

                var context = this_;

                // Add export event
                $('.jsPanel-content .feature-info-export', this_.panelWindow).click(function (e) {
                    const rows = [];

                    var csvContent = "data:text/csv;charset=utf-8,";
                    for (var group in csvData) {
                        for (var i = 0; i < csvData[group].results.length; i++) {
                            var label = '' + csvData[group].results[i][0];
                            var value = '' + csvData[group].results[i][1];
                            rows.push([csvData[group].title, label, $.trim(value.replace(/\,/g, ''))]);
                        }
                    }
                    for (var i = 0; i < rows.length; i++) {
                        var row = rows[i].join(",");
                        csvContent += row + "\r\n";
                    }

                    // Create download file
                    var encodedUri = encodeURI(csvContent);
                    var link = document.createElement("a");
                    link.setAttribute("href", encodedUri);
                    link.setAttribute("download", "my_data.csv");
                    document.body.appendChild(link);
                    link.click();
                    document.body.removeChild(link);
                });

                $('.jsPanel-content a[data-feature-id]', this_.panelWindow).click(function (e) {
                    if (context.layer) {
                        var fid = $(this).data('feature-id');

                        context.layer.getSource().clear();

                        for (var i=0; i < context.features.length; i++) {
                            var f = context.features[i];
                            if (f.get('feature_id') == fid) {
                                if (f.get('proj_code') && f.get('proj_code').length > 0) {
                                    //TODO: GET PROJECTION DEFINITION AND TRANSFORM GEOMETRY
                                } else {
                                    context.layer.getSource().addFeature(f);

                                    var extent = f.getGeometry().getExtent();
                                    context.map_.getView().fit(
                                          f.getGeometry(),
                                          context.map_.getSize(),
                                          {
                                            minResolution: 0.2
                                          }
                                    );
                                }
                                break;
                            }
                        }
                    }
                    return false;
                });

                if (this_.hideLoading) { this_.hideLoading('#' + this_.panelWindow.attr('id') + ' .jsPanel-content'); }
            });

        }

    }

    var handleFeatureInfo = function (e) {
        var controls = this_.getMap().getControls().getArray();
        for (var i = 0; i < controls.length; i++) {
            if (this_ != controls[i] && controls[i].disableControl) {
                controls[i].disableControl();
            }
        }

        var active = this_.get('active');

        if (active) {
            this_.disableControl();
        } else {
            for (var i = 0; i < controls.length; i++) {
                if (this_ != controls[i] && controls[i].deactivateControl) {
                    controls[i].deactivateControl();
                }
            }

            active = true;
            map.on('singleclick', handleMapClick);
            $(this).addClass('active');
            this_.set('active', active);

            addFeatureInfoInteraction();
        }       
    }

    buttonFeatureInfo.addEventListener('click', handleFeatureInfo, false);
    buttonFeatureInfo.addEventListener('touchstart', handleFeatureInfo, false);

    var element = document.createElement('div');
    element.className = (options.className ? options.className + ' ' : '') + 'feature-info-control ol-selectable ol-control';
    element.appendChild(buttonFeatureInfo);

    $(document).on('click', '.feature-info-link-dir', function (e) {
        e.preventDefault();

        if (this_.showDirectory) {
            var args = [this];
            this_.showDirectory.apply(this_, args);

        }
    });

    $(document).on('click', '.feature-info-link-action', function (e) {
        e.preventDefault();

        if (this_.showEditor) {
            var args = [$(this).data('action')];
            this_.executeAction.apply(this_, args);
        }
    });

    $(document).on('click', '.feature-info-link-editor', function (e) {
        e.preventDefault();

        if (this_.executeAction) {
            var args = [this];
            this_.showEditor.apply(this_, args);
        }
    });

    $(document).on('click', '.feature-info-wms-layer', function (e) {
        e.preventDefault();

        if (this_.addWMSLayer) {
            var args = [this];
            this_.addWMSLayer.apply(this_, args);

        }
    });

    ol.control.Control.call(this, {
        element: element,
        target: options.target
    });

    this.set('options', options);
    this.set('button', buttonFeatureInfo);
    this.set('handleMapClick', handleMapClick);
    this.set('removeFeatureInfoInteraction', removeFeatureInfoInteraction);
    this.set('active', false);
};
ol.inherits(app.featureInfoControl, ol.control.Control);

/**
 * Remove the control from its current map and attach it to the new map.
 * Here we create the markup for our layer switcher component.
 * @param {ol.Map} map Map.
 */
app.featureInfoControl.prototype.setMap = function (map) {
    ol.control.Control.prototype.setMap.call(this, map);

    /*
    var layer = null;
    var layers = map.getLayers().getArray();
    for (var i = 0; i < layers.length; i++) {
        if (layers[i].get('name') == 'viewer-feature-info-layer') {
            layer = layers[i];
            break;
        }
    }
    */

    if (!this.layer) {
        var layer = new ol.layer.Vector({
            source: new ol.source.Vector(),
            style: new ol.style.Style({
                fill: new ol.style.Fill({
                    color: 'rgba(255, 255, 255, 0.2)'
                }),
                stroke: new ol.style.Stroke({
                    color: '#ffcc33',
                    width: 2
                }),
                image: new ol.style.Circle({
                    radius: 7,
                    fill: new ol.style.Fill({
                        color: '#ffcc33'
                    })
                })
            }),
            name: 'viewer-feature-info-layer',
            group: 'vector'
        });

        map.addLayer(layer);
        this.layer = layer;
    }
}

app.featureInfoControl.prototype.disableControl = function (e) {
    var controls = this.getMap().getControls().getArray();
    for (var i = 0; i < controls.length; i++) {
        if (this != controls[i] && controls[i].activateControl) {
            controls[i].activateControl();
        }
    }

    $(this.get('button')).removeClass('active');

    this.getMap().un('singleclick', this.get('handleMapClick'));

    var fn = this.get('removeFeatureInfoInteraction');
    fn();

    this.set('active', false);

    if (this.get('options').onDisableControl) {
        this.get('options').onDisableControl(e);
    }
}