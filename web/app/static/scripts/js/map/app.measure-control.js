if (!window.app) {
    window.app = {};
}
var app = window.app;

app.measureControl = function (opt_options) {
    var options = opt_options || {};

    var draw; // global so we can remove it later
    var sketch; //Currently drawed feature

    var feature;

    var buttonMeasureLength = document.createElement('button');
    var toolTipLength = options.buttonTipLabel_l || 'Medir Distância';
    buttonMeasureLength.className = 'measure-length';
    buttonMeasureLength.innerHTML = '<i class="fac-ruler-line" title="' + toolTipLength +  '"><i>';
    buttonMeasureLength.title = toolTipLength;

    var buttonMeasureArea = document.createElement('button');
    var toolTipArea = options.buttonTipLabel_a || 'Medir Área';
    buttonMeasureArea.style.cssText = 'display: none';
    buttonMeasureArea.className = 'measure-area';
    buttonMeasureArea.innerHTML = '<i class="fac-ruler-area" title="' + toolTipArea + '"><i>';
    buttonMeasureArea.title = toolTipArea;

    var this_ = this;

    this_.projection = options.projection;
    this_.containment = options.containment || null;
    this_.panelWindow = null;

    this_.panelonclosed = function (evt) {
        if (this_.disableControl) {
            this_.disableControl();
        }

        this_.panelWindow = null;
        $(this).remove();
    };

    /**
    * format length output
    * param {ol.geom.LineString} line
    * return {string}
    */
    var formatLength = function (line) {
        var length = Math.round(line.getLength() * 1000) / 1000;
        var output;
        if (length > 10000) {
            output = (Math.round(length / 1000 * 1000) / 1000) +
                ' ' + 'km';
        } else {
            output = (Math.round(length * 1000) / 1000) +
                ' ' + 'm';
        }
        return output.replace('.',',');
    };

    /**
    * format length output
    * param {ol.geom.Polygon} polygon
    * return {string}
    */
    var formatArea = function (polygon) {
        var area = polygon.getArea();
        var output;
        if (area > 10000) {
            output = (Math.round(area / 10000 * 1000) / 1000) +
                ' ' + 'ha';
            //output = (Math.round(area / 1000000 * 100) / 100) +
            //    ' ' + 'km<sup>2</sup>';
        } else {
            output = (Math.round(area * 1000) / 1000) +
                ' ' + 'm<sup>2</sup>';
        }
        return output.replace('.',',');
    };

    /**
    * handle pointer move
    * param {Event} evt
    */
    var mouseMoveHandler = function (evt) {
        if (sketch) {
            var outputDistance;
            var outputArea;
            var geom_sketch = (sketch.getGeometry());

            var geom = geom_sketch.clone().transform(this_.map_.getView().getProjection(),this_.projection);

            if (geom instanceof ol.geom.Polygon) {
                var coords = geom.getCoordinates();

                if (coords.length > 0 && coords[0].length > 1) {
                    var line = new ol.geom.LineString(coords[0]);
                    outputDistance = formatLength((line));
                }

                outputArea = formatArea(/** type {ol.geom.Polygon} */(geom));

            } else if (geom instanceof ol.geom.LineString) {
                outputDistance = formatLength( /** type {ol.geom.LineString} */(geom));
            }

            $(".measure-info-area", "#measureOutput").html(outputArea || '');
            $(".measure-info-distance", "#measureOutput").html(outputDistance || '');

            $('.measure-info-area', this_.panelWindow.content).html(outputArea || '');
            $('.measure-info-distance', this_.panelWindow.content).html(outputDistance || '');
        }
    };

    function removeMeasureInteraction() {
        var controls = this_.getMap().getControls().getArray();
        for (var i = 0; i < controls.length; i++) {
            if (this_ != controls[i] && controls[i].activateControl) {
                controls[i].activateControl();
            }
        }

        $(this_.getMap().getViewport()).off('mousemove', mouseMoveHandler);

        var layer = options.layer;
        var source;

        if (layer) {
            source = layer.getSource();

            if (source && feature) {
                source.removeFeature(feature);
            }
        }
        feature = null;

        if(draw) {
            this_.getMap().removeInteraction(draw);
        }

        $(this_.get('button')).removeClass('active');
        this_.set('active', false);
    }

    function addMeasureInteraction(type) {
        var controls = this_.getMap().getControls().getArray();
        for (var i = 0; i < controls.length; i++) {
            if (this_ != controls[i] && controls[i].deactivateControl) {
                controls[i].deactivateControl();
            }
        }

        if (!this_.panelWindow) {
            var html = '<div class="measure-info" style="clear: both;border-bottom: 1px solid #e9e9e9; height: 2em; line-height: 2em; font-size: 12px; clear: both;">';
            html += '<p class="pull-left">Comprimento: </p>';
            html += '<p class="pull-right measure-info-distance">m</p>';
            html += '</div>';
            html += '<div class="measure-info" style="clear: both;border-bottom: 1px solid #e9e9e9; height: 2em; line-height: 2em; font-size: 12px; clear: both;">';
            html += '<p class="pull-left">Área: </p>';
            html += '<p class="pull-right measure-info-area">m²</p>';
            html += '</div>';

            function panelpos() {
                return {
                    my: 'right-top',
                    at: 'right-top',
                    offsetY: $('#map-navbar-container').position().top + $('#map-navbar-container').outerHeight() + 8,
                    offsetX: -55
                };
            }

            this_.panelWindow = $.jsPanel({
                id: 'measure-panel',
                headerTitle: 'Medição',
                contentSize:  { width: '250', height: 'auto' },
                position: panelpos,
                dragit: {
                    containment: 'window',
                },
                contentOverflow: { horizontal: 'hidden', vertical: 'auto' },
                headerControls: {
                    controls:  'closeonly'
                },
                content: html,
                onclosed: this_.panelonclosed,
                resizeit:  false,
                onwindowresize: function(event, panel) {
                    panel.reposition(panelpos());
                }
            });
        } else {
            this_.panelWindow.normalize();
        }

        $(this_.getMap().getViewport()).off('mousemove', mouseMoveHandler).on('mousemove', mouseMoveHandler);

        var layer = options.layer;
        var source;

        if (layer) {
            source = layer.getSource();

            if (source && feature) {
                source.removeFeature(feature);
            }
        }

        feature = null;

        this_.getMap().removeInteraction(draw);

        //var type = (typeSelect.value == 'area' ? 'Polygon' : 'LineString');
        var type = (type == 'area' ? 'Polygon' : 'LineString');
        draw = new ol.interaction.Draw({
            source: source,
            type: /** type {ol.geom.GeometryType} */ (type)
        });
        this_.getMap().addInteraction(draw);

        draw.on('drawstart',
            function (evt) {

                //clear previous feature
                var layer = options.layer;
                var source;

                if (layer) {
                    source = layer.getSource();

                    if (source && feature) {
                        source.removeFeature(feature);
                    }
                }

                // set sketch
                sketch = evt.feature;

            }, this);

        draw.on('drawend',
            function (evt) {
                // unset sketch
                sketch = null;
                feature = evt.feature;
            }, this);
    }

    var handleMeasureLength = function (e) {
        var controls = this_.getMap().getControls().getArray();
        for (var i = 0; i < controls.length; i++) {
            if (this_ != controls[i] && controls[i].disableControl) {
                controls[i].disableControl();
            }
        }

        if ($(this_.get('button')).filter('.measure-length').hasClass('active')) {
            removeMeasureInteraction();
        } else {
            $(this_.get('button')).removeClass('active');

            var active = true;
            $(this_.get('button')).filter('.measure-length').addClass('active');
            this_.set('active', active);
            addMeasureInteraction('length');
        }
    };

    var handleMeasureArea = function (e) {
        var controls = this_.getMap().getControls().getArray();
        for (var i = 0; i < controls.length; i++) {
            if (this_ != controls[i] && controls[i].disableControl) {
                controls[i].disableControl();
            }
        }
        for (var i = 0; i < controls.length; i++) {
            if (this_ != controls[i] && controls[i].deactivateControl) {
                controls[i].deactivateControl();
            }
        }

        if ($(this_.get('button')).filter('.measure-area').hasClass('active')) {
            removeMeasureInteraction();
        } else {
            $(this_.get('button')).removeClass('active');

            var active = true;
            $(this_.get('button')).filter('.measure-area').addClass('active');
            this_.set('active', active);
            addMeasureInteraction('area');
        }
    };

    buttonMeasureLength.addEventListener('click', handleMeasureLength, false);
    buttonMeasureLength.addEventListener('touchstart', handleMeasureLength, false);

    buttonMeasureArea.addEventListener('click', handleMeasureArea, false);
    buttonMeasureArea.addEventListener('touchstart', handleMeasureArea, false);

    var element = document.createElement('div');
    element.className = (options.className ? options.className + ' ' : '') + 'measure-control ol-selectable ol-control';

    var _mouseoutId;

    element.addEventListener("mouseover", function (e) {
        $('button', this).show();

        if (options.target && _mouseoutId) {
            clearTimeout(_mouseoutId);
        }
    }
    , true);
    element.addEventListener("mouseout", function (e) {
        var _this = this;

        if (options.target) {
            _mouseoutId = setTimeout(function () {
                $('button', _this).hide();
                if ($('button.active', _this).length > 0) {
                    $('button.active', _this).show();
                } else {
                    $('button:first', _this).show();
                }
            }, 200);
        }
    }, false);

    element.appendChild(buttonMeasureLength);
    element.appendChild(buttonMeasureArea);

    ol.control.Control.call(this, {
        element: element,
        target: options.target
    });

    var buttonsMeasure = [buttonMeasureLength, buttonMeasureArea];

    this.set('options', options);
    this.set('button', buttonsMeasure);
    this.set('handleMouseMove', mouseMoveHandler);
    this.set('removeMeasureInteraction', removeMeasureInteraction);
    this.set('active', false);
};
ol.inherits(app.measureControl, ol.control.Control);

app.measureControl.prototype.setMap = function(map) {
  ol.control.Control.prototype.setMap.call(this, map);
  if (map) {
    this.projection = this.projection || map.getView().getProjection().getCode();
  }
};

app.measureControl.prototype.disableControl = function (e) {
    var controls = this.getMap().getControls().getArray();
    for (var i = 0; i < controls.length; i++) {
        if (this != controls[i] && controls[i].activateControl) {
            controls[i].activateControl();
        }
    }

    for (var i = 0; i < $(this.get('button')).length; i++) {
        $(this.get('button')).removeClass('active');
    }

    var fn = this.get('removeMeasureInteraction');
    fn();

    this.set('active', false);

    if (this.get('options').onDisableControl) {
        this.get('options').onDisableControl(e);
    }
}