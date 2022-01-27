//requirements
const gulp = require('gulp');
const { series } = require('gulp');
const merge = require("merge-stream");
const del = require('del');
const concat = require('gulp-concat');
const minify = require('gulp-minify');
const cleanCss = require('gulp-clean-css');

//constants
const output_dir = './web/app/static/build';

// tasks
function copy_images() {
  return gulp.src('./web/app/static/images/sort_*.png').pipe(gulp.dest(output_dir + '/images/'));
}

function copy_fonts() {
    return merge([
        gulp.src('./web/app/static/bower_components/font-awesome/fonts/*.*').pipe(gulp.dest(output_dir + '/fonts/')),
        gulp.src('./web/app/static/bower_components/bootstrap/fonts/*.*').pipe(gulp.dest(output_dir + '/fonts/')),
        gulp.src('./web/app/static/bower_components/jspanel3/source/fonts/*.*').pipe(gulp.dest(output_dir + '/css/fonts/')),
        gulp.src('./web/app/static/css/font-simfat/fonts/*.*').pipe(gulp.dest(output_dir + '/fonts/')),
        gulp.src('./web/app/static/css/font-sim/fonts/*.*').pipe(gulp.dest(output_dir + '/fonts/'))
    ]);
};

function pack_js_map_modules() {
	return gulp.src([
        './web/app/static/bower_components/jquery-3.2.1/dist/jquery.min.js',
        './web/app/static/bower_components/bootstrap/dist/js/bootstrap.min.js',
        './web/app/static/bower_components/purl/purl.js',
        './web/app/static/bower_components/moment/min/moment.min.js',
        './web/app/static/bower_components/moment/min/locales.min.js',
        './web/app/static/scripts/js/libs/jquery.blockUI.min.js',
        './web/app/static/scripts/js/libs/jquery.inputmask.js',
        './web/app/static/bower_components/nouislider/nouislider.min.js',
        './web/app/static/bower_components/bootstrap-datetimepicker/build/js/bootstrap-datetimepicker.min.js',
        './web/app/static/bower_components/bootstrap-multiselect/dist/js/bootstrap-multiselect.js',
        './web/app/static/bower_components/jspanel3/source/jquery.jspanel.min.js',
        './web/app/static/bower_components/tinycolor/dist/tinycolor-min.js',
        './web/app/static/bower_components/pick-a-color/build/1.2.3/js/pick-a-color-1.2.3.min.js',
        './web/app/static/bower_components/file-saver/dist/FileSaver.min.js'
        ])
    .pipe(concat('bundle-map-modules.js'))
    .pipe(gulp.dest(output_dir + '/js'));
};

function pack_js_map_ol() {
	return gulp.src([
	        './web/app/static/bower_components/proj4/dist/proj4.js',
	        './web/app/static/bower_components/openlayers/ol-debug.js',
	        //'./web/app/static/scripts/js/libs/ol2/OpenLayers-ows.js',
	        './web/app/static/scripts/js/libs/ol2/OpenLayers.js',
	        './web/app/static/scripts/js/libs/ol2/wms/v1_1_1_INSPIRE.js',
	        './web/app/static/scripts/js/libs/ol2/wms/v1_3_0_INSPIRE.js',
            './web/app/static/scripts/js/libs/ol2/wfs/v1_1_0_INSPIRE.js',
            './web/app/static/scripts/js/libs/ol2/wfs/v2_0_0_INSPIRE.js'
	        ])
		.pipe(concat('bundle-map-ol.js'))
        .pipe(minify({
            ext:{
                min:'.js'
            },
            noSource: true
        }))
		.pipe(gulp.dest(output_dir + '/js'));
};

