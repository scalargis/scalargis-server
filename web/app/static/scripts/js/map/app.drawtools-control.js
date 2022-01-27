if (!window.app) {
    window.app = {};
}
var app = window.app;

app.drawtoolsControl = function (opt_options) {
    var options = opt_options || {};

    var buttonDrawTools = document.createElement('button');
    buttonDrawTools.innerHTML =
        '<i class="fa fa-edit" title="'
        + (options.drawtoolsTipLabel || 'Ferramentas de Desenho')
        +  '"><i>';

    var this_ = this;

    var handleClick = function (e) {
        Portal.Viewer.ShowPanel('drawtools');
    }

    var element = document.createElement('div');
    element.className = (options.className ? options.className + ' ' : '') + 'drawtools-control ol-selectable ol-control';
    element.appendChild(buttonDrawTools);

    ol.control.Control.call(this, {
        element: element,
        target: options.target
    });

    function removeDrawToolsInteraction() {
        //TODO
    }

    buttonDrawTools.addEventListener('click', handleClick, false);
    buttonDrawTools.addEventListener('touchstart', handleClick, false);

    this.set('options', options);
    this.set('button', buttonDrawTools);
    this.set('handleClick', handleClick);
    this.set('removeDrawToolsInteraction', removeDrawToolsInteraction);
    this.set('active', false);
};
ol.inherits(app.drawtoolsControl, ol.control.Control);

app.drawtoolsControl.prototype.disableControl = function (e) {
}

app.drawtoolsControl.prototype.setViewer = function (viewer) {
    this.viewer = viewer;
}
