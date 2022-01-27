if (!window.app) {
    window.app = {};
}
var app = window.app;

app.printControl = function (opt_options) {
    var options = opt_options || {};

    var buttonPrint = document.createElement('button');
    buttonPrint.innerHTML = '<i class="fa fa-print"><i>';

    var this_ = this;

    var handlePrint = function (e) {

        console.log('print');

        $("#sidebar > ul.nav.nav-tabs > li").removeClass("active");
        $("#sidebar > div.tab-content > div.tab-pane").removeClass("active");

        Portal.Plantas.Load(options.url, "#tab-tools");       
    }

    buttonPrint.addEventListener('click', handlePrint, false);
    buttonPrint.addEventListener('touchstart', handlePrint, false);

    var element = document.createElement('div');
    element.className = 'print-control ol-unselectable ol-control';
    element.appendChild(buttonPrint);

    ol.control.Control.call(this, {
        element: element,
        target: options.target
    });

    this.set('disableControl', function (e) {
        //map.un('singleclick', handleMapClick);
    });
};
ol.inherits(app.printControl, ol.control.Control);