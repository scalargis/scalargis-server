if (!Portal) {
    Portal = {};
}
if (!Portal.Viewer) {
    Portal.Viewer = {};
}

Portal.Viewer.Print = (function () {

    var _modulo = 'print';

	var _map;
	var _printLayer;

	var _feature;

    var drawInteractions = {};
    var drawControl;

    var _currentFilter = {
    }

    var _multiGeom = false;

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

    var _paperbox_layer = new ol.layer.Vector({
        source: new ol.source.Vector(),
        style: new ol.style.Style({
            fill: new ol.style.Fill({
                color: 'rgba(255, 255, 255, 0.2)'
            }),
            stroke: new ol.style.Stroke({
                color: 'rgba(200, 200, 200, 0.8)',
                width: 5,
                lineDash: [4, 8]
            })
        }),
        name: 'paperbox-layer',
        group: 'print'
    });

    var _addEditToolbarButtons = function (parentId) {

        var map = Portal.Viewer.getMap();
        var layer = Portal.Viewer.getTemporaryLayer();
        var source = layer.getSource();

        var onDrawStart = function (evt) {
            var layer = Portal.Viewer.getTemporaryLayer();
            var multigeom = Portal.Viewer.Print.getMultiGeom();

            if (layer) {
                var source = layer.getSource();
                //source.clear();
                if (!multigeom) {
                    var fs = source.getFeatures();
                    for (var j=fs.length-1; j>=0; j--){
                        var f = fs[j];
                        if (f.get('modulo') == _modulo) {
                            source.removeFeature(f);
                        }
                    }
                }
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
        drawInteractions['ctrlPrintCreatePoint'] = draw;

        draw = new ol.interaction.Draw({
            source: source,
            type: 'LineString'
        });
        draw.on('drawstart', onDrawStart);
        draw.on('drawend', onDrawEnd);
        drawInteractions['ctrlPrintCreateLine'] = draw;

        draw = new ol.interaction.Draw({
            source: source,
            type: 'Polygon'
        });
        draw.on('drawstart', onDrawStart);
        draw.on('drawend', onDrawEnd);
        drawInteractions['ctrlPrintCreatePolygon'] = draw;

        drawControl = new app.genericDrawControl({
            layer: Portal.Viewer.getTemporaryLayer(),
            onEnableControl: function (evt, draw) {
                //console.log('teste');
            },
            onDisableControl: function (evt) {
                $(".btn-group[data-group='btn-geometry'] button", parentId).removeClass("active");
            }
        });
        map.addControl(drawControl);
    };

    var _validatePrint = function (parentId) {
        $("#validation", parentId).empty().html("").hide();

        var valid = true;
        var html = "<div class='alert alert-danger'>";

        if ($("[data-required-geom]", parentId).length > 0) {
            var layer = Portal.Viewer.getTemporaryLayer();
            var features = layer.getSource().getFeatures();

            var fts_print = $.grep(features, function(item){
                if (item.get('modulo') && item.get('modulo') == 'print') {
                    return true;
                } else {
                    return false;
                }
            });

            if (!fts_print || fts_print.length == 0 ) {
                valid = false;
                html = html + "<div>" + $("[data-required-geom]", parentId).data("required-msg") + "</div>";
            }
        }

        if ( $("#userscale", parentId).hasClass("active")) {
            var val = parseInt($("#escalaDenom", parentId).val());
            if (!val || val<500 || val>500000) { //todo: min and max in config/bd
                valid = false;
                html = html + "<div>O valor da escala definida não é correcto</div>";
            }
        }


        if ($("[data-required]", parentId).length > 0) {
            $.each($("[data-required]", parentId), function(index, item) {
                if ($(item).val() == '') {
                    valid = false;
                    html = html + "<div>" + $(item).data("required-msg") + "</div>";
                }
            });
        }

        if (!valid) {
            html = html + "</div>";
            $("#validation", parentId).empty().html(html).show();
        }

        return valid;
    };

    var _getWMSVisibleLayers = function (scale) {

        var vlayers = [];

        var _getScaleForResolution = function (map, resolution) {
            var view = map.getView();
            var units = map.getView().getProjection().getUnits();
            var dpi = 25.4 / 0.28;
            var mpu = ol.proj.METERS_PER_UNIT[units];
            var scale = resolution * mpu * 39.37 * dpi;
            return scale;
        };

        var _getResolutionForScale = function (map, scale) {
            var units = map.getView().getProjection().getUnits();
            var dpi = 25.4 / 0.28;
            var mpu = ol.proj.METERS_PER_UNIT[units];
            var inchesPerMeter = 39.37;
            var resolution = parseFloat(scale) / (mpu * inchesPerMeter * dpi);
            return resolution;
        }

        var _getLayers = function (layer, list) {
            if (layer.getVisible()) {
                if (layer instanceof ol.layer.Group) {
                    var lls = layer.getLayers().getArray();
                    for (var i=0; i<lls.length; i++) {
                        _getLayers(lls[i], list);
                    }
                } else {
                    var source = layer.getSource();
                    if (source instanceof ol.source.TileWMS || source instanceof ol.source.ImageWMS) {
                        if (source.getUrl) {
                            url = source.getUrl();
                        } else {
                            url = source.getUrls()[0];
                        }

                        var params = {};
                        var p = source.getParams()
                        for (key in p) {
                            params[key] = p[key];
                        }

                        var ldata = {
                            'url': url,
                            'params': params,
                            'opacity': layer.getOpacity(),
                            'minScale': 0,
                            'maxScale': 0
                        };

                        if (layer.getMaxResolution && layer.getMaxResolution() > 0) {
                            ldata['minScale'] = _getScaleForResolution(_map, layer.getMaxResolution());
                        }
                        if (layer.getMinResolution && layer.getMinResolution() > 0) {
                            ldata['maxScale'] = _getScaleForResolution(_map, layer.getMinResolution());
                        }

                        list.push(ldata);
                    }
                }
            }
        }

        var rootLayers = _map.getLayers().getArray();
        for (var i=0; i<rootLayers.length; i++) {
            _getLayers(rootLayers[i], vlayers);
        }

        return vlayers;
    }

    var _init = function () {
    };

    var _load = function (parentId) {

        var parentId = parentId;

        _addEditToolbarButtons(parentId);

        $(parentId).on("click", ".btn-group[data-group='btn-geometry'] button", function (e) {
            var activate = !$(this).hasClass("active");

            $(".btn-group[data-group='btn-geometry'] button", parentId).removeClass("active");

            if (activate) {
                $(this).addClass("active");

                var id = $(this).attr("data-button-id");

                var multigeom = $(this).closest('div.btn-toolbar.geometry-buttons').data('multi-geom');
                if (multigeom == '1') {
                    Portal.Viewer.Print.setMultiGeom(true);
                } else {
                    Portal.Viewer.Print.setMultiGeom(false);
                }

                if (id == "ctrlPrintModifyGeometry") {
                    var featcol = [];
                    Portal.Viewer.getTemporaryLayer().getSource().getFeatures().forEach(function (f) {
                        if (f.get('modulo') == _modulo) {
                            featcol.push(f);
                        }
                    });
                    var draw = new ol.interaction.Modify({
                        features: new ol.Collection(featcol),
                        //// the SHIFT key must be pressed to delete vertices, so
                        //// that new vertices can be drawn at the same position
                        //// of existing vertices
                        deleteCondition: function (event) {
                            return ol.events.condition.shiftKeyOnly(event) &&
                                ol.events.condition.singleClick(event);
                        }
                    });
                    drawControl.enableControl(e, draw);
                } else if (id == "ctrlPrintSelectGeometry") {

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
                            var multigeom = Portal.Viewer.Print.getMultiGeom();
                            if (!multigeom) {
                                for (var j=fs.length-1; j>=0; j--){
                                    var f = fs[j];
                                    if (f.get('modulo') == this.modulo) {
                                        source.removeFeature(f);
                                    }
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

                                    new_feature.setGeometry(feature.getGeometry().clone());

                                    source.addFeature(new_feature);

                                    Portal.Viewer.Print.setFeature(new_feature);

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

        $(parentId).on("click", ".btn-group button[id='btnPrintZoomGeometry']", function (e) {
            var extent = null;
            if (_multiGeom) {
                var layer = Portal.Viewer.getTemporaryLayer();
                var source = layer.getSource();
                var fs = source.getFeatures();
                for (var j = 0; j < fs.length; j++){
                    var f = fs[j];
                    if (f.get('modulo') == _modulo) {
                        if (extent) {
                            extent = ol.extent.extend(extent, f.getGeometry().getExtent());
                        } else {
                            extent = f.getGeometry().getExtent();
                        }
                    }
                }
            } else {
                if (_feature) {
                    extent = _feature.getGeometry().getExtent();
                }
            }
            if (extent) {
                _map.getView().fit(ol.extent.buffer(extent, 200), _map.getSize());
            }
        });

        $(parentId).on("click", "#btnPrintClearGeometry", function () {
            if (_multiGeom) {
                var layer = Portal.Viewer.getTemporaryLayer();
                var source = layer.getSource();
                var fs = source.getFeatures();
                for (var j=fs.length-1; j>=0; j--){
                    var f = fs[j];
                    if (f.get('modulo') == _modulo) {
                        source.removeFeature(f);
                    }
                }
            } else {
                if (_feature) {
                    var source = Portal.Viewer.getTemporaryLayer().getSource();
                    source.removeFeature(_feature);
                }
            }
            _feature = null;
        });

        $(parentId).on("click", "#btnPrintGrupo", { parentId: parentId }, function (e) {

            var action = $(this).data("action");
            var id = $(this).data("id");
            var geom_filter = null;

            var parentId = e.data.parentId;

            if (drawControl) {
                drawControl.disableControl();
            }

            if (!_validatePrint(parentId)) {
                return false;
            }

            var layer = Portal.Viewer.getTemporaryLayer();
            var features = layer.getSource().getFeatures();
            var fts_print = $.grep(features, function(item){
                if (item.get('modulo') && item.get('modulo') == 'print') {
                    return true;
                } else {
                    return false;
                }
            });
            if (fts_print && fts_print.length > 0 ) {
                /*
                var geomWKT = "EPSG=" + Portal.Viewer.getMapSRID() + ";" + Portal.Viewer.getWKTFromGeometry(features[0].getGeometry());
                var geom = Portal.Viewer.getTransformedGeometry(geomWKT, "EPSG:4326");
                geom_filter = Portal.Viewer.getWKTFromGeometry(geom);
                */
                geom_filter = [];
                for (j=0;j<fts_print.length;j++) {
                    geom_filter.push(Portal.Viewer.getWKTFromGeometry(fts_print[j].getGeometry()));
                }
                //geom_filter = Portal.Viewer.getWKTFromGeometry(fts_print[0].getGeometry());
            }

            var layout = $("#layout", parentId).val();

            $.ajax({
                type: 'POST',
                url: action,
                //traditional: true,
                data: {
                    id: id,
                    layout: layout,
                    geom_filter: geom_filter,
                    geom_srid: Portal.Viewer.getMapSRID(),
                    mapa_id: $('#map_id').val()
                },
                beforeSend: function () {
                    Portal.Viewer.ShowLoading(".menu-bar-widget.print .menu-bar-body");
                },
                success: function (r) {
                    if (r.Success) {
                        $("#print-step-2", parentId).empty().html(r.Message);

                        $(".print-steps", parentId).hide();
                        $("#print-step-2", parentId).show();

                        /*
                        $("#pdm-results").html(r.Message);

                        $(".btnExportIntersectPDM", parentId).each(function () {
                            var url = $(this).data('action');
                            var format = $(this).data('format');

                            var params = $.extend({ format: format }, _currentFilter);
                            var query = $.param(params);

                            $(this).attr('href', url + '?' + query);
                        });
                        */
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
                    Portal.Viewer.HideLoading(".menu-bar-widget.print .menu-bar-body");
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

        $(".planta-row-title a", parentId).click({ parentId: parentId }, function (e) {
            e.preventDefault();

            var parentId = e.data.parentId;

            var action = $(this).data("action");
            var mapa_id = $(this).data("mapa-id");
            var id = $(this).data("id");

            if (id == "") {
                $(".print-steps", parentId).hide();
                $("#print-step-0", parentId).show();

                return false;
            }

            $.ajax({
                type: 'POST',
                url: action,
                traditional: true,
                data: {
                    mapa_id: mapa_id,
                    id: id
                },
                beforeSend: function () {
                    Portal.Viewer.ShowLoading(".menu-bar-widget.print .menu-bar-body");
                },
                success: function (r) {
                    if (r.Success) {
                        $("#print-step-1", parentId).empty().html(r.Message);

                        $(".print-steps", parentId).hide();
                        $("#print-step-1", parentId).show();
                    } else {
                        if (r.Data != null && r.Data.info) {
                            $("#validation", parentId).empty().html(r.Message);
                        } else {
                            //TODO
                        }
                    }
                },
                complete: function () {
                    Portal.Viewer.HideLoading(".menu-bar-widget.print .menu-bar-body");
                },
                error: function (r) {
                    //TODO
                }
            });

        });

        $(parentId).on("click", ".step-back", { parentId: parentId }, function (e) {
            e.preventDefault();

            if (drawControl) {
                drawControl.disableControl();
            }

            var parentId = e.data.parentId;
            var target = $(this).data("step");
            var clear = $(this).data("step-clear-back");
            var currentStep = $(this).closest('.print-steps');

            $(".print-steps", parentId).hide();
            $(target, parentId).show();

            if (clear && currentStep.length > 0) {
                currentStep.find('*').off();
                currentStep.empty().html('');
            }
        });

        $(parentId).on("click", ".select-all", { parentId: parentId, map: _map, feature: _feature }, function (e) {
            e.preventDefault();
            $(".print-list span.icon", parentId).removeClass('unchecked-icon').addClass('checked-icon');
            return false;
        });

        $(parentId).on("click", ".unselect-all", { parentId: parentId, map: _map, feature: _feature }, function (e) {
            e.preventDefault();
            $(".print-list span.icon", parentId).removeClass('checked-icon').addClass('unchecked-icon');
            return false;
        });

        $(parentId).on("click", ".print-list span.icon", { parentId: parentId, map: _map, feature: _feature }, function (e) {
            if ($(this).hasClass('checked-icon')) {
                $(this).removeClass('checked-icon').addClass('unchecked-icon');
                //$('li>span.icon', this.parentElement).removeClass('checked-icon').addClass('unchecked-icon');
            } else {
                $(this).removeClass('unchecked-icon').addClass('checked-icon');
                /*
                $('li>span.icon', this.parentElement).removeClass('unchecked-icon').addClass('checked-icon');
                $.each($($(this.parentElement).parents('ul>li'), '.print-list'), function (key, value) {
                    $(this).children('span.icon').first().removeClass('unchecked-icon').addClass('checked-icon');
                })
                */
            }
        });

        $(parentId).on("click", ".print-single", { parentId: parentId, map: _map, feature: _feature }, function (e) {
            e.preventDefault();

            if (drawControl) {
                drawControl.disableControl();
            }

            if (!_validatePrint(parentId)) {
                return false;
            }

            var prints = [];

            var print = {
                'id': $(this).data("id"),
                'name': $(this).data("titulo"),
                'codigo': $(this).data("codigo"),
                'tipo_id': $(this).data("tipo-id"),
                'grupo_id': $(this).data("grupo-id"),
                'layout': $("#layout", e.data.parentId).val(),
                'srid': $(this).data("srid"),
                'url': $(this).data('url')
            }

            prints.push(print);

            var action = $(this).data('action');
            var data = { 'prints': prints };
            var step = $(this).data('step');
            var target = $(this).data('target');

            $.ajax({
                type: 'POST',
                dataType: 'json',
                contentType: "application/json; charset=utf-8",
                url: action,
                data: JSON.stringify(data),
                dataParams: { 'step': step, 'target': target },
                beforeSend: function () {
                    Portal.Viewer.ShowLoading(".menu-bar-widget.print .menu-bar-body");
                },
                success: function (r) {
                    if (r.Success) {
                        $(this.dataParams.target, parentId).empty().html(r.Message);
                        $(this.dataParams.target + " .step-back", parentId).data('step', this.dataParams.step);

                        $(this.dataParams.step, parentId).hide();
                        $(this.dataParams.target, parentId).show();

                        var prints = r.Data.prints;

                        var def = $.Deferred();
                        var deferreds = [];

                        var getCurrentScale = function () {
                            //var map = this.getMap();
                            var view = map.getView(); ;
                            var resolution = view.getResolution();
                            var units = map.getView().getProjection().getUnits();
                            var dpi = 25.4 / 0.28;
                            var mpu = ol.proj.METERS_PER_UNIT[units];
                            var scale = resolution * mpu * 39.37 * dpi;
                            return scale;
                        };

                        var opts = {};

                        opts["mapa_id"] = $('#map_id').val();

                        opts["nif"] = $("#nif", parentId).val();
                        opts["nome"] = $("#nome", parentId).val();
                        opts["morada"] = $("#morada", parentId).val();
                        opts["codpostal"] = $("#codpostal", parentId).val();
                        opts["local"] = $("#local", parentId).val();

                        opts["titulo"] = $("#titulo", parentId).val();
                        opts["escala"] = Math.round(getCurrentScale());
                        opts["finalidade_emissao"] = $("#finalidadeEmissao", parentId).val();
                        opts["guia_pagamento"] = $("#guiaPagamento", parentId).val();


                        if ($("#userscale", parentId).hasClass("active")) {
                            opts["userScale"] = $('#escalaDenom', parentId).val();
                        }

                        if ( $("#predefscale", parentId).hasClass("active")) {
                            var escalaPredef = $("#escalaPredef", parentId).val();
                            if (escalaPredef) {escalaPredef = escalaPredef.split(":")[1].trim()}
                            opts["userScale"] = escalaPredef;
                        }

                        // loop layout widgets
                        var widget_layout_list = [];
                        var widget_layout = {}
                        $('.widget_layout').each(function(i, obj) {
                        widget_layout["codigo"] = $(this).attr('id');
                        widget_layout["type"] = $(this).attr('type');
                        if ($(this).attr('type') == "checkbox"){
                            widget_layout["value"] = $(this).is(':checked')
                        }
                        widget_layout_list.push(widget_layout)
                        });
                        opts["widget_layout_list"] = JSON.stringify(widget_layout_list);


                        var extent = map.getView().calculateExtent(map.getSize());
                        var geomExtent = Portal.Viewer.getPolygonFromExtent(extent.join(' '));

                        var layer = Portal.Viewer.getTemporaryLayer();
                        var features = [];
                        var fs = layer.getSource().getFeatures();
                        for (var i=0;i<fs.length;i++){
                            var f = fs[i];
                            if (f.get('modulo') == _modulo) {
                                features.push(f);
                            }
                        }

                        var wmslayers = _getWMSVisibleLayers();
                        var lls = [];
                        for (i=0;i<wmslayers.length;i++) {
                            var l = wmslayers[i];
                            lls.push('wms' + ';' + l.url + ';' + l.params.LAYERS + ';' + l.opacity + ';' + l.minScale+ ';' + l.maxScale + ';' + (l.params.CQL_FILTER || '') + ';' + (l.params.STYLES || l.params.STYLE || ''));
                        }

                        for (var i=0;i<prints.length;i++) {
                            var prt = prints[i];

                            opts["plantaId"] = prt['id'];
                            opts["tipoId"] = prt['tipo_id'];
                            opts["grupoId"] = prt['grupo_id'];
                            opts["layout"] = prt['layout'];
                            opts["srid"] = prt['srid'];
                            opts["layers"] = lls;

                            if ((opts["srid"] || '') != '') {
                                var extentWKT = "EPSG=" + Portal.Viewer.getMapSRID() + ";" + Portal.Viewer.getWKTFromGeometry(geomExtent);
                                var geom_extent = Portal.Viewer.getTransformedGeometry(extentWKT, "EPSG:" + opts["srid"]);
                                opts["extentWKT"] = Portal.Viewer.getWKTFromGeometry(geom_extent);
                            } else {
                                opts["extentWKT"] = Portal.Viewer.getWKTFromGeometry(geomExtent);
                            }

                            if (features && features.length > 0 ) {
                                var features_print = [];
                                for(var j=0; j < features.length; j++) {
                                    var geom = features[j].getGeometry();
                                    if ((opts["srid"] || '') != '') {
                                        var geomWKT = "EPSG=" + Portal.Viewer.getMapSRID() + ";" + Portal.Viewer.getWKTFromGeometry(geom);
                                        geom = Portal.Viewer.getTransformedGeometry(geomWKT, "EPSG:" + opts["srid"]);
                                    }
                                    features_print.push(Portal.Viewer.getWKTFromGeometry(geom));
                                }
                                opts["geomWKT"] = features_print;
                            }

                            if(Portal.Viewer.DrawTools) {
                               opts["features"] = Portal.Viewer.DrawTools.getFeaturesAsGeoJSON( "EPSG:" + opts["srid"]);
                            }

                            var ajax = null;
                            var ajax_data = {
                                url: prt['url'],
                                method: 'post',
                                data: opts,
                                dataParams:  this.dataParams,
                                dataType: 'json',
                                plantaId: prt['id']
                            };

                            ajax = $.ajax(ajax_data).then(function(res){
                                return { result: res, request: this};
                            }).fail(function(res){
                                return { result: res };
                            });

                            if (ajax) {
                                // Push promise to 'deferreds' array
                                deferreds.push(ajax);
                            }
                        };

                        // get a hook on when all of the promises resolve, some fulfill
                        // this is reusable, you can use this whenever you need to hook on some promises
                        // fulfilling but all resolving.
                        function execute_requests(promises, dataParams){
                            var d = $.Deferred(), results = [];
                            var remaining = promises.length;
                            for(var i = 0; i < promises.length; i++){
                                promises[i].then(function(res){
                                    var data = res.result.Data || {};
                                    results.push({
                                        status: 'success',
                                        result: 'resultado success',
                                        data: data,
                                        dataParams: res.request.dataParams
                                    }); // on success, add to results

                                    var e = $('div[data-id=' + data.planta_id + '] i', res.request.dataParams.target);
                                    if (e.length > 0) { e.attr('class', 'fa fa-check'); }
                                    var link = $('div[data-id=' + data.planta_id + ']', res.request.dataParams.target);
                                    if (link.length > 0) {
                                        var html = '<a href="' + data.url + '" data-file="' + data.filename + '" target="_blank" class="open-print-file" title="Abrir planta">';
                                        html = html + ' abrir <span class="fa fa-external-link-alt" aria-hidden="true"></span>';
                                        html = html + '</a>'
                                        link.append(html);
                                    }
                                }).fail(function(jqXHR, textStatus, errorThrown) {
                                    results.push({
                                        status: 'error',
                                        result: 'resultado fail',
                                        data: null,
                                        dataParams: this.dataParams
                                    }); // on fail, add to results

                                    var e = $('div[data-id=' + this.plantaId + '] i', this.dataParams.target);
                                    if (e.length > 0) { e.attr('class', 'fa fa-exclamation-triangle'); }
                                }).always(function(res){
                                    remaining--; // always mark as finished
                                    if(!remaining) d.resolve(results, dataParams);
                                });
                            }
                            return d.promise(); // return a promise on the remaining values
                        }

                        execute_requests(deferreds, this.dataParams).then(function(results, dataParams){
                            var html = '';
                            var errors = false;

                            for(var i = 0; i < results.length; i++) {
                                var r = results[i];

                                if (!r.status == 'success') {
                                    errors = true;
                                }
                            }

                            if (errors) {
                                $(dataParams.target + ' .alert', parentId).removeClass('alert-info').
                                    addClass('alert-error').html('Não foi possível gerar a planta');
                            } else {
                                $(dataParams.target + ' .alert', parentId).removeClass('alert-info').
                                    addClass('alert-success').html('Planta gerada. Clique em abrir para descarregar a planta.');
                            }
                        });
                    } else {
                        if (r.Data != null && r.Data.info) {
                            //TODO
                        } else {
                            //TODO
                        }
                    }
                },
                complete: function () {
                    Portal.Viewer.HideLoading(".menu-bar-widget.print .menu-bar-body");
                },
                error: function (r) {
                    //TODO
                }
            });

        });

        $(parentId).on("click", ".print-batch", { parentId: parentId, map: _map, feature: _feature }, function (e) {
            e.preventDefault();

            //var elems = $('#batch-print-list input[data-id]:checked' ,e.data.parentId);
            var elems = $('#batch-print-list span[data-id].checked-icon' ,e.data.parentId);

            var prints = [];

            var layout = $('#layout', e.data.parentId).val() || '';

            for (var i=0; i < elems.length; i++) {
                var print = {
                    'id': $(elems[i]).data('id'),
                    'name': $(elems[i]).data('name'),
                    'codigo': $(elems[i]).data('codigo'),
                    'tipo_id': $(elems[i]).data('tipo-id'),
                    'grupo_id': $(elems[i]).data('grupo-id'),
                    'srid': $(elems[i]).data("srid"),
                    'layout': layout,
                    'url': $(elems[i]).data('action')
                }

                //var id = $(elems[i]).data('id');
                //prints.push(id);
                prints.push(print);
            }

            //Exit if nothing selected
            if (prints.length == 0) {
                return false;
            }

            var agruparPlantas = ($(this).data('agruparPlantas') || '').toLowerCase() == 'true';

            var action = $(this).data('action');
            var data = { 'agruparPlantas': agruparPlantas, 'prints': prints };
            var step = $(this).data('step');
            var target = $(this).data('target');

            $.ajax({
                type: 'POST',
                dataType: 'json',
                contentType: "application/json; charset=utf-8",
                url: action,
                data: JSON.stringify(data),
                dataParams: { 'step': step, 'target': target },
                beforeSend: function () {
                    Portal.Viewer.ShowLoading(".menu-bar-widget.print .menu-bar-body");
                },
                success: function (r) {
                    if (r.Success) {

                        $(this.dataParams.target, parentId).empty().html(r.Message);
                        $(this.dataParams.target + " .step-back", parentId).data('step', this.dataParams.step);

                        $(this.dataParams.step, parentId).hide();
                        $(this.dataParams.target, parentId).show();

                        var prints = r.Data.prints;

                        var def = $.Deferred();
                        var deferreds = [];

                        var getCurrentScale = function () {
                            //var map = this.getMap();
                            var view = map.getView(); ;
                            var resolution = view.getResolution();
                            var units = map.getView().getProjection().getUnits();
                            var dpi = 25.4 / 0.28;
                            var mpu = ol.proj.METERS_PER_UNIT[units];
                            var scale = resolution * mpu * 39.37 * dpi;
                            return scale;
                        };

                        var opts = {};

                        opts["mapa_id"] = $('#map_id').val();

                        opts["nif"] = $("#nif", parentId).val();
                        opts["nome"] = $("#nome", parentId).val();
                        opts["morada"] = $("#morada", parentId).val();
                        opts["codpostal"] = $("#codpostal", parentId).val();
                        opts["local"] = $("#local", parentId).val();

                        opts["titulo"] = $("#titulo", parentId).val();
                        opts["escala"] = Math.round(getCurrentScale());
                        opts["finalidade_emissao"] = $("#finalidadeEmissao", parentId).val();
                        opts["guia_pagamento"] = $("#guiaPagamento", parentId).val();

                        if ($("#userscale", parentId).hasClass("active")) {
                            opts["userScale"] = $('#escalaDenom', parentId).val();
                        }

                        // loop layout widgets
                        var widget_layout_list = [];
                        var widget_layout = {}
                        $('.widget_layout').each(function(i, obj) {
                        widget_layout["codigo"] = $(this).attr('id');
                        widget_layout["type"] = $(this).attr('type');
                        if ($(this).attr('type') == "checkbox"){
                            widget_layout["value"] = $(this).is(':checked')
                        }
                        widget_layout_list.push(widget_layout)
                        });
                        opts["widget_layout_list"] = JSON.stringify(widget_layout_list);

                        if ( $("#predefscale", parentId).hasClass("active")) {
                            var escalaPredef = $("#escalaPredef", parentId).val();
                            if (escalaPredef) {escalaPredef = escalaPredef.split(":")[1].trim()}
                            opts["userScale"] = escalaPredef;
                        }
                        var extent = map.getView().calculateExtent(map.getSize());
                        var geomExtent = Portal.Viewer.getPolygonFromExtent(extent.join(' '));

                        var layer = Portal.Viewer.getTemporaryLayer();
                        var features = [];
                        var fs = layer.getSource().getFeatures();
                        for (var i=0;i<fs.length;i++){
                            var f = fs[i];
                            if (f.get('modulo') == _modulo) {
                                features.push(f);
                            }
                        }

                        for (var i=0;i<prints.length;i++) {
                            var prt = prints[i];

                            opts["plantaId"] = prt['id'];
                            opts["tipoId"] = prt['tipo_id'];
                            opts["grupoId"] = prt['grupo_id'];
                            opts["srid"] = prt['srid'];
                            opts["layout"] = prt['layout'];

                            /*
                            if ((opts["srid"] || '') != '') {
                                var extentWKT = "EPSG=" + Portal.Viewer.getMapSRID() + ";" + Portal.Viewer.getWKTFromGeometry(geomExtent);
                                var geom_extent = Portal.Viewer.getTransformedGeometry(extentWKT, "EPSG:" + opts["srid"]);
                                opts["extentWKT"] = Portal.Viewer.getWKTFromGeometry(geom_extent);
                            } else {
                                opts["extentWKT"] = Portal.Viewer.getWKTFromGeometry(geomExtent);
                            }

                            if (features && features.length > 0 ) {
                                if ((opts["srid"] || '') != '') {
                                    var geomWKT = "EPSG=" + Portal.Viewer.getMapSRID() + ";" + Portal.Viewer.getWKTFromGeometry(features[0].getGeometry());
                                    var geom = Portal.Viewer.getTransformedGeometry(geomWKT, "EPSG:" + opts["srid"]);
                                    opts["geomWKT"] = Portal.Viewer.getWKTFromGeometry(geom);
                                } else {
                                    opts["geomWKT"] = Portal.Viewer.getWKTFromGeometry(features[0].getGeometry());
                                }
                            }
                            */
                            if ((opts["srid"] || '') != '') {
                                var extentWKT = "EPSG=" + Portal.Viewer.getMapSRID() + ";" + Portal.Viewer.getWKTFromGeometry(geomExtent);
                                var geom_extent = Portal.Viewer.getTransformedGeometry(extentWKT, "EPSG:" + opts["srid"]);
                                opts["extentWKT"] = Portal.Viewer.getWKTFromGeometry(geom_extent);
                            } else {
                                opts["extentWKT"] = Portal.Viewer.getWKTFromGeometry(geomExtent);
                            }

                            if (features && features.length > 0 ) {
                                var features_print = [];
                                for(var j=0; j < features.length; j++) {
                                    var geom = features[j].getGeometry();
                                    if ((opts["srid"] || '') != '') {
                                        var geomWKT = "EPSG=" + Portal.Viewer.getMapSRID() + ";" + Portal.Viewer.getWKTFromGeometry(geom);
                                        geom = Portal.Viewer.getTransformedGeometry(geomWKT, "EPSG:" + opts["srid"]);
                                    }
                                    features_print.push(Portal.Viewer.getWKTFromGeometry(geom));
                                }
                                opts["geomWKT"] = features_print;
                            }

                            var ajax = null;
                            var ajax_data = {
                                url: prt['url'],
                                method: 'post',
                                data: opts,
                                dataParams:  this.dataParams,
                                dataType: 'json',
                                plantaId: prt['id']
                            };

                            ajax = $.ajax(ajax_data).then(function(res){
                                return { result: res, request: this};
                            }).fail(function(res){
                                return { result: res };
                            });

                            if (ajax) {
                                // Push promise to 'deferreds' array
                                deferreds.push(ajax);
                            }
                        };

                        // get a hook on when all of the promises resolve, some fulfill
                        // this is reusable, you can use this whenever you need to hook on some promises
                        // fulfilling but all resolving.
                        function execute_requests(promises, dataParams){
                            var d = $.Deferred(), results = [];
                            var remaining = promises.length;
                            for(var i = 0; i < promises.length; i++){
                                promises[i].then(function(res){
                                    var data = res.result.Data || {};
                                    results.push({
                                        status: 'success',
                                        result: 'resultado success',
                                        data: data,
                                        dataParams: res.request.dataParams
                                    }); // on success, add to results

                                    var e = $('div[data-id=' + data.planta_id + '] i', res.request.dataParams.target);
                                    if (e.length > 0) { e.attr('class', 'fa fa-check'); }
                                    var link = $('div[data-id=' + data.planta_id + ']', res.request.dataParams.target);
                                    /*
                                    var e = $('div[data-id=' + data.planta_id + '] i','#print-step-3');
                                    if (e.length > 0) { e.attr('class', 'fa fa-check'); }
                                    var link = $('div[data-id=' + data.planta_id + ']','#print-step-3');
                                    */
                                    if (link.length > 0 ) {
                                        if (link.data('download')) {
                                            var html = '<a href="' + data.url + '" data-file="' + data.filename + '" target="_blank" class="open-print-file" title="Abrir planta">';
                                            html = html + ' abrir <span class="fa fa-external-link-alt" aria-hidden="true"></span>';
                                            html = html + '</a>'
                                            link.append(html);
                                        } else {
                                            var html = '<a href="' + data.url + '" data-file="' + data.filename + '" target="_blank" class="open-print-file hidden" />';
                                            link.append(html);
                                        }
                                    }
                                }).fail(function(jqXHR, textStatus, errorThrown) {
                                    results.push({
                                        status: 'error',
                                        result: 'resultado fail',
                                        data: null,
                                        dataParams: this.dataParams
                                    }); // on fail, add to results

                                    var e = $('div[data-id=' + this.plantaId + '] i', this.dataParams.target);
                                    /*
                                    var e = $('div[data-id=' + this.plantaId + '] i','#print-step-3');
                                    */
                                    if (e.length > 0) { e.attr('class', 'fa fa-exclamation-triangle'); }
                                }).always(function(res){
                                    remaining--; // always mark as finished
                                    if(!remaining) d.resolve(results, dataParams);
                                });
                            }
                            return d.promise(); // return a promise on the remaining values
                        }

                        execute_requests(deferreds, this.dataParams).then(function(results, dataParams){
                            var html = '';
                            var errors = false;
                            var downloads = false;
                            var files = [];

                            for(var i = 0; i < results.length; i++) {
                                var r = results[i];

                                if (r.status == 'success') {
                                    downloads = true;
                                    files.push(r.data.filename);
                                } else {
                                    errors = true;
                                }
                            }

                            if (errors && !downloads) {
                                //$('#print-step-3 .alert', parentId).removeClass('alert-info').
                                $(dataParams.target + ' .alert', parentId).removeClass('alert-info').
                                    addClass('alert-error').html('Não foi possível gerar as plantas');
                            } if (errors && downloads) {
                               // $('#print-step-3 .alert', parentId).removeClass('alert-info').
                               $(dataParams.target + ' .alert', parentId).removeClass('alert-info').
                                    addClass('alert-warning').html('Não foi possível gerar todas as plantas. Pode descarregar as plantas disponíveis.');
                            } else {
                                //$('#print-step-3 .alert', parentId).removeClass('alert-info').
                                $(dataParams.target + ' .alert', parentId).removeClass('alert-info').
                                    addClass('alert-success').html('Plantas geradas. Pode descarregar as plantas pretendidas.');
                            }

                            if (files.length > 1) {
                                //$('#print-step-3 .download-all', parentId).removeClass('hidden');
                                $(dataParams.target + ' .download-all', parentId).removeClass('hidden');
                            }

                        });


                    } else {
                        if (r.Data != null && r.Data.info) {
                            //$("#validation", parentId).empty().html(r.Message);
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
                    Portal.Viewer.HideLoading(".menu-bar-widget.print .menu-bar-body");
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

        $(parentId).on("click", ".print-download-all", { parentId: parentId, map: _map, feature: _feature }, function (e) {
            var action = $(this).data('action');
            var download = $(this).data('download') || false;

            var files = [];
            $('a.open-print-file', parentId).each(function () {
              files.push($(this).data("file"));
            });

            var data = {
                mapId: $('#map_id').val(),
                files: files
            }

            $.ajax({
                type: 'POST',
                dataType: 'json',
                contentType: "application/json; charset=utf-8",
                url: action,
                data: JSON.stringify(data),
                beforeSend: function () {
                    Portal.Viewer.ShowLoading(".menu-bar-widget.print .menu-bar-body");
                },
                success: function (r) {
                    if (r.Success) {
                        if (download) {
                            window.open(r.Data.url, 'Download');
                        } else {
                            $(".download-all", parentId).empty().html();
                            $(".download-all", parentId).remove();

                            var html = '<div style="padding: 15px; margin-bottom: 10px;"><a href="' + r.Data.url + '" target="_blank" class="open-print-file" title="Abrir PDF com todas as plantas">';
                            html = html + ' Abrir PDF com todas as plantas <span class="fa fa-external-link-alt" aria-hidden="true"></span>';
                            html = html + '</a></div>';
                            $("#print-step-3").append(html);
                        }
                    } else {

                    }
                },
                complete: function () {
                    Portal.Viewer.HideLoading(".menu-bar-widget.print .menu-bar-body");
                },
                error: function (r) {
                }
            });
        });

        $('.menu-bar-widget.print').bind('onRemoveClassOpen',function() {
            if (!$(this).hasClass('open') && drawControl) {
                drawControl.disableControl();
            }
        });


        $(parentId).on("click", "#btnShowPrintPaperBox", function (e) {
            draw_paperbox();
        });

        $(parentId).on("change", "#predefscale", function (e) {
            draw_paperbox();
        });
        $(parentId).on("change", "#layout", function (e) {
            draw_paperbox();
        });
        $(parentId).on("input", "#escalaDenom", function (e) {
            draw_paperbox();
        });
        $(parentId).on("click", "#mapscale", function (e) {
            draw_paperbox();
        });
        $(parentId).on('shown.bs.tab', function (e) {
          draw_paperbox();
        });
        $(parentId).on("input", "#ckbox_view_paper", function (e) {
            draw_paperbox();
        });

        $(parentId).on("click", "#btnVoltar", function (e) {
            _paperbox_layer.getSource().clear();
        });

        var map = Portal.Viewer.getMap();
        map.on('moveend', function (e) {
            if (!$('#ckbox_view_paper', parentId).prop('checked')  ||
                $('#ckbox_view_paper', parentId).prop('checked') == 0){return}
            if ( $("#mapscale", parentId).hasClass("active") || !(_feature)) {
            setTimeout(function(){ draw_paperbox(); }, 100);
            }
        });

        var tlayer = Portal.Viewer.getTemporaryLayer();
        tlayer.getSource().on( 'addfeature', function (ft) {
            setTimeout(function(){ draw_paperbox(); }, 100);
        });
        tlayer.getSource().on( 'removefeature', function (ft) {
            setTimeout(function(){ draw_paperbox(); }, 100);
        });
        tlayer.getSource().on( 'changefeature', function (ft) {
            setTimeout(function(){ draw_paperbox();}, 100);
        });

        var draw_paperbox = function () {

            _paperbox_layer.getSource().clear();
            if ($('#ckbox_view_paper', parentId).prop('checked') == 0){return}

            var scale;
            if ($("#userscale", parentId).hasClass("active")) {
                scale = $('#escalaDenom', parentId).val();
            }
            else if ( $("#predefscale", parentId).hasClass("active")) {
                var escalaPredef = $("#escalaPredef", parentId).val();
                if (escalaPredef) {escalaPredef = escalaPredef.split(":")[1].trim()}
                scale = escalaPredef;
            }
            else {
                var view = _map.getView(); ;
                var resolution = view.getResolution();
                var units = _map.getView().getProjection().getUnits();
                var dpi = 25.4 / 0.28;
                var mpu = ol.proj.METERS_PER_UNIT[units];
                var scale = resolution * mpu * 39.37 * dpi;
            }

            var layout = $("#layout", parentId).val();
            if (layout == null) {return null}
            var layout_size = layout.split("|")[0];
            var layout_format = layout.split("|")[1];

            if (_multiGeom || _feature) {
                var geom_extent = null;
                if (_multiGeom) {
                    var layer = Portal.Viewer.getTemporaryLayer();
                    var source = layer.getSource();
                    var fs = source.getFeatures();
                    for (var j = 0; j < fs.length; j++){
                        var f = fs[j];
                        if (f.get('modulo') == _modulo) {
                            if (geom_extent) {
                                geom_extent= ol.extent.extend(geom_extent, f.getGeometry().getExtent());
                            } else {
                                geom_extent = f.getGeometry().getExtent();
                            }
                        }
                    }
                } else {
                    if (_feature) {
                        geom_extent = _feature.getGeometry().getExtent();
                    }
                }
                if (geom_extent) {
                    var center_x = geom_extent[0] + (geom_extent[2]-geom_extent[0])/2;
                    var center_y = geom_extent[1] + (geom_extent[3]-geom_extent[1])/2;
                } else {
                    var center_x = map.getView().getCenter()[0];
                    var center_y = map.getView().getCenter()[1];
                }
            } else {
                var center_x = map.getView().getCenter()[0];
                var center_y = map.getView().getCenter()[1];
            }

            var magic = 22;
            var units = "meter"; // TODO: get this from app ?
            if (units == 'meter'){
                var inch_per_units = 39.37
            } else if (units == 'degree') {
                var inch_per_units = 4374754
            }  else {
                console.log("Units not supported... are you on the moon ?");
                return null;
            }

            var layout_map_sizes_for_preview = JSON.parse($('#ckbox_view_paper', parentId).attr('layout_map_sizes_for_preview').replace(/'/g, '"'))
            for (l in layout_map_sizes_for_preview){
                if(layout_map_sizes_for_preview[l].format == layout){
                img_w = layout_map_sizes_for_preview[l].w;
                img_h = layout_map_sizes_for_preview[l].h;
                }
            }

            var res = 1 / ((1 / scale) * inch_per_units * magic);
            var half_w = (img_w * res) / 2;
            var half_h = (img_h * res) / 2;
            var xmin = center_x - half_w;
            var ymin = center_y - half_h;
            var xmax = center_x + half_w;
            var ymax = center_y + half_h;

            var corners_pts = [[
                [xmin,ymin],
                [xmin,ymax],
                [xmax,ymax],
                [xmax,ymin],
                [xmin,ymin] // closing if be used as print polygon...
            ]]

            var paperbox = new ol.geom.Polygon(corners_pts);
            var paperbox_Feature = new ol.Feature(paperbox);

            _paperbox_layer.getSource().addFeature(paperbox_Feature);

        }


    };

	var _setMap = function (map) {

	    _map = map;

	    /* Definicão do layer para desenhar as features */

	    var layer = null;
	    var layers = _map.getLayers().getArray();

	    for (var i = 0; i < layers.length; i++) {
	        if (layers[i].get('name') == 'viewer-print-layer') {
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
	            name: 'viewer-print-layer',
	            group: 'vector'
	        });
	    }

	    _map.addLayer(layer);
	    _printLayer = layer;

	    _map.addLayer(_paperbox_layer);
	};

	var _setFeature = function (feature) {
	    _feature = feature
	}

	var _setMultiGeom = function (mode) {
	    _multiGeom = mode;
	}

	var _getMultiGeom = function() {
	    return _multiGeom;
	}

    return {
        Init: _init,
        Load: _load,
        setMap: _setMap,
        setFeature: _setFeature,
        setMultiGeom: _setMultiGeom,
        getMultiGeom: _getMultiGeom
    }
} ());