Portal.Plantas = (function () {

    var _modulo = 'plantas';

    var drawInteractions = {};
    var drawControl;

    var _checkNIF = function checkNIF(nif, rules, i, options) {
        var c;
        var checkDigit = 0;
        if (nif != null && nif.length == 9) {
            c = nif.charAt(0);
            if (c == '1' || c == '2' || c == '5' || c == '6' || c == '8' || c == '9') {
                checkDigit = c * 9;
                for (i = 2; i <= 8; i++) {
                    checkDigit += nif.charAt(i - 1) * (10 - i);
                }
                checkDigit = 11 - (checkDigit % 11);
                if (checkDigit >= 10) {
                    checkDigit = 0;
                }
                if (checkDigit == nif.charAt(8)) {
                    return true;
                }
            }
        }
        return false;
    };


    var _addAddEditToolbarButtons = function (parentId) {

        var map = Portal.Viewer.getMap();
        var layer = Portal.Viewer.getTemporaryLayer();
        var source = layer.getSource();

        var onDrawStart = function (evt) {
            if (!(evt.feature.getGeometry() instanceof ol.geom.Point)) {
                //clear previous feature
                var layer = Portal.Viewer.getTemporaryLayer();
                var source;

                if (layer) {
                    source = layer.getSource();
                    source.clear();
                }
            }
        }
        var onDrawEnd = function (evt) {

            evt.feature.set('modulo', _modulo);

            if (evt.feature.getGeometry() instanceof ol.geom.Point) {

                var feature = evt.feature.clone();
                feature.set('modulo', _modulo);

                //clear previous feature
                var layer = Portal.Viewer.getTemporaryLayer();
                var source;

                if (layer) {
                    source = layer.getSource();
                    source.clear();

                    source.addFeature(feature);
                }

            } else {
                evt.feature.set('modulo', _modulo);
            }
        }

        var draw = new ol.interaction.Draw({
            source: source,
            type: 'Point'        
        });        
        draw.on('drawstart', onDrawStart);
        draw.on('drawend', onDrawEnd);
        drawInteractions['ctrlPlantasCreatePoint'] = draw;

        draw = new ol.interaction.Draw({
            source: source,
            type: 'LineString'
        });
        draw.on('drawstart', onDrawStart);
        draw.on('drawend', onDrawEnd);
        drawInteractions['ctrlPlantasCreateLine'] = draw;

        draw = new ol.interaction.Draw({
            source: source,
            type: 'Polygon'
        });
        draw.on('drawstart', onDrawStart);
        draw.on('drawend', onDrawEnd);
        drawInteractions['ctrlPlantasCreatePolygon'] = draw;

        drawControl = new app.genericDrawControl({
            layer: Portal.Viewer.getTemporaryLayer(),
            onEnableControl: function (evt, draw) {
                console.log('teste');
            },
            onDisableControl: function (evt) {
                $(".btn-group[data-group='btn-geometry'] a", parentId).removeClass("active");
            }
        });
        map.addControl(drawControl);
    };

    var _init = function () {
    };

    var _load = function (action, elementId) {
        
        var mapId = $("#mapId").val();
        
        if ($("#active-tool", elementId).attr("value") == "plantas") {
            $(elementId).addClass("active");
        } else {
            $.ajax({
                type: 'POST',
                url: action,
                traditional: true,
                data: {
                    mapId: mapId,
                    __RequestVerificationToken: GetRequestVerificationToken()
                },
                beforeSend: function () {
                    _showLoading(true);
                },
                success: function (r) {
                    if (r.Success) {
                        $(elementId).empty().html(r.Message);
                    } else {
                        //TODO
                    }
                },
                complete: function () {
                    _showLoading(false);
                    $("#tab-tools", "#sidebar").addClass("active");
                },
                error: function (r) {
                    //TODO
                }
            });
        }

    };

    var _loadList = function (parentId) {

        //$('label.tree-toggler', parentId).click(function () {
        //    $(this).parent().children('ul.tree').toggle(300);
        //});

        $('.tlp', parentId).tooltip();

        _addAddEditToolbarButtons(parentId);

        $(".btn-group[data-group='btn-geometry'] a", parentId).click(function (e) {
            var activate = !$(this).hasClass("active");

            $(".btn-group[data-group='btn-geometry'] a", parentId).removeClass("active");

            var m = Portal.Viewer.getMap();

            if (activate) {
                $(this).addClass("active");

                var id = $(this).attr("data-button-id"); 
                drawControl.enableControl(e, drawInteractions[id]);
            } else {
                drawControl.disableControl(e);
            }
        });

        $(".btn-group a[id='btnPlantasZoomGeometry']", parentId).click(function () {
            var aux_feat = Portal.Viewer.getFeaturesTemporaryLayer(_modulo, null);
            if (aux_feat.length > 0) {
                var extent = aux_feat[0].getGeometry().getExtent();
                for (var i = 1; i < aux_feat.length; i++) {
                    extent = ol.extent.extend(extent, aux_feat[i].getGeometry().getExtent());                    
                }
                var map = Portal.Viewer.getMap();

                map.getView().fitExtent(extent, map.getSize());
            }
        });

        $(".btn-group a[id='btnPlantasClearGeometry']", parentId).click(function () {
            var aux_feat = Portal.Viewer.getFeaturesTemporaryLayer(_modulo, null);

            for (var i = 0; i < aux_feat.length; i++) {
                var source = Portal.Viewer.getTemporaryLayer().getSource();

                source.removeFeature(aux_feat[i]);
            }
        });


        $(".do-print", parentId).click(function (evt) {

            var action = $(this).attr("data-action");
            var plantaId = $(this).attr("data-id");
            var escala = null;
            var titulo = null;
            var nif = "";
            var nome = "";
            var srid = null;

            if ($("#nif", parentId).length > 0) {
                nif = $("#nif", parentId).val();
            }
            if ($("#nome", parentId).length > 0) {
                nome = $("#nome", parentId).val();
            }
            if ($("#escala", parentId).length > 0 && $("escala", parentId).val() != "") {
                escala = $("#escala", parentId).val();
            } else {
                if ($(this).closest("li").find(".txt-escala").length > 0  && $(this).closest("li").find(".txt-escala").val() != "") {
                    escala = $(this).closest("li").find(".txt-escala").val();
                } else {
                    escala = ~~Portal.Viewer.getMapCurrentScale();
                }
            }
            if ($("#srid", parentId).length > 0) {
                srid = $("#srid", parentId).val();
            }
            /*if ($("#titulo", parentId).length > 0) {
                titulo = $("#titulo", parentId).val();
            }*/
            if ($(this).closest("li").find(".txt-titulo").length > 0 && $(this).closest("li").find(".txt-titulo").val() != "") {
                titulo = $(this).closest("li").find(".txt-titulo").val();
            }

            if ($(this).attr("data-identificacao") != null && $(this).attr("data-identificacao") == "True" && nif.length > 0) {
                if (!_checkNIF(nif)) {
                    var html = "<div class='alert alert-danger'>";
                    html = html + "<a class='close' data-dismiss='alert'>×</a>";
                    html = html + "<h5 class='alert-heading'>Informação</h5>O NIF não está correto.</div>";

                    $("#validation", parentId).empty().html(html);

                    return false;
                }
            }

            if ($(this).attr("data-marcacao-local") != null && $(this).attr("data-marcacao-local") == "True") {
                var aux_feat = Portal.Viewer.getFeaturesTemporaryLayer("plantas", null);
                if (aux_feat.length == 0) {
                    var html = "<div class='alert alert-danger'>";
                    html = html + "<a class='close' data-dismiss='alert'>×</a>";
                    html = html + "<h5 class='alert-heading'>Informação</h5>É obrigatório marcar o local.</div>";

                    $("#validation", parentId).empty().html(html);

                    return true;
                }
            }

            var plantasSrid = $("#plantasSRID", parentId).val();

            var format = new ol.format.WKT();

            var m = Portal.Viewer.getMap();
            var extent = m.getView().calculateExtent(m.getSize());            

            var extentEWKT = format.writeGeometry(ol.geom.Polygon.fromExtent(extent).transform(Portal.Viewer.getMapProjectionCode(), 'EPSG:' + plantasSrid));
            extentEWKT = "SRID=" + plantasSrid + ';' + extentEWKT;
            
            var geomEWKT = null;
            if (Portal.Viewer.getFeaturesTemporaryLayer(_modulo, null).length > 0) {
                var feature = Portal.Viewer.getFeaturesTemporaryLayer(_modulo, null)[0];
                geomEWKT = format.writeGeometry(feature.getGeometry().clone().transform(Portal.Viewer.getMapProjectionCode(), 'EPSG:' + plantasSrid));
                geomEWKT = "SRID=" + plantasSrid + ';' + geomEWKT;
            }

            var layers = $.grep(m.getLayers().getArray(), function (layer) {
                if (layer.get('visible')) {
                    var source = layer.getSource();

                    if (source instanceof ol.source.TileWMS || source instanceof ol.source.ImageWMS) {
                        return true;
                    }
                }
            });
            

            var urlLayers = [];
            var opacityLayers = [];
            if ($(this).attr("data-emissao-livre") != null && $(this).attr("data-emissao-livre") == "True") {
                for (var i = 0; i < layers.length; i++) {
                    var layer = layers[i];
                    var source = layer.getSource();
                    var url = '';
                    var opacity = 1;
                    
                    if (source instanceof ol.source.TileWMS) {
                        url = source.getUrls()[0];
                    } else {
                        url = source.getUrl();
                    }
                    url = url.replace("/gwc/service", "");

                    if (url.indexOf("?") < 0) {
                        url = url + "?";
                    }

                    url += '&LAYERS=' + source.getParams().LAYERS || source.getParams().Layers || source.getParams().layers;
                    url += '&STYLES=';
                    if (source.getParams().STYLES) {
                        url += source.getParams().STYLES;
                    } else if (source.getParams().Styles) {
                        url += source.getParams().Styles;
                    } else if (source.getParams().styles) {
                        url += source.getParams().styles;
                    };
                    url += '&VERSION=' + source.getParams().VERSION || source.getParams().Version || source.getParams().version;

                    opacity = layer.getOpacity();

                    urlLayers.push(url);
                    opacityLayers.push(opacity);
                };
            }

            $("#validation", parentId).empty().html("");

            $.ajax({
                type: 'POST',
                url: action,
                traditional: true,
                data: {
                    plantaId: plantaId,
                    escala: escala,
                    titulo: titulo,
                    nif: nif,
                    nome: nome,
                    srid: plantasSrid,
                    layers: urlLayers,
                    layersOpacity: opacityLayers,
                    extentEWKT: extentEWKT,
                    geomEWKT: geomEWKT,
                    __RequestVerificationToken: GetRequestVerificationToken()
                },
                beforeSend: function () {
                    _showLoading(true);
                },
                success: function (r) {
                    if (r.Success) {
                        var url = r.Data.url;
                        window.open(url, "_blank");
                    } else {
                        if (r.Data != null && r.Data.info) {
                            $("#validation", parentId).empty().html(r.Message);
                        } else {
                            $("#informationDiv").informationModal({
                                heading: 'Informação',
                                body: r.Message,
                                messageClass: "alert alert-danger",
                                callback: null
                            });
                        }
                    }
                },
                complete: function () {
                    _showLoading(false);
                    //$("#tab-tools", "#sidebar").addClass("active");
                },
                error: function (r) {
                    $("#informationDiv").informationModal({
                        heading: 'Informação',
                        body: 'Ocorreu um erro no servidor',
                        messageClass: "alert alert-danger",
                        callback: null
                    });
                }
            });
        });

    };

    var _loadListConsulta = function (formId, modulo, moduloId) {
        var _modulo = modulo;
        var _layer = app.featuresLayer;

        var featureHighlight = function () {
            $(".results-row[data-feature-id]").removeClass("highlighted");
            if (!$(".results-row[data-feature-id = '" + this.attributes.gid + "']").hasClass("highlighted")) {
                $(".results-row[data-feature-id = '" + this.attributes.gid + "']").addClass("highlighted");
            }
        };
        var featureUnhighlight = function () {
            $(".results-row[data-feature-id = '" + this.attributes.gid + "']").removeClass("highlighted");
        };
        var featureSelect = function () {
            $(".results-row[data-feature-id = '" + this.attributes.gid + "']").find(".results-row-actions").show();
        };
        var featureUnselect = function () {
            $(".results-row[data-feature-id = '" + this.attributes.gid + "']").removeClass("highlighted");
            $(".results-row[data-feature-id = '" + this.attributes.gid + "']").find(".results-row-actions").hide();
        };

        var _drawPlantaExtent = function (id, geomEWKT, zoom) {
            var geom = app.getTransformedGeometry(geomEWKT);
            var feature = new OpenLayers.Feature.Vector(geom);

            feature.attributes.gid = id;
            feature.attributes.modulo = _modulo;
            feature.attributes.readonly = true;

            feature.highlight = featureHighlight;
            feature.unhighlight = featureUnhighlight;
            feature.select = featureSelect;
            feature.unselect = featureUnselect;

            _layer.addFeatures(feature, { silent: true });

            if (geom != null && zoom == true) {
                app.mapPanel.map.zoomToExtent(geom.getBounds(), false);
                app.mapPanel.map.zoomTo(22);
            }
        };

        $(".modulo-content .results-area #btnDrawFeatures").click(function () {
            Portal.ClearMapFeatures();

            $('.modulo-content .results-area a[data-extent]').filter(function () {
                return ($(this).attr('data-extent').length > 0);
            }).each(function () {
                var geom = app.getTransformedGeometry($(this).attr("data-extent"));
                _drawPlantaExtent($(this).attr("data-id"), $(this).attr("data-extent"), false);
            });
        });

        $(".modulo-content .results-area #btnClearFeatures").click(function () {
            Portal.ClearMapFeatures();
        });

        $(".modulo-content .results-area [data-id]").click(function () {
            Portal.ClearMapFeatures();

            if ($(this).attr("data-extent") != undefined && $(this).attr("data-extent") != "") {
                _drawPlantaExtent($(this).attr("data-id"), $(this).attr("data-extent"), true);
            }
        });

        var extent = null;

        $('.modulo-content .results-area a[data-extent]').filter(function () {
            return ($(this).attr('data-extent').length > 0);
        }).each(function () {
            var geom = app.getTransformedGeometry($(this).attr("data-extent"));

            if (extent != null) {
                extent.extend(geom.getBounds());
            } else {
                extent = geom.getBounds();
            }

            _drawPlantaExtent($(this).attr("data-id"), $(this).attr("data-extent"), false);
        });

        if (extent != null) {
            app.mapPanel.map.zoomToExtent(extent, false);
        }

        $("#sidebar .tab-content").getNiceScroll().resize();

    };

    var _showLoading = function (show) {
        if (show) {
            Portal.Viewer.ShowLoading(".menu-bar-widget." + _modulo + " .menu-bar-body");
        } else {
            Portal.Viewer.HideLoading(".menu-bar-widget." + _modulo + " .menu-bar-body");
        }
    };

    return {
        Init: _init,
        Load: _load,
        LoadList: _loadList,
        LoadListConsulta: _loadListConsulta
    }
} ());