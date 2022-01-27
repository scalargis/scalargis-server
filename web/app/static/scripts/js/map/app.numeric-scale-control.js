if (!window.app) {
    window.app = {};
}
var app = window.app;

var INCHES_PER_UNIT = {
    'm': 39.37,
    'degrees': 4374754
};
var DOTS_PER_INCH = 72;

app.NumericScaleControl = function (opt_options) {
    var options = opt_options || {};

    var this_ = this;

    // Add control
    var el = $('<div class="numericscale-control ol-control"><input class="form-control input input-xs" type="text" value="" /></div>');
    ol.control.Control.call(this, {
        element: el[0],
        target: options.target
    });

    this.set('options', options);
    this.set('active', false);
};
ol.inherits(app.NumericScaleControl, ol.control.Control);

app.NumericScaleControl.prototype._getScaleForResolution = function(resolution, units) {
    var scale = INCHES_PER_UNIT[units] * DOTS_PER_INCH * resolution;
    var value = Math.round(scale);
    return value;
}

app.NumericScaleControl.prototype._getResolutionForScale = function (scale, units) {
  return parseFloat(scale) / (INCHES_PER_UNIT[units] * DOTS_PER_INCH);
}


app.NumericScaleControl.prototype.setMap = function(map) {
    ol.control.Control.prototype.setMap.call(this, map);

    var me = this;
    var mapListener = function(e) {
        if (!me.get('active')) return; // Do not update if disabled
        var resolution = map.getView().getResolution();
        var scale = me._getScaleForResolution(resolution, 'm');
        var numericScaleFormated = '1:' + scale;
        $(me.element).find('input').val(numericScaleFormated);
    }

    var inputListener = function(e) {
        if (e.keyCode === 13) {
            var scale = parseInt($(this).val().split(':').pop(), 10);
            if (!isNaN(scale)) {
                var resolution = me._getResolutionForScale(scale, 'm');
                map.getView().setResolution(resolution);
            }
        }
    }

    var focusListener = function(e) {
        $(this).select();
    }

    // Add map event
    if (map) {
        map.on('moveend', mapListener);
        $(me.element).find('input').bind('keyup', inputListener);
        $(me.element).find('input').bind('click', focusListener);
    }

    // Remove event listener
    else {
        map.un('moveend', mapListener);
        $(me.element).find('input').unbind('keyup', inputListener);
        $(me.element).find('input').unbind('click', focusListener);
    }
};
