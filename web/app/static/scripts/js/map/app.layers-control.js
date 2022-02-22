if (!window.app) {
    window.app = {};
}
var app = window.app;

/**
 * @class
 * The LayersControl is a layer switcher that can be configured with groups.
 * A minimal configuration is:
 *
 *     new app.LayersControl()
 *
 * In this case, all layers are shown with checkboxes and in a single list.
 * If you want to group layers in separate lists, you can configure the control
 * with a groups config option, for example:
 *
 *     new app.LayersControl({
 *       groups: {
 *         background: {
 *           title: "Base Layers",
 *           exclusive: true
 *         },
 *         default: {
 *           title: "Overlays"
 *         }
 *       }
 *     })
 *
 * Layers that have their 'group' property set to 'background', will be part of
 * the first list. The list will be titled 'Base Layers'. The title is
 * optional. All other layers will be part of the default list. Configure a
 * group with exclusive true to get a radio group.
 *
 * @constructor
 * @extends {ol.control.Control}
 * @param {Object} opt_options Options.
 */
app.LayersControl = function (opt_options) {
    this.defaultGroup = "default";

    this.generateID = function () {
        return s4() + s4() + s4() + s4() + s4() + s4() + s4() + s4();
    }

    var options = opt_options || {};
    var panel = document.createElement('div');
    panel.className = 'layers-control';

    var panelHeader = document.createElement('div');
    panelHeader.className = 'toc-header';
    var hideAll = $('<a href="#" class="hide-all-layers" />').appendTo(panelHeader);
    hideAll.click([this], function (evt) {
        evt.preventDefault;
        var _this = evt.data[0];
        _this.hideAllLayers();
        return false;
    });
    $('<i class="fa fa-low-vision" aria-hidden="true"></i>').appendTo(hideAll);
    $('<span> Desligar todos os temas</span>').appendTo(hideAll);
    panel.appendChild(panelHeader);

    var panelBody = document.createElement('div');
    panelBody.className = 'toc-container';
    panel.appendChild(panelBody);

    var root = document.createElement('ul');
    root.className = 'toc-group';
    panelBody.appendChild(root);

    this.root = root;
    this.rootLayer = null;

    this.getLayerById = function(layer, layer_id) {
        //console.log(lr.get('title') + ': ' + lr.get("layer-id") + '; ' + layer_id);
        if (layer.get("layer-id") == layer_id) {
            return layer;
        } else if (layer instanceof ol.layer.Group) {
			var ls = layer.getLayers();
			var ll = null;
			ls.forEach(function(lll) {
				if (lll.get("layer-id") == layer_id) {
					ll = lll;
					return ll;
				} else {
				    this_.getLayerById(lll, layer_id);
				}
			});
			return ll;
		}
    }

    this_ = this;

    this_.styleRestrictedScales = options.styleRestrictedScales || false;
    this_.parentLayerVisible = options.parentLayerVisible || false;

    this_.wms = options.wms;

    this_.panelInfoTitle = options.panelInfoTitle || 'Informação de Tema';
    this_.panelInfoWindow = null;
    this_.openPanelInfo = function (layer) {
        var info = layer.get('info');
        var url = info.link;
        var title = info.title || null;
        if (title) {
            title = title.replace('{title}', layer.get('title'));
        }

        return $.jsPanel({
            id: this_.generateID(),
            position:    {my: "center-top", at: "center-top", offsetX: 0, offsetY: 0},
            panelSize: {
                width: 800,
                height: 600
            },
            headerTitle: title || this_.panelInfoTitle || 'Informação de Tema',
            contentOverflow: { horizontal: 'hidden', vertical: 'auto' },
            contentAjax: {
                url: url,
                autoload: true,
                done: function (data, textStatus, jqXHR, panel) {
                    console.log('teste');
                }
            },
            callback:    function () {
                console.log('teste');
            },
            onclosed: this_.panelInfoOnClosed,
            dragit: {
                containment: 'window',
            },
            resizeit: {
                start: function (panel, size) {
                },
                stop: function (panel, size) {
                }
            }
        });
    };
    this_.panelInfoOnClosed = function (evt) {
        this_.panelInfoWindow = null;
        $(this).remove();
    };

    this_.refreshScalesRestriction = function (e) {
        var resolution = this.getResolution();
        var units = this.getProjection().getUnits();
        var dpi = 25.4 / 0.28;
        var mpu = ol.proj.METERS_PER_UNIT[units];
        var scale = resolution * mpu * 39.37 * dpi;

        $('li[data-layer-id]','.layers-control').each(function (index) {
            var layer = $(this).data('layer-ol');
            $(this).removeClass('scale-hidden');
            if (layer) {
                if (layer.getMinResolution() > resolution || layer.getMaxResolution() < resolution) {
                    $(this).addClass('scale-hidden');
                }
                //For wms layers width scale restrictions in Capabilities
                if (layer.get('capability')) {
                    var minScale = layer.get('capability').minScale || Infinity;
                    var maxScale = layer.get('capability').maxScale || 0;
                    if (maxScale > scale || minScale < scale) {
                        $(this).addClass('scale-hidden');
                    }
                }
            }
            if (layer instanceof ol.layer.Group && layer.get('single') && layer.get('single') == true) {
                var childs = layer.getLayersArray();
                var childsMinRes, childsMaxRes;
                for (var i=0; i<childs.length; i++) {
                    var child = childs[i];

                    if (childsMinRes == null || child.getMinResolution() <= childsMinRes) {
                        childsMinRes = child.getMinResolution();
                    }
                    if (childsMaxRes == null || child.getMaxResolution() >= childsMaxRes) {
                        childsMaxRes = child.getMaxResolution();
                    }
                }
                if (childsMinRes > resolution || childsMaxRes < resolution) {
                    $(this).addClass('scale-hidden');
                }
            }
        });
    };

    this_.refreshLayersLegend = function (e) {
        var resolution = this.getResolution();
        var units = this.getProjection().getUnits();
        var dpi = 25.4 / 0.28;
        var mpu = ol.proj.METERS_PER_UNIT[units];
        var scale = resolution * mpu * 39.37 * dpi;

        var setParam = function(uri, key, val) {
            return uri
                .replace(new RegExp("([?&]"+key+"(?=[=&#]|$)[^#&]*|(?=#|$))"), "&"+key+"="+encodeURIComponent(val))
                .replace(/^([^?&]+)&/, "$1?");
        }

        $("div[data-min-scale], div[data-max-scale]", ".layer-legend").each(function( index ) {
            var max = $(this).data("max-scale") || 0;
            var min = $(this).data("min-scale") || 0;

            if (scale >= max && (min == 0 || scale <= min)) {
                $(this).show();
            } else {
                $(this).hide();
            }
        });

        $("img.layer-wms-legend", ".layer-legend").each(function( index ) {
            var img_url = $(this).attr('src');
            var s = $(this).attr('src', setParam(img_url, 'scale', scale));
        });
    };

    this_.setParentLayerVisible = function (layer) {
        if (layer.get('parent-layer')) {
            var l = layer.get('parent-layer');
            l.set('visible', true);

            this_.setParentLayerVisible(l);
        }
    };

    ol.control.Control.call(this, {
        element: panel,
        target: options.target
    });

    function s4() {
        return Math.floor((1 + Math.random()) * 0x10000)
                   .toString(16)
                   .substring(1);
    }

};

