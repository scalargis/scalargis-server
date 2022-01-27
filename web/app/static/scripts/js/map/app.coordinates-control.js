if (!window.app) {
    window.app = {};
}
var app = window.app;

app.coordinatesControl = function (opt_options) {
    var options = opt_options || {};

    var buttonCoordinates = document.createElement('button');
    buttonCoordinates.innerHTML = '<i class="fa fa-crosshairs" title="' + (options.coordinatesTipLabel || 'Obter Coordenadas') +  '"><i>';

    var this_ = this;

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
            var coordinate = evt.coordinate;

            $(".menu-button.coordinates").trigger('open');

            if (options.onMapClick) {
                options.onMapClick(evt);
            }           
        }

    }

    var handleCoordinates = function (e) {
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

    function removeCoordinatesInteraction() {
        //$(this_.getMap().getViewport()).off('mousemove', mouseMoveHandler);

        var layer = options.layer;
        var source;

        if (layer) {
            source = layer.getSource();

            if (source && this_.feature) {
                source.removeFeature(this_.feature);
            }
        }
        this_.feature = null;

        $(this_.get('button')).removeClass('active');
        this_.set('active', false);
    }

    buttonCoordinates.addEventListener('click', handleCoordinates, false);
    buttonCoordinates.addEventListener('touchstart', handleCoordinates, false);

    var element = document.createElement('div');
    element.className = (options.className ? options.className + ' ' : '') + 'coordinates-control ol-selectable ol-control';
    element.appendChild(buttonCoordinates);

    ol.control.Control.call(this, {
        element: element,
        target: options.target
    });

    this.set('options', options);
    this.set('button', buttonCoordinates);
    this.set('handleMapClick', handleMapClick);
    this.set('removeCoordinatesInteraction', removeCoordinatesInteraction);
    this.set('active', false);
};
ol.inherits(app.coordinatesControl, ol.control.Control);

app.coordinatesControl.prototype.disableControl = function (e) {
    var controls = this.getMap().getControls().getArray();
    for (var i = 0; i < controls.length; i++) {
        if (this != controls[i] && controls[i].activateControl) {
            controls[i].activateControl();
        }
    }

    $(this.get('button')).removeClass('active');

    this.getMap().un('singleclick', this.get('handleMapClick'));

    var fn = this.get('removeCoordinatesInteraction');
    fn();

    this.set('active', false);

    if (this.get('options').onDisableControl) {
        this.get('options').onDisableControl(e);
    }
}

app.coordinatesControl.prototype.setFeature = function (feature) {
    this.feature = feature;
}