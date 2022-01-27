if (!Portal) {
    Portal = {};
}
if (!Portal.Viewer) {
    Portal.Viewer = {};
}

Portal.Viewer.DrawTools = (function () {
  var _parentId;
  var _modulo = 'drawtools';

  var drawInteractions = {};
  var drawControl;

  // Connected map control
  var _drawtoolsControl;

  /**
   * Current state
  */
  var state = {
        hist: [],
        history_now: 0,
        click: false,
        draw_geom: false,
        draw_symbol: false,
        draw_text: false,
        fill: { r: '255', g: '255', b: '255', a: '1' },
        stroke: { r: '0', g: '0', b: '0', a: '1' },
        stroke_type: 'normal',
        fill_type: '1',
        size: '2',
        geom_type: null,
        symbol_type: 'x',
        text_style: 'normal',
        text_size: '18px',
        text_font: 'Arial',
        text_value: 'texto',
        displayFillPicker: false,
        displayStrokePicker: false,
        editing: null,
        drawings: []
     }

  var sizeOptions = [
        { key: '1', text: '1', value: '1' },
        { key: '2', text: '2', value: '2' },
        { key: '3', text: '3', value: '3' },
        { key: '4', text: '4', value: '4' },
        { key: '5', text: '5', value: '5' },
        { key: '10', text: '10', value: '10' },
        { key: '15', text: '15', value: '15' },
        { key: '20', text: '20', value: '20' },
    ];

  var symbolOptions = [
        { key: '1', text: 'circle', value: 'circle' },
        { key: '2', text: 'square', value: 'square' },
        { key: '3', text: 'triangle', value: 'triangle' },
        { key: '4', text: 'star', value: 'star' },
        { key: '5', text: 'cross', value: 'cross' },
        { key: '10', text: 'x', value: 'x' }
    ];

  var textStyleOptions = [
        { key: '1', text: 'normal', value: 'normal' },
        { key: '2', text: 'italico', value: 'italic' },
        { key: '3', text: 'negrito', value: 'bold' },
    ];

  var textSizeOptions = [
        { key: '1', text: '8px', value: '8px' },
        { key: '2', text: '11px', value: '11px' },
        { key: '3', text: '15px', value: '15px' },
        { key: '4', text: '20px', value: '20px' },
        { key: '5', text: '25px', value: '25px' },
    ];

  var textFontOptions = [
        { key: '1', text: 'Arial', value: 'Arial, Helvetica, sans-serif' },
        { key: '2', text: 'Georgia', value: 'Georgia, serif' },
    ];

  var strokeStyleOptions = [
        { key: '1', text: 'Normal', value: 'solid' },
        { key: '2', text: 'Tracejado', value: 'dashed' }
    ];

  var fillStyleOptions = [
        { key: '1', text: 'Opaco', value: '1' },
        { key: '2', text: 'Transparente', value: '0' }
    ];

  var olmap = null;
  var layers = new ol.Collection();
  var drawingsLayer = null;
  var vectorSource = null;
  var features = new ol.Collection();

  var modify = null;

  var select = new ol.interaction.Select({
    condition: ol.events.condition.singleClick,
    hitTolerance: 5,
    wrapX: false
  });
  var oldSelect = new ol.Collection();

  // Unselect features
  var unselectFeatures = function() {
        oldSelect.forEach(function(feature) {
            if (feature.get('state')) {
              var props = feature.getProperties();
              var tstate = feature.get('state');
              var style = createStyle(feature, tstate, props.state.stroke);
              feature.setStyle(style);
            }
        });

        drawingsLayer.getSource().refresh();
    }
  select.on('select', function(e) {
        if (modify) olmap.removeInteraction(modify);
        var selected = e.selected;
        var deselected = e.deselected;
        //console.log('on select', selected, deselected);

        if (selected) {
          selected.forEach(function (feature) {
            if (feature.get('state')) {
              oldSelect.push(feature);
              var tstate = feature.get('state');
              var style = createStyle(feature, tstate, {r: 255, g: 0, b: 0, a: 1});
              feature.setStyle(style);
            }
          });
        }
        if (deselected) {
          deselected.forEach(function (feature) {
            if (feature.get('state')) {
              var props = feature.getProperties();
              var tstate = feature.get('state');
              var style = createStyle(feature, tstate, props.state.stroke);
              feature.setStyle(style);
            }
          });
        }
        if (!selected && !deselected) {
          unselectFeatures();
        }

        // Refresh vector layer
        drawingsLayer.getSource().refresh();

        // End selection
        if (!selected || selected.length === 0) {
            if (modify) olmap.removeInteraction(modify);
            if (select.getFeatures()) select.getFeatures().clear();
            return setState({
                draw_geom: false,
                draw_symbol: false,
                draw_text: false,
                editing: null
            }, true);
        } else {
            if (selected[0].get('modulo') == _modulo) {
                editFeature(selected[0]);
            }
        }
    });

  draw = null;
  format = new ol.format.WKT();

  var createDrawingStyle = function(type, tstate, altStroke) {
      var size = tstate.size;
      var fill = tstate.fill;
      var stroke = altStroke ? altStroke : tstate.stroke;
      //var fillStr = 'rgba(' + [fill.r, fill.g, fill.b, fill.a].join(',') + ')';
      var fillStr = 'rgba(' + [fill.r, fill.g, fill.b, (tstate.fill_type ? tstate.fill_type : 1)  ].join(',') + ')';
      var strokeStr = 'rgba(' + [stroke.r, stroke.g, stroke.b, stroke.a].join(',') + ')';
      var style = new ol.style.Style({
          stroke: new ol.style.Stroke({
              color: strokeStr,
              width: parseInt(10, 10)
          }),
          fill: new ol.style.Fill({
              color: fillStr
          })
      });
      switch (type) {
          case 'MultiPoint':
          case 'Point':
              style = new ol.style.Style({
                  image: new ol.style.Circle({
                      radius: parseInt(size, 10),
                      fill: new ol.style.Fill({ color: fillStr }),
                      stroke: new ol.style.Stroke({ color: strokeStr, width: 2 })
                  })
              });
              break;
          case 'MultiLineString':
          case 'LineString':
              var strokeStyle = {
                  color: strokeStr,
                  width: parseInt(size, 10)
              };
              if (tstate.stroke_type === 'dashed') strokeStyle['lineDash'] = [4];
              style = new ol.style.Style({
                  stroke: new ol.style.Stroke(strokeStyle)
              });
              break;
          case 'MultiPolygon':
          case 'Polygon':
              var strokeStyle = {
                  color: strokeStr,
                  width: parseInt(size, 10)
              };
              if (tstate.stroke_type === 'dashed') strokeStyle['lineDash'] = [4];
              style = new ol.style.Style({
                  stroke: new ol.style.Stroke(strokeStyle),
                  fill: new ol.style.Fill({ color: fillStr})
              });
              break;
          case 'Circle':
              var strokeStyle = {
                  color: strokeStr,
                  width: parseInt(size, 10)
              };
              if (tstate.stroke_type === 'dashed') strokeStyle['lineDash'] = [4];
              style = new ol.style.Style({
                  stroke: new ol.style.Stroke(strokeStyle),
                  fill: new ol.style.Fill({
                      color: fillStr
                  })
              });
          break;
          default: ;
              break;
      }
      return style;
    }

  var createDrawingText = function(feature, tstate, altStroke) {
  var size = tstate.size;
  var fill = tstate.fill;
  var stroke = altStroke ? altStroke : tstate.stroke;
  var fillStr = 'rgba(' + [fill.r, fill.g, fill.b, fill.a].join(',') + ')';
  var strokeStr = 'rgba(' + [stroke.r, stroke.g, stroke.b, stroke.a].join(',') + ')';

  var text_style = tstate.text_style;
  var text_size = tstate.text_size;
  var text_font = tstate.text_font;
  var text_value = tstate.text_value;

  var label = text_value;
  var fontStr = [text_style, text_size, text_font].join(' ');

  var style = new ol.style.Style({
      text: new ol.style.Text({
          font: fontStr,
          textAlign: "left",
          fill: new ol.style.Fill({ color: fillStr }),
          stroke: new ol.style.Stroke({ "color": strokeStr, "width": parseInt(size, 10) }),
          textBaseline: "top",
          text: label
      })
  });
  return style;
  }

  var createDrawingSymbol = function(type, tstate, altStroke) {
      var size = tstate.size;
      var fill = tstate.fill;
      var stroke = altStroke ? altStroke : tstate.stroke;
      var fillStr = 'rgba(' + [fill.r, fill.g, fill.b, fill.a].join(',') + ')';
      var strokeStr = 'rgba(' + [stroke.r, stroke.g, stroke.b, stroke.a].join(',') + ')';

      var style = new ol.style.Style({
            image: createSymbol(type, { size: size, fillStr: fillStr, strokeStr: strokeStr, width: 2 })
        });

      return style;
  }

  var createSymbol = function (type, options) {
      var symbol = null;
      switch(type) {
          case 'square':
              symbol = new ol.style.RegularShape({
                  fill: new ol.style.Fill({ color: options.fillStr }),
                  stroke: new ol.style.Stroke({ color: options.strokeStr, width: options.width || 2 }),
                  radius: parseInt(options.size, 10),
                  points: 4,
                  angle: Math.PI / 4
              });
              break;
          case 'triangle':
              symbol = new ol.style.RegularShape({
                  fill: new ol.style.Fill({ color: options.fillStr }),
                  stroke: new ol.style.Stroke({ color: options.strokeStr, width: options.width || 2 }),
                  radius: parseInt(options.size, 10),
                  points: 3,
                  rotation: Math.PI / 4,
                  angle: 0
              });
              break;
          case 'star':
              symbol = new ol.style.RegularShape({
                  fill: new ol.style.Fill({ color: options.fillStr }),
                  stroke: new ol.style.Stroke({ color: options.strokeStr, width: options.width || 2 }),
                  radius: parseInt(options.size, 10),
                  points: 5,
                  radius2: 4,
                  angle: 0
              });
              break;
          case 'cross':
              symbol = new ol.style.RegularShape({
                  fill: new ol.style.Fill({ color: options.fillStr }),
                  stroke: new ol.style.Stroke({ color: options.strokeStr, width: options.width || 2 }),
                  radius: parseInt(options.size, 10),
                  points: 4,
                  radius2: 0,
                  angle: 0
              });
              break;
          case 'circle':
              symbol = new ol.style.Circle({
                  fill: new ol.style.Fill({ color: options.fillStr }),
                  stroke: new ol.style.Stroke({ color: options.strokeStr, width: options.width || 2 }),
                  radius: parseInt(options.size, 10)
              });
              break;
          case 'x':
          default:
              symbol = new ol.style.RegularShape({
                  fill: new ol.style.Fill({ color: options.fillStr }),
                  stroke: new ol.style.Stroke({ color: options.strokeStr, width: options.width || 2 }),
                  points: 4,
                  radius: 10,
                  radius2: 0,
                  angle: Math.PI / 4
              });
      }
      return symbol;
  }

  var changeFill = function(color) {
    setState({ fill: color.rgb });
  }

  var changeStroke = function(color) {
    setState({ stroke: color.rgb });
  }

  var toggleFillPicker = function() {
    setState({ displayFillPicker: !state.displayFillPicker, displayStrokePicker: false })
  };

  var closeFillPicker = function() {
    setState({ displayFillPicker: false })
  };

  var toggleStrokePicker = function() {
    setState({ displayStrokePicker: !state.displayStrokePicker, displayFillPicker: false })
  };

  var closeStrokePicker = function() {
    setState({ displayStrokePicker: false })
  };

  var createStyle = function(feature, tstate, altStroke) {
      var style = createDrawingStyle(feature.getGeometry().getType(), tstate, altStroke);
      if (feature.get('type') === 'Symbol') {
          style = createDrawingSymbol(tstate.symbol_type, tstate, altStroke);
      }
      if (feature.get('type') === 'Text') {
          style = createDrawingText(feature, tstate, altStroke);
      }
      return style;
  }

  var updateStyle = function(feature) {
    var style = createStyle(feature, state);
    feature.setStyle(style);
  }

  var updateStyleSelected = function(feature) {
    var style = createStyle(feature, state, {r: 255, g: 0, b: 0, a: 1});
    feature.setStyle(style);
  }

  var editFeature = function(feature) {
    //var state = feature.get('state');
    state = Object.assign(state, feature.getProperties().state);
    setState({
      editing: feature.getProperties(),
      geom_type: feature.getProperties().type.toLowerCase()
    }, true, function() {
      var features = new ol.Collection();
      features.push(feature);
      modify = new ol.interaction.Modify({
        features: features,
        deleteCondition: function(event) {
            return ol.events.condition.shiftKeyOnly(event) &&
                ol.events.condition.singleClick(event);
        }
      });
      olmap.addInteraction(modify);
      modify.setActive(true);
    });
  }


  function uuidv4() {
      return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
        var r = Math.random() * 16 | 0, v = c == 'x' ? r : (r & 0x3 | 0x8);
        return v.toString(16);
      });
    }

  var serializeDrawing = function(feature, state) {
      var id = feature.getId() ? feature.getId() : uuidv4();
      feature.setId(id);
      feature.set('id', id);
      feature.set('modulo', 'drawtools');
      var type = feature.getGeometry().getType();
      if (state.draw_symbol) type = 'Symbol';
      if (state.draw_text) type = 'Text';
      feature.set('type', type);
      feature.set('state', {
          draw_geom: state.draw_geom,
          draw_symbol: state.draw_symbol,
          draw_text: state.draw_text,
          fill: Object.assign({}, state.fill),
          fill_type: state.fill_type,
          stroke: Object.assign({}, state.stroke),
          stroke_type: state.stroke_type,
          size: state.size,
          symbol_type: state.symbol_type,
          text_style: state.text_style,
          text_size: state.text_size,
          text_font: state.text_font,
          text_value: state.text_value
      });
      var serializer = new ol.format.GeoJSON();

      // Export defaults to EPSG:3857
      var serializeOptions = {
          dataProjection: 'EPSG:3857',
          featureProjection: 'EPSG:3857',
          decimals: 6
      }
      var geojson = serializer.writeFeatureObject(feature, serializeOptions);

      // Hack: OL does not serialize with CRS attribute
      geojson.crs = { "type": "name", "properties": { "name": "urn:ogc:def:crs:EPSG::3857" } }
      return geojson;
  }

  var deserializeDrawing = function(drawing) {
      var draw_geom = drawing.properties.state.draw_geom;
      var draw_symbol = drawing.properties.state.draw_symbol;
      var draw_text = drawing.properties.state.draw_text;
      var geom_type = drawing.properties.state.geom_type;
      var symbol_type = drawing.properties.state.symbol_type;
      var size = drawing.properties.state.size;
      var fill = drawing.properties.state.fill;
      var fill_type = drawing.properties.state.fill_type;
      var stroke = drawing.properties.state.stroke;
      var text_style = drawing.properties.state.text_style;
      var text_size = drawing.properties.state.text_size;
      var text_font = drawing.properties.state.text_font;
      var text_value = drawing.properties.state.text_value;
      var stroke_type = drawing.properties.state.stroke_type;

      var serializer = new ol.format.GeoJSON();

      // Export defaults to EPSG:3857
      var serializeOptions = {
          dataProjection: 'EPSG:3857',
          featureProjection: 'EPSG:3857',
          decimals: 6
      }
      var feature = serializer.readFeature(drawing, serializeOptions);
      var style = createStyle(feature, drawing.properties.state);
      feature.setStyle(style);
      feature.set('modulo', 'drawtools');
      feature.set('state', {
          draw_geom: draw_geom,
          draw_symbol: draw_symbol,
          draw_text: draw_text,
          fill: Object.assign({}, fill),
          fill_type: fill_type,
          stroke: Object.assign({}, stroke),
          stroke_type: stroke_type,
          size: size,
          symbol_type: symbol_type,
          text_style: text_style,
          text_size: text_size,
          text_font: text_font,
          text_value: text_value
      });
      return feature;
    }


  // Draw undo
  var clickUndo = function(e) {
    e.preventDefault();

    olmap.removeInteraction(modify);
    select.getFeatures().clear();
    setState({
      editing: null
    }, true, function() {
      var drawings = [];
      var hist = state.hist;
      var history_now = state.history_now;
      if (history_now > 0) {
        history_now--;
        hist[history_now].forEach(function (item) {
          drawings.push(item);
        });
        setState({
            hist: hist,
            history_now: history_now
        }, true, function() {
          //DisplayModel.setDrawings(drawings);
        });
      }
    });
  }

  // Draw redo
  var clickRedo = function(e) {
    e.preventDefault();
    olmap.removeInteraction(modify);
    select.getFeatures().clear();
    setState({
      editing: null
    }, function () {
      var drawings = [];
      var hist = this.state.hist;
      var history_now = this.state.history_now;
      if (history_now + 1 < hist.length) {
        history_now++;
        hist[history_now].forEach(function (item) {
          drawings.push(item);
        });
        setState({
          hist: hist,
          history_now: history_now
        }, true, function ()  {
          //DisplayModel.setDrawings(drawings);
        });
      }
    });
  }

  // Draw delete current
  var clickDelete = function(e) {
    e.preventDefault();
    olmap.removeInteraction(modify);
    select.getFeatures().clear();
    //DisplayModel.setDrawings([]);
    setState({
      hist: [[]],
      history_now: 0,
      editing: null
    });
  }

  var clickSelect = function() {
    setState({
        draw_geom: false,
        draw_symbol: false,
        draw_text: false,
        editing: null
    }, true, function() {
        olmap.removeInteraction(draw);
        select.setActive(true);
    });
  }

  // Get editing feature
  var getEditingFeature = function(id) {
    var found = null;
    var tfeatures = vectorSource.getFeatures();
    for (var i = 0; i < tfeatures.length; i++) {
        var feat = tfeatures[i];
        if (feat.get('id') === id) found = feat;
    }
    return found;
  }

  // Remove feature
  var removeFeature = function() {

    // Validate selected drawing
    if (!state.editing) return;

    // Get selected drawing
    var drawings = state.drawings;
    var feature = getEditingFeature(state.editing.id);

    if (feature) {
      olmap.removeInteraction(modify);
      select.getFeatures().clear();
      drawings = drawings.filter(function (d) {
        d.id !== feature.getId()
      });
      state.drawings = drawings;
      vectorSource.removeFeature(feature);
    }
    setState({
      draw_geom: false,
      draw_symbol: false,
      draw_text: false,
      editing: null
    });

    $("#clear", _parentId).addClass('hidden');
    $("#clearall", _parentId).removeClass('hidden');
  }

  // Remove all features
  var removeAllFeatures = function() {
    // Remove all
    //vectorSource.clear();

    var fs = vectorSource.getFeatures();
    for (var j=fs.length-1; j>=0; j--){
        var f = fs[j];
        if (f.get('modulo') == _modulo) {
            vectorSource.removeFeature(f);
        }
    }

    setState({
      drawings: []
    }, false);
  }

  /**
   * Create a `ol.style.Style` object from style config mapped with
   * style form.
   *
   * @param {ol.Feature} feature to know if it's text or not
   * @param {object} styleCfg the style config object
   * @return {ol.style.Style} the ol style
   */
  var createStyleFromConfig = function(feature, styleCfg) {
    var styleObjCfg = {};

    if (styleCfg.fill) {
        styleObjCfg.fill = new ol.style.Fill({
                color: styleCfg.fill.color
            });
    } else {
        styleObjCfg.fill = null;
    }

    if (styleCfg.stroke) {
      styleObjCfg.stroke = new ol.style.Stroke({
        color: styleCfg.stroke.color,
        width: styleCfg.stroke.width,
        lineDash: styleCfg.stroke.lineDash
      })
    } else {
      styleObjCfg.stroke = null;
    }

    // It is a Text feature
    if (feature.get('type') && feature.get('type').toLocaleLowerCase() == 'text' ) {
      styleObjCfg.text = new ol.style.Text({
        font: styleCfg.text.font,
        text: styleCfg.text.text,
        fill: new ol.style.Fill({
          color: styleCfg.text.fill.color
        }),
        stroke: styleCfg.text.stroke.width > 0 ?
            new ol.style.Stroke({
              color: styleCfg.text.stroke.color,
              width: styleCfg.text.stroke.width
            }) : undefined,
        offsetX: styleCfg.text.offsetX || 0,
        offsetY: styleCfg.text.offsetY || 0,
        textAlign: styleCfg.text.textAlign || 'left',
        textBaseline: styleCfg.text.textAlign || 'top'
      });
    } else if (feature.get('type') == 'Symbol') {
        styleObjCfg.image = createSymbol(styleCfg.shape.type, {
                size: styleCfg.shape.size, fillStr: styleCfg.shape.fill.color,
                strokeStr: styleCfg.shape.stroke.color, width: styleCfg.shape.stroke.width
            });
    } else if (feature.getGeometry().getType() == 'Point') {
      var radius = 5;
      if (styleCfg.image && styleCfg.image.radius) {
        radius = styleCfg.image.radius;
      }

      var color = 'rgba(255,255,255,1)';

      if (styleCfg.image && styleCfg.image.fill && styleCfg.image.fill.color) {
        color = styleCfg.image.fill.color;
      }

      styleObjCfg.image = new ol.style.Circle({
        radius: radius,
        fill: new ol.style.Fill({
          color: color
        }),
        stroke: new ol.style.Stroke({
            color: styleCfg.image.stroke.color,
            width: styleCfg.image.stroke.width,
            lineDash: styleCfg.image.stroke.lineDash
        })
      });
    }
    return new ol.style.Style(styleObjCfg);
  };


  /**
   * Serialize an `ol.style.Style` to a JSON object.
   * Used to store the style as feature property in the GeoJSON.
   * @param {ol.Feature} feature
   * @return {Object} serialized style
   */
  var getStyleObjFromFeature = function(feature) {
    var st =  feature.getStyle();
    var styleObj = {};

    if (st.getFill()) {
        styleObj.fill = {
            color: st.getFill().getColor()
        }
    }

    if (st.getStroke()) {
        styleObj.stroke = {
            color: st.getStroke().getColor(),
            width: st.getStroke().getWidth(),
            lineDash: st.getStroke().getLineDash()
        }
    }

    if (st.getText()) {
      styleObj.text = {
        text: st.getText().getText(),
        font: st.getText().getFont(),
        stroke: {
          color: st.getText().getStroke().getColor(),
          width: st.getText().getStroke().getWidth(),
          lineDash: st.getText().getStroke().getLineDash()
        },
        fill: {
          color: st.getText().getFill().getColor()
        },
        width: parseInt(new RegExp('([0-9]{1,3})(?=px)').
            exec(st.getText().getFont())[0])
      };
    }
    else if (feature.get('type') == 'Symbol') {
      styleObj.shape = {
        type: feature.get('state').symbol_type,
        size: feature.get('state').size,
        fill: {
            color: st.getImage().getFill().getColor()
        },
        stroke: {
          color: st.getImage().getStroke().getColor(),
          width: st.getImage().getStroke().getWidth(),
          lineDash: st.getImage().getStroke().getLineDash()
        }
      }
    }
    else if (feature.getGeometry().getType() == 'Point') {
      styleObj.image = {
        radius: st.getImage().getRadius(),
        fill: {
          color: st.getImage().getFill().getColor()
        },
        stroke: {
            color: st.getImage().getStroke().getColor(),
            width: st.getImage().getStroke().getWidth(),
            lineDash: st.getImage().getStroke().getLineDash()
        }
      };
    }
    return styleObj;
  };

  /*
  var getFeaturesAsJSON = function() {
      var serializer = new ol.format.GeoJSON();

      // Export defaults to EPSG:4326
      var serializeOptions = {
          dataProjection: 'EPSG:4326',
          featureProjection: 'EPSG:3857',
          decimals: 6
      }
      var features = vectorSource.getFeatures();
      var json = serializer.writeFeaturesObject(features, serializeOptions);

      // Hack: OL does not serialize with CRS attribute
      json.crs = { "type": "name", "properties": { "name": "urn:ogc:def:crs:EPSG::4326" } }
      var data = JSON.stringify(json)
      return data;
  }
  */

  var getFeaturesAsGeoJSON = function (projection) {
        var serializer = new ol.format.GeoJSON();
        // Export defaults to EPSG:4326
        var serializeOptions = {
          dataProjection: projection || 'EPSG:4326',
          featureProjection: olmap.getView().getProjection(),
          decimals: 6
        }

        var features = [];

        vectorSource.forEachFeature(function(feature) {
            if (feature.get('modulo') == _modulo) {
                var clone = feature.clone();
                clone.setId(feature.getId());
                if ('state' in clone.values_) {
                    delete clone.values_.state;
                }
                if ('modulo' in clone.values_) {
                    delete clone.values_.modulo;
                }

                // Save the feature style
                clone.set('_style', getStyleObjFromFeature(feature));
                // Save label as attribute text type
                if (clone.get('type') == 'Text') {
                    if (feature.values_.state && feature.values_.state.text_value) {
                        clone.set('text_value', feature.values_.state.text_value);
                    }
                }

                features.push(clone);
            }
        });

        var json = serializer.writeFeaturesObject(features, serializeOptions);
        // Hack: OL does not serialize with CRS attribute
        if (projection) {
            json.crs = { "type": "name", "properties": { "name": "urn:ogc:def:crs:" + projection.replace('::', ':').replace(':', '::')  } }
        } else {
            json.crs = { "type": "name", "properties": { "name": "urn:ogc:def:crs:EPSG::4326" } }
        }
        var data = JSON.stringify(json)

        return data;
  }

  /*
  var download = function(format) {

    // Get data
    var data = getFeaturesAsJSON();

    // Upload data
    var endpoint = $('#DrawTools form').attr('action');
    var file = new Blob([data], {type: 'application/json'});
    var upload = new FormData();
    upload.append('upload', file);
    upload.append('ext', 'geojson');
    upload.append('format', format);
    $.ajax({
        url: endpoint,
        type: 'POST',
        data: upload,
        processData: false,
        contentType: false,
        success: function(data, status) {
          if (status !== 200) return console.log(status);
          if (data.error) return console.log(data.error);
          window.open(data.url);
        }
    });
  }
  */

  function componentToHex(c) {
      var hex = c.toString(16);
      return hex.length == 1 ? "0" + hex : hex;
  }

  function rgbToHex(r, g, b) {
      return componentToHex(r) + componentToHex(g) + componentToHex(b);
  }

  function hexToRgb(hex) {
      var result = /^#?([a-f\d]{2})([a-f\d]{2})([a-f\d]{2})$/i.exec(hex);
      return result ? {
        r: parseInt(result[1], 16),
        g: parseInt(result[2], 16),
        b: parseInt(result[3], 16)
      } : null;
  }

  var componentDidMount = function() {
    // Mount color picker
    $("#DrawTools .pick-a-color").pickAColor({
        showSpectrum          : false,
        showSavedColors       : false,
        saveColorsPerElement  : false,
        fadeMenuToggle        : true,
        showAdvanced          : true,
        showBasicColors       : true,
        showHexInput          : false,
        allowBlank            : false
    });

    // Add titles
    $($("#DrawTools #draw-stroke")[0]).parent().attr('title', 'Côr de rebordo');
    $($("#DrawTools #draw-fill")[0]).parent().attr('title', 'Côr de preenchimento');

    // Update language terms
    $('.pick-a-color-markup .advanced-content .color-preview .color-select.btn.advanced').text('Aplicar');
    $('.pick-a-color-markup .advanced-content .preview-text').text('Pré-visualizar');
    $('.pick-a-color-markup .advanced-content .saturation-text').text('Saturação');
    $('.pick-a-color-markup .advanced-content .lightness-text').text('Luminosidade');
    $('.pick-a-color-markup .advanced-content .hue-text').text('Côr');
    $('.pick-a-color-markup .color-menu-tabs .advanced-tab a').text('Avançado');
    $('.pick-a-color-markup .color-menu-tabs .basicColors-tab a').text('Básico');

    // Update basic colors labels
    var basicColors = {
        white: 'Branco',
        red: 'Vermelho',
        orange: 'Laranja',
        yellow: 'Amarelo',
        green: 'Verde',
        blue: 'Azul',
        purple: 'Roxo',
        black: 'Preto'
    };

    $.each(Object.keys(basicColors), function(i, item) {
        var selector = '.pick-a-color-markup .color-menu .basicColors-content li>a.' + item + ' .color-label';
        $(selector).text(basicColors[item]);
    });

    // Color picker events
    $("#DrawTools .pick-a-color").on("change", function () {
        var prop = $(this).attr('name');
        var hexColor = $(this).val();
        var rgb = hexToRgb(hexColor);
        rgb['a'] = 1;
        var color = { rgb: rgb };
        if (prop === 'stroke') changeStroke(color);
        if (prop === 'fill') {
            rgb['a'] = parseInt(state.fill_type);
            changeFill(color);
        }
        if (state.editing) {
            var feature = getEditingFeature(state.editing.id);
            if (feature) {
                if (prop === 'fill') Object.assign(feature.get('state').fill, rgb);
                if (prop === 'stroke') Object.assign(feature.get('state').stroke, rgb);
                var style = createStyle(feature, state, state.stroke);
                feature.setStyle(style);
            }
        }
    });


    // UI Events
    $(_parentId).on('click', '#DrawTools .btn-geometry-draw', function(e) {
        var activate = !$(this).hasClass("active");

        $(".btn-group[data-group='btn-geometry'] button", _parentId).removeClass("active");
        $("#clear", _parentId).addClass('hidden');
        $("#clearall", _parentId).removeClass('hidden');

        if (select.getFeatures()) {
            select.getFeatures().clear();
        }

        if (activate) {
            $(this).addClass("active");
            var id = $(this).attr("data-button-id");
            drawControl.enableControl(e, drawInteractions[id]);
        } else {
            drawControl.disableControl(e);
        }
    });

    $(_parentId).on('click', '#DrawTools .btn-geometry-zoom', function(e) {
        var extent = null;
        var fs = vectorSource.getFeatures();
        for (var j = 0; j < fs.length; j++){
            var f = fs[j];
            if (f.get('modulo') == _modulo) {
                if (extent) {
                    extent = ol.extent.extend(extent, f.getGeometry().getExtent());
                } else {
                    extent = f.getGeometry().getExtent();
                }
            }
        }
        if (extent) {
            olmap.getView().fit(ol.extent.buffer(extent, 200), olmap.getSize());
        }
    });


    $(_parentId).on('change', '#DrawTools  [name="symbol_type"]', function(e) {
        setState({ symbol_type: $(this).val() });
        if (state.editing) {
            var feature = getEditingFeature(state.editing.id);
            if (feature) {
                feature.get('state').symbol_type = state.symbol_type;
                var style = createStyle(feature, state, state.stroke);
                feature.setStyle(style);
            }
        }
    });
    $(_parentId).on('change', '#DrawTools  [name="text_font"]', function(e) {
        setState({ text_font: $(this).val() });
        if (state.editing) {
            var feature = getEditingFeature(state.editing.id);
            if (feature) {
                feature.get('state').text_font = state.text_font;
                var style = createStyle(feature, state, state.stroke);
                feature.setStyle(style);
            }
        }
    });
    $(_parentId).on('change', '#DrawTools  [name="text_size"]', function(e) {
        setState({ text_size: $(this).val() });
        if (state.editing) {
            var feature = getEditingFeature(state.editing.id);
            if (feature) {
                feature.get('state').text_size = state.text_size;
                var style = createStyle(feature, state, state.stroke);
                feature.setStyle(style);
            }
        }
    });
    $(_parentId).on('change', '#DrawTools  [name="text_style"]', function(e) {
        setState({ text_style: $(this).val() });
        if (state.editing) {
            var feature = getEditingFeature(state.editing.id);
            if (feature) {
                feature.get('state').text_style = state.text_style;
                var style = createStyle(feature, state, state.stroke);
                feature.setStyle(style);
            }
        }
    });
    $(_parentId).on('change', '#DrawTools  [name="text_value"]', function(e) {
        setState({ text_value: $(this).val() });
        if (state.editing) {
            var feature = getEditingFeature(state.editing.id);
            if (feature) {
                feature.get('state').text_value = state.text_value;
                var style = createStyle(feature, state, state.stroke);
                feature.setStyle(style);
            }
        }
    });
    $(_parentId).on('keyup', '#DrawTools  [name="text_value"]', function(e) {
        setState({ text_value: $(this).val() });
        if (state.editing) {
            var feature = getEditingFeature(state.editing.id);
            if (feature) {
                feature.get('state').text_value = state.text_value;
                var style = createStyle(feature, state, state.stroke);
                feature.setStyle(style);
            }
        }
    });
    $(_parentId).on('change', '#DrawTools  [name="size"]', function(e) {
        setState({ size: $(this).val() });
        if (state.editing) {
            var feature = getEditingFeature(state.editing.id);
            if (feature) {
                feature.get('state').size = state.size;
                var style = createStyle(feature, state, state.stroke);
                feature.setStyle(style);
            }
        }
    });
    $(_parentId).on('change', '#DrawTools  [name="stroke_type"]', function(e) {
        setState({ stroke_type: $(this).val() });
        if (state.editing) {
            var feature = getEditingFeature(state.editing.id);
            if (feature) {
                feature.get('state').stroke_type = state.stroke_type;
                var style = createStyle(feature, state, state.stroke);
                feature.setStyle(style);
            }
        }
    });
    $(_parentId).on('change', '#DrawTools  [name="fill_type"]', function(e) {
        setState({ fill_type: $(this).val() });
        if (state.editing) {
            var feature = getEditingFeature(state.editing.id);
            if (feature) {
                Object.assign(feature.get('state').fill, state.fill);
                feature.get('state').fill_type = state.fill_type;
                var style = createStyle(feature, state, state.stroke);
                feature.setStyle(style);
            }
        }
    });


    $(_parentId).on('click', '#DrawTools .draw-action-del', function(e) {
        removeFeature();
    });
    $(_parentId).on('click', '#DrawTools .draw-action-delall', function(e) {

        $.jsPanel({
            paneltype:   'modal',
            headerTitle: 'Eliminar desenhos',
            theme:       'danger',
            show:        'animated',
            contentSize: {width: 250, height: 120},
            content:     '<div style="text-align:center;padding:20px">Deseja eliminar todos os desenhos?</div><div style="text-align:center;padding-top:10px"><div class="col-md-6"><button class="btn btn-block btn-danger btn-sm confirm-delete" type="button">Sim</button></div><div class="col-md-6"><button class="btn btn-block btn-default btn-sm cancel-delete" type="button">Não</button></div></div>',
            callback:    function(panel){
                $("button.confirm-delete", this.content).click(function(){
                    removeAllFeatures();
                    panel.close();
                });
                $("button.cancel-delete", this.content).click(function(){
                    panel.close();
                });
            }
        });
    });
    $(_parentId).on('click', '#DrawTools .btn-export', function(e) {
        //var format = $(this).data('button-id');
        //download(format);
        var data = getFeaturesAsGeoJSON();
        var blob = new Blob([data], {
            type: "data:application/vnd.geo+json;base64;",
        });
        saveAs(blob, "export.json");
    });
    $(_parentId).on('click', '#DrawTools .btn-import', function(e) {
        $("#features-file-import", _parentId).trigger('click');
    });

    $("#features-file-import", _parentId).change(function (e) {
        var fileInput = this;

        var readAsText = function (f, callback) {
            try {
              var reader = new FileReader();
              reader.readAsText(f);
              reader.onload = function(e) {
                if (e.target && e.target.result) {
                  callback(e.target.result);
                } else {
                  console.error('File could not be loaded');
                }
              };
              reader.onerror = function(e) {
                console.error('File could not be read');
              };
            } catch (e) {
              console.error('File could not be read');
            }
        }

        if (fileInput.files.length > 0) {
            readAsText(fileInput.files[0], function(text) {
                var features = new ol.format.GeoJSON().readFeatures(text, {
                  //dataProjection: 'EPSG:4326',
                  featureProjection: olmap.getView().getProjection()
                });

                //// Set each feature its style
                $(features).each(function(i, f) {
                  var style = null;

                  if (f.get('_style')) {
                    style = createStyleFromConfig(f, f.get('_style'));
                  } else {
                    style = new ol.style.Style({
                        fill: new ol.style.Fill({
                            color: 'rgba(255, 255, 255, 0)'
                        }),
                        stroke: new ol.style.Stroke({
                            color: '#ffcc33',
                            width: 2
                        }),
                        image: new ol.style.Circle({
                            radius: 7,
                            fill: new ol.style.Fill({
                                color: '#ffcc33'
                            })
                        })
                    });
                    if (!f.get('id')) {
                        f.set('id', uuidv4());
                    }
                  }

                  f.setStyle(style);
                  f.set('modulo', _modulo);
                  f.setId(uuidv4());

                  var colorFromRGBAStr = function (rgba) {
                    var color = rgba.substring(5, rgba.length-1)
                             .replace(/ /g, '')
                             .split(',');
                    return { r: color[0], g: color[1], b: color[2], a: color[3]}
                  }

                  var setStateFeature = function (feature, style) {
                        var st = {
                          draw_geom: false,
                          draw_symbol: false,
                          draw_text: false,
                          fill: { r: '255', g: '255', b: '255', a: '0' },
                          fill_type: '0',
                          stroke: { r: '0', g: '0', b: '0', a: '1' },
                          stroke_type: 'normal',
                          size: '2',
                          symbol_type: 'x',
                          text_style: 'normal',
                          text_size: '18px',
                          text_font: 'Arial',
                          text_value: 'texto'
                        }

                      if (feature.get('type')) {
                          if (feature.get('type').toLocaleLowerCase() == 'point') {
                            st.draw_geom = true;
                            st.geom_type = 'point';

                            st.size = style.getImage().getRadius();

                            st.fill = colorFromRGBAStr(style.getImage().getFill().getColor());
                            st.fill_type = colorFromRGBAStr(style.getImage().getFill().getColor()).a || '1';
                            st.stroke = colorFromRGBAStr(style.getImage().getStroke().getColor());

                            var lineDash = style.getImage().getStroke().getLineDash();
                            if (lineDash && lineDash.length > 0 && lineDash[0] == 4) {
                                st.stroke_type = 'dashed';
                            } else {
                                st.stroke_type = 'normal';
                            }
                          } else if (feature.get('type').toLocaleLowerCase() == 'polygon') {
                            st.draw_geom = true;
                            st.geom_type = 'polygon';

                            st.size = style.getStroke().getWidth();

                            st.fill = colorFromRGBAStr(style.getFill().getColor());
                            st.fill_type = colorFromRGBAStr(style.getFill().getColor()).a || '1';
                            st.stroke = colorFromRGBAStr(style.getStroke().getColor());

                            var lineDash = style.getStroke().getLineDash();
                            if (lineDash && lineDash.length > 0 && lineDash[0] == 4) {
                                st.stroke_type = 'dashed';
                            } else {
                                st.stroke_type = 'normal';
                            }
                          } else if (feature.get('type').toLocaleLowerCase() == 'linestring') {
                            st.draw_geom = true;
                            st.geom_type = 'line';

                            st.size = style.getStroke().getWidth();

                            st.stroke = colorFromRGBAStr(style.getStroke().getColor());
                            var lineDash = style.getStroke().getLineDash();
                            if (lineDash && lineDash.length > 0 && lineDash[0] == 4) {
                                st.stroke_type = 'dashed';
                            } else {
                                st.stroke_type = 'normal';
                            }
                          } else if (feature.get('type').toLocaleLowerCase() == 'text') {
                            st.draw_text = true;

                            st.size = style.getText().getStroke().getWidth();

                            st.fill = colorFromRGBAStr(style.getText().getFill().getColor());
                            st.fill_type = colorFromRGBAStr(style.getText().getFill().getColor()).a || '1';
                            st.stroke = colorFromRGBAStr(style.getText().getStroke().getColor());

                            var lineDash = style.getText().getStroke().getLineDash();
                            if (lineDash && lineDash.length > 0 && lineDash[0] == 4) {
                                st.stroke_type = 'dashed';
                            } else {
                                st.stroke_type = 'normal';
                            }

                            var font = style.getText().getFont().split(' ');

                            st.text_font = font[2];
                            st.text_size = font[1];
                            st.text_style = font[0];
                            st.text_value = style.getText().getText();
                          } else if (feature.get('type').toLocaleLowerCase() == 'symbol') {
                            st.draw_symbol = true;
                            st.symbol_type = feature.get('_style').shape.type;

                            st.size = style.getImage().getRadius();

                            st.fill = colorFromRGBAStr(style.getImage().getFill().getColor());
                            st.fill_type = colorFromRGBAStr(style.getImage().getFill().getColor()).a || '1';
                            st.stroke = colorFromRGBAStr(style.getImage().getStroke().getColor());

                            var lineDash = style.getImage().getStroke().getLineDash();
                            if (lineDash && lineDash.length > 0 && lineDash[0] == 4) {
                                st.stroke_type = 'dashed';
                            } else {
                                st.stroke_type = 'normal';
                            }
                          }
                      } else {
                        st.draw_geom = true;

                        if (feature.getGeometry().getType().toLowerCase().indexOf('polygon') !== -1) {
                            feature.set('type', 'Polygon');
                        } else if (feature.getGeometry().getType().toLowerCase().indexOf('line') !== -1)  {
                            feature.set('type', 'Line');
                        } else {
                            feature.set('type', 'Point');
                        }
                        st.geom_type = feature.get('type').toLowerCase();
                        var stl = createStyle(feature, st);
                        feature.setStyle(stl);
                      }

                      feature.set('state', st);
                  }

                  //Set state
                  setStateFeature(f, style);

                  //Remove _style property (all information is now on feature style and state
                  if ('_style' in f.getProperties()) {
                    delete f.values_._style;
                  }
                });

                vectorSource.addFeatures(features);

                $(fileInput)[0].value = '';
            });
        }
    });
  }

    /**
     * Update component
     */
    var render = function() {

        $parent = $('#DrawTools');

        if (!state.draw_geom || state.editing != null) {
            $parent.find('.draw-geom').removeClass('active');
        } else {
            switch ((state.geom_type || '').toLocaleLowerCase()) {
                case 'point':
                    $parent.find('[data-button-id="point"]').addClass('active');
                    break;
                case 'line':
                    $parent.find('[data-button-id="line"]').addClass('active');
                    break;
                case 'linestring':
                    $parent.find('[data-button-id="line"]').addClass('active');
                    break;
                case 'polygon':
                    $parent.find('[data-button-id="polygon"]').addClass('active');
                    break;
            }
        }
        if (!state.draw_symbol || state.editing != null) {
            $parent.find('.draw-symbol').removeClass('active');
            $parent.find('#draw-symbol-options').addClass('hidden');
        } else {
            $parent.find('.draw-symbol').addClass('active');
        }
        if (!state.draw_text || state.editing != null) {
            $parent.find('.draw-text').removeClass('active');
            $parent.find('#draw-text-options').addClass('hidden');
        } else {
            $parent.find('.draw-text').addClass('active');
        }
        /*
        if (!state.draw_text && !state.draw_symbol && !state.draw_geom) {
            $parent.find('[data-button-id="select"]').addClass('active');
        } else {
            $parent.find('[data-button-id="select"]').removeClass('active');
        }
        */

        $parent.find('#draw-stroke-options').addClass('hidden');
        $parent.find('#draw-fill-options').addClass('hidden');
        if (state.draw_geom) {
            switch ((state.geom_type || '').toLocaleLowerCase()) {
                case 'point':
                    break;
                case 'line':
                    $parent.find('#draw-stroke-options').removeClass('hidden');
                    break;
                case 'linestring':
                    $parent.find('#draw-stroke-options').removeClass('hidden');
                    break;
                case 'polygon':
                    $parent.find('#draw-fill-options').removeClass('hidden');
                    $parent.find('#draw-stroke-options').removeClass('hidden');
                    break;
            }
        }

        $parent.find('[name="size"]').attr('title', 'Tamanho da linha');
        if (state.draw_symbol) {
            $parent.find('#draw-symbol-options').removeClass('hidden');
            $parent.find('[name="size"]').attr('title', 'Tamanho do símbolo');
        }
        if (state.draw_text) {
            $parent.find('#draw-text-options').removeClass('hidden');
        }

        // Hide/show delete button
        $parent.find('#clear').addClass('hidden');
        $parent.find('#clearall').addClass('hidden');
        var selected = select.getFeatures();
        if (selected.getLength()) $parent.find('#clear').removeClass('hidden');
        else $parent.find('#clearall').removeClass('hidden');

        // render UI options
        if (state.editing) {
            if (state.fill) {
                $('#draw-fill', '.menu-bar.drawtools').val(rgbToHex(state.fill.r, state.fill.g, state.fill.b));
                var rgb = 'rgb(' + state.fill.r + ',' + state.fill.g + ',' + state.fill.b + ')';
                $('.color-preview.current-color', $('.menu-bar.drawtools #draw-fill').parent()).css('background-color', rgb);
            }
            if (state.stroke)  {
                $('#draw-stroke', '.menu-bar.drawtools').val(rgbToHex(state.stroke.r, state.stroke.g, state.stroke.b));
                var rgb = 'rgb(' + state.stroke.r + ',' + state.stroke.g + ',' + state.stroke.b + ')';
                $('.color-preview.current-color', $('.menu-bar.drawtools #draw-stroke').parent()).css('background-color', rgb);
            }
        }

        $('#draw-symbol-options [name="symbol_type"]').empty();
        for (var i = 0; i <= symbolOptions.length -1; i++) {
            $('#draw-symbol-options [name="symbol_type"]').append($('<option>', {
                value: symbolOptions[i].value,
                text: symbolOptions[i].text,
                selected: state.symbol_type === symbolOptions[i].value
            }));
        }
        $('#draw-text-options [name="text_font"]').empty();
        for (var i = 0; i <= textFontOptions.length -1; i++) {
            $('#draw-text-options [name="text_font"]').append($('<option>', {
                value: textFontOptions[i].value,
                text: textFontOptions[i].text,
                selected: state.text_font === textFontOptions[i].value
            }));
        }
        $('#draw-text-options [name="text_style"]').empty();
        for (var i = 0; i <= textStyleOptions.length -1; i++) {
            $('#draw-text-options [name="text_style"]').append($('<option>', {
                value: textStyleOptions[i].value,
                text: textStyleOptions[i].text,
                selected: state.text_style === textStyleOptions[i].value
            }));
        }
        $('#draw-text-options [name="text_size"]').empty();
        for (var i = 0; i <= textSizeOptions.length -1; i++) {
            $('#draw-text-options [name="text_size"]').append($('<option>', {
                value: textSizeOptions[i].value,
                text: textSizeOptions[i].text,
                selected: state.text_size === textSizeOptions[i].value
            }));
        }
        $('#draw-text-options [name="text_value"]').val(state.text_value);
        $('#DrawTools [name="size"]').empty();
        for (var i = 0; i <= sizeOptions.length -1; i++) {
            $('#DrawTools [name="size"]').append($('<option>', {
                value: sizeOptions[i].value,
                text: sizeOptions[i].text,
                selected: '' + (state.size || '') === sizeOptions[i].value
            }));
        }
        $('#draw-stroke-options [name="stroke_type"]').empty();
        for (var i = 0; i <= strokeStyleOptions.length -1; i++) {
            $('#draw-stroke-options [name="stroke_type"]').append($('<option>', {
                value: strokeStyleOptions[i].value,
                text: strokeStyleOptions[i].text,
                selected: state.stroke_type === strokeStyleOptions[i].value
            }));
        }
        $('#draw-fill-options [name="fill_type"]').empty();
        for (var i = 0; i <= fillStyleOptions.length -1; i++) {
            $('#draw-fill-options [name="fill_type"]').append($('<option>', {
                value: fillStyleOptions[i].value,
                text: fillStyleOptions[i].text,
                selected: state.fill_type === fillStyleOptions[i].value
            }));
        }
        $('#DrawTools [name="fill"]').val(rgbToHex(state.fill.r, state.fill.g, state.fill.b));
        $('#DrawTools [name="stroke"]').val(rgbToHex(state.stroke.r, state.stroke.g, state.stroke.b));
    }

    /**
     * Set state
     */
    var setState = function(newState, refresh, cb) {
        state = Object.assign(state, newState);
        if (refresh) {
            render();
        }
        if (cb) cb(state);
    }

    var _addDrawToolbarButtons = function (parentId) {
        var layer = drawingsLayer;
        var source = layer.getSource();

        var onDrawStart = function (evt) {
            //console.log('onDrawStart');
        }
        var onDrawEnd = function (e) {
            // Serialize drawing
            var geojson = serializeDrawing(e.feature, state);
            updateStyle(e.feature);
            state.drawings.push(geojson);

            var hist = state.hist;
            var history_now = state.history_now;

            setTimeout(function () {
                // Add history
                var history_item = [];
                var drawings = vectorSource.getFeatures();
                for (var i = 0; i <= drawings.length - 1; i++) {
                    var item = drawings[i];
                    var itemSerialized = serializeDrawing(item, item.getProperties().state);
                    history_item.push(Object.assign({}, itemSerialized));
                }
                hist.push(history_item);
                state = Object.assign(state, {
                    hist: hist,
                    history_now: history_now+1
                });
            }, 350);

        }

        var draw = new ol.interaction.Draw({
            source: source,
            type: 'Point'
        });
        draw.on('drawstart', onDrawStart);
        draw.on('drawend', onDrawEnd);
        drawInteractions['text'] = draw;

        var draw = new ol.interaction.Draw({
            source: source,
            type: 'Point'
        });
        draw.on('drawstart', onDrawStart);
        draw.on('drawend', onDrawEnd);
        drawInteractions['symbol'] = draw;

        var draw = new ol.interaction.Draw({
            source: source,
            type: 'Point'
        });
        draw.on('drawstart', onDrawStart);
        draw.on('drawend', onDrawEnd);
        drawInteractions['point'] = draw;

        draw = new ol.interaction.Draw({
            source: source,
            type: 'LineString'
        });
        draw.on('drawstart', onDrawStart);
        draw.on('drawend', onDrawEnd);
        drawInteractions['line'] = draw;

        draw = new ol.interaction.Draw({
            source: source,
            type: 'Polygon'
        });
        draw.on('drawstart', onDrawStart);
        draw.on('drawend', onDrawEnd);
        drawInteractions['polygon'] = draw;

        drawInteractions['select'] = select;

        drawControl = new app.genericDrawControl({
            layer: layer,
            onEnableControl: function (evt, draw) {
                if (modify) olmap.removeInteraction(modify);
                unselectFeatures();

                if ($(evt.currentTarget).data('button-id') == 'text') {
                    setState({
                        draw_geom: false,
                        draw_symbol: false,
                        draw_text: true,
                        editing: null
                    }, true);
                } else if ($(evt.currentTarget).data('button-id') == 'symbol') {
                    setState({
                        draw_geom: false,
                        draw_symbol: true,
                        draw_text: false,
                        editing: null
                    }, true);
                } else if ($(evt.currentTarget).hasClass('draw-geom')) {
                    var type = $(evt.currentTarget).data('button-id');
                    setState({
                        draw_geom: true,
                        draw_symbol: false,
                        draw_text: false,
                        geom_type: type,
                        editing: null
                    }, true);
                }
            },
            onDisableControl: function (evt) {
                if (modify) olmap.removeInteraction(modify);
                unselectFeatures();
                $(".btn-group[data-group='btn-geometry'] button", _parentId).removeClass("active");
            }
        });
        olmap.addControl(drawControl);
    };


    /**
     * On Init module
     */
    var _init = function () {

    };

    /**
     * On load module
     */
    var _load = function (parentId) {
        _parentId = parentId;

        componentDidMount();
    };

    // API setMap
	var _setMap = function (map) {
	    /**
	     * Set current map
	     */
	    olmap = map;
        layers = olmap.getLayers();
        //drawingsLayer = Portal.Viewer.getTemporaryLayer();
        drawingsLayer = Portal.Viewer.getDrawtoolsLayer();
        vectorSource = drawingsLayer.getSource();

        //// Load
        drawingsLayer.setVisible(true);
        _addDrawToolbarButtons(_parentId);

        render();
	};

    /**
     * Get OpenLsyers features by attribue's values
     */
	var getFeaturesByAttributes = function(attributes, values) {

	    // Validate
	    if (!attributes) throw new Error('Invalid attributes');
	    if (!values) throw new Error('Invalid attribute values');
	    if (typeof attributes !== 'object') throw new Error('Invalid attributes');
	    if (typeof values !== 'object') throw new Error('Invalid attribute values');
	    if (attributes.length !== values.length) throw new Error('Attributes and values length do not match');

	    var results = [];
	    vectorSource.forEachFeature(function(feat) {
	        var matchCount = 0;
	        $.each(attributes, function(i, item) {
	            if (feat.get(item) === values[i]) matchCount++;
	        });
	        if (matchCount === attributes.length) results.push(feat);
	    });
	    return results;
	}

    /**
     * Get features that intersect geometry
     */
	var getFeaturesByGeometry = function(geometry) {

	    // Validate
	    if (!geometry) throw new Error('Invalid geometry');

	    var results = [];
	    vectorSource.forEachFeature(function(feat) {
	        if (feat.getExtent().intersects(geometry.getExtent())) results.push(feat);
	    });
	    return results;
	}



    // Return module API
    return {
        Init: _init,
        Load: _load,
        setMap: _setMap,
        SetControl: function (control) {
			_drawtoolsControl = control;
		},
		clear: function () {
		    removeAllFeatures();
		},
		getFeatures: function () {
		    return vectorSource.getFeatures()
		},
		getFeaturesByAttributes: function (attributes, values) {
            return getFeaturesByAttributes(attributes, values);
		},
		getFeaturesByGeometry: function (geometry) {
		    return getFeaturesByGeometry(geometry);
		},
		/*
		getFeaturesAsJSON: function () {
            return getFeaturesAsJSON();
		},
		*/
		getFeaturesAsGeoJSON: function (projection) {
            return getFeaturesAsGeoJSON(projection);
		}
    }
} ());