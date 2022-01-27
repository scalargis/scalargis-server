var Portal = Portal || (function () {
    var _init = function () {
    };

    return {
        Init: _init
    }
}());

Portal.Viewer = (function () {

    var _config = null;
    var _map = null;
    var _temporaryLayer = null;
    var _rootLayer = null;

    var _buildSelectionStyles = function () {
        var white = [255, 255, 255, 1];
        var blue = [0, 153, 255, 1];
        var green = [0, 255, 0, 1];
        var width = 3;
        var styles = [
           new ol.style.Style({
             fill: new ol.style.Fill({
               color: [255, 255, 255, 0.5]
             })
           }),
           new ol.style.Style({
             stroke: new ol.style.Stroke({
               color: white,
               width: width + 2
             })
           }),
           new ol.style.Style({
             stroke: new ol.style.Stroke({
               color: green,
               width: width
             })
           }),
           new ol.style.Style({
             image: new ol.style.Circle({
               radius: width * 2,
               fill: new ol.style.Fill({
                 color: green
               }),
               stroke: new ol.style.Stroke({
                 color: white,
                 width: width / 2
               })
             }),
             zIndex: Infinity
           })
         ];

        return styles;
    };

    var _buildActiveStyles = function () {
        var white = [255, 255, 255, 1];
        var blue = [0, 153, 255, 1];
        var red = [255, 0, 0, 1];
        var width = 3;
        var styles = {}
        styles[ol.geom.GeometryType.POLYGON] = [
           new ol.style.Style({
             fill: new ol.style.Fill({
               color: [255, 255, 255, 0.5]
             })
           }),
           new ol.style.Style({
             stroke: new ol.style.Stroke({
               color: blue,
               width: width
             })
           })
         ];
         styles[ol.geom.GeometryType.MULTI_POLYGON] =
             styles[ol.geom.GeometryType.POLYGON];
         styles[ol.geom.GeometryType.LINE_STRING] = [
           new ol.style.Style({
             stroke: new ol.style.Stroke({
               color: white,
               width: width + 2
             })
           }),
           new ol.style.Style({
             stroke: new ol.style.Stroke({
               color: red,
               width: width
             })
           })
         ];
         styles[ol.geom.GeometryType.MULTI_LINE_STRING] =
             styles[ol.geom.GeometryType.LINE_STRING];
         styles[ol.geom.GeometryType.POINT] = [
           new ol.style.Style({
             image: new ol.style.Circle({
               radius: width * 2,
               fill: new ol.style.Fill({
                 color: red
               }),
               stroke: new ol.style.Stroke({
                 color: white,
                 width: width / 2
               })
             }),
             zIndex: Infinity
           })
         ];
         styles[ol.geom.GeometryType.MULTI_POINT] =
             styles[ol.geom.GeometryType.POINT];
         styles[ol.geom.GeometryType.GEOMETRY_COLLECTION] =
             styles[ol.geom.GeometryType.POLYGON].concat(
                 styles[ol.geom.GeometryType.POINT]
             );

        return styles;
    }

    var _selectionStyles = _buildSelectionStyles();
    var _activeStyles = _buildActiveStyles();

    var _init = function () {
    };

    var _load = function (config, mapId) {
        _config = config;

        _loadProjections(_config.map.projections);

        var vLayers = new Array().concat(_config.map.baseLayers);

        var reverseChildLayersOrder = function (lc) {
            lc.getLayers().getArray().reverse();
            lc.getLayers().forEach(function () {
                if (this instanceof ol.layer.Group) {
                    reverseChildLayersOrder(this.getLayers());
                }
            });
        }

        var tlayers = _config.map.tocLayers.reverse();
        for (var i = 0, ii = tlayers.length; i < ii; ++i) {
            if (tlayers[i] instanceof ol.layer.Group) {
                reverseChildLayersOrder(tlayers[i]);
            }
        }

        //Check layers permissions ----------------------------//
        var checkLayerPermission = function (layers) {
            if (layers instanceof Array) {
                for (var i = 0, ii = layers.length; i < ii; ++i) {
                    var l = layers[i];
                    if (!l.get('roles') || l.get('roles').length == 0 || $(roles).filter(l.get('roles') || []).length > 0) {
                        if (l instanceof ol.layer.Group) {
                            checkLayerPermission(l.getLayers());
                        }
                    } else {
                        layers.splice(i, 1);
                    }
                }
            } else {
                layers.forEach(function (l) {
                    if (!l.get('roles') || l.get('roles').length == 0 || $(roles).filter(l.get('roles') || []).length > 0) {
                        if (l instanceof ol.layer.Group) {
                            checkLayerPermission(l.getLayers());
                        }
                    } else {
                        this.remove(l);
                    }
                }, layers);
            }
        }
        checkLayerPermission(tlayers);
        // End check layers permissions ----------------------------//

        var tocLayers = new ol.layer.Group({
                layers: new Array().concat(tlayers),
                group: 'toc-root-group'
        });

        vLayers = vLayers.concat([tocLayers]);
        vLayers = vLayers.concat(_config.map.overlayLayers);

        var viewOptions = {
            projection: ol.proj.get(_config.map.projection)
        };

        if (_config.map.maxZoom) {
            viewOptions['maxZoom'] = _config.map.maxZoom;
        }
        if (_config.map.minZoom) {
            viewOptions['minZoom'] = _config.map.minZoom;
        }

        if (_config.map.zoomFactor) {
            viewOptions['zoomFactor'] = _config.map.zoomFactor;
        }

        if (_config.map.maxResolution) {
            viewOptions['maxResolution'] = _config.map.maxResolution;
        }

        if (_config.map.minResolution) {
            viewOptions['minResolution'] = _config.map.minResolution;
        }

        if (_config.map.restrictedExtent && _config.map.restrictedExtent.bounds) {
            viewOptions['extent'] = ol.proj.transformExtent(_config.map.restrictedExtent.bounds, _config.map.restrictedExtent.projection || ol.proj.get(_config.map.projection), ol.proj.get(_config.map.projection));
        }

        if (_config.map.center) {
            if (_config.map.center.x && _config.map.center.y) {
                viewOptions['center'] = ol.proj.transform([_config.map.center.x, _config.map.center.y], _config.map.center.projection || _config.map.displayProjection || _config.map.projection, _config.map.projection);
            }
            if(_config.map.center.zoom) {
                viewOptions['zoom'] = _config.map.center.zoom;
            }
        }

        var attribution = new ol.control.Attribution({
          collapsible: false
        });

        var map = new ol.Map({
            controls: ol.control.defaults({
              zoom: false,
              attribution: false,
              rotate: false
            }),
            target: mapId,
            layers: vLayers,
            overlays: [],
            view: new ol.View(
                viewOptions
                /*{
                projection: ol.proj.get(_config.map.projection),
                //extent: extent,
                center: ol.proj.transform([_config.map.center.x], _config.map.center.projection || _config.map.center.displayProjection || _config.map.projection, _config.map.projection),
                zoom: 10
                }*/
            )
        });

        _setMap(map);
        _rootLayer = tocLayers;

        _setLayersResolutionFromMaxMinScale();

        return _map;
    };

    var _setLayersResolutionFromMaxMinScale = function() {
        var allLayers = []
        _loadAllLayersAsArray(_rootLayer, allLayers);
        for (j=0; j<allLayers.length; j++) {
            if (allLayers[j].get('minScale')) {
                var resolution = _getResolutionFromScale(allLayers[j].get('minScale'));
                allLayers[j].setMaxResolution(resolution);
            }
            if (allLayers[j].get('maxScale')) {
                var resolution = _getResolutionFromScale(allLayers[j].get('maxScale'));
                allLayers[j].setMinResolution(resolution);
            }
        }
    }

    var _getResolutionFromScale = function (scale) {
        var units = _map.getView().getProjection().getUnits();
        var dpi = 25.4 / 0.28;
        var mpu = ol.proj.METERS_PER_UNIT[units];
        var resolution = scale/(mpu * 39.37 * dpi);
        return resolution;
    };

    var _getScaleFromResolution = function (resolution) {
        var units = _map.getView().getProjection().getUnits();
        var dpi = 25.4 / 0.28;
        var mpu = ol.proj.METERS_PER_UNIT[units];
        var scale = resolution * mpu * 39.37 * dpi;
        return scale;
    }

    var _loadProjections = function (projections) {

        for (var i = 0; i < projections.length; ++i) {
            var projection = projections[i];

            //if (!ol.proj.projections_[projection.code] && projection.definition) {
            if (!ol.proj.get(projection.code) && projection.definition) {
                proj4.defs(projection.code, projection.definition);

                var p = ol.proj.get(projection.code);

                if (projection.extent) {
                    p.setExtent(projection.extent);
                }
                if (projection.worldExtent) {
                    p.setWorldExtent(projection.worldExtent);
                }

                var olProjection = new ol.proj.Projection({
                    code: projection.code,
                    // The extent is used to determine zoom level 0. Recommended values for a
                    // projection's validity extent can be found at http://epsg.io/.
                    extent: projection.extent || null,
                    worldExtent: projection.worldExtent || null,
                    units: projection.units || 'm'
                });
                ol.proj.addProjection(olProjection);
            }


            var code = projection.code.split(':')[1];

            /* Add alias */

            //http://www.opengis.net/gml/srs/epsg.xml#
            proj4.defs('http://www.opengis.net/gml/srs/epsg.xml#' + code, projection.definition);

            var f = new ol.proj.Projection({
                code: 'http://www.opengis.net/gml/srs/epsg.xml#' + code,
                // The extent is used to determine zoom level 0. Recommended values for a
                // projection's validity extent can be found at http://epsg.io/.
                extent: projection.extent,
                units: projection.units || 'm'
            });
            ol.proj.addProjection(f);

            var g = ol.proj.get('http://www.opengis.net/gml/srs/epsg.xml#' + code);

            //urn:ogc:def:crs:EPSG::
            proj4.defs('urn:ogc:def:crs:EPSG::' + code, projection.definition);

            var f = new ol.proj.Projection({
                code: 'urn:ogc:def:crs:EPSG::' + code,
                // The extent is used to determine zoom level 0. Recommended values for a
                // projection's validity extent can be found at http://epsg.io/.
                extent: projection.extent,
                units: projection.units || 'm'
            });
            ol.proj.addProjection(f);

            var t = ol.proj.get('urn:ogc:def:crs:EPSG::' + code);
        }

    };

    var _loadAllLayersAsArray = function(layer, vLayers) {
        if (layer instanceof Array) {
            for (var i=0; i<layer.length;i++) {
                _loadAllLayersAsArray(layer[i], vLayers);
            }
        } else if (layer instanceof ol.layer.Group) {
            vLayers.push(layer);
            var layers = layer.getLayers().getArray();
            for (var i=0; i<layers.length;i++) {
                if (layers[i] instanceof ol.layer.Group) {
                    _loadAllLayersAsArray(layers[i], vLayers);
                } else {
                    vLayers.push(layers[i]);
                }
            }
        } else {
            vLayers.push(layer);
        }
    };

    var _showLoading = function (element, cancel, xhr) {

        var msg = '<div class="loading-indicator"><div class="progress progress-striped active"><div class="progress-bar progress-bar-info" style="width: 100%"></div></div></div>';

        var options = {
            message: msg,
            overlayCSS: {
                backgroundColor: '#000',
                opacity: 0.1,
                cursor: 'wait'
            },
            css: {
                border: '0px solid #aaa',
                width: '50%',
                backgroundColor: '',
            },
            onOverlayClick: $.unblockUI
        };

        if (element) {
            if (cancel) {
                options.onOverlayClick = function (e) {
                    if (xhr) {
                        xhr.abort();
                    }
                    $(element).unblock();
                }
            }

            $(element).block(options);
        } else {
            if (cancel) {
                options.onOverlayClick = function (e) {
                    if (xhr) {
                        xhr.abort();
                    }
                    $.unblockUI()
                }
            }

            options.message = '<div class="loading-indicator"><div class="progress progress-striped active"><div class="progress-bar progress-bar-info" style="width: 100%"></div></div></div>';
            options.css.width = '10%';
            options.css["margin-left"] = '100px';

            $.blockUI(options);
        }
    };

    var _hideLoading = function (element) {
        if (element) {
            $(element).unblock();
        } else {
            $.unblockUI();
        }
    };

    var _setMap = function (map) {
        _map = map;

        var layer = null;

        var layers = _map.getLayers().getArray();

        /*--------- Add Drawtools Layer --------*/
        for (var i = 0; i < layers.length; i++) {
            if (layers[i].get('name') == 'drawtools-layer') {
                layer = layers[i];
                break;
            }
        }
        if (layer == null) {
            layer = new ol.layer.Vector({
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
                name: 'drawtools-layer',
                group: 'vector'
            });
        }
        _map.addLayer(layer);
        _drawtoolsLayer = layer;

        /*--------- Add Temporary Layer --------*/
        layer = null;
        for (var i = 0; i < layers.length; i++) {
            if (layers[i].get('name') == 'temporary-layer') {
                layer = layers[i];
                break;
            }
        }
        if (layer == null) {
            layer = new ol.layer.Vector({
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
                name: 'temporary-layer',
                group: 'vector'
            });
        }
        _map.addLayer(layer);
        _temporaryLayer = layer;

    };

    var _getMap = function () {
        return _map;
    };

    var _getMapProjectionCode = function () {
        return _map.getView().getProjection().getCode();
    };

    var _getMapSRID = function () {
        var code = _getMapProjectionCode();
        var parts = code.split(':');

        return parts[1];
    };

    var _getMapCurrentScale = function () {
        var view = _map.getView(); ;
        var resolution = view.getResolution();
        var units = view.getProjection().getUnits();
        var dpi = 25.4 / 0.28;
        var mpu = view.getProjection().getMetersPerUnit() || ol.proj.METERS_PER_UNIT[units];
        var scale = resolution * mpu * 39.37 * dpi;

        return scale;
    };

    var _getTemporaryLayer = function () {
        return _temporaryLayer;
    };

    var _getDrawtoolsLayer = function () {
        return _drawtoolsLayer;
    };

    var _getFeaturesTemporaryLayer = function (modulo, id) {
        var features = [];

        var source = _temporaryLayer.getSource();
        var fts = source.getFeatures();

        for (var i = 0; i < fts.length; i++) {
            var feature = fts[i];

            if ((!modulo || feature.get('modulo') == modulo) && (!id || feature.get('gid') == id)) {
                features.push(feature);
            }
        }

        return features;
    };

    var _getPolygonFromExtent = function (extent, separator) {
        var v = null;

        if (typeof extent === 'string') {
            v = extent.split(separator || " ");
        } else {
            v = extent;
        }

        var coords = [
            [parseFloat(v[0]), parseFloat(v[3])],
            [parseFloat(v[2]), parseFloat(v[3])],
            [parseFloat(v[2]), parseFloat(v[1])],
            [parseFloat(v[0]), parseFloat(v[1])],
            [parseFloat(v[0]), parseFloat(v[3])]
        ];

        var poly = new ol.geom.Polygon(new Array(coords));

        return poly;
    };

    var _getTransformedGeometry =  function (geomEWKT, destProj) {

        var format = new ol.format.WKT();

        var parts = geomEWKT.split(";");
        var srid = parts[0].split("=")[1];

        var wkt = geomEWKT.split(";")[1];
        var geom = format.readGeometry(wkt);
        var newGeom = geom.transform('EPSG:' + srid, destProj);

        return newGeom;
    };

    var _getWKTFromGeometry = function (geom) {
        var format = new ol.format.WKT();

        var wkt = format.writeGeometry(geom);

        return wkt;
    };

    var _getSelectionStyles = function () {
        return _selectionStyles;
    };

    var _getActiveStyles = function () {
        return _activeStyles;
    };

    var _getConfig = function () {
        return _config;
    };

    var _getId = function () {
        return _config.id;
    };

    var _showDirectory = function (element) {
        var url = $(element).data('action');
        var title = $(element).data('title') || 'Documentos';
        var filter = $(element).data('filter');
        var recursive = $(element).data('recursive');

        var width = eval($(element).data('width'));
        var height = eval($(element).data('height'));

        $.jsPanel({
            id: this.generateID,
            contentAjax: {
                url:    url,
                data: {
                    mapId: Portal.Viewer.getMapId() || null,
                    filter: filter,
                    recursive: recursive
                },
                done:   function( data, textStatus, jqXHR, panel ){
                    this.content.empty().append(data.Message);
                },
                fail:   function( jqXHR ){
                    this.setTheme('danger')
                        .headerTitle('<i class="fa fa-exclamation-triangle"></i> Request failed')
                        .content.empty().append(jqXHR.responseText);
                },
                always: function( arg1, textStatus, arg3, panel ) {
                    //panel.content.prepend('<p style="...">always callback - textStatus: ' + textStatus + '</p>');
                    //this.resize({width:"auto", height:"auto", maxwidth: $(window).width()/2}).reposition();
                }
            },
            headerTitle: title,
            panelSize: {
                width:  width || function() {return $(window).width()/5},
                height: height || 275
            },
            dragit: {
                containment: 'window',
            },
            contentOverflow: { horizontal: 'hidden', vertical: 'auto' },
            headerControls: {
                controls:  'closeonly'
            },
            content: '<div class="msg"><p>Aguarde...</p></div>',
            onclosed: function(event, panel) {
                //panel.reposition(panelpos());
            },
            onwindowresize: function(event, panel) {
                //panel.reposition(panelpos());
            }
        });
    };

    var _showPanel = function (panel) {
        if (panel) {
            if (!$('.menu-bar-widget.' + panel).hasClass('open')) {
                var btn = $(".menu-button." + panel);

                if (btn.length > 0) {
                    btn.trigger("click");
                }
            }
        }
    }

    var _showEditor = function (element, modal, oncontentload, onpanelclosed) {
        var url = $(element).data('action');
        var title = $(element).data('layer-title') || '';

        var width = eval($(element).data('width'));
        var height = eval($(element).data('height'));

        $.jsPanel({
            id: this.generateID,
            paneltype: modal ? 'modal' : '',
            theme: 'bootstrap-primary',
            show: 'animated fadeInDownBig',
            content:     '<div style="padding: 20%"><div class="loading-indicator"><div class="progress progress-striped active"><div class="progress-bar progress-bar-info" style="width: 100%"></div></div></div></div>',
            oncontentload: oncontentload || null,
            contentAjax: {
                url:    url,
                data: {
                    mapId: Portal.Viewer.getMapId() || null
                },
                done:   function( data, textStatus, jqXHR, panel ){
                    var buttons = [
                        {
                            item: "<button type='button'></button>",
                            event: jsPanel.evtStart,
                            btnclass: "btn btn-danger btn-sm",
                            btntext:  " Fechar",
                            callback: function( event ){
                                event.stopPropagation();
                                event.data.close();
                            }
                        }
                    ];

                    if (data.Data.mode == 'write') {
                        buttons.unshift({
                            item:     "<button type='button'></button>",
                            event:    jsPanel.evtStart,
                            btnclass: "btn btn-primary btn-sm",
                            btntext:  " Gravar",
                            callback: function( event ){
                                event.stopPropagation();
                                $('.form-main', event.data).submit();
                            }
                        });
                    }
                    this.content.empty().append(data.Message);
                    this.toolbarAdd("footer", buttons);
                    $(this).on('submit', '.form-main', {panel: panel}, function (e) {
                        e.preventDefault;

                        var panel = e.data.panel;
                        var action = $(this).attr('action');
                        var data = $(this).serialize();

                        $.ajax({
                            type: 'POST',
                            url: action,
                            traditional: true,
                            data: data,
                            params: {
                                panel: panel
                            },
                            beforeSend: function () {
                                Portal.Viewer.ShowLoading($('.jsPanel-content', this.params.panel));
                            },
                            success: function (r) {
                                this.params.panel.content.empty().append(r.Message);
                            },
                            complete: function () {
                                Portal.Viewer.HideLoading($('.jsPanel-content', this.params.panel));
                            },
                            error: function (r) {
                                /*
                                $("#informationDiv").informationModal({
                                    heading: 'Informação',
                                    body: 'Ocorreu um erro no servidor',
                                    messageClass: "alert alert-danger",
                                    callback: null
                                });
                                */
                            }
                        });

                        return false;
                    });
                    $(this).on('click', '.open-external-link', {panel: panel}, function (e) {
                        e.preventDefault();
                        var url = $('input', $( e.target ).parent().parent()).val();
                        if (url) {
                            window.open(url);
                        }
                        return false;
                    });

                    if (panel.option.oncontentload) {
                        panel.option.oncontentload(panel);
                    }

                },
                fail:   function( jqXHR ){
                },
                always: function( arg1, textStatus, arg3, panel ) {
                }
            },
            headerTitle: title,
            panelSize: {
                width:  width || function() {return $(window).width()/4},
                height: height || function() {return $(window).height()/2}
            },
            dragit: {
                containment: 'window',
            },
            contentOverflow: { horizontal: 'hidden', vertical: 'auto' },
            onclosed: onpanelclosed || null
        });
    };


    var _getRootLayer = function () {
        return _rootLayer;
    };

    var _getGeometryArea = function (geometry) {
        var area;
        switch (geometry.getType()) {
            case 'MultiPolygon':
              // for multi-polygons, we need to add the area of each polygon
              area = geometry.getPolygons().reduce(function(left, right) {
                return left + right.getArea();
              }, 0);
              break;
            case 'Polygon':
              // for polygons, we just get the area
              area = geometry.getArea();
              break;
            default:
              // no other geometry types have area as far as we are concerned
              area = 0;
        }
        return area;
    };

    var _showLayer = function (layer, layer_id, parentLayer) {
        var lr = layer;
        var layer_id = layer_id;

        if (lr.get("id") == layer_id) {
            if (parentLayer) {
                parentLayer.set('visible', true);
            } else {
                lr.set('visible', true);
            }
            return;
        } else {
            if (lr instanceof ol.layer.Group) {
                var ls = lr.getLayers();
                ls.forEach(function(lll) {
                    if (lll.get("id") == layer_id) {
                        lll.set('visible', true);
                        return;
                    } else {
                        Portal.Viewer.showLayer(lll, layer_id, lr);
                        return;
                    }
                });
            }
        }
    };

    var _getLayerById = function(layer, layer_id) {
        //console.log(lr.get('title') + ': ' + lr.get("id") + '; ' + layer_id);
        if (layer.get("id") == layer_id) {
            return layer;
        } else if (layer instanceof ol.layer.Group) {
			var ls = layer.getLayers().getArray();
			var ll = null;
            for (var i=0; i<ls.length; i++) {
				if (ls[i].get("id") == layer_id) {
					ll = ls[i];
					break;
				} else {
				    ll = _getLayerById(ls[i], layer_id);
				    if (ll) break;
				}
            }
            return ll;
		}
	};

    var _getLayerByLayerId = function(layer, layer_id) {
        //console.log(lr.get('title') + ': ' + lr.get("layer-id") + '; ' + layer_id);
        if (layer.get("layer-id") == layer_id) {
            return layer;
        } else if (layer instanceof ol.layer.Group) {
			var ls = layer.getLayers().getArray();
			var ll = null;
            for (var i=0; i<ls.length; i++) {
				if (ls[i].get("layer-id") == layer_id) {
					ll = ls[i];
					break;
				} else {
				    ll = _getLayerById(ls[i], layer_id);
				    if (ll) break;
				}
            }
            return ll;
		}
    };

    var _getFeature = function (options, callback) {
        var proxy = _getConfig().map.proxy;
        var url = proxy + '?url=' + options.url;

        var featureRequest = new ol.format.WFS().writeGetFeature({
            srsName: 'EPSG:' + _getMapSRID(),
            featureNS: options.featureNS,
            featurePrefix: options.featurePrefix,
            featureTypes: options.featureTypes,
            outputFormat: options.outputFormat || 'application/json',
            filter: ol.format.ogc.filter.equalTo(options.fieldFilter, options.valueFilter)
        });

        var features = null;

        $.ajax({
            type: 'POST',
            contentType: "text/xml",
            dataType: "text",
            url: url,
            data: new XMLSerializer().serializeToString(featureRequest),
            dataParams: { map: _map },
            success: function (r) {
                var data = JSON.parse(r);
                features = new ol.format.GeoJSON().readFeatures(data);
            },
            error: function (e) {
            },
            complete: function(e) {
                callback(features);
            }
        });
    };

    return {
        Init: _init,
        Load: _load,
        ShowLoading: _showLoading,
        HideLoading: _hideLoading,
        ShowPanel: _showPanel,
        ShowDirectory: _showDirectory,
        ShowEditor: _showEditor,
        setMap: _setMap,
        getMap: _getMap,
        getMapProjectionCode: _getMapProjectionCode,
        getMapSRID: _getMapSRID,
        getMapCurrentScale: _getMapCurrentScale,
        getTemporaryLayer: _getTemporaryLayer,
        getDrawtoolsLayer: _getDrawtoolsLayer,
        getFeaturesTemporaryLayer: _getFeaturesTemporaryLayer,
        getPolygonFromExtent: _getPolygonFromExtent,
        getTransformedGeometry: _getTransformedGeometry,
        getWKTFromGeometry: _getWKTFromGeometry,
        getSelectionStyles: _getSelectionStyles,
        getActiveStyles: _getActiveStyles,
        getConfig: _getConfig,
        getMapId: _getId,
        getRootLayer: _getRootLayer,
        getLayerById: _getLayerById,
        getLayerByLayerId: _getLayerByLayerId,
        getGeometryArea: _getGeometryArea,
        showLayer: _showLayer,
        getFeature: _getFeature,
        getResolutionFromScale: _getResolutionFromScale,
        getScaleFromResolution: _getScaleFromResolution
    }
}());