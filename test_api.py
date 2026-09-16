import urllib.request
import json
import urllib.parse

def test():
    data=urllib.parse.urlencode({'username':'admin@clinic.com','password':'admin123'}).encode()
    req = urllib.request.Request('http://localhost:8000/token', data=data)
    token = json.loads(urllib.request.urlopen(req).read())['access_token']
    
    patient_data=json.dumps({'id': 'pat-1234', 'identifier': '1234567-8', 'name': 'John', 'birth_date': None}).encode()
    req2 = urllib.request.Request('http://localhost:8000/api/v1/patients/', data=patient_data, headers={'Content-Type': 'application/json', 'Authorization': 'Bearer ' + token})
    try:
        res = urllib.request.urlopen(req2)
        print(res.read())
    except Exception as e:
        print(e.read())

test()
