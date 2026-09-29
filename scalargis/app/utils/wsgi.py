def with_waitress_environ(wsgi_app, url_prefix, url_scheme):
    """Apply the Waitress url_prefix and url_scheme settings to each request."""
    prefix = (url_prefix or '').rstrip('/')

    def middleware(environ, start_response):
        if url_scheme:
            environ['wsgi.url_scheme'] = url_scheme
        if prefix:
            path = environ.get('PATH_INFO', '')
            if path != prefix and not path.startswith(prefix + '/'):
                start_response('404 Not Found', [('Content-Type', 'text/plain')])
                return [b'Not Found']
            environ['SCRIPT_NAME'] = environ.get('SCRIPT_NAME', '') + prefix
            environ['PATH_INFO'] = path[len(prefix):]
        return wsgi_app(environ, start_response)

    return middleware
