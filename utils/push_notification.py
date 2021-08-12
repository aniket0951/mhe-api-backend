import jwt
import time
import json
import os 

from hyper import HTTPConnection, HTTP20Connection

device_token='64508C08E4BC9484A3E985BA99AE8626CD03035F696C1CA8C4A9FB8AD5BCFDAD'
device_token1='85E8BE3DFC67EE96836308A45DCB105BE58ABC2C845D81ED1FE519386EDD24CD'

class ApnsPusher:
	def __init__(self, apns_key_id = 'CGVNKX2AWN', apns_key_name = './AuthKey_CGVNKX2AWN.p8', team_id = 'NWQC28349Y', bundle_id = 'com.manipal.patient.ios',device_token=device_token):
		self.ALGORITHM = 'ES256'
		self.APNS_KEY_ID = apns_key_id
		self.APNS_AUTH_KEY = apns_key_name
		self.TEAM_ID = team_id
		self.BUNDLE_ID = bundle_id
		self.DEVICE_TOKEN=device_token

	def send_single_push(self):
		file = open(self.APNS_AUTH_KEY)
		secret = file.read()
		token = jwt.encode({
		            'iss': self.TEAM_ID,
		            'iat': time.time()
		        },
		        secret,
		        algorithm = self.ALGORITHM,
		        headers = {
		            'alg': self.ALGORITHM,
		            'kid': self.APNS_KEY_ID,
		        }
		)
		
		path = '/3/device/{0}'.format(device_token1)
		request_headers = {
	        'apns-expiration': '0',
	        'apns-priority': '10',
	        'apns-topic': self.BUNDLE_ID,
	        'authorization': 'bearer {0}'.format(token.decode('ascii'))
		}
        
		payload = {
                'aps': {
                    'alert': {
						'title':'Test Title',
						'body': 'Hii Test Message 2'
                        },
                    'badeg': 1,
                    'sound': 'default',
                    }
		        }
        
        #Production
		conn = HTTPConnection('api.push.apple.com:443')
  
        #Development
		#conn = HTTPConnection('api.development.push.apple.com:443')
		payload = json.dumps(payload).encode('utf-8')
		conn.request(
	        'POST',
	        path,
	        payload,
	        headers=request_headers
		)
		response = conn.get_response()
		return response

apns_pusher= ApnsPusher() 
resp = apns_pusher.send_single_push()
print('Status: {}'.format(resp.status))
print('reps.read(): {}'.format(resp.read()))