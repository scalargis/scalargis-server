if (!Portal) {
    Portal = {};
}
if (!Portal.Viewer) {
    Portal.Viewer = {};
}

Portal.Viewer.Planos = (function() {
    var _modulo = 'planos';
    var _widget_config = {};
	var _map;
	var _planosLayer;
	var _feature;
    var _currentFilter = {
        srid: 3763,
        geomEWKT: '',
        format: ''
    }

    var _toggleGroupList = function(e) {
        var element = this;
        var target = $(this).siblings('.resultsList')[0];

        if (!target) {
            target = $(this).parent().siblings('.resultsList')[0];
        }

        if ($(target).hasClass('opened')) {
            $(target).removeClass('opened').addClass('closed');
            if ($(element).is('span')) {
                $(element).removeClass('opened-icon').addClass('closed-icon');
            } else if ($(element).is('a')) {
                var icon = $(element).prev('.icon');
                if (!icon[0]) {
                    icon = $('.icon.group-icon', $(element).parent());
                }
                icon.removeClass('opened-icon').addClass('closed-icon');
            }
        } else {
            $(target).removeClass('closed').addClass('opened');
            if ($(element).is('span')) {
                $(element).removeClass('closed-icon').addClass('opened-icon');
            } else if ($(element).is('a')) {
                var icon = $(element).prev('.icon');
                if (!icon[0]) {
                    icon = $('.icon.group-icon', $(element).parent());
                }
                icon.removeClass('closed-icon').addClass('opened-icon');
            }
        }
        return false;
    }

    var _showPlano = function (e) {
        var this_ = $(this);
        var source = _planosLayer.getSource();

        source.clear();

        if (this_.data('plano-features')) {
            var features = this_.data('plano-features');
            source.addFeatures(features);
            _map.getView().fit(ol.extent.buffer(source.getExtent(), 200), map.getSize());
        } else {
            _getFeature(this_, true);
        }

        var showLayer = function (layer, layer_id, parentLayer) {
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
                            showLayer(lll, layer_id, lr);
                            return;
                        }
                    });
                }
            }
        }

        var layer_id = $(this).data('layer-id');
        var ls = _map.getLayers();
            ls.forEach(function (ll) {
                showLayer(ll, layer_id, null);
        });

    }

    var _getFeature = function (element, zoom) {
        /*
        //Widget Config Example
        {
            "layerRequest":{
                "url": "http://www.wkt.pt/geoserver/wfs",
                "srsName": "EPSG:3857",
                "featureNS": "caop.maps.wkt.pt",
                "featurePrefix": "caop",
                "featureTypes": ["conc_5000m"],
                "outputFormat": "application/json",
                "fieldFilter": "dico"
            },
            "drawMode": "mouseover"
        }
        */
        if (_widget_config.layerRequest && _widget_config.layerRequest.url) {
            var value = element.data('value');
            var options = _widget_config.layerRequest;
            options.valueFilter = value;
            Portal.Viewer.getFeature(options, function (features) {
                if (features && features.length && features.length > 0) {
                    var source = _planosLayer.getSource();
                    element.data('plano-features', features);
                    source.addFeatures(features);
                    if (zoom) {
                        _map.getView().fit(ol.extent.buffer(source.getExtent(), 200), map.getSize());
                    }
                }
            });
        }
    };

    var Init = function () {
    }

    var Load = function(parentId) {
        var cfg = $('input.wigdet-config', parentId).val();

        if (cfg) {
            try {
                _widget_config = JSON.parse(cfg.replace(/'/g, '"'));
            } catch(err) {
                //console.log(err);
                _widget_config = {}
            }
        } else {
            _widget_config = {};
        }

        $(parentId).on('click', 'span.group-icon', _toggleGroupList);
        $(parentId).on('click', 'a.group-title', _toggleGroupList);

        $(parentId).on('click', 'span.zoom-icon', _showPlano);
        if (_widget_config.drawMode && _widget_config.drawMode == 'mouseover') {
            $(parentId).on('mouseover', 'span.zoom-icon', function (e) {
                var this_ = $(this);
                var source = _planosLayer.getSource();

                source.clear();

                if ($(this).data('plano-features')) {
                    var features = $(this).data('plano-features');
                    if (features && features.length && features.length > 0) {
                        source.addFeatures(features);
                    }
                } else {
                    _getFeature(this_, false);
                }
            });
            $(parentId).on('mouseout', 'span.zoom-icon', function (e) {
                var source = _planosLayer.getSource();
                source.clear();
            });
        }
    }

	var setMap = function (map) {
	    _map = map;
	    _planosLayer = Portal.Viewer.getTemporaryLayer();
	}
    return {
        Init: Init,
        Load: Load,
        setMap: setMap
    };

})();