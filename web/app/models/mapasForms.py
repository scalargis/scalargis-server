from flask_wtf import FlaskForm as Form
from wtforms import validators, StringField, IntegerField, FieldList, BooleanField, DateField
from wtforms.validators import DataRequired, optional
from wtforms.widgets import HiddenInput
from app.utils import constants


class ConfigMapaSearhForm(Form):
    id = StringField('Id')
    titulo = StringField('Título')
    mapa = StringField('Mapa')
    page = IntegerField('Página', widget=HiddenInput())
    orderField = StringField('Campo de Ordenação')
    sortOrder = StringField('Direcção da Ordenação')


class ConfigMapaForm(Form):
    titulo = StringField('Título', [DataRequired(message=constants.VALIDATOR_REQUIRED_FIELD)])
    descricao = StringField('Descrição')
    configuracao = StringField('Configuração', [DataRequired(message=constants.VALIDATOR_REQUIRED_FIELD)])


class MapaSearhForm(Form):
    id = StringField('Id')
    codigo = StringField('Código')
    titulo = StringField('Título')
    configuracao = StringField('Configuração')
    modulo = StringField('Módulo')
    role = StringField('Grupo')
    page = IntegerField('Página', widget=HiddenInput())
    orderField = StringField('Campo de Ordenação')
    sortOrder = StringField('Direcção da Ordenação')


class MapaModuloForm(Form):
    id = IntegerField('Id')
    titulo = StringField('Título')


class MapaForm(Form):
    codigo = StringField('Código', [DataRequired(message=constants.VALIDATOR_REQUIRED_FIELD)])
    titulo = StringField('Título', [DataRequired(message=constants.VALIDATOR_REQUIRED_FIELD)])
    descricao = StringField('Descrição')
    configuracao = IntegerField('Configuração', [DataRequired(message=constants.VALIDATOR_REQUIRED_FIELD)])
    configuracaoMapa = StringField('Configuração do Mapa')
    portal = BooleanField('Mapa do Portal')
    activo = BooleanField('Activo')
    showHelp = BooleanField('Ajuda')
    showCredits = BooleanField('Créditos')
    showContact = BooleanField('Contacto')
    helpHtml = StringField('Html da Ajuda')
    creditsHtml = StringField('Html dos Créditos')
    template = StringField('Template')
    headerHtml = StringField('Html do Header')
    showWidget = StringField('Widget activo')
    postScript = StringField('Post Script')
    ModulosList = FieldList(StringField('ModulosList'))
    # modulos = FieldList('Módulos', FormField(MapaModuloForm))
    PlantasList = FieldList(StringField('PlantasList'))
    TiposPlantasList = FieldList(StringField('TiposPlantasList'))
    CatalogosList = FieldList(StringField('CatalogosList'))
    RolesList = FieldList(StringField('RolesList'))
    WidgetsList = FieldList(StringField('WidgetsList'))
    sendEmailNotificationsAdmin = BooleanField('Enviar ao administrador notificações por email')
    emailNotificationsAdmin = StringField('Email de notificação')


class TemplatePlantaSearchForm(Form):
    page = IntegerField('Página', widget=HiddenInput())
    orderField = StringField('Campo de Ordenação')
    sortOrder = StringField('Direcção da Ordenação')


class TipoPlantaSearchForm(Form):
    id = StringField('Id')
    codigo = StringField('Código')
    titulo = StringField('Título')
    mapa = StringField('Mapa')
    planta = StringField('Planta')
    page = IntegerField('Página', widget=HiddenInput())
    orderField = StringField('Campo de Ordenação')
    sortOrder = StringField('Direcção da Ordenação')


class TipoPlantaForm(Form):
    codigo = StringField('Código', [DataRequired(message=constants.VALIDATOR_REQUIRED_FIELD)])
    titulo = StringField('Título', [DataRequired(message=constants.VALIDATOR_REQUIRED_FIELD)])
    descricao = StringField('Descrição')
    identificacaoRequerente = BooleanField('Obrigratória identificação')
    marcacaoLocal = BooleanField('Obrigatório marcar local')
    multiGeom = BooleanField('Múltiplas geometrias')
    autorEmissao = BooleanField('Mostrar utilizador que emitiu a planta')
    guiaPagamento = BooleanField('Preencher Guia de Pagamento')
    finalidadeEmissao = BooleanField('Preencher Finalidade da Emissão')
    activo = BooleanField('Activa')
    TiposPlantasList = FieldList(StringField('TiposPlantasList'))
    PlantasList = FieldList(StringField('PlantasList'))
    tolerancia = IntegerField('Tolerância', [optional()])
    showAll = BooleanField('Mostar filhos vazios')
    seleccaoPlantas = BooleanField('Permitir seleção de plantas')
    agruparPlantas = BooleanField('Agrupar plantas')


class PlantaSearhForm(Form):
    id = StringField('Id')
    codigo = StringField('Código')
    nome = StringField('Título')
    titulo = StringField('Título')
    escala = StringField('Escala')
    formato = StringField('Formato')
    orientacao = StringField('Orientação')
    mapa = StringField('Mapa')
    role = StringField('Role')
    page = IntegerField('Página', widget=HiddenInput())
    orderField = StringField('Campo de Ordenação')
    sortOrder = StringField('Direcção da Ordenação')


class SubPlantaSearhForm(Form):
    id = StringField('Id')
    codigo = StringField('Código')
    nome = StringField('Título')
    page = IntegerField('Página', widget=HiddenInput())
    orderField = StringField('Campo de Ordenação')
    sortOrder = StringField('Direcção da Ordenação')


