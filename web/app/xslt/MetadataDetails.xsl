<?xml version="1.0" encoding="iso-8859-1"?>
<!-- Copyright (c)2007, Instituto Geográfico Português, Sistema Nacional de Informação Geográfica,  
      Visualização de metadados ISO 19139, Perfil MIG
      Folha de estilos "MIG GeoPortal 9.3.1" - versão 1.0, 24 Julho de 2009-->
<xsl:stylesheet xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="1.0"
 xmlns:gco="http://www.isotc211.org/2005/gco"
 xmlns:gmd="http://www.isotc211.org/2005/gmd"
 xmlns:dc="http://purl.org/dc/elements/1.1/"
 xmlns:dct="http://purl.org/dc/terms/"
 xmlns:ows="http://www.opengis.net/ows"
 xmlns:cat="http://www.esri.com/metadata/csw/"
 xmlns:srv="http://www.isotc211.org/2005/srv"
 xmlns:csw="http://www.opengis.net/cat/csw/2.0.2"
 xmlns:gml="http://www.opengis.net/gml"
 xmlns:xlink="http://www.w3.org/1999/xlink" exclude-result-prefixes="gco cat gmd dc dct ows cat srv csw gml xlink">
  <xsl:output method="html"/>
  <xsl:strip-space elements="*"/>

  <xsl:param name="siteRoot" />

  <xsl:template match="/">
    <xsl:apply-templates select="//gmd:MD_Metadata | //MD_Metadata"/>
  </xsl:template>

  <xsl:template match="//gmd:MD_Metadata | //MD_Metadata">
    <xsl:variable name="titulo" select="./gmd:identificationInfo/gmd:MD_DataIdentification/gmd:citation/gmd:CI_Citation/gmd:title/gco:CharacterString | 
    ./gmd:identificationInfo/srv:SV_ServiceIdentification/gmd:citation/gmd:CI_Citation/gmd:title/gco:CharacterString | ./identificationInfo/MD_DataIdentification/citation/CI_Citation/title/CharacterString | 
    ./identificationInfo/SV_ServiceIdentification/citation/CI_Citation/title/CharacterString"/>
    <html>
      <head>
        <title>
          SIM Portimão ::
          <xsl:choose>
            <xsl:when test="($titulo != &apos;&apos;)">
              <xsl:value-of select="$titulo"/>
            </xsl:when>
            <xsl:otherwise>
              <xsl:text>??</xsl:text>
            </xsl:otherwise>
          </xsl:choose>
        </title>
        <link rel="stylesheet" type="text/css">
          <xsl:attribute name="href"><xsl:value-of select="$siteRoot"/>/static/css/migSNIG931.css</xsl:attribute>
        </link>
      </head>
      <body>
        <div class="caixaFixa">
          <div style="margin-left: 20px">
            <img src="/static/img/logo_cmp_sim_full.png" width="250" />
          </div>
          <div class="caixaCabecalho">
            <h1>
              <xsl:choose>
                <xsl:when test="($titulo != &apos;&apos;)">
                  <xsl:value-of select="$titulo"/>
                </xsl:when>
                <xsl:otherwise>
                  <xsl:text>???</xsl:text>
                </xsl:otherwise>
              </xsl:choose>
            </h1>
            <span class="red">
              <xsl:choose>
                <xsl:when test="./gmd:hierarchyLevel | ./hierarchyLevel">
                  <xsl:value-of select="./gmd:hierarchyLevel | ./hierarchyLevel"/>
                </xsl:when>
              </xsl:choose>
            </span>
          </div>
          <xsl:if test="./gmd:identificationInfo | ./identificationInfo | .//srv:SV_ServiceIdentification | .//SV_ServiceIdentification">
            <xsl:apply-templates select="./gmd:identificationInfo/gmd:MD_DataIdentification | ./identificationInfo/MD_DataIdentification"/>
            <xsl:apply-templates select="./gmd:identificationInfo/srv:SV_ServiceIdentification | ./identificationInfo/SV_ServiceIdentification"/>
            <xsl:apply-templates select="./gmd:distributionInfo/gmd:MD_Distribution | ./distributionInfo/MD_Distribution"/>
            <xsl:apply-templates select="./gmd:dataQualityInfo/gmd:DQ_DataQuality | ./dataQualityInfo/DQ_DataQuality"/>
            <div class="caixa">
              <div class="tituloCaixaSeccao">Sistema de Referência</div>
              <xsl:apply-templates select="./gmd:referenceSystemInfo/gmd:MD_ReferenceSystem | ./referenceSystemInfo/MD_ReferenceSystem"/>
            </div>
            <div class="caixa">
              <div class="tituloCaixaSeccao">Metametadados</div>
              <div class="caixaElemento">
                <span class="elemento">Identificador Único: </span>
                <span class="TextoElemento">
                  <xsl:value-of select="./gmd:fileIdentifier/gco:CharacterString | ./fileIdentifier/CharacterString"/>
                </span>
              </div>
              <div class="caixaElemento">
                <span class="elemento">Idioma dos Metadados: </span>
                <span class="TextoElemento">
                  <xsl:value-of select="./gmd:language/gmd:LanguageCode | ./language/LanguageCode"/>
                </span>
              </div>
              <xsl:apply-templates select="./gmd:contact | ./contact"/>
              <div class="caixaElemento">
                <span class="elemento">Data dos Metadados: </span>
                <span class="TextoElemento">
                  <xsl:value-of select="./gmd:dateStamp | ./dateStamp"/>
                </span>
              </div>
              <div class="caixaElemento">
                <span class="elemento">Designação da Norma e Perfil de Metadados : </span>
                <span class="TextoElemento">
                  <xsl:value-of select="./gmd:metadataStandardName | ./metadataStandardName"/>
                </span>
              </div>
              <div class="caixaElemento">
                <span class="elemento">Versão da Norma de Metadados : </span>
                <span class="TextoElemento">
                  <xsl:value-of select="./gmd:metadataStandardVersion | ./metadataStandardVersion"/>
                </span>
              </div>
            </div>
          </xsl:if>
          <!--      -->
        </div>
        <span class="footer">Folha de Estilos "MIG Azul e Cinza Claro",  28 de Agosto de 2009 </span>
      </body>
    </html>
  </xsl:template>
  <!-- Template MD_DataIdentification-->
  <xsl:template match="*/gmd:identificationInfo/gmd:MD_DataIdentification | */identificationInfo/MD_DataIdentification">
    <div class="caixa">
      <div class="tituloCaixaSeccao">Identificação do Conjunto de Dados Geográficos</div>
      <div class="caixa">
        <div class="tituloCaixa">Elementos de Referência</div>
        <xsl:apply-templates select="gmd:citation/gmd:CI_Citation | citation/CI_Citation"/>
      </div>
      <div class="caixa">
        <div class="tituloCaixa">Resumo</div>
        <span class="caixaElemento">
          <span class="textoElemento">
            <xsl:value-of select="gmd:abstract/gco:CharacterString | abstract/CharacterString"/>
          </span>
        </span>
        <xsl:apply-templates select="gmd:abstract/gmd:PT_FreeText"/>
      </div>
      <div class="caixa">
        <div class="tituloCaixa">Objectivo</div>
        <span class="caixaElemento">
          <span class="textoElemento">
            <xsl:value-of select="gmd:purpose/gco:CharacterString | purpose/CharacterString"/>
          </span>
        </span>
        <xsl:apply-templates select="gmd:purpose/gmd:PT_FreeText"/>
      </div>
      <xsl:apply-templates select="gmd:pointOfContact | pointOfContact"/>
      <xsl:apply-templates select="gmd:descriptiveKeywords | descriptiveKeywords"/>
      <xsl:apply-templates select="gmd:resourceConstraints | resourceConstraints"/>
      <xsl:apply-templates select="gmd:spatialResolution | spatialResolution"/>
      <xsl:apply-templates select="gmd:extent | extent"/>
      <div class="caixaElemento">
        <span class="elemento">Créditos: </span>
        <xsl:for-each select="gmd:credit/gco:CharacterString | credit/CharacterString">
          <span class="textoElemento">
            <xsl:value-of select="."/>
            <xsl:if test="position()!=last()">;</xsl:if>
          </span>
        </xsl:for-each>
      </div>
      <div class="caixaElemento">
        <span class="elemento">Tipo de Representação Espacial: </span>
        <xsl:for-each select="gmd:spatialRepresentationType/gmd:MD_SpatialRepresentationTypeCode | spatialRepresentationType/MD_SpatialRepresentationTypeCode">
          <span class="textoElemento">
            <xsl:value-of select="."/>
            <xsl:if test="position()!=last()">;</xsl:if>
          </span>
        </xsl:for-each>
      </div>
      <div class="caixaElemento">
        <span class="elemento">Idioma do CDG: </span>
        <span class="textoElemento">
          <xsl:value-of select="gmd:language/gmd:LanguageCode | language/LanguageCode"/>
        </span>
      </div>
      <div class="caixaElemento">
        <span class="elemento">Conjunto de Caracteres Utilizados: </span>
        <span class="textoElemento">
          <xsl:value-of select="gmd:characterSet | characterSet"/>
        </span>
      </div>
      <div class="caixaElemento">
        <span class="elemento">Categoria Temática: </span>
        <xsl:for-each select="gmd:topicCategory/gmd:MD_TopicCategoryCode | topicCategory/MD_TopicCategoryCode">
          <xsl:variable name="nomeCod">
            <xsl:value-of select="."/>
          </xsl:variable>
          <xsl:variable name="nome">
            <xsl:choose>
              <xsl:when test="$nomeCod = 'farming'">Agricultura Pesca Pecuária </xsl:when>
              <xsl:when test="$nomeCod = 'biota'">Biótopos </xsl:when>
              <xsl:when test="$nomeCod = 'boundaries'">Limites Administrativos </xsl:when>
              <xsl:when test="$nomeCod = 'climatologyMeteorologyAtmosphere'">Climatologia Atmosfera </xsl:when>
              <xsl:when test="$nomeCod = 'economy'">Economia </xsl:when>
              <xsl:when test="$nomeCod = 'elevation'">Altimetria Batimetria </xsl:when>
              <xsl:when test="$nomeCod = 'environment'">Ambiente </xsl:when>
              <xsl:when test="$nomeCod = 'geoscientificInformation'">Geociências </xsl:when>
              <xsl:when test="$nomeCod = 'health'">Saúde </xsl:when>
              <xsl:when test="$nomeCod = 'intelligenceMilitary'">Informação Militar</xsl:when>
              <xsl:when test="$nomeCod = 'inlandWaters'">Águas Interiores </xsl:when>
              <xsl:when test="$nomeCod = 'location'">Localização </xsl:when>
              <xsl:when test="$nomeCod = 'oceans'">Oceanos </xsl:when>
              <xsl:when test="$nomeCod = 'planningCadastre'">Planeamento e Cadastro </xsl:when>
              <xsl:when test="$nomeCod = 'society'">Socieadade e Cultura </xsl:when>
              <xsl:when test="$nomeCod = 'structure'">Património Edificado </xsl:when>
              <xsl:when test="$nomeCod = 'transportation'">Transportes </xsl:when>
              <xsl:when test="$nomeCod = 'utilitiesCommunication'">Infraestruturas de Comunicação </xsl:when>
              <xsl:when test="$nomeCod = 'imageryBaseMapsEarthCover'">Cartografia de Base Coberturas Aéreas Imagens Satélite</xsl:when>
            </xsl:choose>
          </xsl:variable>
          <span class="textoElemento">
            <xsl:value-of select="$nome"/>
            <xsl:if test="position()!=last()">;</xsl:if>
          </span>
        </xsl:for-each>
      </div>
    </div>
  </xsl:template>
  <!--Template srv:SV_ServiceIdentification -->
  <xsl:template match="*/gmd:identificationInfo/srv:SV_ServiceIdentification | */identificationInfo/SV_ServiceIdentification">
    <div class="caixa">
      <div class="tituloCaixaSeccao">Identificação do Serviço</div>
      <div class="caixa">
        <div class="tituloCaixa">Elementos de Referência</div>
        <xsl:apply-templates select="gmd:citation/gmd:CI_Citation | citation/CI_Citation"/>
      </div>
      <div class="caixa">
        <div class="tituloCaixa">Resumo</div>
        <xsl:value-of select="gmd:abstract/gco:CharacterString | abstract/CharacterString"/>
        <xsl:apply-templates select="gmd:abstract/gmd:PT_FreeText"/>
      </div>
      <div class="caixa">
        <div class="tituloCaixa">Objectivo</div>
        <xsl:value-of select="gmd:purpose/gco:CharacterString | purpose/CharacterString"/>
        <xsl:apply-templates select="gmd:purpose/gmd:PT_FreeText"/>
      </div>
      <xsl:apply-templates select="gmd:pointOfContact | pointOfContact"/>
      <xsl:apply-templates select="gmd:descriptiveKeywords | descriptiveKeywords"/>
      <xsl:apply-templates select="gmd:resourceConstraints | resourceConstraints"/>
      <xsl:apply-templates select="srv:containsOperations | containsOperations"/>
      <xsl:apply-templates select="srv:extent | extent"/>
      <div class="caixaElemento">
        <span class="elemento">Créditos: </span>
        <xsl:for-each select="gmd:credit/gco:CharacterString | credit/CharacterString">
          <span class="textoElemento">
            <xsl:value-of select="."/>
            <xsl:if test="position()!=last()">;</xsl:if>
          </span>
        </xsl:for-each>
      </div>
      <div class="caixaElemento">
        <span class="elemento">Tipo de Serviço: </span>
        <span class="textoElemento">
          <xsl:value-of select="srv:serviceType/gco:LocalName | serviceType/LocalName"/>
        </span>
      </div>
      <div class="caixaElemento">
        <span class="elemento">Versão do Tipo de Serviço: </span>
        <xsl:for-each select="srv:serviceTypeVersion/gco:CharacterString | serviceTypeVersion/CharacterString">
          <span class="textoElemento">
            <xsl:value-of select="."/>
            <xsl:if test="position()!=last()">;</xsl:if>
          </span>
        </xsl:for-each>
      </div>
      <div class="caixaElemento">
        <span class="elemento">Emparelhamento: </span>
        <span class="textoElemento">
          <xsl:value-of select="srv:couplingType/srv:SV_CouplingType | couplingType/SV_CouplingType"/>
        </span>
      </div>
    </div>
  </xsl:template>
  <!-- Template  SV_OperationMetadata   -->
  <xsl:template match="srv:SV_OperationMetadata | SV_OperationMetadata">
    <div class="caixa">
      <div class="tituloCaixa">Operações</div>
      <div class="caixaElemento">
        <span class="elemento">Operação: </span>
        <span class="textoElemento">
          <xsl:value-of select="srv:operationName/gco:CharacterString | operationName/CharacterString"/>
        </span>
      </div>
      <div class="caixaElemento">
        <span class="elemento">DCP: </span>
        <span class="textoElemento">
          <xsl:value-of select="srv:DCP/srv:DCPList | DCP/DCPList"/>
        </span>
      </div>
      <div class="caixa">
        <div class="tituloCaixa">Ponto de Conexão </div>
        <span class="elemento">Ponto de Conexão </span>
        <xsl:apply-templates select="srv:connectPoint |connectPoint"/>
      </div>
    </div>
  </xsl:template>
  <!-- *********************  Template CI_Citation ******************************************************* -->
  <xsl:template match="gmd:CI_Citation | CI_Citation">
    <div class="caixaElemento">
      <span class="elemento">Titulo: </span>
      <span class="textoElemento">
        <xsl:value-of select="gmd:title/gco:CharacterString | title/CharacterString"/>
        <xsl:apply-templates select="gmd:title/gmd:PT_FreeText"/>
      </span>
    </div>
    <div class="caixaElemento">
      <span class="elemento">Título Alternativo: </span>
      <span class="textoElemento">
        <xsl:value-of select="gmd:alternateTitle/gco:CharacterString | alternateTitle/CharacterString"/>
      </span>
    </div>
    <div class="caixaElemento">
      <span class="elemento">Data de Referência: </span>
      <xsl:apply-templates select="gmd:date/gmd:CI_Date | date/CI_Date"/>
    </div>
    <div class="caixaElemento">
      <span class="elemento">Edição: </span>
      <span class="textoElemento">
        <xsl:value-of select="gmd:edition/gco:CharacterString | edition/CharacterString"/>
      </span>
    </div>
    <div class="caixaElemento">
      <span class="elemento">Data de Edição: </span>
      <span class="textoElemento">
        <xsl:value-of select="gmd:editionDate/gco:Date | editionDate/Date"/>
      </span>
    </div>
    <div class="caixaElemento">
      <span class="elemento">Identificador: </span>
      <span class="textoElemento">
        <xsl:value-of select="gmd:identifier/gmd:MD_Identifier/gmd:code/gco:CharacterString | identifier/MD_Identifier/code/CharacterString"/>
      </span>
    </div>
    <div class="caixaElemento">
      <span class="elemento">Série: </span>
      <span class="textoElemento">
        <xsl:value-of select="gmd:series/gmd:CI_Series/gmd:name/gco:CharacterString | series/CI_Series/name/CharacterString"/>
      </span>
    </div>
    <!--	<br/>
				<xsl:apply-templates select="gmd:citedResponsibleParty | citedResponsibleParty"/> -->
  </xsl:template>
  <!-- *********************** Template PT_FreeText ******************************************************* -->
  <xsl:template match="gmd:PT_FreeText | PT_FreeText">
    <em>
      (eng)
      <xsl:value-of select="gmd:textGroup/gmd:LocalisedCharacterString | textGroup/LocalisedCharacterString"/>
    </em>
  </xsl:template>
  <!-- *********************  Template CI_Date ******************************************************* -->
  <xsl:template match="gmd:CI_Date | CI_Date">
    <span class="textoElemento">
      <xsl:value-of select="gmd:date/gco:Date | date/Date"/>, <xsl:value-of select="gmd:dateType/gmd:CI_DateTypeCode | dateType/CI_DateTypeCode"/>
      <xsl:if test="position()!=last()">;</xsl:if>
    </span>
  </xsl:template>
  <!-- *********************  Template CI_ResponsibleParty ******************************************************* -->
  <xsl:template match="gmd:CI_ResponsibleParty | CI_ResponsibleParty">
    <div class="caixa">
      <div class="tituloCaixa">
        <span class="entidade">
          Contacto (<xsl:value-of select="gmd:role/gmd:CI_RoleCode | role/CI_RoleCode"/>)
        </span>
      </div>
      <div class="caixaElemento">
        <span class="textoElemento">
          <xsl:value-of select="gmd:individualName/gco:CharacterString | individualName/CharacterString"/>
          <xsl:if test="string(gmd:organisationName/gco:CharacterString)">, </xsl:if>
          <xsl:value-of select="gmd:organisationName/gco:CharacterString | organisationName/CharacterString"/>
        </span>
      </div>
      <div class="caixaElemento">
        <span class="textoElemento">
          <xsl:apply-templates select="gmd:contactInfo/gmd:CI_Contact/gmd:phone | contactInfo/CI_Contact/phone"/>
        </span>
      </div>
      <div class="caixaElemento">
        <span class="textoElemento">
          <xsl:apply-templates select="gmd:contactInfo/gmd:CI_Contact/gmd:address | contactInfo/CI_Contact/address"/>
        </span>
      </div>
      <xsl:if test="string(gmd:contactInfo/gmd:CI_Contact/gmd:address/gmd:CI_Address/gmd:electronicMailAddress/gco:CharacterString)">
        <div class="caixaElemento">
          <a class="textoElemento">
            <xsl:attribute name="href">
              mailto:<xsl:value-of select="gmd:contactInfo/gmd:CI_Contact/gmd:address/gmd:CI_Address/gmd:electronicMailAddress/gco:CharacterString | contactInfo/CI_Contact/address/CI_Address/electronicMailAddress/CharacterString"/>
            </xsl:attribute>
            <xsl:value-of select="gmd:contactInfo/gmd:CI_Contact/gmd:address/gmd:CI_Address/gmd:electronicMailAddress/gco:CharacterString | contactInfo/CI_Contact/address/CI_Address/electronicMailAddress/CharacterString"/>
          </a>
        </div>
      </xsl:if>
    </div>
  </xsl:template>
  <!-- *********************  Template CI_Telephone ******************************************************* -->
  <xsl:template match="gmd:CI_Telephone | CI_Telephone">
    Telefone: <xsl:value-of select="gmd:voice/gco:CharacterString | voice/CharacterString"/> , Fax: <xsl:value-of select="gmd:facsimile/gco:CharacterString | facsimile/CharacterString"/>
  </xsl:template>
  <!-- *********************  Template CI_Address ******************************************************* -->
  <xsl:template match="gmd:CI_Address | CI_Address">
    Endereço: <xsl:value-of select="gmd:deliveryPoint/gco:CharacterString | deliveryPoint/CharacterString"/>
    <xsl:if test="string(gmd:city/gco:CharacterString)">, </xsl:if>
    <xsl:value-of select="gmd:city/gco:CharacterString | city/CharacterString"/>
    <xsl:if test="string(gmd:postalCode/gco:CharacterString)">, </xsl:if>
    <xsl:value-of select="gmd:postalCode/gco:CharacterString | postalCode/CharacterString"/>
    <xsl:if test="string(gmd:country/gco:CharacterString)">, </xsl:if>
    <xsl:value-of select="gmd:country/gco:CharacterString | country/CharacterString"/>
  </xsl:template>
  <!-- *********************  Template MD_Keywords ******************************************************* -->
  <xsl:template match="gmd:MD_Keywords | MD_Keywords">
    <div class="caixa">
      <div class="tituloCaixa">
        Palavras-chave Descritivas (<xsl:value-of select="gmd:type | type"/>)
      </div>
      <div class="caixaElemento">
        <span class="elemento">Palavras-chave: </span>
        <xsl:for-each select="gmd:keyword | keyword">
          <span class="textoElemento">
            <xsl:value-of select="."/>
            <xsl:if test="position()!=last()">;</xsl:if>
          </span>
        </xsl:for-each>
      </div>
      <!--
		 <div class="caixaElemento">
		<span class="elemento">Tipo de Palavra-chave: </span>
		<span class="textoElemento">
			<xsl:value-of select="gmd:type | type"/>
		</span>
		</div>
