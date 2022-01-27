if (!window.app) {
    window.app = {};
}
var app = window.app;

app.mapHistoryControl = function (opt_options) {
            var options = opt_options || {};

            var buttonPreviousMap = document.createElement('button');
            var toolTip = options.buttonTipLabel || 'Mapa anterior';
            buttonPreviousMap.innerHTML = '<i class="fa fa-arrow-left" title="' + toolTip + '"><i>';
            buttonPreviousMap.title = toolTip;

            var this_ = this;
            var last_no_move

            function zoomPrevious(){
                options.map_view_history.length > 1 ? options.map_view_history.pop() : null;
                var nb_elements = options.map_view_history.length;
                var previous_state = options.map_view_history[nb_elements - 1];
                if (previous_state){
                    store_map_state = false;
                    map.getView().setCenter(previous_state.center);
                    store_map_state = false;
                    map.getView().setZoom(previous_state.zoom);
                    store_map_state = false;
                    map.getView().setRotation(previous_state.rotation);
                    nb_elements == 1 ? store_map_state = true : false;
                }
            }

    buttonPreviousMap.addEventListener('click', zoomPrevious, false);
    buttonPreviousMap.addEventListener('touchstart', zoomPrevious, false);

    var element = document.createElement('div');
    element.className = (options.className ? options.className + ' ' : '') + 'map-history-control-control  ol-control';
    element.appendChild(buttonPreviousMap);

    ol.control.Control.call(this, {
        element: element,
        target: options.target
    });

    this.set('options', options);
    this.set('button', buttonPreviousMap);
};

ol.inherits(app.mapHistoryControl, ol.control.Control);


