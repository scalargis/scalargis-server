var map;
var mapProxy;
var owsLayers;
var owsCatalog = null;
var widgets = [];
var roles = [];
var store_map_state = true;

var LoadApp = function (url_config, proxy) {
    OpenLayers.ProxyHost = proxy + '?url=';

    mapProxy = proxy;

    Portal.Viewer.ShowLoading("#map");

    var xhr = $.ajax({
        url: url_config,
        method: 'get',
        dataType: 'json'
    }).then(function(res){
        if (res.Success == true) {
            $('<script>')
                .attr('type', 'text/javascript')
                .text('var cfg_tmp = ' + res.Data)
                .appendTo('head');

            var cfg = cfg_tmp;

            //Clear global var
            cfg_tmp = null;
            delete cfg_tmp;

            //Set Mapa Id
            cfg["id"] = $("#container>#map_id").val()

            //Set Widgets configurations
            if (res.Widgets) {
                widgets = res.Widgets;
            }
            
            //Set User Roles
            if (res.Roles) {
                roles = res.Roles;
            }

            loadConfig(cfg, proxy);
            updateLeftMenuPos();
            updateRightMenuPos();
            showDefaultWidget();
            showActiveLayers();
            executeAction(map);
        } else {
            var html = '<div class="message-info alert" role="alert">';
            html += 'Ocorreu um erro ao abrir o mapa.';
            html += '</div>';

             $.jsPanel({
                theme: 'danger',
                resizeit:  false,
                dragit:  false,
                headerTitle: 'Erro',
                headerControls: { controls: 'none' },
                content: html
            });
        }
    }).fail(function(res){
            var html = '<div class="message-info alert" role="alert">';
            html += 'Ocorreu um erro ao abrir o mapa.';
            html += '</div>';

             $.jsPanel({
                theme: 'danger',
                resizeit:  false,
                dragit:  false,
                headerTitle: 'Erro',
                headerControls: { controls: 'none' },
                content: html
            });
    }).always(function(res){
        Portal.Viewer.HideLoading("#map");
    });

    var loadConfig = function (cfg, proxy) {
        //Default map props
        var map_default_props = {
            proxy: proxy,
            style: {},
            selection:  {
                multi: true
            }
        }
        //Fill map with default props
        cfg.map = $.extend({}, map_default_props, cfg.map);

        map = Portal.Viewer.Load(cfg, 'map');

        // map history
        if (hasWidget('zoom_previous')) {
            var map_view_history = [];
            var storeMapView = function (){
                if (!store_map_state) {
                    store_map_state = true;
                    return
                 }
                var state = {
                  zoom: map.getView().getZoom(),
                  center: map.getView().getCenter(),
                  rotation: map.getView().getRotation()
                };

                map_view_history.push(state) > 10 ? map_view_history.shift() : null; // nice  ;)
            }

            map.on('moveend', storeMapView);

            var mapHistoryControl = new app.mapHistoryControl({
                target:  'zoomPreviousPanel',
                className: 'map-control',
                map_view_history: map_view_history
            });

            map.addControl(mapHistoryControl);
        } // end map history


        // ZoomIn/ZoomOut
        map.addControl(new ol.control.Zoom({
            target: 'zoomPanel',
            zoomInTipLabel: 'Aproximar',
            zoomOutTipLabel: 'Afastar',
            className: 'map-control'
        }));

        // ZoomExtent
        var icon = document.createElement('i');
        icon.className = 'fa fa-globe';
        var att = document.createAttribute('aria-hidden');
        att.value = "true";
        icon.setAttributeNode(att);

        var extent = undefined;
        if (cfg.map.extent && cfg.map.extent.bounds) {
            extent = ol.proj.transformExtent(cfg.map.extent.bounds, cfg.map.extent.projection || map.getView().getProjection(), map.getView().getProjection());
        }

        map.addControl(new ol.control.ZoomToExtent({
            target: 'zoomExtentPanel',
            tipLabel: 'Ver Tudo',
            className: 'map-control',
            label: icon,
            extent: extent
        }));
        // End ZoomExtent

        // Measure
        map.addControl(new app.measureControl({
            target: 'measurePanel',
            measureDistanceTipLabel: 'Medir Distância',
            measureAreaTipLabel: 'Medir Área',
            projection: cfg.map.displayProjection,
            className: 'map-control',
            label: icon,
            layer: Portal.Viewer.getTemporaryLayer()
        }));

        // Scaleline
        if (hasWidget('scaleline')) {
            map.addControl(new ol.control.ScaleLine({ target: $('.scaleline-control')[0]}));
        }

        // Attribution
        if (hasWidget('attribution')) {
            map.addControl(new ol.control.Attribution({collapsible: false}));

            setTimeout(
                function(){
                    $(".ol-attribution ul li a").each(function() {
                        $(this).attr("target","_blank");
                    });
                }, 1000
            );
        }

        // Basemaps
        if (hasWidget('basemaps')) {
            map.addControl(new app.BasemapsControl({
                target: 'basemapPanel',
                group: 'basemap'
            }));
        }

        // BasemapsMap
        if (hasWidget('basemaps_map')) {
            map.addControl(new app.BasemapsMapControl({
                //target: $('.basemaps-map-control')[0],
                target: $('.basemaps-map-control')[0],
                group: 'basemap'
            }));
        }

        // TocLayer
        var lc = new app.LayersControl({
            target: 'layersPanel',
            groups: cfg.map.groups,
            styleRestrictedScales: cfg.map.toc ? cfg.map.toc.styleRestrictedScales || null : null,
            parentLayerVisible: cfg.map.toc ? cfg.map.toc.parentLayerVisible || null : null,
            wms: cfg.map.toc ? cfg.map.toc.wms || null : null
        });
        map.addControl(lc);

        // Mouse Position
        if (hasWidget('mouse_position')) {
            //ol.control.MousePosition.prototype.handleMouseOut = function (browserEvent) { };
            mousePositionControl = new app.MousePositionControl({
                coordinateFormat: ol.coordinate.createStringXY(4),
                projection: cfg.map.displayProjection || cfg.map.projection || map.getView().getProjection().getCode(),
                projections : cfg.map.projections,
                target: $('.map-coordsys-control')[0],
                undefinedHTML: '&nbsp;'
            });
            map.addControl(mousePositionControl);
        }

        // Coordinates
        if (hasWidget('coordinates')) {
            if ($('.menu-bar-widget.coordinates').length > 0) {
                var coordinatesControl = new app.coordinatesControl({
                    target:  'coordinatesPanel',
                    coordinatesTipLabel: 'Obter Coordenadas',
                    className: 'map-control',
                    layer: Portal.Viewer.getTemporaryLayer(),
                    onMapClick: function (evt) {
                        var coordinate = evt.coordinate;
                        Portal.Viewer.Coordenadas.Transform(coordinate[0], coordinate[1]);
                    },
                    onDisable: function () {
                        Portal.Viewer.Coordenadas.Disable();
                    }
                });
                map.addControl(coordinatesControl);
                Portal.Viewer.Coordenadas.SetControl(coordinatesControl);
            }
        }

        // DrawTools control
        if (hasWidget('drawtools')) {
            if ($('.menu-bar-widget.drawtools').length > 0) {
                var drawtoolsControl = new app.drawtoolsControl({
                    target:  'drawToolsViewPanel',
                    drawtoolsTipLabel: 'Ferramentas de Desenho',
                    className: 'map-control',
                    layer: Portal.Viewer.getTemporaryLayer(),
                    onDisable: function () {
                        //Portal.Viewer.DrawTools.Disable();
                    }
                });
                map.addControl(drawtoolsControl);
                Portal.Viewer.DrawTools.SetControl(drawtoolsControl);
                drawtoolsControl.setViewer(Portal.Viewer.DrawTools);
            }
        }

        // FeatureInfo
        if (hasWidget('feature_info')) {
            var featureInfoControl = new app.featureInfoControl({
                config: getWidgetConfig('feature_info'),
                target:  'featureInfoPanel',
                containment: '#map',
                proxy: proxy,
                buttonTipLabel: 'Obter Informação',
                className: 'map-control',
                rootLayer: lc.getRootLayer(),
                queryLayers: cfg.map.queryLayers || [],
                showLoading: Portal.Viewer.ShowLoading,
                hideLoading: Portal.Viewer.HideLoading,
                showDirectory: Portal.Viewer.ShowDirectory,
                showEditor: Portal.Viewer.ShowEditor,
                executeAction: function (action) {
                    eval(action);
                },
                addWMSLayer: function (e) {
                    var map = this.getMap();
                    var target_layer = $(e).data('target-layer');
                    var url = $(e).data('url');
                    var layers = $(e).data('layer-name');
                    var name = $(e).data('layer-name');
                    var title = $(e).data('layer-title');
                    var version = '1.3.0';
                    var format = 'image/png';

                    //(url, map, layers, format, transparent, title, crs, tiled, version, styles, sld, group, name, queryable, addToMap, extent)
                    var l = owsLayers.addWMSLayer(url, null, layers, format, true, title, null, true, version, '', '', '', name, false, false, null, target_layer);

                    if (target_layer) {
                        var tl = findLayerBy(this.rootLayer, 'id', target_layer);
                        if (tl) {
                            tl.getLayers().push(l);
                        } else {
                            this.rootLayer.getLayers().push(l);
                        }
                    } else {
                        this.rootLayer.getLayers().push(l);
                    }

                }
            });
            map.addControl(featureInfoControl);
        }

        // Select
        if (hasWidget('feature_select')) {
            var featureSelectControl = new app.featureSelectControl({
                containment: '#map',
                condition: ol.events.condition.click,
                multi: cfg.map.selection.multi,
                rootLayer: lc.getRootLayer(),
                styles: {
                    selection: cfg.map.style.selection || Portal.Viewer.getSelectionStyles(),
                    active: cfg.map.style.active || Portal.Viewer.getActiveStyles()
                }
            });
            map.addControl(featureSelectControl);
        }

        // Google Street View
        if (hasWidget('google_streetview')) {
            var googleStreetViewControl = new app.googleStreetViewControl({
                target: 'googleStreetViewPanel',
                buttonTipLabel: 'Ver Google Street View',
                panelTitle: 'Google Street View',
                className: 'map-control',
                iconStyle: null,
                layer: Portal.Viewer.getTemporaryLayer(),
                onMapClick: null,
                onDisable: null
            });
            map.addControl(googleStreetViewControl);
        }

        // Numeric scale
        if (hasWidget('numeric_scale')) {
            var numericScaleControl = new app.NumericScaleControl({
                target: $('.numericscale-control-container')[0]
            });
            map.addControl(numericScaleControl);
            numericScaleControl.set('active', true);
        }

        // Manage scale controls
        if (hasWidget('numeric_scale') && hasWidget('scaleline')) {

            // Selected scale control
            var selectedScaleControlName = 'scaleline';

            // Hide/show scale control by name
            var toggleScaleControl = function(name) {
                $('.scale-controls .item').each(function(i, el) {
                    if ($(el).data('name') !== name) $(el).addClass('hidden');
                    else $(el).removeClass('hidden');
                });
                selectedScaleControlName = name;
            }

            // Scale control click listener
            var selectScaleControlListener = function() {
                $('.scale-controls').removeClass('open');
                toggleScaleControl($(this).data('name'));
            }

            // Scale control selector listener
            $('.scale-controls .scale-control-selector').click(function() {
                if ($('.scale-controls').hasClass('open') === false) {
                    $('.scale-controls .item').removeClass('hidden');
                    $('.scale-controls').addClass('open');
                    $('.scale-controls .item').click(selectScaleControlListener);
                } else {
                    $('.scale-controls .item').unbind('click', selectScaleControlListener);
                    toggleScaleControl(selectedScaleControlName);
                    $('.scale-controls').removeClass('open');
                }
            });

            // Start default scale control
            toggleScaleControl(selectedScaleControlName);
        } else {

            // Hide scale control selector
            $('.scale-controls').addClass('single');
        }

        //Overview Map
        if (hasWidget('overviewmap')) {
            var overviewMapControl = new ol.control.OverviewMap({
              collapsed: false,
              collapsible: true,
              tipLabel: 'Mapa de enquadramento',
              layers: [
                new ol.layer.Tile({
                  source: new ol.source.OSM()
                })
              ]
            });
            map.addControl(overviewMapControl);
        }

        geonamesServices.setMap(map);

        owsLayers = new OWS({ rootElementId: '.menu-bar-widget.toc', parentId: '.toc #addLayersPanel', layers: lc.rootLayer.getLayers() });
        owsLayers.setMap(map);

        $(".menu-button").bind('open', function(event) {
            $(".menu-button").not(this).each(function() {
                $(this).removeClass("active");
            });

            if (!$(this).hasClass("active")) {
                $(this).addClass("active");
            }

            var menu_bar = '.menu-bar';
            if ($(this).data("target-menu") == 'right') {
                menu_bar = '.menu-bar-right';
            }

            var filter = $(this).data("target");
            var elem = $(menu_bar+filter)[0];


            if (elem) {
                $(menu_bar).not(elem).each(function(){
                    $(this).removeClass("open");
                    $(this).trigger('onRemoveClassOpen');
                });
                if (!$(elem).hasClass("open")) {
                    $(elem).addClass("open");
                }

                setTimeout(function(){
                    updateMapControlsPos(elem);
                }, 300);
            }
        });


        $(".menu-button").click(function(e){
            e.preventDefault();

            var _this = this;

            var menu = '.menu';
            var menu_bar = '.menu-bar';
            if ($(_this).data("target-menu") == 'right') {
                menu = '.menu-right';
                menu_bar = '.menu-bar-right';
            }

            $(".menu-button", menu).not(_this).each(function() {
                $(this).removeClass("active");
            });
            $(_this).toggleClass( "active" );

            var filter = $(_this).data("target");
            var elem = $(menu_bar+filter)[0];
            var action = $(_this).data("action");
            var loaded = $(elem).data("loaded");

            var data = { map_id: $('#map_id').val() };

            var show_panel = function () {
                if (elem) {
                    $(menu_bar).not(elem).each(function(){
                        $(this).removeClass("open");
                        $(this).trigger('onRemoveClassOpen');
                    });
                    $(elem).toggleClass("open");

                    setTimeout(function(){
                        updateMapControlsPos(elem);
                    }, 300);
                }
            }

            if (action && action != '') {
                if (!loaded) {
                    Portal.Viewer.ShowLoading(menu_bar);
                    var jqxhr = $.ajax({
                        type: "POST",
                        data: data,
                        url: action + window.location.search
                    })
                    .done(function(r){
                        if (r.Success) {
                            $(elem).empty().html(r.Message);
                            $(elem).data('loaded', true);
                        }
                        Portal.Viewer.HideLoading(menu_bar);
                    })
                    .fail(function (r) {
                        console.log('fail');
                    })
                    .always(function (r) {
                        show_panel();

                        Portal.Viewer.HideLoading(menu_bar);

                        if (r.Data && r.Data.script) {
                            eval(r.Data.script);
                        }
                    });
                } else {
                    show_panel();
                }
            } else {
                show_panel();
            }
        });

        //$(".menu-bar.home .menu-button-link").click(function(e){
        $(".menu-bar-widget.home .menu-button-link").click(function(e){
            e.preventDefault();

            var _this = this;

            var menu = '.menu';
            var menu_bar = '.menu-bar';
            if ($(_this).data("target-menu") == 'right') {
                menu = '.menu-right';
                menu_bar = '.menu-bar-right';
            }

            $(".menu-button", menu).not(_this).each(function() {
                $(this).removeClass("active");
            });

            var filter = $(_this).data("target");
            //var elem = $(".menu-bar"+filter)[0];
            var elem = $(menu_bar+filter)[0];
            var action = $(_this).data("action");
            var loaded = $(elem).data("loaded");

            var data = { map_id: $('#map_id').val() };

            var show_panel = function () {
                $(".menu-button"+filter).toggleClass( "active" );
                if (elem) {
                    //$('.menu-bar').not(elem).each(function(){
                    $(menu_bar).not(elem).each(function(){
                        $(this).removeClass("open");
                        $(this).trigger('onRemoveClassOpen');
                    });
                    $(elem).toggleClass("open");

                    setTimeout(function(){
                        updateMapControlsPos(elem);
                    }, 300);
                }
            }

            if (action && action != '') {
                if (!loaded) {
                    Portal.Viewer.ShowLoading(menu_bar);
                    var jqxhr = $.ajax({
                        type: "POST",
                        url: action,
                        data: data
                    })
                    .done(function(r){
                        if (r.Success) {
                            $(elem).empty().html(r.Message);
                            $(elem).data('loaded', true);
                        }
                        Portal.Viewer.HideLoading(menu_bar);
                    })
                    .fail(function (r) {
                        console.log('fail');
                    })
                    .always(function (r) {
                        show_panel();

                        Portal.Viewer.HideLoading(menu_bar);

                        if (r.Data && r.Data.script) {
                            eval(r.Data.script);
                        }
                    });
                } else {
                    show_panel();
                }
            } else {
                show_panel();
            }
        });

        $(".search-button").on("click", function(e) {
            e.preventDefault();

            var ctx = $(this).closest(".input-group");
            $("input.search-input", ctx).val("");
            $(this).removeClass("searching active");
        });

        $(".nav-layers-panel a").click(function (e) {
            e.preventDefault();

            var target = $(this).data("target");

            $(".layers-panel").hide();
            $(target).show();

            $(".nav-layers-panel>a").not(this).show();
            $(this).hide();
        });

        $("a.login").click(function (e) {
            e.preventDefault();
            $("#menu-info-container").hide("fast");
            $($(this).data("target")).toggle();
            return false;
        });
        $("a.menu-info").click(function (e) {
            e.preventDefault();
            $("#user-info-container").hide("fast");
            $($(this).data("target")).toggle();
            return false;
        });
        $(document).click(function() {
            $("#user-info-container").hide("fast");
        });
        $("#user-info-container").click(function (e) {
            e.stopPropagation();
        });

        $("#menu-info-container").click(function() {
            $("#send-feedback", "#contact-form").empty().html('').hide('fast');
        });

        $("#contact-form").submit(function(e){
            e.preventDefault();

            var name = $("#name", "#contact-form").val();
            var email = $("#email", "#contact-form").val();
            var message = $("#message", "#contact-form").val();

            Portal.Viewer.ShowLoading("#menu-info-container");

            $("#send-feedback", "#contact-form").empty().html('').removeClass('alert-success alert-warning').hide();

            var jqxhr = $.ajax({
                    type: "POST",
                    url: $("#contact-form").data("action"),
                    data: "name=" + name + "&email=" + email + "&message=" + message
                })
                .done(function(r){
                    if (r.Success) {
                        $("#send-feedback", "#contact-form").empty().html(r.Message).addClass('alert-success');
                        $("#message", "#contact-form").val('');
                    } else {
                        $("#send-feedback", "#contact-form").empty().html(r.Message).addClass('alert-warning');
                    }
                })
                .fail(function (r) {
                    $("#send-feedback", "#contact-form").empty().html('Ocorreu um erro ao enviar a mensagem').addClass('alert-warning');
                })
                .always(function (r) {
                    Portal.Viewer.HideLoading("#menu-info-container");
                    $("#send-feedback", "#contact-form").show();
                });
        });

        Portal.Viewer.Coordenadas.Load('TransformCoordenadas');

        Portal.Viewer.DrawTools.Load('.menu-bar-widget.drawtools');
        Portal.Viewer.DrawTools.setMap(map);

        Portal.Viewer.PDM.Load('.menu-bar-widget.pdm');
        Portal.Viewer.PDM.setMap(map);

        Portal.Viewer.Print.Load('.menu-bar-widget.print');
        Portal.Viewer.Print.setMap(map);

        Portal.Viewer.Catalog.Load(null, lc.rootLayer.getLayers());
        Portal.Viewer.Catalog.setMap(map);

        Portal.Viewer.Search.Load('.menu-bar-widget.search');
        Portal.Viewer.Search.setMap(map);

        Portal.Viewer.Planos.Load('.menu-bar-widget.planos_list');
        Portal.Viewer.Planos.setMap(map);

        if ($('.menu-bar-right') && $('.menu-bar-right').length > 0) {

        }

        /*
        var requestRest = function (token) {
            if (token) {
                $.ajax({
                  type: 'GET',
                  url: '/api/v1/cats',
                  beforeSend: function(request) {
                    request.setRequestHeader("X-API-KEY", token);
                  },
                  success: function(resp) {
                    console.log(resp);
                  }
                });
            } else {
                $.ajax({
                  type: 'GET',
                  url: '/api/v1/cats',
                  success: function(resp) {
                    console.log(resp);
                  }
                });
            }
        }

        $.ajax({
          type: 'POST',
          dataType: 'json',
          contentType: "application/json; charset=utf-8",
          data: '{ "username": "ricardogsena", "password": "password" }',
          url: '/api/v1/authentication/authenticate',
          success: function(resp) {
            console.log(resp);
          },
          complete: function(data) {
            //requestRest(data.responseJSON.token);
            requestRest(GetAuthToken());
          }
        });
        */

        /*
        var token = $('#auth_token').val();
        if (token) {
            console.log(token);

            $.ajax({
              type: 'GET',
              beforeSend: function(request) {
                request.setRequestHeader("Authentication-Token", token);
              },
              url: '/todo/api/v1.0/tasks',
              success: function(resp) {
                console.log(resp);
              }
            });
        } else {
            $.ajax({
              type: 'GET',
              url: '/todo/api/v1.0/tasks',
              success: function(resp) {
                console.log(resp);
              }
            });
        }
        */
    }

    var showDefaultWidget = function () {
        var widget = $("#show_widget").val();

        if(window.location.hash) {
          widget = window.location.hash.substr(1);
        }

        if (widget) {
            var btn = $(".menu-button." + widget);

            if (btn.length > 0) {
                btn.trigger("click");
            }
        }
    }

    var updateMapControlsPos = function (elem) {
        if ($(elem).hasClass('menu-bar')) {
            $('.ol-overviewmap').css('left', $(elem).position().left + $(elem).outerWidth() + 5);
        } else if ($(elem).hasClass('menu-bar-right')) {
            $('#map-toolbar-container').css('right', $(elem).outerWidth() + $('#map-toolbar-container').outerWidth() + 3);
            $('.map-coordsys-control').css('right', $(elem).outerWidth() + $('#map-toolbar-container').outerWidth());
            $('.basemaps-map-control').css('right', $(elem).outerWidth() + $('#map-toolbar-container').outerWidth() + 10);
            $('.ol-attribution').css('right', $(elem).outerWidth() + $('#map-toolbar-container').outerWidth() + $('.basemaps-map-control').outerWidth() + 12);
            $('.scale-controls').css('right', $(elem).outerWidth() + $('#map-toolbar-container').outerWidth() + $('.map-coordsys-control').outerWidth() + 25);
        }
    }

    var updateLeftMenuPos = function () {
        var left = $('.menu').outerWidth();
        $('.ol-overviewmap').css('left', left + 5);
    }

    var updateRightMenuPos = function () {
        var s = $('.basemaps-map-control');

        if ($('#header').length == 0) {
            var top_pos = $('#map-navbar-container').position().top + $('#map-navbar-container').outerHeight();
            $('.menu-right').css('top', top_pos + 1);
            $('.menu-bar-right').css('top', top_pos + 1);

            $('.ol-overviewmap').css('bottom', 5);
        }

        var menu = $('.menu-right');
        var menu_area = $('.menu-bar-widget.menu-bar-right');
        var right_pos = ($(menu).outerWidth() || 0) + ($(menu_area).outerWidth() || 0);

        $('#map-toolbar-container').css('right', right_pos  + 3);
        $('.map-coordsys-control').css('right', right_pos);
        $('.basemaps-map-control').css('right', right_pos + 10);
        $('.ol-attribution').css('right', right_pos + $('.basemaps-map-control').outerWidth() + 12);
        $('.scale-controls').css('right', right_pos + $('.map-coordsys-control').outerWidth() + 25);
    }

    var showActiveLayers = function () {
        var layers = $("#show_layers").val();

        if (layers) {
            var list = layers.split(";");
            for (var i=0; i<list.length; i++) {
                var layer_id = list[i];
                Portal.Viewer.showLayer(Portal.Viewer.getRootLayer(), layer_id, null);
            }
        }
    }

    var executeAction = function(map) {
        var url_param_json = JSON.parse($("#url_params").val());
        if (url_param_json['nb_params'] == 0) {return null}

        var cfg = Portal.Viewer.getConfig();

        var wkt_geom = url_param_json['geom']
        if (wkt_geom != null) {
            var format = new ol.format.WKT();
            var geom = format.readGeometry(wkt_geom);
            geom.transform('EPSG:3763', Portal.Viewer.getMapProjectionCode());

            _layer = Portal.Viewer.getTemporaryLayer();
            //Draw feature
            var feature = new ol.Feature({
                geometry: geom,
                fid: 1
            });

            //Set custom selection style from config
            if (cfg.map.style && cfg.map.style.selection) {
                feature.setStyle(cfg.map.style.selection);
            } else if (cfg.map.selection && cfg.map.selection.style) {
                feature.setStyle(cfg.map.selection.style);
            }

            //Add feature to map
            _layer.getSource().addFeature(feature);
            _feature_over = feature;

            //Zoom to feature
            _map = map;
            if (cfg.map.selection && cfg.map.selection.maxZoom && cfg.map.selection.maxZoom > 0) {
                _map.getView().fit(
                geom.getExtent(),
                _map.getSize(),
                { maxZoom: cfg.map.selection.maxZoom }
                )
            } else {
                var zoom_ops = { minResolution: 0.1 };
                if (geom instanceof ol.geom.Point) {
                    zoom_ops.minResolution = 1;
                }
                _map.getView().fit(
                geom.getExtent(),
                _map.getSize(),
                zoom_ops
                )
            }
        }

        var post_action = url_param_json['url_args']['action'];
        if (post_action == null) {
            return null
        } else {
            action_url = "/" + post_action.replace(/\./g,'/')
        }

        var xhr = $.ajax({
            url: action_url,
            type: 'post',
            dataType: 'json'
            }).then(function(res){
                if (res.Success == true) {

                 if (wkt_geom == null && res.Data['show_alert_if_null_geom']) {
                    ShowAlert(res.Data['alert_body'], res.Data['alert_title'], res.Data['alert_type'])
                 }

                 if (wkt_geom != null || ( wkt_geom == null && res.Data['activate_layer_if_null_geom']))
                    for (var i = 0; i < res.Data['layers'].length; i++) {
                        lay = res.Data['layers'][i];
                        ol_lay = findLayerBy(map.getLayerGroup(),'id',lay['name']);
                        ol_lay.setVisible(lay['visible']);
                    }
            }
            else {
                console.log('Error')
            }
        }).fail(function(res){
            console.log('fail')
        }).always(function(res){
            //console.log('always')
        });
    }

    var hasWidget = function (widget) {
        for(var i = 0; i < widgets.length; i++)
        {
            if (widgets[i].codigo == widget ) {
                return true;
            }
        }
        return false;
    }

    var getWidgetConfig = function (widget) {
        var config = null;

        for(var i = 0; i < widgets.length; i++)
        {
            if (widgets[i].codigo == widget ) {
                if (widgets[i].config) {
                    config = widgets[i].config;
                }
                break;
            }
        }
        return config;
    }
}


