geonamesServices = (function () {

	var _elementId = '#searchbox';

	var _map = null;

    var _setMap = function (map) {
    	_map = map;
    };

  	var _geonamesBH = new Bloodhound({
	    name: 'GeoNames',
	    datumTokenizer: function (d) {
	      return Bloodhound.tokenizers.whitespace(d.name);
	    },
	    queryTokenizer: Bloodhound.tokenizers.whitespace,
	    remote: {
          //url: "http://api.geonames.org/searchJSON?username=bootleaf&featureClass=P&maxRows=10&country=PT&adminCode1=09&style=FULL&lang=pt&name_startsWith=%QUERY",
          url: "../autocomplete?term=%QUERY",
	      filter: function (data) {
	        //return $.map(data.geonames, function (result) {
	        return $.map(data, function (result) {
	          return {
                //name: result.name + ', ' + result.adminName2,
	            //lat: result.lat,
	            //lng: result.lng,
                name: result.nome,
                extra_info: result.extra_info,
                tipo: result.tipo,
                geom_json: result.geom_json,
	            source: 'GeoNames'
	          };
	        });
	      },
	      ajax: {
	        beforeSend: function (jqXhr, settings) {
	          //settings.url += '&east= + map.getBounds().getEast() + '&west=' + map.getBounds().getWest() + '&north=' + map.getBounds().getNorth() + '&south=' + map.getBounds().getSouth();
	          //$("#searchicon").removeClass('fa-search').addClass('fa-refresh fa-spin');
	          $("#searchicon").removeClass('active').addClass('searching');
	        },
	        complete: function (jqXHR, status) {
	          //$('#searchicon').removeClass("fa-refresh fa-spin").addClass('fa-search');
	          $('#searchicon').removeClass("searching").addClass('active');
	        }
	      }
	    },
	    limit: 10
	});

	_geonamesBH.initialize();


	/* instantiate the typeahead UI */
	$(_elementId).typeahead({
	    minLength: 1,
	    highlight: true,
	    hint: false
	}, {
	    name: "GeoNames",
	    displayKey: "name",
	    source: _geonamesBH.ttAdapter(),
	    templates: {
	      header: "<h4 class='typeahead-header'>&nbsp;Resultados</h4>",
	      suggestion: function (item) {
	        var text_value = item.name;
	        if (item.extra_info && item.extra_info != '') {
	            text_value = text_value + ' (' + item.extra_info + ')';
	        }

	        if (item.tipo == 'places') {
	            return '<div title="Lugar"><span class="icon-suggestion place"></span><span>' + text_value + '</span></div>';
	        } else if (item.tipo == 'roads') {
	           return '<div title="Rua/Estrada"><span class="icon-suggestion road"></span><span>' + text_value + '</span></div>';
	        } else {
	            return '<div title=""><span class="icon-suggestion"></span><span>' + text_value + '</span></div>';
	        }
	      }
	    }
	}).on("typeahead:selected", function (obj, datum) {
	    if (datum.source === "GeoNames") {

	      //var center = ol.proj.transform([parseFloat(datum.lng), parseFloat(datum.lat)], 'EPSG:4326', 'EPSG:3857');
	      //_map.getView().setCenter(center);
	      //_map.getView().setZoom(11);

           var format = new ol.format.GeoJSON();
           var geom = format.readGeometry(datum.geom_json);
           var extent = geom.transform('EPSG:4326', 'EPSG:3857').getExtent();

           var zoom_ops = { minResolution: 0.1 };
           if (geom instanceof ol.geom.Point) {
                zoom_ops.minResolution = 1;
           }

           _map.getView().fit(
               extent,
               _map.getSize(),
               zoom_ops
           );
	    }

	    /*
	    if ($(".navbar-collapse").height() > 50) {
	      $(".navbar-collapse").collapse("hide");
	    }
	    */
	}).on("typeahead:opened", function () {
	    /*
	    $(".navbar-collapse.in").css("max-height", $(document).height() - $(".navbar-header").height());
	    $(".navbar-collapse.in").css("height", $(document).height() - $(".navbar-header").height());
	    */
	}).on("typeahead:closed", function () {
	    /*
	    $(".navbar-collapse.in").css("max-height", "");
	    $(".navbar-collapse.in").css("height", "");
	    */
	});
	$(".twitter-typeahead").css("position", "static");
	$(".twitter-typeahead").css("display", "block");

	/* Highlight search box text on click */
	$(_elementId).click(function () {
	  $(this).select();
	});

    return {
    	setMap: _setMap
    }

} ());