ol.inherits(app.LayersControl, ol.control.Control);

/**
 * Remove the control from its current map and attach it to the new map.
 * Here we create the markup for our layer switcher component.
 * @param {ol.Map} map Map.
 */
app.LayersControl.prototype.setMap = function (map) {
    ol.control.Control.prototype.setMap.call(this, map);

    var rootLayer = null;

    var layers = map.getLayers().getArray();
    for (var i = 0, ii = layers.length; i < ii; ++i) {
        var layer = layers[i];
        if (layer.get('group') == 'toc-root-group') {
            rootLayer = layer;
            break;
        }
    }

    if (rootLayer || null) {
        layers = rootLayer.getLayers().getArray();
        for (var i = layers.length - 1, ii = 0; i >= ii; --i) {
            var layer = layers[i];
            if (layer instanceof ol.layer.Group) {
                if (layer.get('single') && layer.get('single') == true) {
                    this.addLayerToList(layer, this.root, 0, rootLayer);
                } else {
                    this.addLayerGroupToList(layer, this.root, 0, rootLayer);
                }
            } else {
                this.addLayerToList(layer, this.root, 0, rootLayer);
            }
        }
    }

    this.rootLayer = rootLayer;

    var lc = this.rootLayer.getLayers();

    lc.on('add', function (evt) {
        var l = evt.element;
        if (l instanceof ol.layer.Group) {
            this.addLayerGroupToList(l, null, 0);
        } else {
            this.addLayerToList(l, null, 0);
        }
        if (this.styleRestrictedScales) {
            this.refreshScalesRestriction.apply(this.map_.getView(), null);
        }
    }, this);

    lc.on('remove', function (evt) {
        var l = evt.element;
        $('li[layer-id="' + l.get('layer-id') + '"]').remove();
    }, this);

    map.getView().on('change:resolution', this_.refreshLayersLegend);

    if (this.styleRestrictedScales) {
        map.getView().on('change:resolution', this_.refreshScalesRestriction);
        this.refreshScalesRestriction.apply(map.getView(), null);
    }
};