function findLayerBy(layer, key, value) {
    if (layer.get(key) === value) {
     //console.log(layer.get(key));
        return layer;
    }

    // Find recursively if it is a group
    if (layer.getLayers) {
        var layers = layer.getLayers().getArray(),
                len = layers.length, result;
        for (var i = 0; i < len; i++) {
            result = findLayerBy(layers[i], key, value);
            if (result) {
                return result;
            }
        }
    }

    return null;
}


var ShowAlert = function(alert_txt, alert_title, alert_theme) {
   var html = '<div class="message-info alert" role="alert">';
    html += '<h3>' + alert_txt +'</h3>';
    html += '</div>';

     $.jsPanel({
        theme: alert_theme,
        resizeit:  false,
        dragit:  false,
        headerTitle: alert_title,
        headerControls: { controls: 'closeonly' },
        content: html
    });
}



var GetAuthToken = function () {
    var token = null
    if ($('#auth_token') && $('#auth_token').val) {
        token = $('#auth_token').val();
    }
    return token;
}

$.expr[':'].icontains = $.expr.createPseudo(function(text) {
    return function(e) {
        return $(e).text().toUpperCase().indexOf(text.toUpperCase()) >= 0;
    };
});

if (!String.format) {
  String.format = function(format) {
    var args = Array.prototype.slice.call(arguments, 1);
    return format.replace(/{(\d+)}/g, function(match, number) {
      return typeof args[number] != 'undefined'
        ? args[number]
        : match
      ;
    });
  };
}

/* IE11 does not support String.endsWith */
if (!String.prototype.endsWith) {
  String.prototype.endsWith = function(searchString, position) {
      var subjectString = this.toString();
      if (typeof position !== 'number' || !isFinite(position) || Math.floor(position) !== position || position > subjectString.length) {
        position = subjectString.length;
      }
      position -= searchString.length;
      var lastIndex = subjectString.indexOf(searchString, position);
      return lastIndex !== -1 && lastIndex === position;
  };
}

/* IE11 does not support Number.isInteger */
Number.isInteger = Number.isInteger || function(value) {
    return typeof value === "number" &&
           isFinite(value) &&
           Math.floor(value) === value;
};