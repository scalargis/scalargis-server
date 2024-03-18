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


    def truncateLayerTileCache(self, ws_name, service_name, format, srs):
        # empty gwc layer cache (no bbox)

        url = '%s/gwc/rest/seed/%s:%s.json' % (self.url, ws_name, service_name)
        headers = {'Content-Type': 'application/json'}
        auth = (self.username, self.password)

        data = """
        {'seedRequest':{'name':'%s:%s',
        'format':'%s',
        'srs':{'number': %s},
        'zoomStart':1,'zoomStop':20,
        'type':'truncate','threadCount':1}}} 
        """ % ( ws_name, service_name, format, srs)

        r = requests.post(url, headers=headers, auth=auth, data=data)
        return {"status": r.status_code, "reason": r.reason}

    def seedLayerTileCache(self, ws_name, service_name, srs, format,zoomStart, zoomStop, threadCount):
        # seed gwc layer

        url = '%s/gwc/rest/seed/%s:%s.json' % (self.url, ws_name, service_name)
        headers = {'Content-Type': 'application/json'}
        auth = (self.username, self.password)

        data = """
        {'seedRequest':{'name':'%s:%s',
        'format':'%s',
        'srs':{'number':%s},
        'zoomStart':%s,'zoomStop':%s,
        'type':'seed','threadCount':%s}}} 
        """ % ( ws_name, service_name, format, srs, zoomStart, zoomStop, threadCount)

        r = requests.post(url, headers=headers, auth=auth, data=data)
        return {"status": r.status_code, "reason": r.reason}