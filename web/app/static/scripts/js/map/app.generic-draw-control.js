if (!window.app) {
    window.app = {};
}
var app = window.app;

app.genericDrawControl = function (opt_options) {
    var options = opt_options || {};

    var sketch; //Currently drawed feature

    var feature;

    var active = false;

    var this_ = this;

    var element = document.createElement('div');

    ol.control.Control.call(this, {
        element: element,
        target: options.target
    });

    this.set('options', options);
};
ol.inherits(app.genericDrawControl, ol.control.Control);

app.genericDrawControl.prototype.disableControl = function (e) {
    var controls = this.getMap().getControls().getArray();
    for (var i = 0; i < controls.length; i++) {
        if (this != controls[i] && controls[i].activateControl) {
            controls[i].activateControl();
        }
    }

    if (this.get('currentDrawInteraction')) {
        var map = this.getMap();
        var draw = this.get('currentDrawInteraction');
        map.removeInteraction(draw);
    }

    if (this.get('options').onDisableControl) {
        this.get('options').onDisableControl(e);
    }
}

app.genericDrawControl.prototype.enableControl = function (e, draw) {
    var map = this.getMap();

    if (this.get('currentDrawInteraction')) {
        var oldDraw = this.get('currentDrawInteraction');
        map.removeInteraction(oldDraw);
    }

    var controls = map.getControls().getArray();
    for (var i = 0; i < controls.length; i++) {
        if (this != controls[i] && controls[i].disableControl) {
            controls[i].disableControl();
        }
    }
    for (var i = 0; i < controls.length; i++) {
        if (this != controls[i] && controls[i].deactivateControl) {
            controls[i].deactivateControl();
        }
    }
    map.removeInteraction(draw);
    this.getMap().addInteraction(draw);
    this.set('currentDrawInteraction', draw);

    if (this.get('options').onEnableControl) {
        this.get('options').onEnableControl(e, draw);
    }
}