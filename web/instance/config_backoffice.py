backoffice_cfg = {
  "version": "1.0",
  "config": {
    "menu" : [
        { "label": "Dashboard", "icon": "pi pi-fw pi-home", "to": "/", "roles": ["Admin", "Manager", "Authenticated"] },
        {
          "label": "Visualizadores", "icon": "pi pi-fw pi-sitemap",
          "items": [
            { "label": "Novo", "icon": "pi pi-fw pi-id-card", "to": "/viewers/create",
              "roles": ["Admin", "Manager", "Authenticated"] },
            { "label": "Lista", "icon":  "pi pi-fw pi-check-square", "to": "/viewers/list",
              "roles": ["Admin", "Manager", "Authenticated"] }
          ]
        },
        {
            "label": "Emissão de Plantas", "icon": "pi pi-fw pi-sitemap",
            "items": [
                {"label": "Elementos", "icon": "pi pi-fw pi-id-card", "to": "/prints/elements/list",
                 "roles": ["Admin", "Manager"]},
                {"label": "Grupos", "icon": "pi pi-fw pi-check-square", "to": "/prints/groups/list",
                 "roles": ["Admin", "Manager", "Authenticated"]},
                {"label": "Plantas", "icon": "pi pi-fw pi-check-square", "to": "/prints/list",
                 "roles": ["Admin", "Manager", "Authenticated"]}
            ]
        },
        {
            "label": "Módulos", "icon": "pi pi-fw pi-sitemap",
            "items": [
                { "label": "Cadastro", "icon": "pi pi-fw pi-id-card", "to": "/modules/cadastro",
                "roles": ["Admin", "DGT_Cadastro_admin"] }
            ]
        },
        {
            "label": "Segurança", "icon": "fas fa-users-cog", "roles": ["Admin"],
            "items": [
                { "label": "Utilizadores", "icon": "fas fa-user", "to": "/security/users/list" },
                {"label": "Grupos", "icon": "fas fa-users", "to": "/security/groups/list"},
                { "label": "Perfis", "icon": "fas fa-user-friends", "to": "/security/roles/list" }
            ]
        },
        {
            "label": "Definições", "icon": "fas fa-sliders-h", "roles": ["Admin"],
            "items": [
                { "label": "Parâmetros", "icon": "fas fa-cog", "to": "/settings/parameters/list" },
                { "label": "Sistemas de Coordenadas", "icon": "fas fa-globe", "to": "/settings/coordinate_systems/list" }
            ]
        },
        { "label": "Documentação", "icon": "pi pi-fw pi-question", "link": "https://snic.dgterritorio.gov.pt/snic_help/",
          "target": "_blank"}
    ],
    "components": [
        {
            "id": "cadastro",
            "type": "Cadastro",
            "title": "Gestão de Cadastro",
            "config_json": {
                "header": "Gestão de Cadastro"
            },
            "config_version": "1.0",
            "regions": [],
            "target": "managermenu",
            "children": []
        }
    ],
    "contacts": [
        {
            "name": "Ricardo Sena",
            "email": "ricardo.sena@wkt.pt"
        },
        {
            "name": "Frédéric Lehodey",
            "email": "fred@wkt.pt",
            "icon": "/assets/layout/images/avatar_3.png"
        }
    ],
    "stats": {
      "types": [
        {"label": "Visualização de mapas", "value": "VM"},
        {"label": "Emissão de plantas", "value": "EP"}
      ],
      "timeranges": [
          {"label": "Desde sempre", "value": "all"},
          {"label": "Últimos 7 dias", "value": "7"},
          {"label": "Últimos 30 dias", "value": "30"},
          {"label": "Últimos 100 dias", "value": "100"},
          {"label": "Último ano", "value": "365"}
      ],
      "selected_type": "VM",
      "selected_timerange": "30"
    }
  }
}

BACKOFFICE_CONFIG = backoffice_cfg