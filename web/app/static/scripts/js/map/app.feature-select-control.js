if (!window.app) {
    window.app = {};
}
var app = window.app;

app.featureSelectControl = function (opt_options) {
    var options = opt_options || {};

    this.generateID = function () {

        var s4 = function() {
            return Math.floor((1 + Math.random()) * 0x10000)
                       .toString(16)
                       .substring(1);
        }

        return s4() + s4() + s4() + s4() + s4() + s4() + s4() + s4();
    }

     // Function to get layer by Id form map layers collection
    this.getLayer = function (layer, layer_id) {
        var lr = layer;
        var layer_id = layer_id;

        var selected_layer = null;

        if (lr.get("layer-id") == layer_id) {
            selected_layer = lr;
        } else {
            if (lr instanceof ol.layer.Group) {
                var ls = lr.getLayers().getArray();

                for (var i=0; i<ls.length; i++) {
                    var lll = ls[i];
                    if (lll.get("layer-id") == layer_id) {
                        selected_layer = lll;
                    } else {
                        selected_layer = this_.getLayer(lll, layer_id, lr);
                    }
                    if (selected_layer) {
                        break;
                    }
                }
            }
        }

        return selected_layer;
    }

    var this_ = this;

    this_.containment = options.containment || null;

    this_.panelWindow = null;

    this_.panelonclosed = function (evt) {
        if (this_.disableControl) {
            this_.disableControl();
        }
        if (this_.get('select-control')) {
            this_.get('select-control').getFeatures().forEach(function (f, index, v){
                f.setStyle(null);
            });
            this_.get('select-control').getFeatures().clear();
        }

        this_.panelWindow = null;
        $(this).remove();
    };

    this_.rootLayer = options.rootLayer || null;

    function removeFeatureSelectInteraction() {
        this_.set('active', false);
    }

    function addFeatureSelectInteraction(type) {
    }

    function featureSelectInteraction(feature) {
    };

    var handleFeatureSelectMain = function (e) {
    }

    var handleFeatureSelect = function (e) {

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
            active = true;

            this_.set('active', active);

            addFeatureInfoInteraction();
        }

    }

    var element = document.createElement('div');
    ol.control.Control.call(this, {
        element: element,
        target: options.target
    });


    //var buttonsFeatureSelect = [buttonFeatureSelectPoint, buttonFeatureSelectLine, buttonFeatureSelectPolygon];
    var buttonsFeatureSelect = [];

    var filterLayers = function (feature, layer) {
        if (layer) {
            if (layer.get('selectable')) {
                feature.set('layer-id', layer.get('layer-id'));
                return true;
            } else {
                return false;
            }
        } else {
            return false;
        }
    };
    var filterLayersHover = function (feature, layer) {
        if (layer) {
            if ((layer.get('selectable') && layer.get('highlight') == null) || layer.get('highlight') == true) {
                return true;
            } else {
                return false;
            }
        } else {
            return false;
        }
    };

    var styles = null;
    if (options.styles && options.styles.selection) {
        styles = options.styles.selection;
    }

    var hoverSelectControl = new ol.interaction.Select({
        condition: ol.events.condition.pointerMove,
        filter: filterLayersHover,
        multi: false,
        style: styles
    });
    map.addInteraction(hoverSelectControl);

    var selectControl = new ol.interaction.Select({
        condition: ol.events.condition.click,
        filter: filterLayers,
        multi: options.multi,
        style: styles
    });
    map.addInteraction(selectControl);
    selectControl.on('select', function(e) {
        if (this_.get('hover-select-control') && this_.get('hover-select-control').getFeatures()) {
            this_.get('hover-select-control').getFeatures().clear();
        }

        for (var i=0; i < e.deselected.length; i++) {
            var f = e.deselected[i];
            f.setStyle(null);
        }

        var buildPanelWindow = function (html) {
            function panelpos() {
                return {
                    my: 'right-top',
                    at: 'right-top',
                    offsetY: $('#map-navbar-container').position().top + $('#map-navbar-container').outerHeight() + 8,
                    offsetX: -55
                };
            }

            this_.panelWindow = $.jsPanel({
                id: 'feature-select-panel',
                headerTitle: 'Informação',
                panelSize: {
                    width:  function() {return $(window).width()/5},
                    height: 275
                },
                position: panelpos,
                dragit: {
                    containment: 'window',
                },
                contentOverflow: { horizontal: 'hidden', vertical: 'auto' },
                headerControls: {
                    controls:  'closeonly'
                },
                content: html,
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
        }

        if (e.target.getFeatures() && e.target.getFeatures().getLength() == 0) {
            var html = '<div class="msg msg-alert">';
            html += '<p>Não foram seleccionados elementos</p>';
            html += '</div>';

            if (!this_.panelWindow) {
                buildPanelWindow(html);
            } else {
                this_.panelWindow.content.empty().append(html);
                this_.panelWindow.normalize();
            }

            return;
        }

        var html = '';
        var features = e.target.getFeatures().getArray();

        for (var i=0; i < features.length; i++) {
            var feature = features[i];
            feature.set('feature_id', this_.generateID());

            var layer = null;
            this_.getMap().getLayers().forEach(function (l) {
                var ll = this_.getLayer(l, feature.get('layer-id'));

                if (ll) {
                    layer = ll;
                    return;
                }
            });

            var values = feature.getProperties();
            var template = null;
            var layer_id = null;

            if (layer) {
                template = layer.get('template');
                layer_id = layer.get('layer-id');
            }

            var tbl = '<table class="table table-striped table-bordered table-condensed">';

            var geom_key = null;

            for (var key in values) {
                var val = values[key];
                if (val instanceof ol.geom.Geometry) {
                    geom_key = key;
                    break;
                }
            }

            if (values.features && values.features instanceof Array) {
                var cluster_features = values.features
                var format = new ol.format.WKT();
                for (var h=0; h < cluster_features.length; h++) {
                    var cluster_feature = cluster_features[h];
                    var cluster_values = cluster_feature.getProperties();

                    if (geom_key) {
                        var geom = cluster_feature.getGeometry();
                        var geom_wkt  = format.writeGeometry(geom);

                        var feature_id = cluster_feature.getId();

                        tbl += '<tr><td colspan="2">';
                        tbl += '<a href="#" class="zoom-feature" data-layer-id="' + layer_id + '" data-feature-id="' + feature_id + '" data-feature-geom="' + geom_wkt + '">';
                        tbl += '<i class="fa fa-search-plus" aria-hidden="true"></i> Ver</td></tr>';
                    }


                    if (template && template.fields && template.fields.length > 0) {
                        var fields = template.fields;

                        for (var j=0; j<fields.length; j++) {
                            var value = fields[j].value;

                            if (fields[j].field != null) {
                                for (var key in cluster_values) {
                                    if (key == fields[j].field) {
                                        value = cluster_values[key];
                                        break;
                                    }
                                }
                            }

                            var content = value;

                            if (fields[j].type == 'hyperlink') {
                                var url = null;
                                var val = value;
                                if (fields[j].field != null) {
                                    url = String.format(fields[j].url, value);
                                } else {
                                    url = fields[j].url;
                                }
                                if (fields[j].value != null) {
                                    val = fields[j].value;
                                }
                                content = '<a href="' + url + '" target="_blank">' + val + '</a>';
                            }

                            hasContent = true;

                            tbl += '<tr><td>' + fields[j].title + '</td><td>' + (content || '') + '</td></tr>';
                        }
                    } else {
                        for (var key in cluster_values) {
                            var value = cluster_values[key];
                            if (!(value instanceof ol.geom.Geometry)) {
                                tbl += '<tr><td>' + key + '</td><td>' + (value || '') + '</td></tr>';
                            }
                            hasContent = true;
                        }
                    }

                }
            } else {
                if (geom_key) {
                    if (feature.get('proj_code') && feature.get('proj_code').length > 0) {
                        tbl += '<tr><td colspan="2"><a href="#" data-feature-select-id="' + feature.get('feature_id') + '" title="Sistema de coordenadas não suportado"><i class="fa fa-exclamation-circle" aria-hidden="true"></i> </td></tr>';
                    } else {
                        tbl += '<tr><td colspan="2"><a href="#" class="zoom-feature" data-feature-select-id="' + feature.get('feature_id') + '"><i class="fa fa-search-plus" aria-hidden="true"></i> Ver</td></tr>';
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
                        }

                        hasContent = true;

                        tbl += '<tr><td>' + fields[j].title + '</td><td>' + (content || '') + '</td></tr>';
                    }
                } else {
                    for (var key in values) {
                        var value = values[key];
                        if (!(value instanceof ol.geom.Geometry)) {
                            tbl += '<tr><td>' + key + '</td><td>' + (value || '') + '</td></tr>';
                        }
                        hasContent = true;
                    }
                }
            }

            tbl += '</table>';

            if (hasContent === true) {
                html += tbl;
            }
        }

        if (!this_.panelWindow) {
            buildPanelWindow(html);
        } else {
            this_.panelWindow.content.empty().append(html);
            this_.panelWindow.normalize();
        }

        $('.jsPanel-content a.zoom-feature', this_.panelWindow).bind("click", { context: this_ },function (e) {
            var feature_id = $(this).data('feature-select-id');
            var context = e.data.context;
            var features = context.get('select-control').getFeatures().getArray();

            var feature = null;
            var feature_geom = null;

            if (feature_id) {
                for (var i=0; i < features.length; i++) {
                    var f = features[i];
                    f.setStyle(null);

                    if (f.get('feature_id') && f.get('feature_id') == feature_id) {
                        feature = f;
                        //break;
                    }
                }
            } else {
                var layer_id = $(this).data('layer-id');
                var feature_id = $(this).data('feature-id');

                var this_ = e.data.context;

                var layer = null;
                this_.getMap().getLayers().forEach(function (l) {
                    var ll = this_.getLayer(l, layer_id);

                    if (ll) {
                        layer = ll;
                        return;
                    }
                });

                if (layer) {
                    feature = layer.getSource().getSource().getFeatureById(feature_id);
                    context.get('select-control').getFeatures().clear();
                    context.get('select-control').getFeatures().push(feature);
                 }
            }

            if (feature && feature.getGeometry()) {
                var geom = feature.getGeometry();
                var style = null;
                if (options.styles.active) {
                    if (options.styles.active instanceof Array) {
                        style = options.styles.active;
                    } else if (options.styles.active[geom.getType()]) {
                        style = options.styles.active[geom.getType()];
                    } else {
                        style = options.styles.active;
                    }
                }
                if (style) {
                    feature.setStyle(style);
                }
                context.getMap().getView().fit(
                      geom,
                      context.getMap().getSize(),
                      {
                        minResolution: 0.2
                      }
                );
            }
        });
    });
    selectControl.setActive(true);

    this.set('select-control', selectControl);
    this.set('hover-select-control', hoverSelectControl)

    this.set('options', options);
    this.set('button', buttonsFeatureSelect);
    this.set('removeFeatureSelectInteraction', removeFeatureSelectInteraction);
    this.set('featureSelectInteraction', featureSelectInteraction);
    this.set('active', true);

};
ol.inherits(app.featureSelectControl, ol.control.Control);

app.featureSelectControl.prototype.disableControl = function (e) {

    for (var i = 0; i < $(this.get('button')).length; i++) {
        $(this.get('button')).removeClass('active');
    }

    var fn = this.get('removeFeatureSelectInteraction');
    fn();

    this.set('active', false);

    if (this.get('options').onDisableControl) {
        this.get('options').onDisableControl(e);
    }
}

app.featureSelectControl.prototype.activateControl = function (e) {
    var ctrl = this.get('select-control');
    ctrl.setActive(true);

    var ctrl = this.get('hover-select-control');
    ctrl.setActive(true);
}

app.featureSelectControl.prototype.deactivateControl = function (e) {
    var ctrl = this.get('select-control');
    ctrl.setActive(false);

    var ctrl = this.get('hover-select-control');
    ctrl.getFeatures().clear();
    ctrl.setActive(false);
}