app.LayersControl.prototype.addLayerToList = function (layer, element, level, visible, parentGroupLayer) {
    var layer_id = this.generateID();
    layer.set('layer-id', layer_id);

    if (parentGroupLayer) {
        layer.set('parent-layer', parentGroupLayer);
    }

    if (parentGroupLayer && parentGroupLayer.get('exclusive') &&  parentGroupLayer.get('exclusive') == true) {
        layer.set('exclusive', true);
    } else {
        layer.set('exclusive', false);
    }

    layer.on('change:visible', function(e){
        var l = this;
        var visible = this.get('visible');
        var li = $('li[data-layer-id="' + l.get('layer-id') + '"]');
        var icon = $('span.icon.layer-visibility-icon', li)

        if (visible) {
            if (l.get('exclusive')) {
                if (icon.hasClass('exclusive-hidden-icon')) {
                    icon.removeClass('exclusive-hidden-icon');
                }
                if (!icon.hasClass('exclusive-visible-icon')) {
                    icon.addClass('exclusive-visible-icon');
                }

                if (l.get('parent-layer')) {
                    var player = l.get('parent-layer');
                    player.getLayers().forEach(function (layer) {
                        if (layer.get('layer-id') != l.get('layer-id')) {
                            layer.setVisible(false);
                        }
                    });
                }
            } else {
                if (icon.hasClass('hidden-icon')) {
                    icon.removeClass('hidden-icon');
                }
                if (!icon.hasClass('visible-icon')) {
                    icon.addClass('visible-icon');
                }
            }

            if (this_.parentLayerVisible) {
                this_.setParentLayerVisible(l);
            }

        } else {
            if (l.get('exclusive')) {
                if (icon.hasClass('exclusive-visible-icon')) {
                    icon.removeClass('exclusive-visible-icon');
                }
                if (!icon.hasClass('exclusive-hidden-icon')) {
                    icon.addClass('exclusive-hidden-icon');
                }
            } else {
                if (icon.hasClass('visible-icon')) {
                    icon.removeClass('visible-icon');
                }
                if (!icon.hasClass('hidden-icon')) {
                    icon.addClass('hidden-icon');
                }
            }
        }
    });

    var options = layer.get('toc') || null;

    var item = document.createElement('li');
    item.className = 'toc-group-item';
    if (options && options.visible != null && !options.visible) {
        item.className += ' toc-group-item-hidden';
    }
    if (visible != null && !visible) {
        item.style.display = "none";
    }
    $(item).data('layer-ol',layer);

    var att = document.createAttribute('data-layer-id');
    att.value = layer_id;
    item.setAttributeNode(att);

    att = document.createAttribute('data-level');
    att.value = level;
    item.setAttributeNode(att);

    var icon_block = document.createElement('div');
    icon_block.className = 'left-icon-block';

    for (var i=0; i<level; i++) {
        $('<span class="indent" />').appendTo(icon_block);
    }

    /* Visibility */
    var visible_icon = "hidden-icon";

    if (parentGroupLayer && parentGroupLayer.get('exclusive') &&  parentGroupLayer.get('exclusive') == true) {
        visible_icon = "exclusive-hidden-icon";
        if (layer.get('visible')) {
            visible_icon = "exclusive-visible-icon";
        }
    } else {
        if (layer.get('visible')) {
            visible_icon = "visible-icon";
        }
    }

    if (!options || !('visibility' in options) || options.visibility) {
        $('<span class="icon layer-visibility-icon" />')
        .addClass(visible_icon)
        .click([map, layer], function (evt) {
              evt.preventDefault();

              var map = evt.data[0];
              var layer = evt.data[1];

              if (layer.get('visible')) {
                layer.set('visible', false);
              } else {
                layer.set('visible', true);
              }
        }).appendTo(icon_block);
    } else {
        $('<span class="icon layer-visibility-icon" />')
        .addClass(icon_block)
        .addClass("disabled-icon")
        .appendTo(icon_block);
    }
    $(icon_block).appendTo(item);

    var title_block = document.createElement('div');
    if (layer.get('extent_layer')) {
        title_block.className = 'title-block extent';
        title_block.setAttribute('title', 'Localizar');

        $(title_block).click([map, layer], function (evt) {
            if (layer.get('extent_layer') && layer.get('extent_layer').bounds) {
                var poly = Portal.Viewer.getPolygonFromExtent(layer.get('extent_layer').bounds);
                var geom = poly.transform(layer.get('extent_layer').projection, map.getView().getProjection().getCode());
                map.getView().fit(geom.getExtent(), map.getSize());
            }
        });
    } else {
        title_block.className = 'title-block';
    }
    $('<span />').html(layer.get('title')).appendTo(title_block);
    $(title_block).appendTo(item);

    var buttons_block = document.createElement('div');
    buttons_block.className = 'button-block';

    /* Properties (default - show) */
    var show_props = false;

    if (!options || !('properties' in options) || options.properties) {
        if (!options || !('transparency' in options) || options.transparency) {
            show_props  = true;
        }
        if (!options || !('remove' in options) || options.remove) {
            show_props  = true;
        }
    }

    if (show_props) {
        $('<span class="tool" title="Propriedades"><i class="fa fa-ellipsis-v" /></span>')
        .click([map, layer], function (evt) {
            var div = $(this).parent().nextAll("div.layer-properties");

            $("div.layers-control span.tool").not(this).removeClass('active');
            if ($(this).hasClass('active')) {
                $(this).removeClass('active');
            } else {
                $(this).addClass('active');
            }

            $("div.layer-extra").not(div).each(function() {
                $(this).hide();
            });
            div.toggle();
        }).appendTo(buttons_block);
    }


    /* Info (default - no show) */
    if (layer.get('info')) {
        $('<span class="tool" title="Informação"><i class="fas fa-info-circle" /></span>')
        .click([map, layer], function (evt) {
            var info = layer.get('info');
            var url = info.link;

            if (info.mode && info.mode == 'external') {
                var win = window.open(url, '_blank');
                win.focus();
            } else {
                if (!this_.panelInfoWindow) {
                    this_.panelInfoWindow = this_.openPanelInfo(layer);
                } else {
                    this_.panelInfoWindow.close();
                    this_.panelInfoWindow = this_.openPanelInfo(layer);
                }
            }

        }).appendTo(buttons_block);
    }

    /* Legend (default - show) */
    if (!options || !('legend' in options) || options.legend) {
        $('<span class="tool" title="Legenda"><i class="fa fa-list" /></span>')
        .click([map, layer], function (evt) {
            var div = $(this).parent().nextAll("div.layer-legend");

            $("div.layers-control span.tool").not(this).removeClass('active');
            if ($(this).hasClass('active')) {
                $(this).removeClass('active');
            } else {
                $(this).addClass('active');
            }

            $("div.layer-extra").not(div).each(function() {
                $(this).hide();
            });
            div.toggle();
        }).appendTo(buttons_block);
    }
    $(buttons_block).appendTo(item);

    /* Extra Data */
    if (layer.get('data')) {
        var layer_data = $('<div class="layer-extra-data" />');

        var ctl = $(layer.get('data').html || '');
        ctl.appendTo(layer_data);

        layer_data.appendTo(item);
    }

    /* Properties */
    if (show_props) {
        var props = $('<div class="layer-extra layer-properties" />');

        /*Transparency*/
        if (!options || !('transparency' in options) || options.transparency) {
            var slider = $('<div class="layer-opacity-slider">')[0];
            var opacity = layer.getOpacity() * 100;
            noUiSlider.create(slider, {
                start: [ opacity ],
                range: {
                    'min': [  0 ],
                    'max': [ 100 ]
                }
            });
            slider.noUiSlider.on('slide', function(evt){
                var value = this.get() / 100;
                layer.setOpacity(value);
            });
            var ctl = $('<div class="layer-opacity"><label>Transparência:</label></div>');
            $(slider).appendTo(ctl);
            ctl.appendTo(props);
        }

        /* Remove Layer */
        if (!options || !('remove' in options) || options.remove) {
            $('<span class="tool" title="Remover do mapa">Remover</span>')
            .click([map, layer], function (evt) {
                var parent = $(this).closest('.toc-group-item');

                var removeLayer = function (layer, layer_id, parentLayer) {
                    var lr = layer;
                    var layer_id = layer_id;

                    if (lr.get("layer-id") == layer_id) {
                        if (parentLayer) {
                            parentLayer.remove(lr);
                        } else {
                            map.removeLayer(lr);
                        }
                        return;
                    } else {
                        if (lr instanceof ol.layer.Group) {
                            var ls = lr.getLayers();
                            ls.forEach(function(lll) {
                                if (lll.get("layer-id") == layer_id) {
                                    ls.remove(lll);
                                    return;
                                } else {
                                    removeLayer(lll, layer_id, lr);
                                    return;
                                }
                            });
                        }
                    }
                }

                var map = evt.data[0];
                var layer = evt.data[1];
                var layer_id = layer.get("layer-id");

                var ls = map.getLayers();
                ls.forEach(function (ll) {
                    removeLayer(ll, layer_id, null);
                });
                $(parent).remove();

            }).appendTo(props);
        }

        props.appendTo(item);
    }

    var buildHtmlLegend = function (layer, item) {
        var url = null;

        var legend = $('<div class="layer-extra layer-legend" />');
        legend.html(layer.get('legend').html || '');

        if (layer.get('legend') && layer.get('legend').title) {
            legend.prepend('<div class="layer-legend-title">' + layer.get('legend').title + '</div>');
        }

        legend.appendTo(item);
    }

    var buildWMSLegend = function(layer, item) {
        var source = layer.getSource();
        var url = null;

        var legend = $('<div class="layer-extra layer-legend" />');

        if (layer.get('capability') && layer.get('capability').styles) {
            for (var i=0; i<layer.get('capability').styles.length;i++) {
                if (layer.get('capability').styles[i].name.toLocaleLowerCase() == 'default') {
                    if (layer.get('capability').styles[i].legend && layer.get('capability').styles[i].legend.href) {
                        url = layer.get('capability').styles[i].legend.href;
                    }
                }
            }
        }

        if (!url) {
            if (source.getUrl) {
                url = source.getUrl();
            } else if (source.getUrls) {
                url = source.getUrls()[0];
            }

            if (url) {
                if (url.indexOf('?') < 0) url = url + '?';
                url = url + 'SERVICE=WMS&REQUEST=GetLegendGraphic&LAYER=' + source.getParams().LAYERS;
                url = url + '&FORMAT=image/png';
                if (source.getParams().SLD) {
                    url = url + '&SLD=' + source.getParams().SLD;
                } else if (source.getParams().STYLES) {
                    url = url + '&STYLE=' + source.getParams().STYLES;
                }
                if (source.getParams().VERSION) {
                    url = url + '&VERSION=' + source.getParams().VERSION;
                }
            }
        }

        if (url) {
            if (this_.wms && this_.wms.legendOptions) {
                url = url + '&LEGEND_OPTIONS=' + this_.wms.legendOptions;
            } else if (layer.get('legend') && layer.get('legend').wms && layer.get('legend').wms.legendOptions) {
                url = url + '&LEGEND_OPTIONS=' +  layer.get('legend').wms.legendOptions;
            }

            if (this_.wms && this_.wms.rule) {
                url = url + '&RULE=' + this_.wms.rule;
            } else if (layer.get('legend') && layer.get('legend').wms && layer.get('legend').wms.rule) {
                url = url + '&RULE=' +  layer.get('legend').wms.rule;
            }
        }

        if (url) {
            var _encodeUrl = function (url) {
                var urlParts = url.split("?");
                var newUrl = encodeURIComponent(urlParts[0] + "?" + urlParts[1]);
                return newUrl;
            };

            if (window.location.protocol === 'https:' && $.url(url).attr('protocol') == 'http') {
                url = OpenLayers.ProxyHost + _encodeUrl(url);
            }

            if (layer.get('dynamicLegend')) {
                legend.html('<img class="layer-wms-legend" src="' + url + '" />');
            } else {
                legend.html('<img src="' + url + '" />');
            }
        }

        if (layer.get('legend') && layer.get('legend').title) {
            legend.prepend('<div class="layer-legend-title">' + layer.get('legend').title + '</div>');
        }

        legend.appendTo(item);
    }

    var buildArcGISLegend = function (layer, item) {
        var source = layer.getSource();
        var url = null;

        if (source.getUrl) {
            url = source.getUrl();
        } else if (source.getUrls) {
            url = source.getUrls()[0];
        }

        $.ajax({
            type: 'GET',
            dataType: "json",
            url: url + '/legend',
            data: {
                f: 'json'
            },
            parametersData: { 'layer': layer, 'item': item },
            beforeSend: function () {
            },
            success: function (r) {
                var layer = this.parametersData.layer;
                var source = layer.getSource();

                var vlayers = null;

                if (source.getParams()) {
                    var params = source.getParams();

                    for (var p in params) {
                        if (params.hasOwnProperty(p) && "layers" == (p+ "").toLowerCase()) {
                            if (params[p] && params[p] != "") {
                                var ll = "";
                                if (params[p].indexOf(":") >= 0) {
                                    ll = params[p].split(":")[1];
                                } else {
                                    ll = params[p];
                                }
                                vlayers = ll.split(",");
                            };
                            break;
                        }
                    }

                    if (r.layers) {
                        var html = "";
                        if (vlayers && vlayers.length > 0) {
                            for (var i = 0; i < r.layers.length; i++) {
                                for (var z = 0; z < vlayers.length; z++) {
                                    var id = vlayers[z];

                                    if (id == (r.layers[i].layerId + "")) {
                                        var l = r.layers[i];
                                        html += "<div data-min-scale='" + l.minScale + "' data-max-scale='" + l.maxScale + "'><div>" + l.layerName + "</div>";
                                        html += "<ul>";
                                        for (var j=0; j < l.legend.length; j++){
                                            var leg = l.legend[j];
                                            html += "<li><img src='data:" + leg.contentType + ";base64," + leg.imageData + "'><span>" + leg.label + "</span></li>";
                                        }
                                        html += "</ul></div>";

                                        break;
                                    }
                                }
                            }
                        } else {
                            for (var i=0; i < r.layers.length; i++) {
                                var l = r.layers[i];
                                html += "<div data-min-scale='" + l.minScale + "' data-max-scale='" + l.maxScale + "'><div>" + l.layerName + "</div>";
                                html += "<ul>";
                                for (var j=0; j < l.legend.length; j++){
                                    var leg = l.legend[j];
                                    html += "<li><img src='data:" + leg.contentType + ";base64," + leg.imageData + "'><span>" + leg.label + "</span></li>";
                                }
                                html += "</ul></div>";
                            }
                        }
                        var legend = $('<div class="layer-extra layer-legend" />')
                        legend.html(html);
                        if (layer.get('legend') && layer.get('legend').title) {
                            legend.prepend('<div class="layer-legend-title">' + layer.get('legend').title + '</div>');
                        }
                        legend.appendTo(item);
                    }
                }
            },
            complete: function () {
            },
            error: function (r) {
            }
        });
    }

    if (layer.get('legend') && layer.get('legend').html) {
        buildHtmlLegend(layer, item);
    } else {
        var source = null;
        if (layer.getSource) {
            source = layer.getSource();
        }
        if (source instanceof ol.source.TileWMS || source instanceof ol.source.ImageWMS) {
            buildWMSLegend(layer, item);
        } else if (source instanceof ol.source.TileArcGISRest || source instanceof ol.source.ImageArcGISRest) {
            buildArcGISLegend(layer, item);
        }
    }

    if (element) {
        element.appendChild(item);
    } else {
        if(this.root.firstChild) {
            this.root.insertBefore(item,this.root.firstChild);
        } else {
            this.root.appendChild(item);
        }
    }
}

