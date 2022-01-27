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

    <table class="table table-bordered table-striped" style="table-layout: fixed">
      <tbody>

            <xsl:apply-templates select="csw:GetRecordsResponse/csw:SearchResults" />

      </tbody>
    </table>
  </xsl:template>

  <xsl:template match="csw:SearchResults">
    <xsl:for-each select="./csw:Record">
      <xsl:apply-templates select="." />
    </xsl:for-each>
  </xsl:template>

  <xsl:template match="csw:Record">
    <tr>
      <td style="break-word; overflow-wrap: break-word;">
        <a href="#" class="a-record">
          <xsl:attribute name="fid">
            <xsl:value-of select="./dc:identifier" />
          </xsl:attribute>
          <xsl:if test="./ows:WGS84BoundingBox">
            <xsl:apply-templates select="./ows:WGS84BoundingBox" />
          </xsl:if>
          <xsl:apply-templates select="./dc:title"/>
        </a>
		
      <p class="muted top-margin-10">
        <xsl:value-of select="substring(./dct:abstract, 1, 250)" />
        <xsl:if test="string-length(./dct:abstract) > 250" >
          <xsl:text> ...</xsl:text>
        </xsl:if>
      </p>
	  
	  
      <div>
		  <div class="col-md-4">
			<a target="_blank" class="metadataLink">
			  <xsl:attribute name="href">
				<xsl:value-of select="$urlBase" />/catalog/search/resource/details.page?uuid=<xsl:value-of select="./dc:identifier[contains(@scheme,'DocID')]"/>
			  </xsl:attribute>
			  <xsl:value-of select="$labelMetadados" />
			</a>
			
		  </div>	  
          <div class="col-md-4">
            <a target="_blank" class="metadataLink">
              <xsl:attribute name="href">

                <xsl:value-of select="./dct:references[contains(@scheme,'Document')]"/>
              </xsl:attribute>
              <xsl:value-of select="$labelXML" />
            </a>
          </div>
          <div class="col-md-offset-1 col-md-3">
            <xsl:choose>
			  <xsl:when test="(./dc:type='application' or ./dc:type='liveData') and (contains(translate(./dct:references[contains(@scheme,'Server')],'WMS','wms'),'wms'))">
				<a href="#" class="metadataLink">
				
				  <xsl:attribute name="data-wms-link">
					<xsl:value-of select="./dct:references[contains(@scheme,'Server')]"/>
				  </xsl:attribute>
				  <xsl:value-of select="$labelAddService" />
				</a>
				
			  </xsl:when>
			</xsl:choose>
		   </div>
		</div>
	</td>
  </tr>
  </xsl:template>

  <!-- Geographic box block -->
  <xsl:template match="ows:WGS84BoundingBox">
    <xsl:attribute name="data-extent-bbox">
      <xsl:value-of select="./ows:LowerCorner"/>
      <xsl:text> </xsl:text>
      <xsl:value-of select="./ows:UpperCorner"/>
    </xsl:attribute>
  </xsl:template>

</xsl:stylesheet>