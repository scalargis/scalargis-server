if (!Portal) {
    Portal = {};
}
if (!Portal.Viewer) {
    Portal.Viewer = {};
}

Portal.Viewer.Catalog = (function () {

    var _modulo = 'catalog';

	var _map;
	var _layer;

    var _init = function () {
    };

    var _load = function (parentId, layersCollection) {
        $("#searchCatalogo").on("show", function (event) {
            $(this).next(".results-area").empty();
        });

        $("#catalogo").change(function () {

            _showLoading(true);

            $("#searchCatalogo").next(".results-area").empty().html('');

            var url = $(this).data('url') + '?id=' + $(this).val();

            $.ajax({
                type: 'POST',
                url: url,
                traditional: true,
                data: { id: $(this).val() },
                success: function (r) {
                    $("#catalogoFields").empty();

                    if (r.Success) {
                        $("#catalogoFields").html(r.Message);
                        _init_controls();
                    } else {
                        /*
                        $("#windowModal").modal("hide");
                        $("#informationDiv").informationModal({
                            heading: 'Informação',
                            body: 'Ocorreu um erro ao abrir o catálogo.',
                            messageClass: "alert alert-success",
                            callback: function () {
                                window.location = $("#formService").prop("action");
                            }
                        });
                        */
                    }
                },
                error: function (r) {
                    $("#catalogoFields").html('').destroy();
                },
                complete: function (e) {
                    _showLoading(false);
                }
            });
        });

        /* Form submit */
        $('#formCatalogo').submit(function (e) {
            e.preventDefault();

            var mapSrid = Portal.Viewer.getMapProjectionCode();
            var extent = _map.getView().calculateExtent(_map.getSize());
            var bbox = ol.proj.transformExtent(extent, _map.getView().getProjection(), ol.proj.get('EPSG:4326')).join(',');

            owsCatalog.setMap(map);

            $('#formCatalogo #MapExtent').val(bbox);

            _showLoading(true);

            $.ajax({
                type: 'POST',
                url: $(this).attr('action'),
                traditional: true,
                data: $(this).serialize(),
                success: function (r) {
                    $("#resultsCatalogo").html("");
                    if (r.Success) {
                        $("#searchAreaCatalogo").collapse("hide");
                        $("#searchCatalogo").next(".results-area").html(r.Message).show();
                        _loadData();
                    } else {
                        var html = "<div class='alert alert-danger'>" + r.Message + "</div>";
                        $("#searchCatalogo").next(".results-area").html(html).show();
                    }
                },
                error: function (e) {
                    var msg = "Ocorreu um erro ao pesquisar o catálogo"
                    var html = "<div class='alert alert-danger'>" + msg + "</div>";
                    $("#searchCatalogo").next(".results-area").html(html);
                },
                complete: function(e) {
                    _showLoading(false);
                }
            });
        });

        //TODO - clear form
        $('.btn-clear-form','#formCatalogo').click(function(e) {
            e.preventDefault();
            $(this).closest('form').trigger('reset');
            $(this).closest('form').children('.results-area').html('');
        });

        $('.nav-catalog-layers-panel', '.catalog').click(function (e) {
            $('#formCatalogo', '.catalog').show();
            $('.nav-catalog-layers-panel', '.catalog').hide();
            $('#addLayersCatalog', '.catalog').hide();
        });

        $('#resultsCatalogo').on('click', 'a[data-page]', function (e) {
            _showLoading(true);

            $.ajax({
                type: 'POST',
                url: $("#formCatalogo").attr("action"),
                traditional: true,
                data: $("#formCatalogo").serialize() + "&page=" + $(this).attr("data-page"),
                success: function (r) {
                    $("#resultsCatalogo").html("");
                    if (r.Success) {
                        $("#resultsCatalogo").html(r.Message).show();
                        _loadData();
                    } else {
                        if ($("#Id").prop("value") == "0") $("#Id").prop("value", r.Id);

                        $("#windowModal").modal("hide");

                        $("#informationDiv").informationModal({
                            heading: 'Informação',
                            body: "Ocorreu um erro ao pesquisar o catálogo.",
                            messageClass: "alert alert-error",
                            callback: function () {
                            }
                        });
                    }
                },
                error: function (r) {
                    $("#resultsCatalogo").html("");
                },
                complete: function (e) {
                    _showLoading(false);
                }
            });
        });

        $('#resultsCatalogo').on('click', 'a[data-wms-link]', function (e) {
            var url = $(this).data('wms-link');

            $('#formCatalogo', '.catalog').hide();
            $('#addLayersCatalog', '.catalog').show();
            $('.nav-catalog-layers-panel', '.catalog').show();

            owsCatalog.getCapabilities(url.trim(), null, 'wms');
        });

        //var options = { rootElementId: '.menu-bar.catalog .menu-bar-body', parentId: '#addLayersCatalog', layers: layersCollection }
        //var options = { rootElementId: '.menu-bar.catalog', parentId: '.menu-bar.catalog #addLayersCatalog', layers: layersCollection }
        var options = { rootElementId: '.menu-bar-widget.catalog', parentId: '.menu-bar-widget.catalog #addLayersCatalog', layers: layersCollection }
        owsCatalog = new OWS(options);

        _init_controls();
    };

    var _init_controls = function() {
        /* Tipo de Catálogo GeoNetwork */
        var options = {};
        options.format = 'DD/MM/YYYY';
        options.keepOpen = false;
        options.showClose = true;
        options.showClear = true;
        options.locale = 'pt';
        $('.date').datetimepicker(options);
        $('.dateclearbutton').on('click', function (e) {
            $(this).closest('.date').data("DateTimePicker").date(null);
        });


        $('.tipoPesqCat').click(function () {
            $('.pesqCatAvancada').toggle();
            $(this).text(!$('.pesqCatAvancada').is(':visible') ? 'Pesquisa Avançada' : 'Pesquisa Simples');
            $("#PesquisaAvancada").val($('.pesqCatAvancada').is(':visible'));
        });

        $('#Temas').multiselect({
            buttonWidth: '100%',
            maxHeight: 200,
            includeSelectAllOption: true,
            enableClickableOptGroups: true,
            selectAllText: 'Todos',
            allSelectedText: 'Todos',
            nonSelectedText: 'Escolha um ou mais temas',
            nSelectedText: ' Temas'
        });
    }

    var _loadData = function () {
        $('#resultsCatalogo a[fid]').each(function (index) {
            if ($(this).attr('data-extent-bbox') != undefined && $(this).attr('data-extent-bbox') != '') {

                var mapSrid = Portal.Viewer.getMapProjectionCode();

                var geom = Portal.Viewer.getPolygonFromExtent($(this).attr('data-extent-bbox')).transform('EPSG:4326', Portal.Viewer.getMapProjectionCode());
                var feature = new ol.Feature({
                    geometry: geom,
                    fid: $(this).attr('fid'),
                    modulo: 'metadados'
                });

                $(this).hover(
                        function () {
                            _layer.getSource().addFeature(feature);
                        },
                        function () {
                            _layer.getSource().removeFeature(feature);
                        }
                );
                $(this).click(function () {
                    if (feature != null && feature.getGeometry() != null) {
                        var extent = feature.getGeometry().getExtent();
                        _map.getView().fit(extent,_map.getSize());
                    }
                });
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