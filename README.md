# ScalarGIS Server

Python/Flask backend — REST API, database (PostGIS), Waitress server. Serves static frontend builds in production.

> **Two-repo setup:** run the server first, then set up the client. → [scalargis-client README](../scalargis-client/README.md)

---

## Prerequisites

| | Version | Notes |
|---|---|---|
| Python | 3.12 | [python.org](https://www.python.org/downloads/) — check **Add Python to PATH** |
| PostgreSQL + PostGIS | 12+ | [EDB installer](https://www.enterprisedb.com/downloads/postgres-postgresql-downloads), add PostGIS via Stack Builder |

---

## Windows Development

**Clone and install:**
```powershell
git clone https://github.com/scalargis/scalargis-server.git
cd scalargis-server
python -m venv venv
venv\Scripts\activate
pip install -r requirements-win.txt
```

> `requirements-win.txt` includes pre-built Windows wheels for GDAL and Fiona.

**Create the database** (pgAdmin or psql):
```sql
CREATE DATABASE scalargis;
\c scalargis
CREATE EXTENSION postgis;
```

**Create `scalargis/instance/development_local.py`:**
```python
SQLALCHEMY_DATABASE_URI = "postgresql+psycopg2://postgres:postgres@localhost:5432/scalargis"
```

**Set the config and run:**
```powershell
$env:APP_CONFIG_FILE = "development_local.py"
cd scalargis
python server.py
```

On first run, the database schema and default data are created automatically.

| URL | |
|---|---|
| http://localhost:5000/mapa/demo | Demo viewer |
| http://localhost:5000/backoffice | Admin (`admin` / `admin`) |

**Multiple project configs:** create separate files (e.g. `development_local_projecta.py`, `development_local_projectb.py`) and switch `APP_CONFIG_FILE` between them. For IDE run configurations, load both `.env` and `.env.local` as env files and set `APP_CONFIG_FILE` as an inline env variable.

---

## Docker Deployment

Copy and edit the local env override file:
```powershell
copy .env .env.local
```

Key variables in `.env` / `.env.local`:

| Variable | Default | Description |
|---|---|---|
| `CONTAINER_NAME` | `scalargis-server` | Container name and hostname |
| `IMAGE_NAME` | `wkt/scalargis-server` | Image name:tag |
| `PORT` | `5000` | Internal container port |
| `HOST_PORT` | `5000` | Host-mapped port |
| `THREADS` | `12` | Waitress worker threads |
| `CHANNEL_TIMEOUT` | `120` | Waitress channel timeout (seconds) |
| `CONNECTION_LIMIT` | `200` | Max concurrent connections |
| `URL_PREFIX` | *(empty)* | URL prefix for reverse proxy deployments |
| `URL_SCHEME` | `http` | `http` or `https` |
| `TRUSTED_PROXY` | *(empty)* | Trusted proxy IP (`*` to trust any, e.g. behind Apache) |
| `HOST_DATA_DIR` | `./data` | Host path for persistent data volume |
| `APP_CONFIG_FILE` | *(empty)* | Config file in `scalargis/instance/` (defaults to `docker/docker_db.py`) |

```powershell
docker compose up -d
```

Starts two services: **scalargis** (server on `HOST_PORT`) and **db** (PostGIS `postgis/postgis:17-3.5-alpine` on port 5001). Server config is loaded from `docker/docker_db.py` by default (mounted as volume).

---

## Extensions

Extensions add project-specific API routes and models. Clone into `scalargis/app/extensions/` and activate in your config:

```powershell
cd scalargis/app/extensions
git clone <url> extension_name
git clone <url> another_extension
```

```python
# in development_local.py
SCALARGIS_EXTENSIONS = ['extension_name', 'another_extension']
```

Restart the server after changing extensions. Extension repos are on GitLab — contact maintainers for access.

---

## Config Reference

Key settings for `scalargis/instance/development_local.py` (overrides `scalargis/instance/default.py`):

```python
DEBUG = True
SQLALCHEMY_DATABASE_URI = "postgresql+psycopg2://user:pass@host:5432/db"
SCALARGIS_DEFAULT_LOCALE = 'pt'
SCALARGIS_PLUGINS = ['proxy', 'geonames', 'spatial_toolbox']
SCALARGIS_EXTENSIONS = ['extension_name', 'another_extension']
SCALARGIS_PROXY_CORS = ['http://localhost:4200']
# Additional DB binds for extensions that use a separate DB:
SQLALCHEMY_BINDS = {"other_db": "sqlite:///path/to/other.db"}
```

Full list of defaults in `scalargis/instance/default.py`.