-->
      <xsl:if test="gmd:thesaurusName | thesaurusName">
        <!-- Léxico -->
        <div class="caixa">
          <div class="tituloCaixa">Thesaurus</div>
          <xsl:apply-templates select="gmd:thesaurusName | thesaurusName"/>
        </div>
      </xsl:if>
    </div>
  </xsl:template>
  <!-- *********************  Template MD_LegalConstraints ******************************************************* -->
  <xsl:template match="gmd:MD_LegalConstraints | MD_LegalConstraints">
    <div class="caixa">
      <div class="tituloCaixa">Restrições</div>
      <div class="caixaElemento">
        <span class="elemento">Limitação Ao Uso: </span>
        <span class="textoElemento">
          <xsl:value-of select="gmd:useLimitation | useLimitation"/>
        </span>
      </div>
      <div class="caixaElemento">
        <span class="elemento">Restrições de Acesso: </span>
        <xsl:for-each select="gmd:accessConstraints | accessConstraints">
          <span class="textoElemento">
            <xsl:value-of select="."/>
            <xsl:if test="position()!=last()">;</xsl:if>
          </span>
        </xsl:for-each>
      </div>
      <div class="caixaElemento">
        <span class="elemento">Restrições ao Uso: </span>
        <xsl:for-each select="gmd:useConstraints | useConstraints">
          <span class="textoElemento">
            <xsl:value-of select="."/>
            <xsl:if test="position()!=last()">;</xsl:if>
          </span>
        </xsl:for-each>
      </div>
      <div class="caixaElemento">
        <span class="elemento">Outras Restrições: </span>
        <xsl:for-each select="gmd:otherConstraints | otherConstraints">
          <span class="textoElemento">
            <xsl:value-of select="."/>
            <xsl:if test="position()!=last()">;</xsl:if>
          </span>
        </xsl:for-each>
      </div>
    </div>
  </xsl:template>
  <!-- *********************  Template MD_Resolution ******************************************************* -->
  <xsl:template match="gmd:MD_Resolution | MD_Resolution">
    <div class="caixa">
      <div class="tituloCaixa">Resolução Espacial</div>
      <div class="caixaElemento">
        <span class="elemento">Escala Equivalente (denominador): </span>
        <span class="textoElemento">
          <xsl:value-of select="gmd:equivalentScale/gmd:MD_RepresentativeFraction/gmd:denominator | equivalentScale/MD_RepresentativeFraction/denominator"/>
        </span>
      </div>
      <div class="caixaElemento">
        <span class="elemento">Distância no Terreno (metros): </span>
        <span class="textoElemento">
          <xsl:value-of select="gmd:distance | distance"/>
        </span>
      </div>
    </div>
  </xsl:template>
  <!-- *********************  Template EX_Extent ******************************************************* -->
  <xsl:template match="gmd:EX_Extent | EX_Extent">
    <div class="caixa">
      <div class="tituloCaixa">Extensão</div>
      <span class="elemento">Descrição da Extensão: </span>
      <span class="textoElemento">
        <xsl:value-of select="gmd:description | description"/>
      </span>
      <xsl:apply-templates select="gmd:geographicElement | geographicElement"/>
      <xsl:apply-templates select="gmd:temporalElement | temporalElement"/>
      <xsl:apply-templates select="gmd:verticalElement | verticalElement"/>
    </div>
  </xsl:template>
  <!-- *********************  Template EX_GeographicBoundingBox ******************************************************* -->
  <xsl:template match="gmd:EX_GeographicBoundingBox | EX_GeographicBoundingBox">
    <div class="caixa">
      <div class="tituloCaixa">Extensão Geográfica</div>
      <div class="caixaElemento">
        <span class="textoElemento">
          W: <xsl:value-of select="gmd:westBoundLongitude/gco:Decimal | westBoundLongitude/Decimal"/>, E: <xsl:value-of select="gmd:eastBoundLongitude/gco:Decimal | eastBoundLongitude/Decimal"/>, S: <xsl:value-of select="gmd:southBoundLatitude/gco:Decimal | southBoundLatitude/Decimal"/>, N: <xsl:value-of select="gmd:northBoundLatitude/gco:Decimal | northBoundLatitude/Decimal"/>
        </span>
      </div>
    </div>
  </xsl:template>
  <!-- *********************  Template EX_GeographicDescription ******************************************************* -->
  <xsl:template match="gmd:EX_GeographicDescription | EX_GeographicDescription">
    <div class="caixaElemento">
      <!--<span class="elemento">Código de Tipo de Área Geográfica: </span><span class="textoElemento"><xsl:value-of select="gmd:extentTypeCode"/></span><br/>-->
      <span class="elemento">Identificador Geográfico: </span>
      <span class="textoElemento">
        <xsl:value-of select="gmd:geographicIdentifier | geographicIdentifier"/>
      </span>
    </div>
  </xsl:template>
  <!-- *********************  Template EX_VerticalExtent ******************************************************* -->
  <xsl:template match="gmd:EX_VerticalExtent | EX_VerticalExtent">
    <div class="caixa">
      <div class="tituloCaixa">Extensão Vertical (metros)</div>
      <div class="caixaElemento">
        <span class="elemento">Valor Mínimo: </span>
        <span class="textoElemento">
          <xsl:value-of select="gmd:minimumValue | minimumValue"/>
        </span>
      </div>
      <div class="caixaElemento">
        <span class="elemento">Valor Máximo: </span>
        <span class="textoElemento">
          <xsl:value-of select="gmd:maximumValue | maximumValue"/>
        </span>
      </div>
    </div>
  </xsl:template>
  <!-- *********************  Template EX_TemporalExtent ******************************************************* -->
  <xsl:template match="gmd:EX_TemporalExtent | EX_TemporalExtent">
    <div class="caixa">
      <div class="tituloCaixa">Extensão Temporal</div>
      <div class="caixaElemento">
        <span class="elemento">Desde: </span>
        <span class="textoElemento">
          <xsl:value-of select="gmd:extent/gml:TimePeriod/gml:beginPosition | extent/TimePeriod/beginPosition"/>
        </span>
      </div>
      <div class="caixaElemento">
        <span class="elemento">Até: </span>
        <span class="textoElemento">
          <xsl:value-of select="gmd:extent/gml:TimePeriod/gml:endPosition | extent/TimePeriod/endPosition"/>
        </span>
      </div>
    </div>
  </xsl:template>
  <!-- *********************  Template MD_ReferenceSystem ******************************************************* -->
  <xsl:template match="gmd:MD_ReferenceSystem | MD_ReferenceSystem">
    <xsl:variable name="codigo">
      <xsl:value-of select="gmd:referenceSystemIdentifier/gmd:RS_Identifier/gmd:codeSpace/gco:CharacterString | referenceSystemIdentifier/RS_Identifier/codeSpace/CharacterString"/>:<xsl:value-of select="gmd:referenceSystemIdentifier/gmd:RS_Identifier/gmd:code/gco:CharacterString | referenceSystemIdentifier/RS_Identifier/code/CharacterString"/>
    </xsl:variable>
    <xsl:variable name="nome">
      <xsl:choose>
        <xsl:when test="$codigo = 'EPSG:25829'">ETRS89 / UTM zone 29N</xsl:when>
        <xsl:when test="$codigo= 'EPSG:4528'">ETRS89 Coordenadas Geográficas</xsl:when>
        <xsl:when test="$codigo= 'EPSG:20790'">Coordenadas Militares (Datum Lx)</xsl:when>
        <xsl:when test="$codigo = 'EPSG:27492'">Datum 73 Hayford-Gauss</xsl:when>
        <xsl:when test="$codigo = 'EPSG:4326'">Coordenadas Geográficas WGS84</xsl:when>
        <xsl:when test="$codigo = 'EPSG:2189'">Açores Ilhas Centrais UTM</xsl:when>
        <xsl:when test="$codigo= 'EPSG:2188'">Açores Ilhas Ocidentais UTM</xsl:when>
        <xsl:when test="$codigo= 'EPSG:3062'">Açores Ilhas Orientais UTM</xsl:when>
        <xsl:when test="$codigo= 'EPSG:3061'">Madeira e Porto Santo UTM</xsl:when>
        <xsl:when test="$codigo = 'CRS-EU:ETRS89'">ETRS89 Coordenadas Geográficas</xsl:when>
        <xsl:when test="$codigo= 'CRS-EU:ETRS-TMzn'">ETRS89 Transversa de Mercator</xsl:when>
        <xsl:when test="$codigo= 'CRS-EU:20790'">Coordenadas Militares (Datum Lx)</xsl:when>
        <xsl:when test="$codigo = 'CRS-EU:PT_D73 / TM_D73'">Datum 73 Hayford-Gauss</xsl:when>
        <xsl:when test="$codigo = 'CRS-EU:4326'">Coordenadas Geográficas WGS84</xsl:when>
        <xsl:when test="$codigo = 'CRS-EU:PT_AZO_CENT / UTM'">Açores Ilhas Centrais UTM</xsl:when>
        <xsl:when test="$codigo= 'CRS-EU:PT_AZO_OCCI / UTM'">Açores Ilhas Ocidentais UTM</xsl:when>
        <xsl:when test="$codigo= 'CRS-EU:PT_AZO_ORIE / UTM'">Açores Ilhas Orientais UTM</xsl:when>
        <xsl:when test="$codigo= 'CRS-EU:PT_MAD / UTM'">Madeira e Porto Santo UTM</xsl:when>
        <xsl:when test="$codigo = 'EPSG:32629'">WGS84 UTM 29N</xsl:when>
        <xsl:when test="$codigo = 'EPSG:32625'">WGS84 UTM 25N</xsl:when>
        <xsl:when test="$codigo = 'EPSG:32626'">WGS84 UTM 26N</xsl:when>
        <xsl:when test="$codigo = 'EPSG:32628'">WGS84 UTM 28N</xsl:when>
        <xsl:when test="$codigo = 'EPSG:3763'">ETRS89 / Portugal TM06</xsl:when>
        <xsl:when test="$codigo = 'CRS-EU:PT_DLX(HAY) / TM_DLX'">Datum Lisboa Hayford-Gauss</xsl:when>
      </xsl:choose>
    </xsl:variable>
    <div class="caixaElemento">
      <span class="elemento">Nome do Sistema de Referência: </span>
      <span class="textoElemento">
        <xsl:value-of select="$nome"/>
      </span>
    </div>
    <div class="caixaElemento">
      <span class="elemento">Código do Sistema de Referência: </span>
      <span class="textoElemento">
        <xsl:value-of select="$codigo"/>
      </span>
    </div>
  </xsl:template>
  <!-- *********************  Template MD_Distribution ******************************************************* -->
  <xsl:template match="gmd:MD_Distribution | MD_Distribution">
    <div class="caixa">
      <div class="tituloCaixaSeccao">Distribuição</div>
      <xsl:apply-templates select="gmd:distributionFormat | distributionFormat"/>
      <xsl:apply-templates select="gmd:distributor | distributor"/>
      <xsl:apply-templates select="gmd:transferOptions | transferOptions"/>
    </div>
  </xsl:template>
  <!-- *********************  Template MD_DigitalTransferOptions ******************************************************* -->
  <xsl:template match="gmd:MD_DigitalTransferOptions | MD_DigitalTransferOptions">
    <div class="caixa">
      <div class="tituloCaixa">Opções de Distribuição</div>
      <div class="caixaElemento">
        <span class="elemento">Unidades de Distribuição: </span>
        <span class="textoElemento">
          <xsl:value-of select="gmd:unitsOfDistribution/gco:CharacterString | unitsOfDistribution/CharacterString"/>
        </span>
      </div>
      <div class="caixaElemento">
        <span class="elemento">Tamanho de Transferência (Mb): </span>
        <span class="textoElemento">
          <xsl:value-of select="gmd:transferSize | transferSize"/>
        </span>
      </div>
      <div class="caixa">
        <div class="tituloCaixa">Acesso Online</div>
        <xsl:apply-templates select="gmd:onLine | onLine"/>
      </div>
    </div>
  </xsl:template>
  <!-- *********************  Template MD_Format ******************************************************* -->
  <xsl:template match="gmd:MD_Format | MD_Format">
    <div class="caixa">
      <div class="tituloCaixa">Formato</div>
      <div class="caixaElemento">
        <span class="elemento">Nome do Formato: </span>
        <span class="textoElemento">
          <xsl:value-of select="gmd:name/gco:CharacterString | name/CharacterString"/>
        </span>
      </div>
      <div class="caixaElemento">
        <span class="elemento"> Versão: </span>
        <span class="textoElemento">
          <xsl:value-of select="gmd:version/gco:CharacterString | version/CharacterString"/>
        </span>
      </div>
    </div>
  </xsl:template>
  <!-- *********************  Template CI_OnLineResource ******************************************************* -->
  <xsl:template match="gmd:CI_OnlineResource | CI_OnlineResource">
    <xsl:if test="string(gmd:linkage/gmd:URL)">
      <div class="caixaElemento">
        <span class="elemento">Endereço URL: </span>
        <a class="textoElemento">
          <xsl:attribute name="href">
            <xsl:value-of select="gmd:linkage/gmd:URL | linkage/URL"/>
          </xsl:attribute>
          <xsl:value-of select="gmd:linkage/gmd:URL | linkage/URL"/>
        </a>
      </div>
      <div class="caixaElemento">
        <span class="elemento">Função do Recurso Online: </span>
        <span class="textoElemento">
          <xsl:value-of select="gmd:function/gmd:CI_OnLineFunctionCode | function/CI_OnLineFunctionCode"/>
        </span>
      </div>
    </xsl:if>
  </xsl:template>
  <!-- *********************  Template DQ_DataQuality ******************************************************* -->
  <xsl:template match="gmd:DQ_DataQuality | DQ_DataQuality">
    <div class="caixa">
      <xsl:variable name="c" select="count(gmd:scope//gmd:levelDescription | scope//levelDescription)"/>
      <xsl:choose>
        <xsl:when test="$c =0">
          <div class="tituloCaixaSeccao">Qualidade</div>
        </xsl:when>
        <xsl:when test="$c =1">
          <div class="tituloCaixaSeccao">
            Qualidade  <xsl:value-of select="gmd:scope//gmd:levelDescription | scope//levelDescription"/>
          </div>
        </xsl:when>
        <xsl:otherwise>
          <div class="tituloCaixaSeccao">
            Qualidade - <xsl:for-each select="gmd:scope//gmd:levelDescription | scope//levelDescription">
              <xsl:value-of select="."/>
              <xsl:if test="position()!=last()">;</xsl:if>
            </xsl:for-each>
          </div>
        </xsl:otherwise>
      </xsl:choose>
      <div class="caixaElemento">
        <span class="elemento">Nível Hierárquico dos Dados: </span>
        <span class="textoElemento">
          <xsl:value-of select="gmd:scope/gmd:DQ_Scope/gmd:level/gmd:MD_ScopeCode | scope/DQ_Scope/level/MD_ScopeCode"/>
        </span>
      </div>
      <xsl:apply-templates select="gmd:scope/gmd:DQ_Scope/gmd:extent | scope/DQ_Scope/extent"/>
      <xsl:apply-templates select="gmd:lineage | lineage"/>
      <xsl:apply-templates select="gmd:report | report"/>
    </div>
  </xsl:template>
  <!-- *********************  Template LI_Lineage ******************************************************* -->
  <xsl:template match="gmd:LI_Lineage | LI_Lineage">
    <div class="caixa">
      <div class="tituloCaixa">Histórico</div>
      <div class="caixa">
        <div class="tituloCaixa">Declaração</div>
        <span class="caixaElemento">
          <span class="textoElemento">
            <xsl:value-of select="gmd:statement | statement"/>
          </span>
        </span>
        <xsl:apply-templates select="gmd:statement/gmd:PT_FreeText | statement/PT_FreeText"/>
      </div>
      <xsl:apply-templates select="gmd:processStep | processStep"/>
      <xsl:apply-templates select="gmd:source | source"/>
    </div>
  </xsl:template>
  <!-- *********************  Template LI_ProcessStep ******************************************************* -->
  <xsl:template match="gmd:LI_ProcessStep | LI_ProcessStep">
    <div class="caixa">
      <div class="tituloCaixa">Etapa do Processo</div>
      <div class="caixa">
        <div class="tituloCaixa">Descrição da Etapa</div>
        <xsl:value-of select="gmd:description/gco:CharacterString | description/CharacterString"/>
      </div>
      <div class="caixaElemento">
        <span class="elemento">Justificação da Etapa: </span>
        <span class="textoElemento">
          <xsl:value-of select="gmd:rationale/gco:CharacterString | rationale/CharacterString"/>
        </span>
      </div>
      <div class="caixaElemento">
        <span class="elemento">Data e Hora da Execução da Etapa: </span>
        <span class="textoElemento">
          <xsl:value-of select="gmd:dateTime/gco:DateTime | dateTime/DateTime"/>
        </span>
      </div>
    </div>
  </xsl:template>
  <!-- *********************  Template LI_Source ******************************************************* -->
  <xsl:template match="gmd:LI_Source | LI_Source">
    <div class="caixa">
      <div class="tituloCaixa">Fonte dos Dados</div>
      <div class="caixaElemento">
        <span class="elemento">Descrição da Fonte: </span>
        <span class="textoElemento">
          <xsl:value-of select="gmd:description/gco:CharacterString | description/CharacterString"/>
        </span>
      </div>
      <div class="caixaElemento">
        <span class="elemento">Denominador da Escala da Fonte: </span>
        <span class="textoElemento">
          <xsl:value-of select="gmd:scaleDenominator/gmd:MD_RepresentativeFraction/gmd:denominator/gco:Integer | scaleDenominator/MD_RepresentativeFraction/denominator/Integer"/>
        </span>
      </div>
      <xsl:apply-templates select="gmd:sourceCitation | sourceCitation"/>
    </div>
  </xsl:template>
  <!-- *********************  Template DQ_AbsoluteExternalPositionalAccuracy ******************************************************* -->
  <xsl:template match="gmd:DQ_AbsoluteExternalPositionalAccuracy | gmd:DQ_CompletenessCommission | gmd:DQ_CompletenessOmission
	| gmd:DQ_ConceptualConsistency | gmd:DQ_TopologicalConsistency | gmd:DQ_RelativeInternalPositionalAccuracy
	| gmd:DQ_ConceptualConsistency | gmd:DQ_DomainConsistency | gmd:DQ_FormatConsistency
	| gmd:DQ_GriddedDataPositionalAccuracy | gmd:DQ_AccuracyOfATimeMeasurement
	| gmd:DQ_TemporalConsistency | gmd:DQ_TemporalValidity | gmd:DQ_ThematicClassificationCorrectness
	| gmd:DQ_NonQuantitativeAttributeAccuracy | gmd:DQ_QuantitativeAttributeAccuracy | DQ_AbsoluteExternalPositionalAccuracy | DQ_CompletenessCommission | DQ_CompletenessOmission
	| DQ_ConceptualConsistency | DQ_TopologicalConsistency | DQ_RelativeInternalPositionalAccuracy
	| DQ_ConceptualConsistency | DQ_DomainConsistency | DQ_FormatConsistency
	| DQ_GriddedDataPositionalAccuracy | DQ_AccuracyOfATimeMeasurement
	| DQ_TemporalConsistency | DQ_TemporalValidity | DQ_ThematicClassificationCorrectness
	| DQ_NonQuantitativeAttributeAccuracy | DQ_QuantitativeAttributeAccuracy">
    <xsl:variable name="relatorio">
      <xsl:value-of select="name()"/>
    </xsl:variable>
    <xsl:variable name="nome">
      <xsl:choose>
        <xsl:when test="$relatorio = 'gmd:DQ_AbsoluteExternalPositionalAccuracy'">Exactidão Posicional Absoluta Externa</xsl:when>
        <xsl:when test="$relatorio= 'gmd:DQ_CompletenessCommission'">Completamento por Excesso </xsl:when>
        <xsl:when test="$relatorio= 'gmd:DQ_CompletenessOmission'">Completamento por Omissão </xsl:when>
        <xsl:when test="$relatorio = 'gmd:DQ_ConceptualConsistency'">Consistência Lógica  </xsl:when>
        <xsl:when test="$relatorio = 'gmd:DQ_TopologicalConsistency'">Consistência Topológica </xsl:when>
        <xsl:when test="$relatorio = 'gmd:DQ_RelativeInternalPositionalAccuracy'">Exactidão Posicional Relativa Interna</xsl:when>
        <xsl:when test="$relatorio= 'gmd:DQ_ConceptualConsistency'">Consistência Conceptual</xsl:when>
        <xsl:when test="$relatorio= 'gmd:DQ_DomainConsistency'">Consistência de Domínio</xsl:when>
        <xsl:when test="$relatorio= 'gmd:DQ_FormatConsistency'">Consistência de Formato</xsl:when>
        <xsl:when test="$relatorio = 'gmd:DQ_GriddedDataPositionalAccuracy'">Exactidão Posicional de Dados Matriciais</xsl:when>
        <xsl:when test="$relatorio= 'gmd:DQ_AccuracyOfATimeMeasurement'">Exactidão da Medida Temporal</xsl:when>
        <xsl:when test="$relatorio= 'gmd:DQ_TemporalConsistency'">Consistência Temporal</xsl:when>
        <xsl:when test="$relatorio = 'gmd:DQ_TemporalValidity'">Validade Temporal</xsl:when>
        <xsl:when test="$relatorio = 'gmd:DQ_ThematicClassificationCorrectness'">Exactidão Temática </xsl:when>
        <xsl:when test="$relatorio = 'gmd:DQ_NonQuantitativeAttributeAccuracy'">Exactidão de Atributos Não Quantitativos</xsl:when>
        <xsl:when test="$relatorio= 'gmd:DQ_QuantitativeAttributeAccuracy'">Exactidão de Atributos Quantitativos</xsl:when>
        <xsl:when test="$relatorio = 'DQ_AbsoluteExternalPositionalAccuracy'">Exactidão Posicional Absoluta Externa</xsl:when>
        <xsl:when test="$relatorio= 'DQ_CompletenessCommission'">Completamento por Excesso </xsl:when>
        <xsl:when test="$relatorio= 'DQ_CompletenessOmission'">Completamento por Omissão </xsl:when>
        <xsl:when test="$relatorio = 'DQ_ConceptualConsistency'">Consistência Lógica  </xsl:when>
        <xsl:when test="$relatorio = 'DQ_TopologicalConsistency'">Consistência Topológica </xsl:when>
        <xsl:when test="$relatorio = 'DQ_RelativeInternalPositionalAccuracy'">Exactidão Posicional Relativa Interna</xsl:when>
        <xsl:when test="$relatorio= 'DQ_ConceptualConsistency'">Consistência Conceptual</xsl:when>
        <xsl:when test="$relatorio= 'DQ_DomainConsistency'">Consistência de Domínio</xsl:when>
        <xsl:when test="$relatorio= 'DQ_FormatConsistency'">Consistência de Formato</xsl:when>
        <xsl:when test="$relatorio = 'DQ_GriddedDataPositionalAccuracy'">Exactidão Posicional de Dados Matriciais</xsl:when>
        <xsl:when test="$relatorio= 'DQ_AccuracyOfATimeMeasurement'">Exactidão da Medida Temporal</xsl:when>
        <xsl:when test="$relatorio= 'DQ_TemporalConsistency'">Consistência Temporal</xsl:when>
        <xsl:when test="$relatorio = 'DQ_TemporalValidity'">Validade Temporal</xsl:when>
        <xsl:when test="$relatorio = 'DQ_ThematicClassificationCorrectness'">Exactidão Temática </xsl:when>
        <xsl:when test="$relatorio = 'DQ_NonQuantitativeAttributeAccuracy'">Exactidão de Atributos Não Quantitativos</xsl:when>
        <xsl:when test="$relatorio= 'DQ_QuantitativeAttributeAccuracy'">Exactidão de Atributos Quantitativos</xsl:when>
      </xsl:choose>
    </xsl:variable>
    <div class="caixa">
      <div class="tituloCaixa">
        Relatório - 	<xsl:value-of select="$nome"/>
      </div>
      <div class="caixaElemento">
        <span class="elemento">Designação da Medida: </span>
        <xsl:for-each select="gmd:nameOfMeasure | nameOfMeasure">
          <span class="textoElemento">
            <xsl:value-of select="."/>
            <xsl:if test="position()!=last()">;</xsl:if>
          </span>
        </xsl:for-each>
      </div>
      <div class="caixaElemento">
        <span class="elemento">Identificação da Medida: </span>
        <span class="textoElemento">
          <xsl:value-of select="gmd:measureIdentification | measureIdentification"/>
        </span>
      </div>
      <div class="caixaElemento">
        <span class="elemento">Descrição da Medida: </span>
        <span class="textoElemento">
          <xsl:value-of select="gmd:measureDescription | measureDescription"/>
        </span>
      </div>
      <div class="caixaElemento">
        <span class="elemento">Tipo de Método de Avaliação: </span>
        <span class="textoElemento">
          <xsl:value-of select="gmd:evaluationMethodType | evaluationMethodType"/>
        </span>
      </div>
      <div class="caixaElemento">
        <span class="elemento">Descrição do Método de Avaliação: </span>
        <span class="textoElemento">
          <xsl:value-of select="gmd:evaluationMethodDescription | evaluationMethodDescription"/>
        </span>
      </div>
      <xsl:apply-templates select="gmd:evaluationProcedure | evaluationProcedure"/>
      <div class="caixaElemento">
        <span class="elemento">Data e Hora da Medição: </span>
        <span class="textoElemento">
          <xsl:value-of select="gmd:dateTime/gco:DateTime | dateTime/DateTime"/>
        </span>
      </div>
      <xsl:apply-templates select="gmd:result | result"/>
    </div>
  </xsl:template>
  <!-- *********************  Template DQ_ConformanceResult ******************************************************* -->
  <xsl:template match="gmd:DQ_ConformanceResult | DQ_ConformanceResult">
    <div class="caixa">
      <div class="tituloCaixa">Resultado da Medição (Conformidade)</div>
      <div class="caixa">
        <div class="tituloCaixa">Elementos de Referência da Especificação de Conformidade</div>
        <xsl:apply-templates select="gmd:specification | specification"/>
      </div>
      <div class="caixaElemento">
        <span class="elemento">Explicação da Conformidade: </span>
        <span class="TextoElemento">
          <xsl:value-of select="gmd:explanation | explanation"/>
        </span>
      </div>
      <div class="caixaElemento">
        <span class="elemento">Decisão de Conformidade: </span>
        <span class="TextoElemento">
          <xsl:value-of select="gmd:pass | pass"/>
        </span>
      </div>
    </div>
  </xsl:template>
  <!-- *********************  Template DQ_QuantitativeResult ******************************************************* -->
  <xsl:template match="gmd:DQ_QuantitativeResult | DQ_QuantitativeResult">
    <div class="caixa">
      <div class="tituloCaixa">Resultado da Medição</div>
      <div class="caixaElemento">
        <span class="elemento">Tipo do Valor: </span>
        <span class="TextoElemento">
          <xsl:value-of select="gmd:valueType | valueType"/>
        </span>
      </div>
      <div class="caixaElemento">
        <span class="elemento">Unidade do Valor: </span>
        <span class="TextoElemento">
          <xsl:value-of select="gmd:valueUnit | valueUnit"/>
        </span>
      </div>
      <div class="caixaElemento">
        <span class="elemento">Estatística de Erro: </span>
        <span class="TextoElemento">
          <xsl:value-of select="gmd:errorStatistic | errorStatistic"/>
        </span>
      </div>
      <div class="caixaElemento">
        <span class="elemento">Valor: </span>
        <xsl:for-each select="gmd:value | value">
          <span class="textoElemento">
            <xsl:value-of select="."/>
            <xsl:if test="position()!=last()">;</xsl:if>
          </span>
        </xsl:for-each>
      </div>
    </div>
  </xsl:template>
</xsl:stylesheet>