app.LayersControl.prototype.addLayerGroupToList = function (layer, element, level, visible, parentGroupLayer) {
    var layer_id = this.generateID();
    layer.set('layer-id', layer_id);

    if (parentGroupLayer) {
        layer.set('parent-layer', parentGroupLayer);
    }

    if (parentGroupLayer && parentGroupLayer.get('exclusive') &&  parentGroupLayer.get('exclusive') == true) {
        layer.set('exclusive', true);
    } else {
        layer.set('exclusive', false);
    }

    layer.on('change:visible', function(e){
        var l = this;
        var visible = this.get('visible');
        var li = $('li[data-layer-id="' + l.get('layer-id') + '"]');
        var icon = $('span.icon.layer-visibility-icon', li)

        if (visible) {
            if (l.get('exclusive')) {
                if (icon.hasClass('exclusive-hidden-icon')) {
                    icon.removeClass('exclusive-hidden-icon');
                }
                if (!icon.hasClass('exclusive-visible-icon')) {
                    icon.addClass('exclusive-visible-icon');
                }

                if (l.get('parent-layer')) {
                    var player = l.get('parent-layer');
                    player.getLayers().forEach(function (layer) {
                        if (layer.get('layer-id') != l.get('layer-id')) {
                            layer.setVisible(false);
                        }
                    });
                }
            } else {
                if (icon.hasClass('hidden-icon')) {
                    icon.removeClass('hidden-icon');
                }
                if (!icon.hasClass('visible-icon')) {
                    icon.addClass('visible-icon');
                }
            }

            if (this_.parentLayerVisible) {
                this_.setParentLayerVisible(l);
            }

        } else {
            if (l.get('exclusive')) {
                if (icon.hasClass('exclusive-visible-icon')) {
                    icon.removeClass('exclusive-visible-icon');
                }
                if (!icon.hasClass('exclusive-hidden-icon')) {
                    icon.addClass('exclusive-hidden-icon');
                }
            } else {
                if (icon.hasClass('visible-icon')) {
                    icon.removeClass('visible-icon');
                }
                if (!icon.hasClass('hidden-icon')) {
                    icon.addClass('hidden-icon');
                }
            }
        }
    });

    var options = layer.get('toc') || null;

    var group = document.createElement('ul');
    group.className = 'toc-group layer-group';
    if (visible != null && !visible) {
        group.style.display = "none";
    }

    var item = document.createElement('li');
    item.className = 'toc-group-item layer-group';
    $(item).data('layer-ol',layer);

    var att = document.createAttribute('data-layer-id');
    att.value = layer_id;
    item.setAttributeNode(att);

    att = document.createAttribute('data-level');
    att.value = level;
    item.setAttributeNode(att);

    var icon_block = document.createElement('div');
    icon_block.className = 'left-icon-block';

    for (var i=0; i<level; i++) {
        $('<span class="indent" />').appendTo(icon_block);
    }

    var expanded = true;
    var css_expanded = 'expanded-icon';
    if (layer.get('expanded') != null && !layer.get('expanded')) {
        expanded = false;
        css_expanded = 'expand-icon';
    }
    $('<span class="icon ' + css_expanded + '" />')
    .click([map, layer], function (evt) {
        var li = $(this).closest('li');
        var lv = li.data('level');

        var visible = true;

        if ($(this).hasClass('expanded-icon')) {
            visible = false;
            $(this).removeClass('expanded-icon').addClass('expand-icon');
        } else {
            $(this).removeClass('expand-icon').addClass('expanded-icon');
        }

        var childs = li.parent().children();
        for (var ic=1; ic<childs.length; ic++) {
            if (visible) {
                $(childs[ic]).show();
            } else {
                $(childs[ic]).hide();
            }
        }
    })
    .appendTo(icon_block);

    var visible_icon = "hidden-icon";
    if (layer.get('visible')) {
        visible_icon = "visible-icon"
    }
    $('<span class="icon layer-visibility-icon" />')
    .addClass(visible_icon)
    .click([map, layer], function (evt) {
          evt.preventDefault();

          var map = evt.data[0];
          var layer = evt.data[1];

          if (layer.get('visible')) {
            $(this).removeClass('visible-icon').addClass('hidden-icon');
            layer.set('visible', false);
          } else {
            $(this).addClass('visible-icon').removeClass('hidden-icon');
            layer.set('visible', true);
          }
    }).appendTo(icon_block);

    $(icon_block).appendTo(item);

    var title_block = document.createElement('div');
    title_block.className = 'title-block';
    $('<span />').html(layer.get('title')).appendTo(title_block);
    $(title_block).appendTo(item);

    var buttons_block = document.createElement('div');
    buttons_block.className = 'button-block';

    /* Properties (default - hidden) */
    var show_props = false;

    if (options && ('properties' in options) && options.properties) {
        if (options && ('transparency' in options) && options.transparency) {
            show_props  = true;
        }
    }

    if (show_props) {
        $('<span class="tool" title="Propriedades"><i class="fa fa-ellipsis-v" /></span>')
        .click([map, layer], function (evt) {
            var div = $(this).parent().nextAll("div.layer-properties");

            $("div.layers-control span.tool").not(this).removeClass('active');
            if ($(this).hasClass('active')) {
                $(this).removeClass('active');
            } else {
                $(this).addClass('active');
            }

            $("div.layer-extra").not(div).each(function() {
                $(this).hide();
            });
            div.toggle();
        }).appendTo(buttons_block);
    }

    /* Info (default - no show) */
    if (layer.get('info')) {
        $('<span class="tool" title="Informação"><i class="fas fa-info-circle" /></span>')
        .click([map, layer], function (evt) {
            var info = layer.get('info');
            var url = info.link;

            if (info.mode && info.mode == 'external') {
                var win = window.open(url, '_blank');
                win.focus();
            } else {
                if (!this_.panelInfoWindow) {
                    this_.panelInfoWindow = this_.openPanelInfo(layer);
                } else {
                    this_.panelInfoWindow.close();
                    this_.panelInfoWindow = this_.openPanelInfo(layer);
                }
            }

        }).appendTo(buttons_block);
    }
    $(buttons_block).appendTo(item);

    /* Properties */
    if (show_props) {
        var props = $('<div class="layer-extra layer-properties" />');

        /*Transparency*/
        if (!options || !('transparency' in options) || options.transparency) {
            var slider = $('<div class="layer-opacity-slider">')[0];
            var opacity = layer.getOpacity() * 100;
            noUiSlider.create(slider, {
                start: [ opacity ],
                range: {
                    'min': [  0 ],
                    'max': [ 100 ]
                }
            });
            slider.noUiSlider.on('slide', function(evt){
                var value = this.get() / 100;
                layer.setOpacity(value);
            });
            var ctl = $('<div class="layer-opacity"><label>Transparência:</label></div>');
            $(slider).appendTo(ctl);
            ctl.appendTo(props);
        }

        props.appendTo(item);
    }

    /* Extra Data */
    if (layer.get('data')) {
        var layer_data = $('<div class="layer-extra-data" />');

        var ctl = $(layer.get('data').html || '');
        ctl.appendTo(layer_data);

        layer_data.appendTo(item);
    }

    group.appendChild(item);

    if (element) {
        element.appendChild(group);
    } else {
        this.root.appendChild(group);
    }

    var layers = layer.getLayers().getArray();
    for (var i = layers.length - 1, ii = 0; i >= ii; --i) {
        var l = layers[i];

        if (l instanceof ol.layer.Group) {
            if (l.get('single') && l.get('single') == true) {
                this.addLayerToList(l, group, level + 1, expanded, layer);
            } else {
                this.addLayerGroupToList(l, group, level + 1, expanded, layer);
            }
        } else {
            this.addLayerToList(l, group, level + 1, expanded, layer);
        }
    }

    var lc = layer.getLayers();
    lc.on('add', function (evt) {
        var l = evt.element;
        var level = 1;
        try {
            if ($(group).children('[data-level]:first').data('level')) {
                level = parseInt($(group).children('[data-level]:first').data('level')) + 1;
            }
        } catch (err) {}
        this.addLayerToList(l, group, level);
    }, this);

    layer.set('toc-group', true);

}

app.LayersControl.prototype.hideAllLayers = function () {
    $('.icon.visible-icon', this.root).each(function(i, obj) {
        $(obj).trigger('click');
    });
}

app.LayersControl.prototype.getRootLayer = function () {
    return this.rootLayer;
}

app.LayersControl.prototype.refreshLayersControl = function () {
    return this.rootLayer;
}