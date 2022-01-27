/**
 * @classdesc
 * A control to show the 2D coordinates of the mouse cursor. By default, these
 * are in the view projection, but can be in any supported projection.
 * By default the control is shown in the top right corner of the map, but this
 * can be changed by using the css selector `.ol-mouse-position`.
 *
 * @constructor
 * @extends {ol.control.Control}
 * @param {olx.control.MousePositionOptions=} opt_options Mouse position
 *     options.
 * @api stable
 */
app.MousePositionControl = function(opt_options) {

    var options = opt_options ? opt_options : {};

    var element = document.createElement('DIV');
    element.className = options.className !== undefined ? options.className : 'ol-mouse-position';

    var html = '<div class="input-group">';
    html = html + '<div class="form-control">';
    html = html + '<div class="map-coordsys-mouse-position"></div>';
    html = html + '</div>';
    html = html + '<div class="input-group-btn dropup">';
    html = html + '<input type="hidden" class="map-coordsys-selected" value="' + options.projection + ' " />';
    html = html + '<button type="button" class="btn dropdown-toggle" data-toggle="dropdown" aria-haspopup="true" aria-expanded="false"><span class="map-coordsys-text">' + options.projection + '</span> <span class="caret"></span></button>';
    html = html + '<ul class="dropdown-menu dropdown-menu-right map-coordsys-list">';
    html = html + '</ul>';
    html = html + '</div>';
    html = html + '</div>';

    $(options.target).html(html);

    for (var i = 0; i < options.projections.length; ++i) {
        var projection = options.projections[i];

        var visible = true

        if (!('visible' in projection) || projection.visible) {
            var html = '<li><a href="#" data-code="' + projection.code + '">' + (projection.title || projection.code) + '</a></li>';
            $('.map-coordsys-list', options.target).append(html);
        }
    }


    var ctl = this;
    $('a', '.map-coordsys-list').click(function (evt) {
        var code = $(this).data('code');
        $('.map-coordsys-selected').val(code);
        $('.map-coordsys-control .map-coordsys-text').html(code);
        ctl.setProjection(ol.proj.get(code));
    });

    var divMousePos = $('.map-coordsys-mouse-position', options.target)[0];
    var element = document.createElement('DIV');

    var render = options.render ?
      options.render : ol.control.MousePosition.render;

    ol.control.Control.call(this, {
    element: element,
    render: render,
    target: divMousePos //options.target
    });

    ol.events.listen(this,
      ol.Object.getChangeEventType(app.MousePositionControl.MousePositionProperty.PROJECTION),
      this.handleProjectionChanged_, this);

    if (options.coordinateFormat) {
    this.setCoordinateFormat(options.coordinateFormat);
    }
    if (options.projection) {
    this.setProjection(ol.proj.get(options.projection));
    }

    /**
    * @private
    * @type {string}
    */
    this.undefinedHTML_ = options.undefinedHTML !== undefined ? options.undefinedHTML : '';

    /**
    * @private
    * @type {string}
    */
    this.renderedHTML_ = element.innerHTML;

    /**
    * @private
    * @type {ol.proj.Projection}
    */
    this.mapProjection_ = null;

    /**
    * @private
    * @type {?ol.TransformFunction}
    */
    this.transform_ = null;

    /**
    * @private
    * @type {ol.Pixel}
    */
    this.lastMouseMovePixel_ = null;

};
ol.inherits(app.MousePositionControl, ol.control.Control);


/**
 * Update the mouseposition element.
 * @param {ol.MapEvent} mapEvent Map event.
 * @this {ol.control.MousePosition}
 * @api
 */
app.MousePositionControl.render = function(mapEvent) {
  var frameState = mapEvent.frameState;
  if (!frameState) {
    this.mapProjection_ = null;
  } else {
    if (this.mapProjection_ != frameState.viewState.projection) {
      this.mapProjection_ = frameState.viewState.projection;
      this.transform_ = null;
    }
  }
  this.updateHTML_(this.lastMouseMovePixel_);
};


/**
 * @private
 */
app.MousePositionControl.prototype.handleProjectionChanged_ = function() {
  this.transform_ = null;
};


/**
 * Return the coordinate format type used to render the current position or
 * undefined.
 * @return {ol.CoordinateFormatType|undefined} The format to render the current
 *     position in.
 * @observable
 * @api stable
 */