function pack_js_map_app() {
	return gulp.src([
        './web/app/static/scripts/js/map/app.layers-control.js',
        './web/app/static/scripts/js/map/app.basemaps-control.js',
        './web/app/static/scripts/js/map/app.basemaps-map-control.js',
        './web/app/static/scripts/js/map/app.zoom-extent-control.js',
        './web/app/static/scripts/js/map/app.map-history-control.js',
        './web/app/static/scripts/js/map/app.measure-control.js',
        './web/app/static/scripts/js/map/app.mouse-position-control.js',
        './web/app/static/scripts/js/map/app.coordinates-control.js',
        './web/app/static/scripts/js/map/app.numeric-scale-control.js',
        './web/app/static/scripts/js/map/app.feature-info-control.js',
        './web/app/static/scripts/js/map/app.feature-select-control.js',
        './web/app/static/scripts/js/map/app.google-streetview-control.js',
        './web/app/static/scripts/js/map/app.drawtools-control.js',
        './web/app/static/scripts/js/map/app.generic-draw-control.js',
        './web/app/static/scripts/js/map/portal.viewer.js',
        './web/app/static/scripts/js/map/portal.viewer.coordenadas.js',
        './web/app/static/scripts/js/map/portal.viewer.pdm.js',
        './web/app/static/scripts/js/map/portal.viewer.print.js',
        './web/app/static/scripts/js/map/portal.viewer.ows.js',
        './web/app/static/scripts/js/map/portal.viewer.catalog.js',
        './web/app/static/scripts/js/map/portal.viewer.search.js',
        './web/app/static/scripts/js/map/portal.viewer.planos.js',
        './web/app/static/scripts/js/map/portal.viewer.confrontation.js',
        './web/app/static/scripts/js/map/portal.viewer.drawtools.js',
        './web/app/static/scripts/js/map/main.js'
        ])
    .pipe(concat('bundle-map-app.js'))
    .pipe(minify({
        ext:{
            min:'.js'
        },
        noSource: true
    }))
    .pipe(gulp.dest(output_dir + '/js'));
};

function pack_js_map_app_post() {
	return gulp.src([
        './web/app/static/bower_components/typeahead.js/dist/typeahead.bundle.js',
        './web/app/static/scripts/js/map/geonames-services.js'
        ])
    .pipe(concat('bundle-map-app-post.js'))
    .pipe(minify({
        ext:{
            min:'.js'
        },
        noSource: true
    }))
    .pipe(gulp.dest(output_dir + '/js'));
};

function pack_css_map() {
	return gulp.src([
        './web/app/static/bower_components/openlayers/ol.css',
        './web/app/static/bower_components/bootstrap/dist/css/bootstrap.css',
        './web/app/static/bower_components/font-awesome/css/font-awesome.min.css',
        './web/app/static/css/font-simfat/css/font-simfat.css',
        './web/app/static/bower_components/nouislider/nouislider.min.css',
        './web/app/static/bower_components/bootstrap-datetimepicker/build/css/bootstrap-datetimepicker.min.css',
        './web/app/static/bower_components/bootstrap-multiselect/dist/css/bootstrap-multiselect.css',
        './web/app/static/bower_components/pick-a-color/build/1.2.3/css/pick-a-color-1.2.3.min.css',
        //'./web/app/static/scripts/js/jsPanel-3.9.3/jquery.jspanel.min.css',
        './web/app/static//bower_components/jspanel3/source/jquery.jspanel.min.css',
        './web/app/static/css/common.css',
        './web/app/static/css/map.css'
        ])
    .pipe(concat('bundle-map.css'))
    .pipe(cleanCss())
    .pipe(gulp.dest(output_dir + '/css'));
};

function pack_css_map_header() {
	return gulp.src([
        './web/app/static/bower_components/openlayers/ol.css',
        './web/app/static/bower_components/bootstrap/dist/css/bootstrap.css',
        './web/app/static/bower_components/font-awesome/css/font-awesome.min.css',
        './web/app/static/css/font-simfat/css/font-simfat.css',
        './web/app/static/css/font-sim/css/font-sim.css',
        './web/app/static/bower_components/nouislider/nouislider.min.css',
        './web/app/static/bower_components/bootstrap-datetimepicker/build/css/bootstrap-datetimepicker.min.css',
        './web/app/static/bower_components/bootstrap-multiselect/dist/css/bootstrap-multiselect.css',
        './web/app/static/bower_components/pick-a-color/build/1.2.3/css/pick-a-color-1.2.3.min.css',
        //'./web/app/static/scripts/js/jsPanel-3.9.3/jquery.jspanel.min.css',
        './web/app/static/bower_components/jspanel3/source/jquery.jspanel.min.css',
        './web/app/static/css/common.css',
        './web/app/static/css/map.css',
        './web/app/static/css/map_header.css'
        ])
    .pipe(concat('bundle-map-header.css'))
    .pipe(cleanCss())
   .pipe(gulp.dest(output_dir + '/css'));
};

