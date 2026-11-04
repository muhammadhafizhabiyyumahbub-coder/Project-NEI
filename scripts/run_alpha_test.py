import urllib.request, json

def post(url, body=None):
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(url, data=data, headers={'Content-Type':'application/json'}, method='POST')
    return json.loads(urllib.request.urlopen(req).read())

pid = post('http://localhost:8000/api/v1/projects', {'name':'run-test2'}).get('id')
task = post(f'http://localhost:8000/api/v1/projects/{pid}/tasks',
            {'user_request':'create 10x3x1 box in rhino','risk_level':'L0'})
tid = task['id']
print('task:', tid, task['state'])
try:
    r = post(f'http://localhost:8000/api/v1/tasks/{tid}/run')
    v = json.loads(r.get('verification_json') or '{}')
    for c in v.get('checks', []):
        print(' ', c['target'], c['result'], c.get('evidence'))
    print('status:', v.get('status'), 'state:', r['state'])
except urllib.error.HTTPError as e:
    print('HTTP', e.code, e.read().decode())
