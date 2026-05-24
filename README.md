# ScalarGIS Server

Backend for the ScalarGIS platform. Built with Python/Flask, SQLAlchemy, PostGIS, and served by Waitress in production.

## Two-Repo Setup

ScalarGIS is split into two repositories that work together:

| Repo | Role | README |
| --- | --- | --- |
| **scalargis-server** (this repo) | Python backend -- API, database, serves production builds | You are here |
| **scalargis-client** | React frontend -- viewer and backoffice apps | [scalargis-client README](../scalargis-client/README.md) |

**Setup order:** Install and run the server first (this README), then set up the client (see the client README). The frontend dev server proxies all API calls to this backend, so it must be running.

## Prerequisites

| Requirement | Version | Notes |
| --- | --- | --- |
| **Python** | 3.12 | 3.9 - 3.12 supported; 3.12 recommended |
| **PostgreSQL** | 12+ | With the **PostGIS** extension installed |
| **Git** | any recent | |

### Installing Python

Download Python 3.12 from [python.org](https://www.python.org/downloads/). During installation, check **"Add Python to PATH"**.

Verify:

```powershell
python --version   # Should show Python 3.12.x
```

### Installing PostgreSQL + PostGIS

1. Download PostgreSQL from [postgresql.org](https://www.postgresql.org/downloads/windows/) or use the [EDB installer](https://www.enterprisedb.com/downloads/postgres-postgresql-downloads).
2. During installation (or after, via Stack Builder), install the **PostGIS** bundle.
3. Note your PostgreSQL **username**, **password**, **port** (default: 5432), and **host** (default: localhost).

## Setup

### 1. Clone the repository

```powershell
git clone https://github.com/scalargis/scalargis-server.git
cd scalargis-server
```

### 2. Create a Python virtual environment

```powershell
python -m venv venv
```

### 3. Activate the virtual environment

```powershell
venv\Scripts\activate
```

You should see `(venv)` at the start of your prompt. All following commands assume the venv is active.

### 4. Install Python dependencies

```powershell
pip install --upgrade pip
pip install -r requirements-win.txt
```

> **Note:** The `requirements-win.txt` file includes pre-built Windows wheels for GDAL and Fiona. On Linux, use `requirements.txt` instead.

### 5. Create the database

Using **pgAdmin** or **psql**, create a new PostgreSQL database and enable PostGIS:

```sql
CREATE DATABASE scalargis;
\c scalargis
CREATE EXTENSION postgis;
```

### 6. Create a local config file

Create the file `scalargis/instance/development_local.py` with your database connection:

```python
SQLALCHEMY_DATABASE_URI = "postgresql+psycopg2://<user>:<password>@<host>:<port>/<db_name>"
```

Replace the placeholders with your PostgreSQL credentials. Example:

```python
SQLALCHEMY_DATABASE_URI = "postgresql+psycopg2://postgres:postgres@localhost:5432/scalargis"
```

This file overrides the defaults in `scalargis/instance/default.py`. It is not committed to Git.

### 7. Set the config environment variable

```powershell
$env:APP_CONFIG_FILE = "development_local.py"
```

### 8. Run the server

```powershell
cd scalargis
python server.py
```

On first run, the database schema is automatically created (tables, default data, etc.).

The server starts on **http://localhost:5000** with Waitress (6 threads by default).

### Verify it works

| URL | Description |
| --- | --- |
| http://localhost:5000/mapa/demo | Demo map viewer |
| http://localhost:5000/backoffice | Admin backoffice (credentials: `admin` / `admin`) |

## Configuration Reference

The config file (`development_local.py`) supports these commonly used settings:

```python
# Enable debug mode (auto-reload, detailed errors)
DEBUG = True

# Database connection
SQLALCHEMY_DATABASE_URI = "postgresql+psycopg2://postgres:postgres@localhost:5432/scalargis"

# Additional database connections (for extensions that use their own DB)
SQLALCHEMY_BINDS = {
    "demo": "sqlite:///path/to/demo.db",
}

# Default locale
SCALARGIS_DEFAULT_LOCALE = 'pt'

# Plugins to load (built-in server plugins)
SCALARGIS_PLUGINS = ['proxy', 'geonames', 'spatial_toolbox']

# Extensions to load (see "Extensions" section below)
SCALARGIS_EXTENSIONS = []

# CORS origins allowed by the proxy plugin
SCALARGIS_PROXY_CORS = ['http://localhost:3000', 'http://localhost:4200']
```

See `scalargis/instance/default.py` for the full list of defaults.

### Using a project-specific config

You can create multiple config files for different projects (e.g., `development_local_mapaspt.py`, `development_local_snic3.py`) and switch between them:

```powershell
$env:APP_CONFIG_FILE = "development_local_mapaspt.py"
cd scalargis
python server.py
```

## Extensions (Backend)

Extensions add project-specific backend functionality (API endpoints, database models, etc.). They live in `scalargis/app/extensions/` and are loaded at startup based on the `SCALARGIS_EXTENSIONS` config.

### Installing extensions

Clone each extension repository into the extensions directory:

```powershell
cd scalargis/app/extensions

# Example: install authama, keycloaksso, and mapaspt extensions
git clone <authama-repo-url> authama
git clone <keycloaksso-repo-url> keycloaksso
git clone <mapaspt-repo-url> mapaspt
```

> Extension repositories are hosted on GitLab. Contact the project maintainers for access.

### Activating extensions

Add the extension folder names to `SCALARGIS_EXTENSIONS` in your `development_local.py`:

```python
SCALARGIS_EXTENSIONS = ['authama', 'keycloaksso', 'mapaspt']
```

Restart the server after changing extensions.

> **Note:** Extension folder names are the directory names inside `app/extensions/` and are case-sensitive.

### Extension structure

Each extension provides a `__init__.py` that creates a Flask Blueprint and exposes it as `module_api` (for REST API routes) and/or `module` (for template routes). Extensions may also have their own configuration keys (e.g., `KEYCLOAK_*`, `INTELIGT_*`) documented in their respective README or ARCHITECTURE files.

## Server Environment Variables

| Variable | Default | Description |
| --- | --- | --- |
| `APP_CONFIG_FILE` | (none) | Config filename inside `scalargis/instance/` |
| `PORT` | `5000` | HTTP listen port |
| `THREADS` | `6` | Waitress worker threads |
| `CHANNEL_TIMEOUT` | `120` | Waitress channel timeout (seconds) |
| `CONNECTION_LIMIT` | `100` | Max concurrent connections |
| `URL_PREFIX` | `""` | URL prefix (for reverse proxy deployments) |
| `URL_SCHEME` | `http` | URL scheme (`http` or `https`) |
| `TRUSTED_PROXY` | (none) | Trusted proxy IP for X-Forwarded-For |

## Deploying Frontend to Server

After building the frontend client, the compiled files are placed directly into the server's static folders. See the [scalargis-client README](../scalargis-client/README.md) for build commands. The output lands at:

- `scalargis/app/static/viewer/`
- `scalargis/app/static/backoffice/`

Once deployed, the server serves the frontend at the same URLs (no separate frontend server needed in production).

## PyCharm Setup

If you prefer using PyCharm instead of the command line, follow these steps.

### 1. Open the project

**File > Open** and select the `scalargis-server` folder.

### 2. Create a Python 3.12 virtual environment

1. Go to **File > Settings > Project: scalargis-server > Python Interpreter**.
2. Click the gear icon (or **Add Interpreter**) > **Add Local Interpreter**.
3. Choose **Virtualenv Environment > New**.
4. Set **Base interpreter** to your Python 3.12 installation (e.g. `C:\Users\<you>\AppData\Local\Programs\Python\Python312\python.exe`).
5. Leave the **Location** as the default (`venv` inside the project).
6. Click **OK**.

### 3. Install dependencies

Open PyCharm's **Terminal** tab (bottom panel) — it auto-activates the venv. Run:

```powershell
pip install --upgrade pip
pip install -r requirements-win.txt
```

> **Tip:** If pip fails on GDAL or Fiona, make sure you're using `requirements-win.txt` (not `requirements.txt`) — it includes pre-built Windows wheels.

### 4. Create a Run Configuration

1. Go to **Run > Edit Configurations > + > Python**.
2. Set these fields:

| Field | Value |
| --- | --- |
| **Name** | `ScalarGIS Server` |
| **Script path** | `scalargis\server.py` |
| **Working directory** | `<project-root>\scalargis` |
| **Environment variables** | `APP_CONFIG_FILE=development_local.py` |

3. Click **OK**.

### 5. Database and config file

Follow [Step 5 (Create the database)](#5-create-the-database) and [Step 6 (Create a local config file)](#6-create-a-local-config-file) from the CLI setup above — these are the same regardless of IDE.

### 6. Run

Click the green **Run** button (or press **Shift+F10**). The server starts on **http://localhost:5000**.

### PyCharm tips

- **Database tool:** You can connect PyCharm to your PostgreSQL database via **View > Tool Windows > Database** for browsing tables and running queries.
- **Flask debug mode:** To use Flask's auto-reloader instead of Waitress, change the Run Configuration script to `flask` with parameters `run`, and add `FLASK_APP=app` to the environment variables.
- **Mark sources root:** If PyCharm shows import errors for `app.*` or `instance.*`, right-click the `scalargis/` folder > **Mark Directory as > Sources Root**.

## Quick Start (TL;DR)

```powershell
# Clone
git clone https://github.com/scalargis/scalargis-server.git
cd scalargis-server

# Python venv
python -m venv venv
venv\Scripts\activate
pip install -r requirements-win.txt

# Database (create "scalargis" DB with PostGIS extension in pgAdmin/psql)

# Config
# Create scalargis/instance/development_local.py with:
#   SQLALCHEMY_DATABASE_URI = "postgresql+psycopg2://postgres:postgres@localhost:5432/scalargis"

# Run
$env:APP_CONFIG_FILE = "development_local.py"
cd scalargis
python server.py

# Open http://localhost:5000/backoffice (admin/admin)
```
