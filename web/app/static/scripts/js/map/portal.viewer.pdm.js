if (!Portal) {
    Portal = {};
}
if (!Portal.Viewer) {
    Portal.Viewer = {};
}

Portal.Viewer.PDM = (function () {

    var _modulo = 'pdm';

	var _map;
	var _pdmLayer;

	var _feature;

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
        drawInteractions['ctrlPDMCreatePoint'] = draw;

        draw = new ol.interaction.Draw({
            source: source,
            type: 'LineString'
        });
        draw.on('drawstart', onDrawStart);
        draw.on('drawend', onDrawEnd);
        drawInteractions['ctrlPDMCreateLine'] = draw;

        draw = new ol.interaction.Draw({
            source: source,
            type: 'Polygon'
        });
        draw.on('drawstart', onDrawStart);
        draw.on('drawend', onDrawEnd);
        drawInteractions['ctrlPDMCreatePolygon'] = draw;

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

        $(parentId).on('click', "#btnShowAnalisePDM",function (e) {
            $(".pdm-steps", parentId).hide();
            $("#pdm-step-1", parentId).show();
        });

        $(parentId).on("click", ".doc-group-header", function (e) {
            e.preventDefault();
            $(this).parent().next("div").toggle();
        });

        $(parentId).on('click', '.step-back', function(e) {
            e.preventDefault();

            if (drawControl) {
                drawControl.disableControl();
            }

            var target = $(this).data("step");

            if (_feature) {
                var source = Portal.Viewer.getTemporaryLayer().getSource();
                source.removeFeature(_feature);
            }
            _feature = null;

            /* Clear Form */
	        if (_pdmLayer.getSource().clear) {
	            _pdmLayer.getSource().clear();
	        }

            $("#pdm-results").empty().html("");
	        $("#validation", parentId).empty().html("");

            $(".pdm-steps", parentId).hide();
            $(target, parentId).show();
        });

        _addEditToolbarButtons(parentId);

        $(parentId).on('click', '.btn-group[data-group="btn-geometry"] button', function (e) {
            var activate = !$(this).hasClass("active");

            $(".btn-group[data-group='btn-geometry'] button", parentId).removeClass("active");

            if (activate) {
                $(this).addClass("active");

                var id = $(this).attr("data-button-id");

                if (id == "ctrlPDMModifyGeometry") {
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
                    } else if (id == "ctrlPDMSelectGeometry") {

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

        $(parentId).on('click', '.btn-group button[id="btnPDMZoomGeometry"]', function (e) {
            if (_feature) {
                _map.getView().fit(ol.extent.buffer(_feature.getGeometry().getExtent(), 200), _map.getSize());
            }
        });

        $(parentId).on('click', '#btnPDMClearGeometry', function (e) {
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
            }

	        if (!_feature) {
	            var html = "<div class='alert alert-danger'>É obrigatório indicar no mapa o local de confrontação com o PDM</div>"
                $("#validation", parentId).empty().html(html).show();

                return false;
	        }


            /* Clear Form */
	        if (_pdmLayer.getSource().clear) {
	            _pdmLayer.getSource().clear();
	        }

            $("#pdm-results").empty().html("");
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
	            };

            $.ajax({
                type: 'POST',
                url: action,
                traditional: true,
                data: {
                    srid: srid,
                    geomEWKT: geomEWKT,
                    mapId: $('#map_id').val()
                },
                beforeSend: function () {
                    Portal.Viewer.ShowLoading(".menu-bar.pdm .menu-bar-body");
                },
                success: function (r) {
                    if (r.Success) {
                        $("#pdm-results").html(r.Message);

                        $(".btnExportIntersectPDM", parentId).each(function () {
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
                    Portal.Viewer.HideLoading(".menu-bar.pdm .menu-bar-body");
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

        $(parentId).on("click", ".results-pdm-geom", function (e) {
            _pdmLayer.getSource().clear();

            $(".results-pdm-geom", parentId).each(function () {
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
                    _pdmLayer.getSource().addFeature(feature);
                }
            });
        });

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

        /* End results events */
    };

	var _setMap = function (map) {

	    _map = map;

	    /* Definicão do layer para desenhar as features */

	    var layer = null;
	    var layers = _map.getLayers().getArray();

	    for (var i = 0; i < layers.length; i++) {
	        if (layers[i].get('name') == 'viewer-pdm-layer') {
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
	            name: 'viewer-pdm-layer',
	            group: 'vector'
	        });
	    }

	    _map.addLayer(layer);
	    _pdmLayer = layer;

	};

    return {
        Init: _init,
        Load: _load,
        setMap: _setMap
    }
} ());