function pack_js_backoffice_modules() {
	return gulp.src([
        './web/app/static/bower_components/jquery-3.2.1/dist/jquery.min.js',
        './web/app/static/bower_components/jquery-ui-1.12.1/jquery-ui.min.js',
        './web/app/static/bower_components/bootstrap/dist/js/bootstrap.min.js',
        './web/app/static/bower_components/moment/min/moment.min.js',
        './web/app/static/bower_components/moment/min/locales.min.js',
        './web/app/static/bower_components/bootstrap-select/dist/js/bootstrap-select.min.js',
        './web/app/static/bower_components/bootstrap-select/dist/js/i18n/defaults-pt_PT.min.js',
        './web/app/static/bower_components/bootstrap-datetimepicker/build/js/bootstrap-datetimepicker.min.js',
        './web/app/static/bower_components/metisMenu/dist/metisMenu.min.js',
        './web/app/static/bower_components/d3/d3.js',
        './web/app/static/scripts/js/libs/svg/tools.js',
        './web/app/static/scripts/js/libs/sb-admin-2.js',
        './web/app/static/bower_components/codemirror/lib/codemirror.js',
        './web/app/static/bower_components/codemirror/addon/edit/matchbrackets.js',
        './web/app/static/bower_components/codemirror/addon/comment/continuecomment.js',
        './web/app/static/bower_components/codemirror/addon/comment/comment.js',
        './web/app/static/bower_components/codemirror/mode/javascript/javascript.js',
        './web/app/static/bower_components/codemirror/mode/xml/xml.js',
        './web/app/static/bower_components/codemirror/mode/css/css.js',
        './web/app/static/bower_components/codemirror/mode/htmlmixed/htmlmixed.js'
        ])
    .pipe(concat('bundle-backoffice-modules.js'))
    .pipe(gulp.dest(output_dir + '/js'));
};

function pack_css_backoffice() {
	return gulp.src([
        './web/app/static/bower_components/bootstrap/dist/css/bootstrap.css',
        './web/app/static/bower_components/font-awesome/css/font-awesome.min.css',
        './web/app/static/bower_components/bootstrap-select/dist/css/bootstrap-select.min.css',
        './web/app/static/bower_components/bootstrap-datetimepicker/build/css/bootstrap-datetimepicker.min.css',
        './web/app/static/bower_components/metisMenu/dist/metisMenu.min.css',
        './web/app/static/css/libs/timeline.css',
        './web/app/static/css/libs/sb-admin-2.css',
        './web/app/static/bower_components/codemirror/lib/codemirror.css',
        './web/app/static/css/style.css'
        ])
    .pipe(concat('bundle-backoffice.css'))
    .pipe(cleanCss())
   .pipe(gulp.dest(output_dir + '/css'));
};

function clean(cb) {
  return del([
    output_dir + '/fonts/*.*',
    output_dir + '/js/*.*',
    output_dir + '/css/*.*',
    output_dir + '/images/*.*'
  ]);
}

/*
function build(cb) {
  // body omitted
  console.log('build - public');
  cb();
}
*/
const build = series(
    clean,
    copy_images, copy_fonts,
    pack_js_map_modules, pack_js_map_ol, pack_js_map_app, pack_js_map_app_post,
    pack_css_map, pack_css_map_header, pack_js_backoffice_modules, pack_css_backoffice
  );

//exports
exports.build = build;
exports.copy_images = copy_images;
exports.copy_fonts = copy_fonts;
exports.pack_js_map_modules = pack_js_map_modules;
exports.pack_js_map_ol = pack_js_map_ol;
exports.pack_js_map_app = pack_js_map_app;
exports.pack_js_map_app_post = pack_js_map_app_post;
exports.pack_css_map = pack_css_map;
exports.pack_css_map_header = pack_css_map_header;
exports.pack_js_backoffice_modules = pack_js_backoffice_modules;
exports.pack_css_backoffice = pack_css_backoffice;
exports.clean = clean;
exports.default = build;