class PlantaForm(Form):
    codigo = StringField('Código', [DataRequired(message=constants.VALIDATOR_REQUIRED_FIELD)])
    nome = StringField('Nome', [DataRequired(message=constants.VALIDATOR_REQUIRED_FIELD)])
    titulo = StringField('Título')
    descricao = StringField('Descrição')
    escala = IntegerField('Escala', [optional()])
    formato = StringField('Formato')
    orientacao = StringField('Orientação')
    template = StringField('Template')
    configuracao = StringField('Configuração')
    identificacao = BooleanField('Obrigratória identificação')
    marcacaoLocal = BooleanField('Obrigatório marcar local')
    desenharLocal = BooleanField('Desenhar Local')
    multiGeom = BooleanField('Múltiplas geometrias')
    emissaoLivre = BooleanField('Emissão Livre')
    tituloEmissao = BooleanField('Adicionar título')
    autorEmissao = BooleanField('Mostrar utilizador que emitiu a planta')
    guiaPagamento = BooleanField('Preencher Guia de Pagamento')
    finalidadeEmissao = BooleanField('Preencher Finalidade da Emissão')
    srid = IntegerField('Sistema de Coordenadas', [optional()])
    activo = BooleanField('Activa')
    RolesList = FieldList(StringField('RolesList'))


class PlantaLayoutForm(Form):
    planta_id = IntegerField('PlantaId', [DataRequired(message=constants.VALIDATOR_REQUIRED_FIELD)])
    formato = StringField('Formato', [DataRequired(message=constants.VALIDATOR_REQUIRED_FIELD)])
    orientacao = StringField('Orientação', [DataRequired(message=constants.VALIDATOR_REQUIRED_FIELD)])
    configuracao = StringField('Configuração', [DataRequired(message=constants.VALIDATOR_REQUIRED_FIELD)])


class SubPlantaForm(Form):
    codigo = StringField('Código', [DataRequired(message=constants.VALIDATOR_REQUIRED_FIELD)])
    nome = StringField('Nome', [DataRequired(message=constants.VALIDATOR_REQUIRED_FIELD)])
    configuracao = StringField('Configuração')


class CatalogoMetadadosSearchForm(Form):
    id = StringField('Id')
    codigo = StringField('Código')
    titulo = StringField('Título')
    mapa = StringField('Mapa')
    page = IntegerField('Página', widget=HiddenInput())
    orderField = StringField('Campo de Ordenação')
    sortOrder = StringField('Direcção da Ordenação')


class CatalogoMetadadosForm(Form):
    codigo = StringField('Código', [DataRequired(message=constants.VALIDATOR_REQUIRED_FIELD)])
    titulo = StringField('Titulo', [DataRequired(message=constants.VALIDATOR_REQUIRED_FIELD)])
    descricao = StringField('Descrição')
    url_base = StringField('Url Base')
    url_csw = StringField('Url CSW', [DataRequired(message=constants.VALIDATOR_REQUIRED_FIELD)])
    autenticacao = BooleanField('Autenticação')
    username = StringField('Username')
    password = StringField('Password')
    activo = BooleanField('Activo')
    tipo = StringField('Tipo')
    portal = BooleanField('Portal')
    xslt_results_file = StringField('Ficheiro de XSLT de resultados')
    xslt_results = StringField('XSLT de resultados')
    xslt_metadata_file = StringField('Ficheiro de XSLT de ficha')
    xslt_metadata = StringField('XSLT de ficha')
    MapasList = FieldList(StringField('MapasList'))


class SettingsSiteSearhForm(Form):
    id = StringField('Id')
    codigo = StringField('Código')
    nome = StringField('Nome')
    page = IntegerField('Página', widget=HiddenInput())
    orderField = StringField('Campo de Ordenação')
    sortOrder = StringField('Direcção da Ordenação')


class SettingsSiteForm(Form):
    code = StringField('Código', [DataRequired(message=constants.VALIDATOR_REQUIRED_FIELD)])
    name = StringField('Nome')
    notes = StringField('Descrição')
    setting_value = StringField('Valor do parâmetro', [DataRequired(message=constants.VALIDATOR_REQUIRED_FIELD)])


class AuditLogSearchForm(Form):
    id = StringField('Id')
    data_ref_inicio = DateField('Data Início', format='%d/%m/%Y', validators=(validators.Optional(),))
    data_ref_fim = DateField('Data Fim', format='%d/%m/%Y', validators=(validators.Optional(),))
    mapa = StringField('Mapa')
    operacao = StringField('Operação')
    page = IntegerField('Página', widget=HiddenInput())
    orderField = StringField('Campo de Ordenação')
    sortOrder = StringField('Direcção da Ordenação')


class ContactoMensagemForm(Form):
    name = StringField()
    email = StringField()
    message = StringField()


class ContactoMensagemSearchForm(Form):
    id = StringField('Id')
    data_inicio = DateField('Data Início', format='%d/%m/%Y', validators=(validators.Optional(),))
    data_fim = DateField('Data Fim', format='%d/%m/%Y', validators=(validators.Optional(),))
    mapa = StringField('Mapa')
    user = StringField('Utilizador')
    estado = StringField('Estado')
    page = IntegerField('Página', widget=HiddenInput())
    orderField = StringField('Campo de Ordenação')
    sortOrder = StringField('Direcção da Ordenação')
