from urllib.parse import quote


def client_layer_url_params(descriptor):
    fields = descriptor.split(';')
    params = []
    if len(fields) > 9 and fields[9]:
        params.append(['authkey', quote(fields[9], safe='')])
    if len(fields) > 10 and fields[10]:
        params.append(['TIME', quote(fields[10], safe='')])
    return params
