# Reverse proxy and runtime base path (server)

The server runs behind a reverse proxy. The proxy sets the URL prefix per request through the
`X-Forwarded-Prefix` header. One build serves the domain root and any sub-path with no rebuild
and no container recreate. An absent header gives root behavior, the same as before.

Example: the same running container serves `https://maps.example.org/` and
`https://maps.example.org/gis`.

## How the prefix flows through the server

The prefix is one WSGI value: `SCRIPT_NAME`, which Flask exposes as `request.script_root`.
`ProxyFix` reads it from the `X-Forwarded-Prefix` header.

| Value | Source | Effect |
|---|---|---|
| Mount prefix (`window.SCALARGIS_ROOT_PATH`) | `request.script_root` | API, proxy, uploads, asset helper |
| Router basename | `SCALARGIS_BASE_URL` config, else `request.script_root` | React Router basename |
| `index.html` entry asset tags | `request.script_root` prefixed at serve time | entry `<script>`, `modulepreload`, entry CSS |

### `ProxyFix`

`app/__init__.py` enables `ProxyFix` when `TRUSTED_PROXY` is set, with `x_prefix=1`:

```python
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_prefix=1)
```

`x_prefix=1` makes `request.script_root` follow `X-Forwarded-Prefix`. No header → empty prefix →
root behavior.

### `get_base_url()`

`app/utils/http.py` returns the config value first, then the runtime prefix:

```python
return (current_app.config.get('SCALARGIS_BASE_URL') or request.script_root or '').rstrip('\/')
```

An install that sets `SCALARGIS_BASE_URL` keeps its exact value. An install that leaves it empty
takes the runtime prefix, so the router basename follows the proxy.

### `index.html` entry tags

`map/controllers.py` and `backoffice/controllers.py` prefix the mount path onto the entry asset
tags when they serve the page:

```python
out_html = out_html.replace('="/static/viewer/', '="' + root_path + '/static/viewer/')
```

The replace matches the tag attributes (`src="/static/viewer/…"`, `href="/static/viewer/…"`)
only. It must NOT match a bare `/static/viewer/`, because the client's `window.__sgAsset` helper
holds that same literal and already prepends the prefix at runtime. A bare replace would rewrite
the helper too and prefix the path twice. Empty `root_path` is a no-op, so the output is
byte-identical to before.

### Waitress `url_prefix`

`server.py` and `server_services.py` keep the Waitress `url_prefix=url_prefix` argument, fed by
the `URL_PREFIX` env var. The header wins when present. `URL_PREFIX` still serves any install
that does not send the header.

## Apache, per install

`mod_headers` must be loaded. `TRUSTED_PROXY` must be set on the app container, so `ProxyFix` is
active.

### Sub-path install (prefix `/gis`)

The proxy strips the prefix and re-declares it with the header:

```apache
ProxyPass        /gis  http://<app>:5000/
ProxyPassReverse /gis  http://<app>:5000/
RequestHeader set X-Forwarded-Prefix "/gis"
```

The app builds every URL (assets, routes, API) under `/gis`.

### Root install (anti-spoof)

The proxy strips any prefix a client may send:

```apache
ProxyPass        /  http://<app>:5000/
ProxyPassReverse /  http://<app>:5000/
RequestHeader unset X-Forwarded-Prefix
```

The `unset` is the anti-spoof guard. Without it a client could inject `X-Forwarded-Prefix` and
force a prefix. A root install must unset the header.

## Change the path of a running install

1. Edit the two lines (`ProxyPass` and `X-Forwarded-Prefix`) in the vhost.
2. Reload Apache.

No `docker compose build`. No recreate of the app container.

## Verify

```sh
# root (header unset): assets with no prefix
curl -s https://maps.example.org/mapa/<slug> | grep -oE '(src|href)="[^"]*static[^"]*"'
# → /static/viewer/...

# sub-path (header set): everything under the prefix
curl -s https://maps.example.org/gis/mapa/<slug> | grep -oE '(src|href)="[^"]*static[^"]*"'
# → /gis/static/viewer/...
```

Then open a viewer in the browser and confirm the chunks, the CSS fonts, and a worker all return
200 under the prefix. The client side of the mechanism is in the client deployment doc,
`runtime-base-path.md`.
