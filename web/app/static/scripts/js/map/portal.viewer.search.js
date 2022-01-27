if (!Portal) {
    Portal = {};
}
if (!Portal.Viewer) {
    Portal.Viewer = {};
}

Portal.Viewer.Search = (function () {

    var _modulo = 'search';

	var _map;
	var _layer;

	var _address_roads = [];
	var _address_locators = null;

	var _records_data = {};
	var _feature = null;
	var _feature_over = null;

    var _init = function () {
    };

    var _load = function (parentId) {
        $(".menu-button-link", parentId).click(function (e) {
            var target = $(this).data("target");
            var action = $(this).data("action");
            var data = {
                    map_id: $('#map_id').val() || null,
                    widget_id: $(this).data("widget-id") || null
                };

            if (action) {
                _showLoading(true);
                $.ajax({
                    type: 'POST',
                    url: action,
                    data: data,
                    traditional: true,
                    success: function (r) {
                        $(".search-steps", parentId).hide();
                        $(target + " .form-area", parentId).html(r.Message);
                        $(target, parentId).show();
                        if (r.Data && r.Data.script) {
                            eval(r.Data.script);
                        }
                    },
                    error: function (e) {
                        _showLoading(false);
                    },
                    complete: function(e) {
                        _showLoading(false);
                    }
                });
            } else {
                $(".search-steps", parentId).hide();
                $(target, parentId).show();
            }
        });

        $(".step-back", parentId).click(function(e) {
            var target = $(this).data("step");

            /*
            $("#search-results").empty().html("");
	        $("#validation", parentId).empty().html("");
	        */

	        //var layer = Portal.Viewer.getTemporaryLayer();
            var source = _layer.getSource();
            //source.clear();
            var fs = source.getFeatures();
            for (var j=fs.length-1; j>=0; j--){
                var f = fs[j];
                if (f.get('modulo') == _modulo) {
                    source.removeFeature(f);
                }
            }

            //Clear wms layer filtering
            var wcfg = $("input[name='WidgetConfig']", $(this).closest("div.search-steps")).val();
            if (wcfg) {
                var cfg = JSON.parse(wcfg.replace(/\'/g, '\"'));
                if (cfg && cfg.filter_layer && cfg.filter_layer.name) {
                    var l = findLayerBy(Portal.Viewer.getRootLayer(), 'id', cfg.filter_layer.name);
                    if (l) {
                        var source = l.getSource();
                        var params = source.getParams();
                        delete params['CQL_FILTER'];
                        source.updateParams(params);
                    }
                }
            }

            $(".search-steps", parentId).hide();
            $(target, parentId).show();
        });

        $(parentId).on('click', '.btn-clear-form', _form_clear);
        $(parentId).on('submit', '.form-search', _form_submit);
        $(parentId + ' .results-area.search-widget').on('click', 'a[data-page]', function (e) {
            _showLoading(true);

            var targetElement = $(this).closest('.results-area');
            var form = $('form', $(this).closest('.results-area').parent());

            $.ajax({
                type: 'POST',
                url: $(form).attr("action"),
                traditional: true,
                data: $(form).serialize() + "&page=" + $(this).attr("data-page"),
                extraData: { targetElement: targetElement },
                success: function (r) {
                    var element = this.extraData.targetElement;
                    $(element).html("");
                    if (r.Success) {
                        $(".panel-collapse", $(element).parent()).collapse("hide");
                        $(element).html(r.Message).show();

                        var code = $(element).data('search-code');
                        _records_data[code] = r.Data;
                    } else {
                        var html = "<div class='alert alert-danger'>" + r.Message + "</div>";
                        $(element).html(html).show();
                    }
                },
                error: function (e) {
                    var element = this.extraData.targetElement;

                    var msg = "Ocorreu um erro ao executar a pesquisa."
                    var html = "<div class='alert alert-danger'>" + msg + "</div>";
                    $(element).html(html).show();
                },
                complete: function(e) {
                    _showLoading(false);
                }
            });
        });

        $(parentId).on('click', 'a[data-record-id]', _click_record);
        $(parentId).on('mouseenter', 'a[data-record-id]', _mouseenter_record);
        $(parentId).on('mouseleave', 'a[data-record-id]', _mouseleave_record);
        $(parentId).on('click', 'a[data-child-record-id]', _click_child_record);
        $(parentId).on('mouseenter', 'a[data-child-record-id]', _mouseenter_child_record);
        $(parentId).on('mouseleave', 'a[data-child-record-id]', _mouseleave_record);
        $(parentId).on('change', 'select[data-select-action]', _change_select);

        /*
         Show Panel with contents of document directory
        */
        $(parentId).on("click", "a.link-dir[data-action]", function (e) {
            e.preventDefault();

            var args = [this];

            var this_ = {
                generateID: function () {
                    var s4 = function() {
                        return Math.floor((1 + Math.random()) * 0x10000)
                                   .toString(16)
                                   .substring(1);
                    }

                    return s4() + s4() + s4() + s4() + s4() + s4() + s4() + s4();
                }
            };

            Portal.Viewer.ShowDirectory.apply(this_, args);
        });

        /* Addresses */
        $('#formSearchAddress', parentId).submit(function (e) {
            e.preventDefault();

            var mapSrid = Portal.Viewer.getMapProjectionCode();
            var extent = _map.getView().calculateExtent(_map.getSize());
            //var bbox = ol.proj.transformExtent(extent, _map.getView().getProjection(), ol.proj.get('EPSG:4326')).join(',');
            extent = ol.geom.Polygon.fromExtent(ol.proj.transformExtent(extent, _map.getView().getProjection(), ol.proj.get('EPSG:4326')));
            var mapExtent = Portal.Viewer.getWKTFromGeometry(extent);

            $('#MapExtent', this).val(mapExtent);

            _showLoading(true);

            $.ajax({
                type: 'POST',
                url: $(this).attr('action'),
                traditional: true,
                data: $(this).serialize(),
                success: function (r) {
                    $("#resultsSearchAddress").html("");
                    if (r.Success) {
                        $("#searchAreaAddress").collapse("hide");
                        $("#formSearchAddress").next(".results-area").html(r.Message).show();
                        _loadAddressData(r.Data);
                    } else {
                        var html = "<div class='alert alert-danger'>" + r.Message + "</div>";
                        $("#formSearchAddress").next(".results-area").html(html).show();
                    }
                },
                error: function (e) {
                    var msg = "Ocorreu um erro ao executar a pesquisa."
                    var html = "<div class='alert alert-danger'>" + msg + "</div>";
                    $("#searchAddress").next(".results-area").html(html);
                },
                complete: function(e) {
                    _showLoading(false);
                }
            });
        });

        $('#resultsSearchAddress').on('click', 'a[data-page]', function (e) {
            _showLoading(true);

            $.ajax({
                type: 'POST',
                url: $("#formSearchAddress").attr("action"),
                traditional: true,
                data: $("#formSearchAddress").serialize() + "&page=" + $(this).attr("data-page"),
                success: function (r) {
                    $("#resultsSearchAddress").html("");
                    if (r.Success) {
                        $("#resultsSearchAddress").html(r.Message).show();
                        _loadAddressData(r.Data);
                    } else {
                        if ($("#Id").prop("value") == "0") $("#Id").prop("value", r.Id);

                        $("#windowModal").modal("hide");

                        $("#informationDiv").informationModal({
                            heading: 'Informação',
                            body: "Ocorreu um erro ao executar a pesquisa.",
                            messageClass: "alert alert-error",
                            callback: function () {
                            }
                        });
                    }
                },
                error: function (r) {
                    $("#resultsSearchAddress").html("");
                },
                complete: function (e) {
                    _showLoading(false);
                }
            });
        });

        $('#resultsSearchAddress').on('click', 'a.road-record', _click_road);
        $('#resultsSearchAddress').on('mouseenter', 'a.road-record', _mouseenter_road);
        $('#resultsSearchAddress').on('mouseleave', 'a.road-record', _mouseleave_road);

        $('#resultsSearchAddress').on('click', 'a.road-locator-record', _click_road_locator);
        $('#resultsSearchAddress').on('mouseenter', 'a.road-locator-record', _mouseenter_road_locator);
        $('#resultsSearchAddress').on('mouseleave', 'a.road-locator-record', _mouseleave_road_locator);
        /* End Addresses */
    };

    /* Addresses Search Widget */
    function _click_road(e) {
        e.preventDefault();

        _clear_feature();

        var road_id = $(this).data('road-id');
        var max_zoom = $(this).data('max-zoom') || null;

        var road = null;
        var features = [];

        for (var i=0;i<_address_roads.length;i++) {
            if (_address_roads[i].id == road_id) {
                road = _address_roads[i];
                break;
            }
        }

        if (road){
           var format = new ol.format.WKT();

           var extent = ol.extent.createEmpty();

           for (var i=0;i<road.centerlines.length;i++) {
                var geom = format.readGeometry(road.centerlines[i].geom_wkt);
                geom.transform('EPSG:' + road.centerlines[i].geom_srid, Portal.Viewer.getMapProjectionCode());

                ol.extent.extend(extent, geom.getExtent());

                //Draw feature
                var feature = new ol.Feature({
                    geometry: geom,
                    fid: road_id,
                    modulo: 'search'
                });
                _layer.getSource().addFeature(feature);
                features.push(feature);
           }

           _feature = features;

           //Zoom to feature
           var cfg = Portal.Viewer.getConfig();
           if (cfg.map.selection && cfg.map.selection.maxZoom && cfg.map.selection.maxZoom > 0) {
               _map.getView().fit(
                   extent,
                   _map.getSize(),
                   { maxZoom: cfg.map.selection.maxZoom }
               );
           } else {
               var zoom_ops = { minResolution: 0.1 };
               if (geom instanceof ol.geom.Point) {
                    zoom_ops.minResolution = 1;
               }
               _map.getView().fit(
                   extent,
                   _map.getSize(),
                   zoom_ops
               );
           }

        }
    }

    function _mouseenter_road(e) {
        e.preventDefault();

        _clear_feature_over();

        var road_id = $(this).data('road-id');

        var road = null;
        var features = [];

        for (var i=0;i<_address_roads.length;i++) {
            if (_address_roads[i].id == road_id) {
                road = _address_roads[i];
                break;
            }
        }

        if (road){
           var format = new ol.format.WKT();

           for (var i=0;i<road.centerlines.length;i++) {
                var geom = format.readGeometry(road.centerlines[i].geom_wkt);
                geom.transform('EPSG:' + road.centerlines[i].geom_srid, Portal.Viewer.getMapProjectionCode());

                //Draw feature
                var feature = new ol.Feature({
                    geometry: geom,
                    fid: road_id,
                    modulo: 'search'
                });
                _layer.getSource().addFeature(feature);
                features.push(feature);
           }

           _feature_over = features;
        }
    }

    function _mouseleave_road(e) {
        e.preventDefault();

        _clear_feature_over();
    }

    function _click_road_locator(e) {
        e.preventDefault();

        _clear_feature();

        var road_id = $(this).data('road-id');
        var locator_id = $(this).data('road-locator-id');
        var max_zoom = $(this).data('max-zoom');

        var locator = null;

        for (var i=0;i<_address_roads.length;i++) {
            if (_address_roads[i].id == road_id) {
                for (var j=0;j<_address_roads[i].locators.length;j++) {
                    if (_address_roads[i].locators[j].id == locator_id) {
                        locator = _address_roads[i].locators[j];
                        break;
                    }
                }
                if (locator) {
                    break;
                }
            }
        }

        if (locator) {
           var format = new ol.format.WKT();
           var geom = format.readGeometry(locator.geom_wkt);
           geom.transform('EPSG:' + locator.geom_srid, Portal.Viewer.getMapProjectionCode());

            //Draw feature
            var feature = new ol.Feature({
                geometry: geom,
                fid: locator_id,
                modulo: 'search'
            });
            _layer.getSource().addFeature(feature);
            _feature = feature;

           //Zoom to feature
           var cfg = Portal.Viewer.getConfig();
           if (cfg.map.selection && cfg.map.selection.maxZoom && cfg.map.selection.maxZoom > 0) {
               _map.getView().fit(
                   geom.getExtent(),
                   _map.getSize(),
                   { maxZoom: cfg.map.selection.maxZoom }
               );
           } else {
               var zoom_ops = { minResolution: 0.1 };
               if (geom instanceof ol.geom.Point) {
                    zoom_ops.minResolution = 1;
               }
               _map.getView().fit(
                   geom.getExtent(),
                   _map.getSize(),
                   zoom_ops
               );
           }
        }
    }

    function _mouseenter_road_locator(e) { // define event handler
        e.preventDefault();

        _clear_feature_over();

        var road_id = $(this).data('road-id');
        var locator_id = $(this).data('road-locator-id');

        var locator = null;

        for (var i=0;i<_address_roads.length; i++) {
            if (_address_roads[i].id == road_id) {
                for (var j=0;j<_address_roads[i].locators.length;j++) {
                    if (_address_roads[i].locators[j].id == locator_id) {
                        locator = _address_roads[i].locators[j];
                        break;
                    }
                }
                if (locator) {
                    break;
                }
            }
        }

        if (locator) {
           var format = new ol.format.WKT();
           var geom = format.readGeometry(locator.geom_wkt);
           geom.transform('EPSG:' + locator.geom_srid, Portal.Viewer.getMapProjectionCode());

            //Draw feature
            var feature = new ol.Feature({
                geometry: geom,
                fid: locator_id,
                modulo: 'search'
            });
            _layer.getSource().addFeature(feature);
            _feature_over = feature;
        }
    }

    function _mouseleave_road_locator(e) { // define event handler
        e.preventDefault();

        _clear_feature_over();
    }

    function _clear_feature_over () {
        if (_feature_over) {
            if (_feature_over instanceof Array) {
                for (var i=0;i<_feature_over.length;i++) {
                    _layer.getSource().removeFeature(_feature_over[i]);
                }
            } else {
                _layer.getSource().removeFeature(_feature_over);
            }
        }
        _feature_over = null;
    }

    function _clear_feature () {
        if (_feature) {
            if (_feature instanceof Array) {
                for (var i=0;i<_feature.length;i++) {
                    try {
                        _layer.getSource().removeFeature(_feature[i]);
                    } catch (e) {}
                }
            } else {
                try {
                    _layer.getSource().removeFeature(_feature);
                } catch (e) {}
            }
        }
        _feature = null;
    }

    var _loadAddressData = function(data) {
        _address_roads = data;
    };


    /* General Search Widget */
    var _form_submit = function (e) {
        e.preventDefault();

        var mapSrid = Portal.Viewer.getMapProjectionCode();
        var extent = _map.getView().calculateExtent(_map.getSize());
        //var bbox = ol.proj.transformExtent(extent, _map.getView().getProjection(), ol.proj.get('EPSG:4326')).join(',');
        extent = ol.geom.Polygon.fromExtent(ol.proj.transformExtent(extent, _map.getView().getProjection(), ol.proj.get('EPSG:4326')));
        var mapExtent = Portal.Viewer.getWKTFromGeometry(extent);

        var targetElement = $(this).parent().next('.results-area');

        $('#MapExtent', this).val(mapExtent);

        _showLoading(true);

        $.ajax({
            type: 'POST',
            url: $(this).attr('action'),
            traditional: true,
            data: $(this).serialize(),
            extraData: { targetElement: targetElement },
            success: function (r) {
                var element = this.extraData.targetElement;
                $(element).html("");
                if (r.Success) {
                    $(".panel-collapse", $(element).parent()).collapse("hide");
                    $(element).html(r.Message).show();

                    var code = $(element).data('search-code');
                    _records_data[code] = r.Data;

                    //Apply wms layer filtering
                    //var wcfg = $(element).prevAll("input[name='WidgetConfig']").first().val();
                    var wcfg = $("input[name='WidgetConfig']", $(element).parent()).val();
                    if (wcfg) {
                        var cfg = JSON.parse(wcfg.replace(/\'/g, '\"'));
                        if (cfg && cfg.filter_layer && cfg.filter_layer.name) {
                            var l = findLayerBy(Portal.Viewer.getRootLayer(), 'id', cfg.filter_layer.name);
                            if (l && cfg.filter_layer.fields && cfg.filter_layer.fields.length) {
                                var source = l.getSource();
                                var params = source.getParams();
                                var form = $("form", $(element).parent());
                                var filter = '';
                                for (var i=0; i<cfg.filter_layer.fields.length; i++) {
                                    var field_name = cfg.filter_layer.fields[i].layer_field_name || cfg.filter_layer.fields[i].name;

                                    if ($("[name='" + cfg.filter_layer.fields[i].name + "']", form).length) {
                                        var field_value = $("[name='" + cfg.filter_layer.fields[i].name + "']", form).val();
                                        if (field_value) {
                                            if (filter) {
                                                filter += " AND ";
                                            }

                                            var field_type = cfg.filter_layer.fields[i].type || '';
                                            var expression_value = cfg.filter_layer.fields[i].value;
                                            if (field_type.toLowerCase() == 'integer') {
                                                filter += field_name + " = " + field_value;
                                            } else {
                                                if (expression_value) {
                                                    field_value = expression_value.replace('{value}', field_value);
                                                }
                                                filter += field_name + " ILIKE '" + field_value + "'";
                                            }
                                        }
                                    }
                                }

                                if (filter) {
                                    params['CQL_FILTER'] = filter;
                                } else {
                                    delete params['CQL_FILTER'];
                                }
                                source.updateParams(params);
                            }
                        }
                    }
                } else {
                    var html = "<div class='alert alert-danger'>" + r.Message + "</div>";
                    $(element).html(html).show();
                }
            },
            error: function (e) {
                var element = this.extraData.targetElement;
                var msg = "Ocorreu um erro ao executar a pesquisa."
                var html = "<div class='alert alert-danger'>" + msg + "</div>";
                $(element).html(html).show();
            },
            complete: function(e) {
                _showLoading(false);
            }
        });
    };

    var _form_clear = function (e) {
        e.preventDefault();

        $(this).closest('form').trigger('reset');
        $(this).closest('form').parent().next('.results-area').html('');

        var source = _layer.getSource();
        //source.clear();
        var fs = source.getFeatures();
        for (var j=fs.length-1; j>=0; j--){
            var f = fs[j];
            if (f.get('modulo') == _modulo) {
                source.removeFeature(f);
            }
        }

        //Clear wms layer filtering
        var wcfg = $("input[name='WidgetConfig']", $(this).closest('form').parent().parent()).val();
        if (wcfg) {
            var cfg = JSON.parse(wcfg.replace(/\'/g, '\"'));
            if (cfg && cfg.filter_layer && cfg.filter_layer.name) {
                var l = findLayerBy(Portal.Viewer.getRootLayer(), 'id', cfg.filter_layer.name);
                if (l) {
                    var source = l.getSource();
                    var params = source.getParams();
                    delete params['CQL_FILTER'];
                    source.updateParams(params);
                }
            }
        }
    };

    var _click_record =  function (e) {
        e.preventDefault();

        _clear_feature();

        var record_id = $(this).data('record-id');
        var code = $(this).closest('.results-area').data('search-code');
        var records = _records_data[code];
        var max_zoom = $(this).data('max-zoom');

        var record = null;
        var features = [];

        for (var i=0;i<records.length;i++) {
            if (records[i].id == record_id) {
                record = records[i];
                break;
            }
        }

        if (record && record.geom_wkt) {
           var format = new ol.format.WKT();
           var geom = format.readGeometry(record.geom_wkt);
           geom.transform('EPSG:' + record.geom_srid, Portal.Viewer.getMapProjectionCode());

            //Draw feature
            var feature = new ol.Feature({
                geometry: geom,
                fid: record_id,
                modulo: 'search',
                sub_modulo: code
            });
            _layer.getSource().addFeature(feature);
            _feature = feature;

           //Zoom to feature
           var cfg = Portal.Viewer.getConfig();
           if (cfg.map.selection && cfg.map.selection.maxZoom && cfg.map.selection.maxZoom > 0) {
               _map.getView().fit(
                   geom.getExtent(),
                   _map.getSize(),
                   { maxZoom: cfg.map.selection.maxZoom }
               );
           } else {
               var zoom_ops = { minResolution: 0.1 };
               if (geom instanceof ol.geom.Point) {
                    zoom_ops.minResolution = 1;
               }
               _map.getView().fit(
                   geom.getExtent(),
                   _map.getSize(),
                   zoom_ops
               );
           }
        }
    };

    var _mouseenter_record = function (e) { // define event handler
        e.preventDefault();

        _clear_feature_over();

        var record_id = $(this).data('record-id');
        var code = $(this).closest('.results-area').data('search-code');
        var records = _records_data[code];

        var record = null;

        for (var i=0;i<records.length; i++) {
            if (records[i].id == record_id) {
                record = records[i];
                break;
            }
        }

        if (record && record.geom_wkt) {
           var format = new ol.format.WKT();
           var geom = format.readGeometry(record.geom_wkt);
           geom.transform('EPSG:' + record.geom_srid, Portal.Viewer.getMapProjectionCode());

            //Draw feature
            var feature = new ol.Feature({
                geometry: geom,
                fid: record_id,
                modulo: 'search',
                sub_modulo: code
            });
            _layer.getSource().addFeature(feature);
            _feature_over = feature;
        }
    };

    var _mouseleave_record = function (e) {
        e.preventDefault();

        _clear_feature_over();
    };

    function _click_child_record(e) {
        e.preventDefault();

        _clear_feature();

        var parent_record_id = $(this).data('parent-record-id');
        var child_record_id = $(this).data('child-record-id');
        var code = $(this).closest('.results-area').data('search-code');
        var child_collection = $(this).data('child-collection');
        var records = _records_data[code];

        var child_record = null;

        for (var i=0;i<records.length; i++) {
            if (records[i].id == parent_record_id) {
                var rec = records[i];
                var childs = rec[child_collection];

                for (var j=0;j<childs.length;j++) {
                    if (childs[j].id == child_record_id) {
                        child_record = childs[j];
                        break;
                    }
                }
                if (child_record) {
                    break;
                }
            }
        }

        if (child_record) {
           var format = new ol.format.WKT();
           var geom = format.readGeometry(child_record.geom_wkt);
           geom.transform('EPSG:' + child_record.geom_srid, Portal.Viewer.getMapProjectionCode());

            //Draw feature
            var feature = new ol.Feature({
                geometry: geom,
                fid: child_record_id,
                modulo: 'search'
            });
            _layer.getSource().addFeature(feature);
            _feature = feature;

           //Zoom to feature
           var cfg = Portal.Viewer.getConfig();
           if (cfg.map.selection && cfg.map.selection.maxZoom && cfg.map.selection.maxZoom > 0) {
               _map.getView().fit(
                   geom.getExtent(),
                   _map.getSize(),
                   { maxZoom: cfg.map.selection.maxZoom }
               );
           } else {
               var zoom_ops = { minResolution: 0.1 };
               if (geom instanceof ol.geom.Point) {
                    zoom_ops.minResolution = 1;
               }
               _map.getView().fit(
                   geom.getExtent(),
                   _map.getSize(),
                   zoom_ops
               );
           }
        }
    };

    var _mouseenter_child_record = function (e) {
        e.preventDefault();

        _clear_feature_over();

        var parent_record_id = $(this).data('parent-record-id');
        var child_record_id = $(this).data('child-record-id');
        var code = $(this).closest('.results-area').data('search-code');
        var child_collection = $(this).data('child-collection');
        var records = _records_data[code];

        var child_record = null;

        for (var i=0;i<records.length; i++) {
            if (records[i].id == parent_record_id) {
                var rec = records[i];
                var childs = rec[child_collection];

                for (var j=0;j<childs.length;j++) {
                    if (childs[j].id == child_record_id) {
                        child_record = childs[j];
                        break;
                    }
                }
                if (child_record) {
                    break;
                }
            }
        }

        if (child_record) {
           var format = new ol.format.WKT();
           var geom = format.readGeometry(child_record.geom_wkt);
           geom.transform('EPSG:' + child_record.geom_srid, Portal.Viewer.getMapProjectionCode());

            //Draw feature
            var feature = new ol.Feature({
                geometry: geom,
                fid: child_record_id,
                modulo: 'search'
            });
            _layer.getSource().addFeature(feature);
            _feature_over = feature;
        }
    };

    var _change_select = function (e) {
        var action = $(this).data('select-action');
        var param = $(this).data('select-param');
        var targetElement = $('#' + $(this).data('select-target'));

        $(targetElement).empty().append('<option value=""></option>');

        var data = {};
        data[param] = $(this).val();

        _showLoading(true);

        $.ajax({
            type: 'POST',
            url: action,
            traditional: true,
            data: data,
            extraData: { targetElement: targetElement },
            success: function (r) {
                var element = this.extraData.targetElement;
                if (r.Success) {
                    var list = r.Data;
                    for (var i=0; i<list.length;i++) {
                        $(element).append('<option value="' + list[i].key + '">' + list[i].value + '</option>');
                    }
                }
            },
            error: function (e) {
            },
            complete: function(e) {
                _showLoading(false);
            }
        });
    };

    var _showLoading = function (show) {
        if (show) {
            Portal.Viewer.ShowLoading(".menu-bar-widget." + _modulo + " .menu-bar-body");
        } else {
            Portal.Viewer.HideLoading(".menu-bar-widget." + _modulo + " .menu-bar-body");
        }
    };

	var _setMap = function (map) {
	    _map = map;
	    _layer = Portal.Viewer.getTemporaryLayer();
	};

    return {
        Init: _init,
        Load: _load,
        setMap: _setMap
    }
} ());