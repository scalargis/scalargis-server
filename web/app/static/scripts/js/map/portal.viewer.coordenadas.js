Portal.Viewer.Coordenadas = (function () {

	var _formId;

	var _coordinatesControl;

	var _feature;

	var _decimalSeparator;

	var _init = function () {
	};

	var _load = function (formId) {

		_formId = "#" + formId;


	    var positivenumberFieldStrictInput = function(event) {
            var e = event || window.event;  // get event object
            var key = e.keyCode || e.which; // get key cross-browser

            if(key==8 || key==46 || key == 9 || key==17 || key==91 || key==18 ||
                    key==116 || key==89 || key==67 || key==88 || key==35 || key==36) //back, delete tab, ctrl, win, alt, f5, paste, copy, cut, home, end
                return true;

            if (key==16) //shift
                return true;

            if (key==86) //ctrl-v
                return true;

            if(key==190) //point
                return true;

            if(key>=37 && key<=40) //arrows
                return true;

            if(key>=48 && key<=57) // top key
                return true;

            if(key>=96 && key<=105) //num key
                return true;
            //console.log('Not allowed key pressed '+key);

            if (e.preventDefault) e.preventDefault(); //normal browsers
                e.returnValue = false; //IE
        }

	    var numberFieldStrictInput = function(event) {
            var e = event || window.event;  // get event object
            var key = e.keyCode || e.which; // get key cross-browser

            if(key==8 || key==46 || key == 9 || key==17 || key==91 || key==18 ||
                    key==116 || key==89 || key==67 || key==88 || key==35 || key==36) //back, delete tab, ctrl, win, alt, f5, paste, copy, cut, home, end
                return true;

            if (key==16) //shift
                return true;

            if (key==86) //ctrl-v
                return true;

            if (key==189 || key==173 || key==109) //minus (173 - firefox; 109 - numpad)
                return true;

            if(key==190) //point
                return true;

            if(key>=37 && key<=40) //arrows
                return true;

            if(key>=48 && key<=57) // top key
                return true;

            if(key>=96 && key<=105) //num key
                return true;
            console.log('Not allowed key pressed '+key);

            if (e.preventDefault) e.preventDefault(); //normal browsers
                e.returnValue = false; //IE
        }

        $('#x', _formId).keydown(numberFieldStrictInput);
        $('#y', _formId).keydown(numberFieldStrictInput);

        $('#lon-dd', _formId).keydown(positivenumberFieldStrictInput);
        $('#lat-dd', _formId).keydown(positivenumberFieldStrictInput);

        $('#code', _formId).change(function (e) {
            var selected = $("option:selected", this);
            var unidades = $(selected).data('unidades') || 'm';
            //var parent = $(this).closest('form');
            $('.coords', _formId).removeClass('hidden').addClass('hidden');
            $('.coords.coords-' + unidades, _formId).removeClass('hidden');
        });

        $('.opt-unidades', _formId).change(function (e) {
            var parent = $(this).closest('form');
            $('div[data-unidades]', parent).hide();
            $('div[data-unidades="' + $(this).val() + '"]', parent).show();

            if ($(this).val() == 'dms') {
                var lon_dd =  + ' ' + $('#lon-dd', parent).val();
                var lat_dd =  + ' ' + $('#lat-dd', parent).val();

                var lon = Portal.Viewer.Coordenadas.ConvertDD2DMS(parseFloat(lon_dd), true);
                var lat = Portal.Viewer.Coordenadas.ConvertDD2DMS(parseFloat(lat_dd), false);

                if (lon && lat) {
                    $('#lon-dms', parent).val(lon);
                    $('#lon-dms-sign', parent).val($('#lon-dd-sign', parent).val());
                    $('#lat-dms', parent).val(lat);
                    $('#lat-dms-sign', parent).val($('#lat-dd-sign', parent).val());
                } else {
                    $('#lon-dms', parent).val('');
                    $('#lat-dms', parent).val('');
                }
            } else {
                var lon_dms = $('#lon-dms-sign', parent).val() + ' ' + $('#lon-dms', parent).val();
                var lat_dms = $('#lat-dms-sign', parent).val() + ' ' + $('#lat-dms', parent).val();

                var lon = Portal.Viewer.Coordenadas.ConvertDMS2DD(lon_dms);
                var lat = Portal.Viewer.Coordenadas.ConvertDMS2DD(lat_dms);

                if (lon && lat) {
                    $('#lon-dd', parent).val(Math.round(Math.abs(lon) * 10000000) / 10000000);
                    lon < 0 ? $('#lon-dd-sign', parent).val("W") : $('#lon-dd-sign', parent).val("E");
                    $('#lat-dd', parent).val(Math.round(Math.abs(lat) * 10000000) / 10000000);
                    lat < 0 ? $('#lat-dd-sign', parent).val("S") : $('#lat-dd-sign', parent).val("N");
                } else {
                    $('#lon-dd', parent).val('');
                    $('#lat-dd', parent).val('');
                }
            }
        });

		$(_formId).submit(function (e) {
			e.preventDefault();

			handleTransform($(this), true);
		});

	}

	var _transform = function (x, y) {

		var decimalSeparator = _decimalSeparator || '.';
		var coordX = (Math.round(x * 1000) / 1000).toString().replace('.', decimalSeparator).replace(',', decimalSeparator);
		var coordY = (Math.round(y * 1000) / 1000).toString().replace('.', decimalSeparator).replace(',', decimalSeparator);

		//$('#srid', _formId).val(Portal.Viewer.getMapSRID()).trigger('change');
		$('#code', _formId).val(Portal.Viewer.getMapProjectionCode()).trigger('change');
		$('#x', _formId).val(coordX);
		$('#y', _formId).val(coordY);

		handleTransform($(_formId), false);
	}

	var _disable = function () {
		var layer = Portal.Viewer.getTemporaryLayer();
		var source;

		if (layer) {
			source = layer.getSource();

			if (source && _feature) {
				source.removeFeature(_feature);
			}
		}
		_feature = null;
	}

	var handleTransform = function (form, center) {
        var code = $('#code', form).val();
        var srid = $('#code option:selected', form).data('srid');
        var units = $('#code option:selected', form).data('unidades');
        var x = $('#x', form).val();
        var y = $('#y', form).val();

        if (units == 'd') {
            var format = $('[name=opt-unidades]:checked', form).val();
            if (format == 'dd') {
                x = parseFloat($('#lon-dd', form).val());
                if ($('#lon-dd-sign', form).val() == 'W') {
                    x = x * -1;
                }
                y = parseFloat($('#lat-dd', form).val());
                if ($('#lat-dd-sign', form).val() == 'S') {
                    y = y * -1;
                }
            } else if (format == 'dms') {
                var lon = Portal.Viewer.Coordenadas.ConvertDMS2DD($('#lon-dms-sign', form).val() + ' ' + $('#lon-dms', form).val());
                var lat = Portal.Viewer.Coordenadas.ConvertDMS2DD($('#lat-dms-sign', form).val() + ' ' + $('#lat-dms', form).val());

                x = lon;
                y = lat;
            }
        } else if (units == 'dm') {
            var lon = Portal.Viewer.Coordenadas.ConvertDM2DD($('#lon-dm-sign', form).val() + ' ' + $('#lon-dm', form).val());
            var lat = Portal.Viewer.Coordenadas.ConvertDM2DD($('#lat-dm-sign', form).val() + ' ' + $('#lat-dm', form).val());

            x = lon;
            y = lat;
        }

        var data = {
            'code': code,
            'srid': srid,
            'x': x,
            'y': y,
            'mapSrid': Portal.Viewer.getMapSRID()
        }

        Portal.Viewer.ShowLoading($(_formId).closest('.menu-bar-body')[0]);

		$.ajax({
			type: 'POST',
			url: form.attr("action"),
			traditional: true,
			//data: form.serialize() + "&mapSrid=" + Portal.Viewer.getMapSRID(),
			data: $.param(data),
			success: function (r) {
				$("#resultsCoordenadas").html("");
				if (r.Success) {
					$("#resultsCoordenadas").html(r.Message)

					var coords = [r.Data.x, r.Data.y];
					                        
					var map = Portal.Viewer.getMap();
					var layer = Portal.Viewer.getTemporaryLayer();
					var source;

					if (layer) {
						source = layer.getSource();

						if (source && _feature) {
							try {
								source.removeFeature(_feature);
							} catch (ex) {}
						}
					}

					_feature = new ol.Feature({
						geometry: new ol.geom.Point(coords)
					});
					layer.getSource().addFeature(_feature);

                    _coordinatesControl.setFeature(_feature);

					if (center) {
						map.getView().setZoom(15);
						map.getView().setCenter(coords);
					}

				} else {
					//TODO: error handling
				}
				Portal.Viewer.HideLoading($(_formId).closest('.menu-bar-body')[0]);
			},
			error: function (r) {
				$('#searchCoordenadas').next('.results-area').html('');
				Portal.Viewer.HideLoading($(_formId).closest('.menu-bar-body')[0]);
			}
		});
	}

	var _convertDMS2DD = function (dms) {
	    var val = null;

        var parts = dms.replace("º", "").replace("''","").replace("'","").split(" ");

        parts[1] = parseInt(parts[1]);
        parts[2] = parseInt(parts[2]);
        parts[3] = parseFloat(parts[3]);

        val = parts[1] + parts[2]/60 + parts[3]/3600;
        if (parts[0] == 'W' || parts[0] == 'S') {
            val = val * -1;
        }
	    return val;
	}

	var _convertDM2DD = function (dms) {
	    var val = null;

        var parts = dms.replace("º", "").replace("'","").split(" ");

        parts[1] = parseInt(parts[1]);
        parts[2] = parseFloat(parts[2]);

        val = parts[1] + parts[2]/60;
        if (parts[0] == 'W' || parts[0] == 'S') {
            val = val * -1;
        }
	    return val;
	}

    var _convertDD2DMS = function (deg, is_lon) {
        var val = null;

        var d = Math.floor (deg);
        var minfloat = (deg-d)*60;
        var m = Math.floor(minfloat);
        var secfloat = (minfloat-m)*60;
        var s = parseFloat(Math.round(secfloat * 100) / 100).toFixed(2);

        if (is_lon) {
            val = ("000" + d).slice(-3) + "º " + ("00" + m).slice(-2) + "' " + ("0000" + s).slice(-5) + "''";
        } else {
            val = ("00" + d).slice(-2) + "º " + ("00" + m).slice(-2) + "' " + ("0000" + s).slice(-5) + "''";
        }

        return  val;
    }

	return {
		Init: _init,
		Load: _load,
		SetControl: function (control) {
			_coordinatesControl = control;
		},
		Transform: _transform,
		ConvertDD2DMS: _convertDD2DMS,
		ConvertDMS2DD: _convertDMS2DD,
		ConvertDM2DD: _convertDM2DD,
		Disable: _disable
	}
}());