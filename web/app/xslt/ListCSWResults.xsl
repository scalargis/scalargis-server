<?xml version="1.0" encoding="UTF-8"?>
<xsl:stylesheet xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="1.0"
 xmlns:gco="http://www.isotc211.org/2005/gco"
 xmlns:gmd="http://www.isotc211.org/2005/gmd"
 xmlns:dc="http://purl.org/dc/elements/1.1/"
 xmlns:dct="http://purl.org/dc/terms/"
 xmlns:ows="http://www.opengis.net/ows"
 xmlns:cat="http://www.esri.com/metadata/csw/"
 xmlns:srv="http://www.isotc211.org/2005/srv"
 xmlns:csw="http://www.opengis.net/cat/csw/2.0.2">

  <xsl:output method="html" encoding="iso-8859-1"/>

  <xsl:param name="catalog" />
  <xsl:param name="urlBase" />
  <xsl:param name="resultsTitle" />
  <xsl:param name="labelMetadados" />
  <xsl:param name="labelXML" />
  <xsl:param name="labelAddService" />
  <xsl:param name="labelOpen" />  

  <xsl:template match="/">
    <table class="table table-bordered table-striped">
      <tbody>
	    <xsl:apply-templates select="//csw:SearchResults | //SearchResults"/>
      </tbody>
    </table>
  </xsl:template>
  
  <xsl:template match="//csw:SearchResults | //SearchResults">
	<!--<div><xsl:value-of select="$catalog"/>1</div>-->
    <xsl:for-each select="./gmd:MD_Metadata">
      <xsl:apply-templates select="."/>
    </xsl:for-each>
  </xsl:template>
  
  <xsl:template match="gmd:MD_Metadata">
    <tr>
      <td>     
        <xsl:apply-templates select="./gmd:identificationInfo"/>
      </td>
    </tr>	
  </xsl:template>

  <xsl:template match="gmd:identificationInfo">

    <xsl:if test="gmd:MD_DataIdentification">
      <a href="#" class="a-record">
        <xsl:attribute name="fid">
          <xsl:value-of select="../gmd:fileIdentifier/gco:CharacterString" />
        </xsl:attribute>
        <xsl:if test="./gmd:MD_DataIdentification/gmd:extent/gmd:EX_Extent">
          <xsl:apply-templates select="./gmd:MD_DataIdentification/gmd:extent/gmd:EX_Extent"/>
        </xsl:if>
        <xsl:apply-templates select="./gmd:MD_DataIdentification/gmd:citation"/>
      </a>
      
      <p class="muted top-margin-10">
        <xsl:value-of select="substring(./gmd:MD_DataIdentification/gmd:abstract/gco:CharacterString, 1, 200)" />
        <xsl:if test="string-length(./gmd:MD_DataIdentification/gmd:abstract/gco:CharacterString) > 250" >
          <xsl:text> ...</xsl:text>
        </xsl:if>
      </p>      
      
      <div>
        <div class="col-md-4">
          <a target="_blank" class="metadataLink">
            <xsl:attribute name="href"><xsl:value-of select="$urlBase"/>?catalog=<xsl:value-of select="$catalog"/>&amp;uuid=<xsl:value-of select="../gmd:fileIdentifier/gco:CharacterString" />&amp;format=details</xsl:attribute>
            <xsl:value-of select="$labelMetadados" />
          </a>                
        </div>
        <div class="col-md-4">
          <a target="_blank" class="metadataLink">
            <xsl:attribute name="href"><xsl:value-of select="$urlBase"/>?uuid=<xsl:value-of select="../gmd:fileIdentifier/gco:CharacterString" />&amp;catalog=<xsl:value-of select="$catalog"/>&amp;format=xml</xsl:attribute>
            <xsl:value-of select="$labelXML" />
          </a>        
        </div>
        <div class="col-md-offset-1 col-md-3">
          <xsl:for-each select="../gmd:distributionInfo/gmd:MD_Distribution/gmd:transferOptions/gmd:MD_DigitalTransferOptions/gmd:onLine/gmd:CI_OnlineResource[./gmd:protocol/gco:CharacterString='OGC:WMS' or contains(./gmd:linkage/gmd:URL, 'wms')]">
            <xsl:if test="position() = 1">
              <xsl:text> </xsl:text>
              <a href="#" class="metadataLink">
                <xsl:attribute name="data-wms-link">
                  <xsl:value-of select="gmd:linkage/gmd:URL"/>
                </xsl:attribute>
                <xsl:if test="gmd:name/gco:CharacterString">
                  <xsl:attribute name="data-wms-layer">
                    <xsl:value-of select="gmd:name/gco:CharacterString"/>
                  </xsl:attribute>
                </xsl:if>
                <xsl:value-of select="$labelAddService" />
              </a>
            </xsl:if>
          </xsl:for-each>
        </div>      
      </div>
    
    </xsl:if>
    
    <xsl:if test="srv:SV_ServiceIdentification">
      <a href="#" class="a-record">
        <xsl:attribute name="fid">
          <xsl:value-of select="../gmd:fileIdentifier/gco:CharacterString" />
        </xsl:attribute>
        <xsl:attribute name="title">
          <xsl:apply-templates select="./srv:SV_ServiceIdentification/gmd:citation"/>
        </xsl:attribute>        
        <xsl:if test="./srv:SV_ServiceIdentification/srv:extent/gmd:EX_Extent">
          <xsl:apply-templates select="./srv:SV_ServiceIdentification/srv:extent/gmd:EX_Extent"/>
        </xsl:if>
        <xsl:apply-templates select="./srv:SV_ServiceIdentification/gmd:citation"/>
      </a>  
      
      <p class="muted top-margin-10">
        <xsl:value-of select="substring(./srv:SV_ServiceIdentification/gmd:abstract/gco:CharacterString, 1, 250)" />
        <xsl:if test="string-length(./srv:SV_ServiceIdentification/gmd:abstract/gco:CharacterString) > 250" >
          <xsl:text> ...</xsl:text>
        </xsl:if>
      </p>   
      
      <div>
        <div class="col-md-4">
          <a target="_blank" class="metadataLink">
            <xsl:attribute name="href"><xsl:value-of select="$urlBase"/>?catalog=<xsl:value-of select="$catalog"/>&amp;uuid=<xsl:value-of select="../gmd:fileIdentifier/gco:CharacterString" />&amp;format=details</xsl:attribute>
            <xsl:value-of select="$labelMetadados" />
          </a>                
        </div>
        <div class="col-md-4">
          <a target="_blank" class="metadataLink">
            <xsl:attribute name="href"><xsl:value-of select="$urlBase"/>?uuid=<xsl:value-of select="../gmd:fileIdentifier/gco:CharacterString" />&amp;catalog=<xsl:value-of select="$catalog"/>&amp;format=xml</xsl:attribute>
            <xsl:value-of select="$labelXML" />
          </a>        
        </div>
        <div class="col-md-offset-1 col-md-3">
          <xsl:if test="./srv:SV_ServiceIdentification/srv:containsOperations/srv:SV_OperationMetadata/srv:connectPoint/gmd:CI_OnlineResource/gmd:linkage">
            <xsl:text> </xsl:text>
            <a href="#" class="metadataLink">
              <xsl:attribute name="data-wms-link">
                <xsl:value-of select="./srv:SV_ServiceIdentification/srv:containsOperations/srv:SV_OperationMetadata/srv:connectPoint/gmd:CI_OnlineResource/gmd:linkage"/>
              </xsl:attribute>
              <xsl:value-of select="$labelAddService" />
            </a>
          </xsl:if>        
        </div>      
      </div>
    
    </xsl:if>
  </xsl:template>

  <!-- 'Citation->title -->
  <xsl:template match="gmd:citation">
    <xsl:value-of select="./gmd:CI_Citation/gmd:title/gco:CharacterString" />
  </xsl:template>

  <!-- 'Identification->Geographic box' block -->
  <xsl:template match="gmd:EX_Extent">
    <xsl:if test="./gmd:geographicElement/gmd:EX_GeographicBoundingBox">
      <xsl:attribute name="data-extent-bbox">
        <xsl:value-of select="./gmd:geographicElement/gmd:EX_GeographicBoundingBox/gmd:westBoundLongitude/gco:Decimal"/>
        <xsl:text> </xsl:text>
        <xsl:value-of select="./gmd:geographicElement/gmd:EX_GeographicBoundingBox/gmd:southBoundLatitude/gco:Decimal"/>
        <xsl:text> </xsl:text>
        <xsl:value-of select="./gmd:geographicElement/gmd:EX_GeographicBoundingBox/gmd:eastBoundLongitude/gco:Decimal"/>
        <xsl:text> </xsl:text>
        <xsl:value-of select="./gmd:geographicElement/gmd:EX_GeographicBoundingBox/gmd:northBoundLatitude/gco:Decimal"/>
      </xsl:attribute>
    </xsl:if>
  </xsl:template>
  
</xsl:stylesheet>