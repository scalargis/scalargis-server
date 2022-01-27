/**
 * Define a namespace for the application.
 */
if (!window.app) {
    window.app = {};
}
var app = window.app;

/**
 * @class
 * The BasemapsControl is a layer switcher for basemap layers.
 * A minimal configuration is:
 *
 *     new app.BasemapsControl()
 *
 * @constructor
 * @extends {ol.control.Control}
 * @param {Object} opt_options Options.
 */
app.BasemapsControl = function (opt_options) {

    this.generateID = function () {
        return s4() + s4() + s4() + s4() + s4() + s4() + s4() + s4();
    }

    var options = opt_options || {};

    this.group = options.group || "basemap";

    var panel = document.createElement('div');
    panel.className = 'basemaps-control';

    var list = document.createElement('ul');
    list.className = 'basemaps-list';
    this.container = list;

    panel.appendChild(this.container);

    ol.control.Control.call(this, {
        element: panel,
        target: options.target
    });

    function s4() {
        return Math.floor((1 + Math.random()) * 0x10000)
                   .toString(16)
                   .substring(1);
    }

};

ol.inherits(app.BasemapsControl, ol.control.Control);

/**
 * Remove the control from its current map and attach it to the new map.
 * Here we create the markup for our layer switcher component.
 * @param {ol.Map} map Map.
 */
app.BasemapsControl.prototype.setMap = function (map) {
    ol.control.Control.prototype.setMap.call(this, map);
    var layers = map.getLayers().getArray();

    var vlayers = [];

    for (var i = 0, ii = layers.length; i < ii; ++i) {
        layer = layers[i];

        if (layer.get("group") == this.group) {
            vlayers.push(layer);
        }
    }

    if (vlayers.length > 1) {
        for (var i = 0, ii = vlayers.length; i < ii; ++i) {
            this.addLayerToList(vlayers[i]);
        }
    } else if (vlayers.length == 1 && vlayers[0] instanceof ol.layer.Group) {
        this.addLayerGroupToList(vlayers[0]);
    } else if (vlayers.length == 1) {
        this.addLayerToList(vlayers[0]);
    }

};

/**
 * Build HTML for layer
 * <li>
 *  <div class="thumbnail" data-layer-id="ags-terrain">
 *     <img src="/static/images/basemaps/TERRAIN.jpg" />
 *     <div class="caption">
 *       <p>ArcGIS TERRAIN</p>
 *     </div>
 *   </div>
 * </li>
 * @param {ol.Layer} layer Layer.
*/
app.BasemapsControl.prototype.addLayerToList = function (layer) {
    var title = layer.get('title');

    var li = document.createElement('li');
    var layerId = this.generateID();

    var divThumb = document.createElement('div');
    divThumb.className = 'thumbnail';
    if (layer.get('visible')) {
        divThumb.classList ? divThumb.classList.add('active') : divThumb.className += ' active';
    }
    var att = document.createAttribute('data-layer-id');
    att.value = layerId;
    divThumb.setAttributeNode(att);

    var container = this.container;
    var group = this.group;

    $(divThumb).click(function () {
        $('.thumbnail', container).not(this).each(function() {
            $(this).removeClass("active");
        });
        $(this).toggleClass( "active" );

        var layerId = $(this).data("layer-id");
        var layers = map.getLayers().getArray();
        for (var i = 0, ii = layers.length; i < ii; ++i) {
          layer = layers[i];

          if (layer.get("basemap-group"))  {
            var gl = layer.getLayers().getArray();

            for (var j = 0, jj = gl.length; j < jj; ++j) {
              var l = gl[j];
              if (l.get("layer-id") == layerId) {
                gl[j].set('visible', $(this).hasClass("active"));
              } else {
                gl[j].set('visible', false);
              }
            }
          } else if (layer.get("group") == group) {
              if (layer.get("layer-id") == layerId) {
                layers[i].set('visible', $(this).hasClass("active"));
              } else {
                layers[i].set('visible', false);
              }
          }
        }
    });

    var img = document.createElement('img');
    att = document.createAttribute('src');
    att.value = layer.get('icon') || '';
    img.setAttributeNode(att);
    divThumb.appendChild(img);

    var divCaption = document.createElement('div');
    divCaption.className = 'caption';
    var para = document.createElement("p");
    var text = document.createTextNode(layer.get('title') || '');
    para.appendChild(text);
    divCaption.appendChild(para);
    divThumb.appendChild(divCaption);
    li.appendChild(divThumb);
    this.container.appendChild(li);

    layer.set('layer-id', layerId);
}

/**
 *
 * @param {ol.layer.Group} layer Layer.
*/
app.BasemapsControl.prototype.addLayerGroupToList = function (layer) {

    var layers = layer.getLayers().getArray();

    for (var i = 0, ii = layers.length; i < ii; ++i) {
        this.addLayerToList(layers[i]);
    }

    layer.set('basemap-group', true);
}