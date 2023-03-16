# Instalação

> git clone https://github.com/scalargis/scalargis-server.git

> cd scalargis-server


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

##### Windows
> (venv) pip install -r requirements-win.txt

##### Linux
> (venv) pip install -r requirements.txt

### Criar base de dados e instalar extensão Postgis  

Criar a base de dados através do pgAdim


### Inicializar a BD

##### Windows 
> (venv) set FLASK_APP=app.main  
> (venv) set APP_CONFIG_FILE=<config_file_name>    
> (venv) cd scalargis  
> (venv) flask init-db

##### Linux
> (venv) export FLASK_APP=app.main  
> (venv) export APP_CONFIG_FILE=<config_file_name>  
> (venv) cd scalargis  
> (venv) flask init-db  

### Executar app

##### Windows 
> (venv) set PYTHONPATH=\<path\>\scalargis-server\scalargis;\<path\>\scalargis-server\scalargis\app   
> (venv) cd web\app  
> (venv) python main.py

##### Linux
> (venv) export PYTHONPATH=/<path\>/scalargis-server/scalargis:/<path\>/scalargis-server/scalargis/app  
> (venv) cd web/app  
> (venv) python main.py

### Utilizar a aplicação
Abir no browser o url http://localhost:5000/mapa


## Instalação de componente cliente

Instalar o repositório da componente cliente ao lado da diretoria scalargis-server 

> git clone https://github.com/scalargis/scalargis-client.git

> cd scalargis_client

> yarn install

