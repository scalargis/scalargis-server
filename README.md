# ScalarGIS Server

Python/Flask backend — REST API, database (PostGIS), Waitress server. Serves static frontend builds in production.

> **Two-repo setup:** run the server first, then set up the client. → [scalargis-client README](../scalargis-client/README.md)

---

## Prerequisites

| | Version | Notes |
|---|---|---|
| Python | 3.12 | `requirements-win.txt` has Windows wheels for GDAL and Fiona on Python 3.9 to 3.12 only |
| Docker Desktop | any recent | Runs PostgreSQL with PostGIS. A native PostgreSQL with PostGIS also works. |

---

## Windows Development

**Clone:**
```powershell
git clone https://github.com/scalargis/scalargis-server.git
cd scalargis-server
```

**Database** (PostGIS in Docker, host port 5433):
```powershell
docker run -d --name scalargis-local-db -p 5433:5432 -e POSTGRES_PASSWORD=postgres postgis/postgis:17-3.5-alpine
docker exec scalargis-local-db psql -U postgres -c "CREATE DATABASE scalargis;"
```

On the first start, the server adds the `postgis` extension, creates the `scalargis` schema, and loads the seed data.

**Python environment:**
```powershell
py -3.12 -m venv venv
venv\Scripts\python.exe -m pip install -r requirements-win.txt
venv\Scripts\python.exe -m pip install "setuptools<81"
```

Flask-Security 3 imports `pkg_resources`, and setuptools 81 and later do not have it. Keep setuptools below 81.

**Create `scalargis/instance/development_local.py`** (git ignores `instance/development_local*.py`):
```python
DEBUG = True
SQLALCHEMY_DATABASE_URI = "postgresql+psycopg2://postgres:postgres@localhost:5433/scalargis"
SCALARGIS_PLUGINS = ['proxy', 'geonames', 'spatial_toolbox']
SCALARGIS_EXTENSIONS = []
```

**Run:**
```powershell
$env:APP_CONFIG_FILE = "development_local.py"
cd scalargis
..env\Scripts\python.exe server.py
```

The first start can take one to two minutes and logs `Database schema created!`. A missing `APP_CONFIG_FILE` file is
skipped with no error, and the server then uses `instance/default.py` (port 5432).

| URL | |
|---|---|
| http://localhost:5000/mapa/demo | Demo viewer (needs a client build, see the client README) |
| http://localhost:5000/backoffice | Admin (`admin` / `admin`) |

If the first start fails after the schema is made, later starts skip the creation and `admin` / `admin` fails.
Drop the schema, fix the cause, and start again:
```powershell
docker exec scalargis-local-db psql -U postgres -d scalargis -c "DROP SCHEMA IF EXISTS scalargis CASCADE;"
```

**Multiple project configs:** create one file per project (e.g. `development_local_projecta.py`) and switch `APP_CONFIG_FILE` between them.

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
