# -*- coding: utf-8 -*-
"""
/***************************************************************************
        WKT SI Tools
        copyright            : (C)  WKT - SI
 ***************************************************************************/
"""
import requests

class GeoserverRestRequests():

    """Geoserver Rest via Requests"""
    def __init__(self,url,user,passw):
        self.url = url
        self.username = user
        self.password = passw

    def create_workspace(self, ws_name):
        url = '%s/rest/workspaces' % self.url
        headers = {'Content-Type': 'text/xml'}
        auth = (self.username, self.password)
        data = "<workspace><name>%s</name></workspace>" % ws_name
        r = requests.post(url, headers=headers, auth=auth, data=data)
        print(r)
        return r.text


    def create_datastore(self, ws_name, store_name, file_name):
        url = '%s/rest/workspaces/%s/coveragestores?configure=all' % (self.url, ws_name)
        headers = {'Content-Type': 'text/xml'}
        auth = (self.username, self.password)
        data = "<coverageStore><name>%s</name><enabled>true</enabled><type>GeoTIFF</type><url>%s</url><workspace>%s</workspace></coverageStore>" % (store_name,file_name,ws_name)
        r = requests.post(url, headers=headers, auth=auth, data=data)
        return r.text


    def publish_raster(self,ws_name,store_name,service_name,srs):
        url = '%s/rest/workspaces/%s/coveragestores/%s/coverages' % (self.url, ws_name, store_name)
        headers = {'Content-Type': 'text/xml'}
        auth = (self.username, self.password)
        data = "<coverage><name>%s</name><srs>EPSG:%s</srs><projectionPolicy>FORCE_DECLARED</projectionPolicy><title>%s</title></coverage>" % (service_name,srs,service_name)
        r = requests.post(url, headers=headers, auth=auth, data=data)
        return r.text

    def publish_postgis(self,ws_name,store_name,service_name,srs):
        url = '%s/rest/workspaces/%s/datastores/%s/featuretypes' % (self.url, ws_name, store_name)
        headers = {'Content-Type': 'text/xml'}
        auth = (self.username, self.password)
        data = """<featureType><name>%s</name><nativeCRS>EPSG:%s</nativeCRS><srs>EPSG:%s</srs></featureType>""" % (service_name,srs,srs)
        r = requests.post(url, headers=headers, auth=auth, data=data)
        return r.text

    def setDefaultStyle(self,ws_name,service_name,style_name):
        url = '%s/rest/layers/%s:%s' % (self.url, ws_name, service_name)
        headers = {'Content-Type': 'text/xml'}
        auth = (self.username, self.password)
        data="""<layer><defaultStyle><name>%s</name></defaultStyle><enabled>true</enabled></layer>"""  % (style_name)
        r = requests.put(url, headers=headers, auth=auth, data=data)
        return r.text
     
    # other styles (not default)
    def setStyle(self,ws_name,service_name,style_name):
        url = '%s/rest/layers/%s:%s' % (self.url, ws_name, service_name)
        headers = {'Content-Type': 'text/xml'}
        auth = (self.username, self.password)
        data="""<layer>
            <styles class="linked-hash-set">
                <style>
                    <name>%s</name>
                 </style>
            </styles>
        </layer>"""  % (style_name)
        r = requests.put(url, headers=headers, auth=auth, data=data)
        return r.text
        
    def removeLayer(self,ws_name, store_name, service_name):
        url = '%s/rest/layers/%s:%s' % (self.url, ws_name, service_name)
        headers = {'Content-Type': 'text/xml'}
        auth = (self.username, self.password)
        r = requests.delete(url, headers=headers, auth=auth)
        
        url = '%s/rest/workspaces/%s/datastores/%s/featuretypes/%s.xml' % (self.url, ws_name, store_name, service_name)
        headers = {'Content-Type': 'text/xml'}
        auth = (self.username, self.password)
        r = requests.delete(url, headers=headers, auth=auth)

        return r.text


    def cleanLayerTileCacheByBbox(self, ws_name, service_name, bbox=""):
        url = '%s/gwc/rest/seed/%s:%s' % (self.url, ws_name, service_name)
        headers = {'Content-Type': 'text/xml'}
        auth = (self.username, self.password)

        
        data = """
        {'seedRequest':{'name':'%s:%s','bounds':{'coords':{ 'double':['-124.0','22.0','66.0','72.0']}},
        'srs':{'number':3857},'zoomStart':1,'zoomStop':20,'format':'image\/png','type':'truncate','threadCount':1}}} 
        """ % (self.url, ws_name, service_name)

        r = requests.post(url, headers=headers, auth=auth, data=data)
        return r.text