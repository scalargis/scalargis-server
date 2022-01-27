﻿/**
 * Define a namespace for the application.
 */
if (!window.app) {
    window.app = {};
}
var app = window.app;


//
// Define zoom extent control.
//



/**
 * @constructor
 * @extends {ol.control.Control}
 * @param {Object=} opt_options Control options.
 */
app.ZoomExtentControl = function(opt_options) {

  var options = opt_options || {};
  this.extent_ = options.extent;

  var anchor = document.createElement('a');
  anchor.href = '#zoom-to';
  anchor.className = 'zoom-to';

  var this_ = this;
  var handleZoomTo = function(e) {
    this_.handleZoomTo(e);
  };

  anchor.addEventListener('click', handleZoomTo, false);
  anchor.addEventListener('touchstart', handleZoomTo, false);

  var element = document.createElement('div');
  element.className = 'zoom-extent ol-unselectable';
  element.appendChild(anchor);

  ol.control.Control.call(this, {
    element: element,
    map: options.map,
    target: options.target
  });

};
ol.inherits(app.ZoomExtentControl, ol.control.Control);


/**
 * @param {Event} e Browser event.
 */
app.ZoomExtentControl.prototype.handleZoomTo = function(e) {
  // prevent #zoomTo anchor from getting appended to the url
  e.preventDefault();

  /*
  var map = this.getMap();
  var view = map.getView();
  view.fitExtent(this.extent_, map.getSize());
  */

  var map = this.getMap();
  var view = map.getView();
  var extent = !this.extent_ ? view.getProjection().getExtent() : this.extent_;
  var size = /** @type {ol.Size} */ (map.getSize());
  view.fit(extent, size);

};


/**
 * Overload setMap to use the view projection's validity extent
 * if no extent was passed to the constructor.
 * @param {ol.Map} map Map.
 */
app.ZoomExtentControl.prototype.setMap = function(map) {
  ol.control.Control.prototype.setMap.call(this, map);
  if (map && !this.extent_) {
    this.extent_ = map.getView().getProjection().getExtent();
  }
};