app.MousePositionControl.prototype.getCoordinateFormat = function() {
  return /** @type {ol.CoordinateFormatType|undefined} */ (
      this.get(app.MousePositionControl.MousePositionProperty.COORDINATE_FORMAT));
};


/**
 * Return the projection that is used to report the mouse position.
 * @return {ol.proj.Projection|undefined} The projection to report mouse
 *     position in.
 * @observable
 * @api stable
 */
app.MousePositionControl.prototype.getProjection = function() {
  return /** @type {ol.proj.Projection|undefined} */ (
      this.get(app.MousePositionControl.MousePositionProperty.PROJECTION));
};


/**
 * @param {Event} event Browser event.
 * @protected
 */
app.MousePositionControl.prototype.handleMouseMove = function(event) {
  var map = this.getMap();
  this.lastMouseMovePixel_ = map.getEventPixel(event);
  this.updateHTML_(this.lastMouseMovePixel_);
};


/**
 * @param {Event} event Browser event.
 * @protected
 */
app.MousePositionControl.prototype.handleMouseOut = function(event) {
    var map = this.getMap();
    var coordinate = map.getCoordinateFromPixel([event.x, event.y]);
    var html = null;

    if (coordinate) {
        var transform;

        var projection = this.getProjection();

        if (projection) {
            transform = ol.proj.getTransform(map.getView().getProjection(), projection);
        } else {
            transform_ = ol.proj.identityTransform;
        }

        transform(coordinate, coordinate);

        var coordinateFormat = this.getCoordinateFormat();
        var html;
        if (coordinateFormat) {
            html = coordinateFormat(coordinate);
        } else {
            html = coordinate.toString();
        }
    }

    if (html) {
        this.element.innerHTML = html;
        this.renderedHTML_ = html;
    } else {
        this.updateHTML_(html)
    }
    this.lastMouseMovePixel_ = null;
};


/**
 * @inheritDoc
 * @api stable
 */
app.MousePositionControl.prototype.setMap = function(map) {
  ol.control.Control.prototype.setMap.call(this, map);
  if (map) {
    var viewport = map.getViewport();
    this.listenerKeys.push(
        ol.events.listen(viewport, ol.events.EventType.MOUSEMOVE,
            this.handleMouseMove, this),
        ol.events.listen(viewport, ol.events.EventType.MOUSEOUT,
            this.handleMouseOut, this)
    );
  }
};


/**
 * Set the coordinate format type used to render the current position.
 * @param {ol.CoordinateFormatType} format The format to render the current
 *     position in.
 * @observable
 * @api stable
 */
app.MousePositionControl.prototype.setCoordinateFormat = function(format) {
  this.set(app.MousePositionControl.MousePositionProperty.COORDINATE_FORMAT, format);
};


/**
 * Set the projection that is used to report the mouse position.
 * @param {ol.proj.Projection} projection The projection to report mouse
 *     position in.
 * @observable
 * @api stable
 */
app.MousePositionControl.prototype.setProjection = function(projection) {
  this.set(app.MousePositionControl.MousePositionProperty.PROJECTION, projection);
};


/**
 * @param {?ol.Pixel} pixel Pixel.
 * @private
 */
app.MousePositionControl.prototype.updateHTML_ = function(pixel) {
  var html = this.undefinedHTML_;
  if (pixel && this.mapProjection_) {
    if (!this.transform_) {
      var projection = this.getProjection();
      if (projection) {
        this.transform_ = ol.proj.getTransformFromProjections(
            this.mapProjection_, projection);
      } else {
        this.transform_ = ol.proj.identityTransform;
      }
    }
    var map = this.getMap();
    var coordinate = map.getCoordinateFromPixel(pixel);
    if (coordinate) {
      this.transform_(coordinate, coordinate);
      var coordinateFormat = this.getCoordinateFormat();
      if (coordinateFormat) {
        html = coordinateFormat(coordinate);
      } else {
        html = coordinate.toString();
      }
    }
  }
  if (!this.renderedHTML_ || html != this.renderedHTML_) {
    this.element.innerHTML = html;
    this.renderedHTML_ = html;
  }

};

/**
 * @enum {string}
 */
app.MousePositionControl.MousePositionProperty = {
  PROJECTION: 'projection',
  COORDINATE_FORMAT: 'coordinateFormat'
};