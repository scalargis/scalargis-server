if (!window.app) {
    window.app = {};
}
var app = window.app;

app.googleStreetViewControl = function (opt_options) {
    var options = opt_options || {};

    this.generateID = function () {

        var s4 = function() {
            return Math.floor((1 + Math.random()) * 0x10000)
                       .toString(16)
                       .substring(1);
        }

        return s4() + s4() + s4() + s4() + s4() + s4() + s4() + s4();
    }

    var this_ = this;

    this_.layer = options.layer;

    this_.iconStyle = options.iconStyle || new ol.style.Style({
                image: new ol.style.Icon({
                    anchor: [0.5, 1],
                    anchorXUnits: 'fraction',
                    anchorYUnits: 'fraction',
                    src: '../static/images/icons/location-icon.svg'
                })
            });

    this_.panelTitle = options.panelTitle || 'Google Street View';
    this_.panelWindow = null;
    this_.panelonclosed = function (evt) {
        if (this_.disableControl) {
            this_.disableControl();
        }

        if (this_.feature) {
            var layer = this_.layer;
            var source;

            if (layer) {
                source = layer.getSource();

                if (source && this_.feature) {
                    source.removeFeature(this_.feature);
                }
            }
            this_.feature = null;
        }

        this_.panelWindow = null;
        $(this).remove();
    };

    var buttonGoogleStreetView = document.createElement('button');
    var toolTip = options.buttonTipLabel || 'Ver local no Google Street View';
    buttonGoogleStreetView.innerHTML = '<i class="fa fa-street-view" title="' + toolTip +  '"><i>';
    buttonGoogleStreetView.title = toolTip;

    var handleMapClick = function (evt) {

        var map = this_.getMap();

        var ints = map.getInteractions().getArray();
        var drawing = false;

        for (var i = 0; i < ints.length; i++) {
            if (map.getInteractions().getArray()[i] instanceof ol.interaction.Draw) {
                drawing = true;
                break;
            }
        }

        if (!drawing) {
            /*
            if (options.onMapClick) {
                <options.onMapClick(evt);
            }
            */
            var lonlat = ol.proj.transform(evt.coordinate, map.getView().getProjection().getCode(), 'EPSG:4326');
            var layer = this_.layer;
            var source;

            if (layer) {
                source = layer.getSource();

                if (source && this_.feature) {
                    try {
                        source.removeFeature(this_.feature);
                    } catch (ex) {}
                }
            }

            this_.feature = new ol.Feature({
                geometry: new ol.geom.Point(evt.coordinate)
            });
            this_.feature.setStyle(this_.iconStyle);
            layer.getSource().addFeature(this_.feature);

            if (!this_.panelWindow) {
                this_.panelWindow = $.jsPanel({
                    id: this_.generateID(),
                    position:    {my: "left-top", at: "left-top", offsetX: 15, offsetY: 15},
                    contentSize: {width: 500, height: 350},
                    headerTitle: this_.panelTitle,
                    content: '',
                    callback:    function () {
                        var panoramaOptions = {
                            position: new google.maps.LatLng(lonlat[1],lonlat[0]),
                            pov: {
                              heading: 34,
                              pitch: 10
                            }
                        };
                        var elem = $('div.jsPanel-content', this)[0];
                        var panorama = new  google.maps.StreetViewPanorama(elem, panoramaOptions);
                        panorama.addListener('position_changed', function() {
                            var feature = this_.feature;
                            if (feature) {
                                var map = this_.getMap();
                                var pos = panorama.getPosition();
                                var coords = ol.proj.transform([pos.lng(), pos.lat()], 'EPSG:4326', map.getView().getProjection().getCode());
                                feature.set('geometry', new ol.geom.Point(coords));
                            }
                        });

                        //this['panorama'] = panorama;
                        this_.panorama = panorama;
                    },
                    onclosed: this_.panelonclosed,
                    onmaximized: function(){
                        var p = this_.panorama;
                        google.maps.event.trigger(p, 'resize');
                    },
                    dragit: {
                        containment: 'window',
                    },
                    resizeit: {
                        start: function (panel, size) {
                        },
                        stop: function (panel, size) {
                            var p = this_.panorama;
                            google.maps.event.trigger(p, 'resize');
                        }
                    }
                });
            } else {
                this_.panelWindow.normalize();
                this_.panorama.setPosition(new google.maps.LatLng(lonlat[1],lonlat[0]));
            }
        }
    }

    var handleGoogleStreetView = function (e) {
        var controls = this_.getMap().getControls().getArray();
        for (var i = 0; i < controls.length; i++) {
            if (this_ != controls[i] && controls[i].disableControl) {
                controls[i].disableControl();
            }
        }

        var active = this_.get('active');

        if (active) {
            this_.disableControl();
        } else {
            for (var i = 0; i < controls.length; i++) {
                if (this_ != controls[i] && controls[i].deactivateControl) {
                    controls[i].deactivateControl();
                }
            }

            active = true;
            map.on('singleclick', handleMapClick);
            $(this).addClass('active');
            this_.set('active', active);
        }
    }

    function removeGoogleStreetViewInteraction() {
        $(this_.get('button')).removeClass('active');
        this_.set('active', false);
    }

    buttonGoogleStreetView.addEventListener('click', handleGoogleStreetView, false);
    buttonGoogleStreetView.addEventListener('touchstart', handleGoogleStreetView, false);

    var element = document.createElement('div');
    element.className = (options.className ? options.className + ' ' : '') + 'google-streetview-control ol-selectable ol-control';
    element.appendChild(buttonGoogleStreetView);

    ol.control.Control.call(this, {
        element: element,
        target: options.target
    });

    this.set('options', options);
    this.set('button', buttonGoogleStreetView);
    this.set('handleMapClick', handleMapClick);
    this.set('removeGoogleStreetViewInteraction',  removeGoogleStreetViewInteraction);
    this.set('active', false);
};
ol.inherits(app.googleStreetViewControl, ol.control.Control);

app.googleStreetViewControl.prototype.disableControl = function (e) {
    var controls = this.getMap().getControls().getArray();
    for (var i = 0; i < controls.length; i++) {
        if (this != controls[i] && controls[i].activateControl) {
            controls[i].activateControl();
        }
    }

    $(this.get('button')).removeClass('active');

    this.getMap().un('singleclick', this.get('handleMapClick'));

    var fn = this.get('removeGoogleStreetViewInteraction');
    fn();

    this.set('active', false);

    if (this.get('options').onDisableControl) {
        this.get('options').onDisableControl(e);
    }
}

app.googleStreetViewControl.prototype.setFeature = function (feature) {
    this.feature = feature;
}