# Instalação  

> git clone https://github.com/ricardogsena/scalargis-server.git
>
> cd scalargis-server
>
> git checkout develop

### Instalar a aplicação em virtualenv

##### Windows 
> x:\Python3x\python -m venv venv
>
> venv\scripts\activate
>
> (venv) python -m pip install --upgrade pip

##### Linux
> python3 -m venv venv
>
> source venv/bin/activate
>
> (venv) pip install --upgrade pip

### Instalar dependências de pyhton

> (venv) pip install -r requirements.txt

### Criar base de dados e instalar extensão Postgis  

Criar a base de dados através do pgAdim e instalar nela a extensão Postgis  

`create extension postgis`

### Inicializar a BD

##### Windows 
> (venv) set FLASK_APP=app.main
>
> (venv) set PYTHONPATH=&#92;<em>path</em>\scalargis-server\web
>
> (venv) cd web
>
> (venv) flask init-db

##### Linux
> (venv) export FLASK_APP=app.main
>
> (venv) export PYTHONPATH=/<em>path</em>/scalargis-server/web
>
> (venv) cd web
>
> (venv) flask init-db    

### Instalar dependências
> npm install
>
> bower install

### Bundle javascript files
> node_modules\.bin\gulp build

### Executar app

##### Windows 
> (venv) set PYTHONPATH=&#92;<em>path</em>\scalargis-server\web;&#92;<em>path</em>\scalargis-server\web\app
>
> (venv) cd web\app
>
> (venv) python main.py

##### Linux
> (venv) export PYTHONPATH=/<em>path</em>/scalargis-server/web:/<em>path</em>/scalargis-server/web/app
> 
> (venv) cd web/app
> 
> (venv) python main.py

## Integrar projecto de aplicação cliente (Frontend)

Instalar repositório de aplicação cliente fora do projecto principal  

> git clone https://github.com/ricardogsena/scalargis-client.git
>
> cd scalargis-client
>
> yarn

##### Adicionar projecto(s) de plugin(s) (opcional)
> cd frontend/src/components
> 
> git submodule add -f -b master https://github.com/ricardogsena/scalargis-client-plugin-toc.git TOC  

##### Editar configurações utilizadas no build (opcional)
Editar ficheiro package.json e definir:  
`"homepage": "static/frontend"`

Copiar o ficheiro .env.example para .env e alterar os valores das seguintes variáveis:  
`REACT_APP_BASE_URL="/static/frontend/"`    
`REACT_APP_CONFIG_URL="/static/frontend/config.example.json"`
`REACT_APP_MAP_PROXY="/map/proxy?url="`

##### Executar o build
> npm run build

### Criar symlink para directoria build do projecto cliente no projecto principal

##### Windows
> mklink /D &#92;<em>path</em>\scalargis-server\web\app\static\frontend &#92;<em>path</em>\scalargis-client\frontend\build

#### Linux
> ln -s /<em>path</em>/scalargis-client/frontend/build /<em>path</em>/scalargis-server/static/frontend
