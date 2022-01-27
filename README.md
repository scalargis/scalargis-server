# Instalação  

> git clone https://github.com/ricardogsena/scalargis-server.git

> cd scalargis-server

> git checkout develop

### Instalar a aplicação em virtualenv

##### Windows 
> x:\Python3x\python -m venv venv  
> venv\scripts\activate  
> (venv) python -m pip install --upgrade pip

##### Linux
> python3 -m venv venv  
> source venv/bin/activate  
> (venv) pip install --upgrade pip

### Instalar dependências de pyhton

> (venv) pip install -r requirements.txt

### Criar base de dados e instalar extensão Postgis  

Criar a base de dados através do pgAdim e instalar nela a extensão Postgis  

`create extension postgis`

### Inicializar a BD

##### Windows 
> (venv) set FLASK_APP=app.main  
> (venv) set PYTHONPATH=\<path>\scalargis-server\web  
> (venv) cd web  
> (venv) flask init-db

##### Linux
> (venv) export FLASK_APP=app.main  
> (venv) export PYTHONPATH=/<path>/webig_app/web  
> (venv) cd web  
> (venv) flask init-db  

### Instalar dependências
> npm install
> bower install
> node_modules\.bin\gulp build

### Bundle javascript files
> yarn webpack --mode production

### Executar app

##### Windows 
> (venv) set PYTHONPATH=\<path\>\websig_app\web;\<path\>\websig_app\web\app   
> (venv) cd web\app  
> (venv) python main.py

##### Linux
> (venv) export PYTHONPATH=\<path\>/webig_app/web:\<path\>/webig_app/web/app  
> (venv) cd web/app  
> (venv) python main.py

## Integrar projecto de aplicação cliente (Frontend)

Instalar repositório de aplicação cliente fora do projecto principal  

> git clone https://gitlab.wkt.pt/DGT/websig_client.git

> cd websig_client

> npm install

##### Adicionar projecto(s) de plugin(s) (opcional)
> cd src/plugins  
> git submodule add -f -b master https://gitlab.wkt.pt/DGT/websig_client_plugin_toc.git TOC  

##### Editar configurações utilizadas no build (opcional)
Editar ficheiro package.json e definir:  
`"homepage": "static/client"`

Copiar o ficheiro .env.example para .env e alterar os valores das seguintes variáveis:  
`REACT_APP_BASE_URL="/static/client/"`    
`REACT_APP_CONFIG_URL="/static/client/config.example.json"`
`REACT_APP_MAP_PROXY="/map/proxy?url="`

##### Executar o build
> npm run build

### Criar symlink para directoria build do projecto cliente no projecto principal

##### Windows
> mklink /D \<path\>\websig_app\web\app\static\client \<path\>\websig_client\build

#### Linux
> ln -s \<path\>/websig_client/build \<path\>/websig_app/static/client
