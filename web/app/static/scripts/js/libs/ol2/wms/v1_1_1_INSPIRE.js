/* Copyright (c) 2006-2013 by OpenLayers Contributors (see authors.txt for
 * full list of contributors). Published under the 2-clause BSD license.
 * See license.txt in the OpenLayers distribution or repository for the
 * full text of the license. */

/**
 * @requires OpenLayers/Format/WMSCapabilities/v1_1_1.js
 */

/**
 * Class: OpenLayers.Format.WMSCapabilities/v1_1_1_WMSC
 * Read WMS-C Capabilities version 1.1.1.
 * 
 * Inherits from:
 *  - <OpenLayers.Format.WMSCapabilities.v1_1_1>
 */
OpenLayers.Format.WMSCapabilities.v1_1_1_INSPIRE = OpenLayers.Class(
    OpenLayers.Format.WMSCapabilities.v1_1_1, {
    
    /**
     * Property: version
     * {String} The specific parser version.
     */
    version: "1.1.1",
    
    /**
     * Property: profile
     * {String} The specific profile
     */
    profile: "INSPIRE",
    
    /**
     * Constructor: OpenLayers.Format.WMSCapabilities.v1_1_1
     * Create a new parser for WMS-C capabilities version 1.1.1.
     *
     * Parameters:
     * options - {Object} An optional object whose properties will be set on
     *     this instance.
     */

    /**
     * Property: namespaces
     * {Object} Mapping of namespace aliases to namespace URIs.
     */
    namespaces: {
        wms: "http://www.opengis.net/wms",
        xlink: "http://www.w3.org/1999/xlink",
        xsi: "http://www.w3.org/2001/XMLSchema-instance",
        inspire_vs: "http://inspire.ec.europa.eu/schemas/inspire_vs/1.0",
        inspire_common: "http://inspire.ec.europa.eu/schemas/common/1.0"
    },     

    /**
     * Property: readers
     * Contains public functions, grouped by namespace prefix, that will
     *     be applied when a namespaced node is found matching the function
     *     name.  The function will be applied in the scope of this parser
     *     with two arguments: the node being read and a context object passed
     *     from the parent.
     */
    readers: {
        "wms": OpenLayers.Util.applyDefaults({
        }, OpenLayers.Format.WMSCapabilities.v1_1_1.prototype.readers["wms"]),
        "inspire_vs":  {
            "ExtendedCapabilities": function(node, obj) {
                obj.inspire = {};                
                this.readChildNodes(node, obj.inspire);
             }
        },
        "inspire_common": {
            "MetadataUrl": function(node, obj) {
                obj.metadataUrl = {};
                obj.metadataUrl.type = this.getAttributeNS(node, this.namespaces.xsi, "type");                
                this.readChildNodes(node, obj.metadataUrl);
            },
            "URL":  function(node, obj) {
                obj.url = this.getChildValue(node);
            },
            "MediaType": function(node, obj) {
                obj.mediaType = this.getChildValue(node);
            },
            "SupportedLanguages": function(node, obj) {
                obj.supportedLanguages = { languages: []};
                obj.supportedLanguages.type = this.getAttributeNS(node, this.namespaces.xsi, "type");              
                this.readChildNodes(node, obj.supportedLanguages);
            },   
            "DefaultLanguage": function(node, obj) {
                //obj.default = {};
                //this.readChildNodes(node, obj.default);
                this.readChildNodes(node, obj);
            },
            "Language": function(node, obj) {
                //obj.value = this.getChildValue(node);
                obj.language = this.getChildValue(node);
            },
            "SupportedLanguage": function(node, obj) {
                var language = {};
                obj.languages.push(language);
                this.readChildNodes(node, language);
            },
            "ResponseLanguage": function(node, obj) {
                obj.responseLanguage = {};
                this.readChildNodes(node, obj.responseLanguage);                
            }
        }
    },

    CLASS_NAME: "OpenLayers.Format.WMSCapabilities.v1_1_1_INSPIRE" 

});
