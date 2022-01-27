if (!Portal) {
    Portal = {};
}
if (!Portal.Viewer) {
    Portal.Viewer = {};
}

Portal.Viewer.Confrontation = (function () {

    var _modulo = 'confrontation';

	var _map;
	var _confrontationLayer;

	var _feature;
	var _real_feature;

    var drawInteractions = {};
    var drawControl;

    var _currentFilter = {
        srid: 3763,
        geomEWKT: '',
        format: ''
    }

	var _featureStyle = new ol.style.Style({
	    fill: new ol.style.Fill({
	        color: 'rgba(255, 255, 255, 0.2)'
	    }),
	    stroke: new ol.style.Stroke({
	        color: '#1b465a',
	        width: 5
	    }),
	    image: new ol.style.Circle({
	        fill: new ol.style.Fill({
	            color: '#ff0000'
	        }),
	        stroke: new ol.style.Stroke({
	            color: '#1b465a',
	            width: 5
	        }),
	        radius: 6
	    })
	});

	var _realFeatureStyle = new ol.style.Style({
	    fill: new ol.style.Fill({
	        color: 'rgba(255, 255, 255, 0.2)'
	    }),
	    stroke: new ol.style.Stroke({
	        color: 'red',
	        width: 5
	    }),
	    image: new ol.style.Circle({
	        fill: new ol.style.Fill({
	            color: '#ff0000'
	        }),
	        stroke: new ol.style.Stroke({
	            color: '#1b465a',
	            width: 5
	        }),
	        radius: 6
	    })
	});

    var _addEditToolbarButtons = function (parentId) {

        var map = Portal.Viewer.getMap();
        var layer = Portal.Viewer.getTemporaryLayer();
        var source = layer.getSource();

        var onDrawStart = function (evt) {

            var layer = Portal.Viewer.getTemporaryLayer();
            var source;

            if (layer) {
                source = layer.getSource();
                source.clear();
            }
        }
        var onDrawEnd = function (evt) {

            evt.feature.set('modulo', _modulo);

            evt.feature.setStyle(_featureStyle);

            _feature = evt.feature;
        }

        var draw = new ol.interaction.Draw({
            source: source,
            type: 'Point'
        });
        draw.on('drawstart', onDrawStart);
        draw.on('drawend', onDrawEnd);
        drawInteractions['ctrlCFTCreatePoint'] = draw;

        draw = new ol.interaction.Draw({
            source: source,
            type: 'LineString'
        });
        draw.on('drawstart', onDrawStart);
        draw.on('drawend', onDrawEnd);
        drawInteractions['ctrlCFTCreateLine'] = draw;

        draw = new ol.interaction.Draw({
            source: source,
            type: 'Polygon'
        });
        draw.on('drawstart', onDrawStart);
        draw.on('drawend', onDrawEnd);
        drawInteractions['ctrlCFTCreatePolygon'] = draw;

        drawControl = new app.genericDrawControl({
            layer: Portal.Viewer.getTemporaryLayer(),
            onEnableControl: function (evt, draw) {
                //console.log('teste');
            },
            onDisableControl: function (evt) {
                $(".btn-group[data-group='btn-geometry'] a", parentId).removeClass("active");
            }
        });
        map.addControl(drawControl);
    };


    var _init = function () {
    };

    var _load = function (parentId) {

        _addEditToolbarButtons(parentId);

        $(parentId).on('click', '.btn-group[data-group="btn-geometry"] button', function (e) {
            var activate = !$(this).hasClass("active");

            $(".btn-group[data-group='btn-geometry'] button", parentId).removeClass("active");

            if (activate) {
                $(this).addClass("active");

                var id = $(this).attr("data-button-id");

                if (id == "ctrlCFTModifyGeometry") {
                    var draw = new ol.interaction.Modify({
                        features: new ol.Collection(Portal.Viewer.getTemporaryLayer().getSource().getFeatures()),
                        //// the SHIFT key must be pressed to delete vertices, so
                        //// that new vertices can be drawn at the same position
                        //// of existing vertices
                        deleteCondition: function (event) {
                            return ol.events.condition.shiftKeyOnly(event) &&
                                ol.events.condition.singleClick(event);
                        }
                    });
                    drawControl.enableControl(e, draw);

                } else if (id == "ctrlCFTSelectGeometry") {

                    var select = new ol.interaction.Select({
                        condition: ol.events.condition.click //,
                        //filter: filterLayers,
                        //multi: options.multi,
                        //style: styles
                    });
                    drawControl.enableControl(e, select);

                    select.on('select', function(e) {
                        var layer = Portal.Viewer.getTemporaryLayer();

                        if (layer) {
                            var source = layer.getSource();

                            //source.clear();
                            var fs = source.getFeatures();
                            for (var j=fs.length-1; j>=0; j--){
                                var f = fs[j];
                                if (f.get('modulo') == this.modulo) {
                                    source.removeFeature(f);
                                }
                            }

                            if (e.target.getFeatures() && e.target.getFeatures().getLength()> 0) {

                                var features = e.target.getFeatures().getArray();

                                for (var i=0; i < features.length; i++) {
                                    var feature = features[i];

                                    //var new_feature = feature.clone();
                                    var new_feature = new ol.Feature();
                                    new_feature.setStyle(this.style);
                                    new_feature.set('modulo', this.modulo);
                                    if (feature.getGeometry() instanceof ol.geom.MultiPoint) {
                                        new_feature.setGeometry(feature.getGeometry().clone().getPoint(0));
                                    } else if (feature.getGeometry() instanceof ol.geom.MultiLineString) {
                                        new_feature.setGeometry(feature.getGeometry().clone().getLineString(0));
                                    } else if (feature.getGeometry() instanceof ol.geom.MultiPolygon) {
                                        new_feature.setGeometry(feature.getGeometry().clone().getPolygon(0));
                                    } else {
                                        new_feature.setGeometry(feature.getGeometry().clone());
                                    }

                                    source.addFeature(new_feature);
                                    _feature = new_feature;

                                    e.target.getFeatures().clear();

                                    break;
                                }
                            }
                        }
                    }, { style: _featureStyle, modulo: _modulo });
                } else {
                    drawControl.enableControl(e, drawInteractions[id]);
                }
            } else {
                drawControl.disableControl(e);
            }
        });

        $(parentId).on('click', '.btn-group button[id="btnCFTZoomGeometry"]', function (e) {
            if (_feature) {
                _map.getView().fit(ol.extent.buffer(_feature.getGeometry().getExtent(), 200), _map.getSize());
            }
        });

        $(parentId).on('click', '#btnCFTClearGeometry', function (e) {
            if (_feature) {
                var source = Portal.Viewer.getTemporaryLayer().getSource();
                source.removeFeature(_feature);
            }
            _feature = null;
        });

        $(parentId).on('click', '#btnAnalisar', function (e) {
	        e.preventDefault();

            if (drawControl) {
                drawControl.disableControl();
                $(parentId).find(".btn-group[data-group='btn-geometry'] button").removeClass("active");
            }

	        if (!_feature) {
	            var html = "<div class='alert alert-danger'>É obrigatório indicar no mapa o local de confrontação</div>"
                $("#validation", parentId).empty().html(html).show();
                return false;
	        } else {
	            $("#cftinfo", parentId).hide();
	        }


            /* Clear Form */
	        if (_confrontationLayer.getSource().clear) {
	            _confrontationLayer.getSource().clear();
	        }

	        if (_real_feature) {
	            try {
	                var source = Portal.Viewer.getTemporaryLayer().getSource();
	                source.removeFeature(_real_feature);
	            } catch (e) {}
	            _real_feature = null;
	        }

            $("#confrontation-results").empty().html("");
	        $("#validation", parentId).empty().html("");
	        /* End clear */

            var action = $(this).attr("data-action");
            var srid = 3763;

            if ($("#srid", parentId).length > 0) {
                srid = $("#srid", parentId).val();
            }

            var format = new ol.format.WKT();

            var geomEWKT = null;

            if (_feature) {
                geomEWKT = format.writeGeometry(_feature.getGeometry());
                geomEWKT = "SRID=" + Portal.Viewer.getMapSRID() + ';' + geomEWKT;
            }

	        _currentFilter = {
                srid: srid,
                geomEWKT: geomEWKT,
                buffer: $('#ctrlCFTBuffer').val() || 0,
                mapId: $('#map_id').val(),
                config: $('#ctrlCFTConfig').val() || ''
            };

            $.ajax({
                type: 'POST',
                url: action,
                traditional: true,
                data: _currentFilter,
                beforeSend: function () {
                    Portal.Viewer.ShowLoading(".menu-bar-widget.confrontation .menu-bar-body");
                },
                success: function (r) {
                    if (r.Success) {
                        $("#confrontation-results").html(r.Message);

                        // Get real geometry
                        if (r.Data && r.Data.output_geom) {
                            var _wkt = r.Data.output_geom.split(';').pop();
                            var _readOptions = {
                                dataProjection: 'EPSG:'+srid,
                                featureProjection: 'EPSG:'+Portal.Viewer.getMapSRID()
                            };
                            _real_feature = format.readFeature(_wkt, _readOptions);
                            _real_feature.setStyle(_realFeatureStyle);
                        }

                        $(".btnExportIntersectCFT", parentId).each(function () {
                            var url = $(this).data('action');
                            var format = $(this).data('format');
                            var params = $.extend({ format: format }, _currentFilter);
                            var query = $.param(params);

                            $(this).attr('href', url + '?' + query);
                        });
                    } else {
                        if (r.Data != null && r.Data.info) {
                            $("#validation", parentId).empty().html(r.Message);
                        } else {
                            /*
                            $("#informationDiv").informationModal({
                                heading: 'Informação',
                                body: r.Message,
                                messageClass: "alert alert-danger",
                                callback: null
                            });
                            */
                        }
                    }
                },
                complete: function () {
                    Portal.Viewer.HideLoading(".menu-bar-widget.confrontation .menu-bar-body");
                    //$("#tab-tools", "#sidebar").addClass("active");
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
        });


        /* Results events*/
        $(parentId).on("click", ".tree-toggler.nav-header", function (evt) {
            $(this).next().toggle();
        });

        /* Toggle real geometry */
        $(parentId).on('click', '#cftRealGeom', function (e) {
            var source = Portal.Viewer.getTemporaryLayer().getSource();
            if (this.checked) {
                 source.addFeature(_real_feature);
            } else {
                source.removeFeature(_real_feature);
            }
        });

        /* Toggle group container visibility */
        $(parentId).on('click', '.cft-toggle-group', function (e) {
            var schema = $(this).data('schema');
            var table = $(this).data('table');
            var targetId = "#cft-group-results-" + [schema, table].join('-');
            var visible = $(targetId).css('display');
            $(this).text(visible === 'none' ? '-' : '+');
            $(targetId).toggle();
        });

        /* Toggle group geometries */
        $(parentId).on('click', '.cft-toggle-group-geom', function(e) {
            var group = this;
            var schema = $(this).data('schema');
            var table = $(this).data('table');
            var targetId = "#cft-group-results-" + [schema, table].join('-');
            $(parentId).find(targetId + ' input.results-cft-geom').each(function(i, el) {
                if (group.checked && !this.checked) $(this).click();
                if (!group.checked && this.checked) $(this).click();
            });
        });

        $(parentId).on("click", ".results-cft-geom", function (e) {

            // Find feature
            var targetFeat = findConfrontationFeature(this);

            // Add / remove feature
            if (!this.checked && targetFeat) {
                _confrontationLayer.getSource().removeFeature(targetFeat);
            }
            if (this.checked && !targetFeat) {
                addConfrontationFeature(this);
            }
        });

        function findConfrontationFeature(el) {
            var targetFeat = null;
            var id = $(el).data('record-id');
            var features = _confrontationLayer.getSource().getFeatures();
            for (var i = 0; i < features.length; i++) {
                if (features[i].get('recordId') === id) targetFeat = features[i];
            }
            return targetFeat;
        }

        function addConfrontationFeature(el) {
            if ($(el).attr("data-geom") != undefined && $(el).attr("data-geom") != "") {
                var ewkt = $(el).data('geom');
                var recordId = $(el).data('record-id');
                var options = {
                    recordId: recordId
                };

                if (ewkt != null && ewkt.length > 0) {
                    var geom = Portal.Viewer.getTransformedGeometry(ewkt, Portal.Viewer.getMapProjectionCode());
                    options['geometry'] = geom;
                }

                var feature = new ol.Feature(options);
                _confrontationLayer.getSource().addFeature(feature);
            }
        }

        /*
            $(".results-cft-geom", parentId).each(function () {
                if (this.checked && $(this).attr("data-geom") != undefined && $(this).attr("data-geom") != "") {
                    var ewkt = $(this).data('geom');
                    var recordId = $(this).data('record-id');
                    var options = {
                        recordId: recordId
                    };

                    if (ewkt != null && ewkt.length > 0) {
                        var geom = Portal.Viewer.getTransformedGeometry(ewkt, Portal.Viewer.getMapProjectionCode());
                        options['geometry'] = geom;
                    }

                    var feature = new ol.Feature(options);
                    _confrontationLayer.getSource().addFeature(feature);
                }
            });
        });
        */

        /*
        $(parentId).on("click", "#chkLocal", function (e) {
            var layer = Portal.Viewer.getTemporaryLayer();

            if (!this.checked) {
                if (_feature) {
                    layer.getSource().removeFeature(_feature);
                }
            } else {
                if (_feature) {
                    layer.getSource().addFeature(_feature);
                }
            }
        });
        */

        /* End results events */
    };

	var _setMap = function (map) {

	    _map = map;

	    /* Definicão do layer para desenhar as features */

	    var layer = null;
	    var layers = _map.getLayers().getArray();

	    for (var i = 0; i < layers.length; i++) {
	        if (layers[i].get('name') == 'viewer-confrontation-layer') {
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
	            name: 'viewer-confrontation-layer',
	            group: 'vector'
	        });
	    }

	    _map.addLayer(layer);
	    _confrontationLayer = layer;

	};

    return {
        Init: _init,
        Load: _load,
        setMap: _setMap
    }
} ());