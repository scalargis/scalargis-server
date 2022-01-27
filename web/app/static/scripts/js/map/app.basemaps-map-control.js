/**
 * Define a namespace for the application.
 */
if (!window.app) {
    window.app = {};
}
var app = window.app;

/**
 * @class
 * The BasemapsMapControl is a layer switcher for basemap layers.
 * A minimal configuration is:
 *
 *     new app.BasemapsMapControl()
 *
 * @constructor
 * @extends {ol.control.Control}
 * @param {Object} opt_options Options.
 */
app.BasemapsMapControl = function (opt_options) {

    this.generateID = function () {
        return s4() + s4() + s4() + s4() + s4() + s4() + s4() + s4();
    }

    var options = opt_options || {};

    this.group = options.group || "basemap";
    this.target = options.target;

    var panel = document.createElement('div');
    panel.className = 'basemaps-map-panel';

    var divActive = document.createElement('div');
    divActive.className = 'basemaps-active-layer';

    // Thumbnail
    var img= document.createElement('img');
    att = document.createAttribute('src');
    att.value = '';
    img.setAttributeNode(att);
    divActive.appendChild(img);

    // Caption
    var divCaption = document.createElement('div');
    divCaption.className = 'caption';
    var para = document.createElement("p");
    var text = document.createTextNode('');
    para.appendChild(text);
    divCaption.appendChild(para);
    divActive.appendChild(divCaption);

    $(divActive).click(function () {
        var parent = $(this).parent();
        $('.basemaps-layers-list', parent).toggleClass('open');
    });

    panel.appendChild(divActive);

    var list = document.createElement('div');
    list.className = 'basemaps-layers-list';
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

ol.inherits(app.BasemapsMapControl, ol.control.Control);

/**
 * Remove the control from its current map and attach it to the new map.
 * Here we create the markup for our layer switcher component.
 * @param {ol.Map} map Map.
 */
app.BasemapsMapControl.prototype.setMap = function (map) {
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
 *   <div class="basemaps-layer active" data-layer-id="d91a17a035fc4a040e123e685ea8711c">
 *       <img src="../static/images/basemaps/Stamen-watercolor-labels.jpg">
 *       <div class="caption"><p>Stamen</p></div>
 *  </div>
 * @param {ol.Layer} layer Layer.
*/
app.BasemapsMapControl.prototype.addLayerToList = function (layer) {
    var title = layer.get('title');

    var div = document.createElement('div');
    div.className = 'basemaps-layer';
    var layerId = this.generateID();
    if (layer.get('visible')) {
        div.classList ? div.classList.add('active') : div.className += ' active';
        $('.basemaps-active-layer img', '.basemaps-map-control').attr('src', layer.get('icon') || '');
        $('.basemaps-active-layer', parent).attr(layer.get('title') || '');
        $('.basemaps-active-layer .caption p', parent).html(layer.get('title') || '');
    }
    var att = document.createAttribute('data-layer-id');
    att.value = layerId;
    div.setAttributeNode(att);

    var parent = this.target;
    var container = this.container;
    var group = this.group;

    $(div).click(function () {
        $('.basemaps-layer', container).not(this).each(function() {
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
                if ($(this).hasClass("active")) {
                    $('.basemaps-active-layer img', parent).attr('src', $('img', this).attr('src'));
                    $('.basemaps-active-layer .caption p', parent).html(l.get('title') || '');
                } else {
                  $('.basemaps-active-layer img', parent).attr('src', '../static/images/basemaps/blank.jpg');
                  $('.basemaps-active-layer .caption p', parent).html('Sem Base');
                }
              } else {
                gl[j].set('visible', false);
              }
            }
          } else if (layer.get("group") == group) {
              if (layer.get("layer-id") == layerId) {
                layers[i].set('visible', $(this).hasClass("active"));
                if ($(this).hasClass("active")) {
                    $('.basemaps-active-layer img', parent).attr('src', $('img', this).attr('src'));
                    $('.basemaps-active-layer', parent).attr('title', layer.get('title') || '');
                    $('.basemaps-active-layer .caption p', parent).html(layer.get('title') || '');
                } else {
                  $('.basemaps-active-layer img', parent).attr('src', '../static/images/basemaps/blank.jpg');
                  $('.basemaps-active-layer', parent).attr('title','Sem Base');
                  $('.basemaps-active-layer .caption p', parent).html('Sem Base');
                }
              } else {
                layers[i].set('visible', false);
              }
          }
        }

        $('.basemaps-layers-list', parent).toggleClass('open');

    });

    var img = document.createElement('img');
    att = document.createAttribute('src');
    att.value = layer.get('icon') || '';
    img.setAttributeNode(att);
    div.appendChild(img);

    var divCaption = document.createElement('div');
    divCaption.className = 'caption';
    var para = document.createElement("p");
    var text = document.createTextNode(layer.get('title') || '');
    para.appendChild(text);
    divCaption.appendChild(para);
    div.appendChild(divCaption);

    this.container.appendChild(div);

    layer.set('layer-id', layerId);
}

/**
 *
 * @param {ol.layer.Group} layer Layer.
*/
app.BasemapsMapControl.prototype.addLayerGroupToList = function (layer) {
    var layers = layer.getLayers().getArray();

    for (var i = 0, ii = layers.length; i < ii; ++i) {
        this.addLayerToList(layers[i]);
    }

    layer.set('basemap-group', true);
}