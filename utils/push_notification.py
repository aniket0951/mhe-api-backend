import jwt
import time
import json

from hyper import HTTPConnection
from django.conf import settings

class ApnsPusher:
	def __init__(
			self, 
			apns_key_id = settings.APNS_KEY_ID, 
			apns_key_name = settings.APNS_CERT_PATH, 
			team_id = settings.TEAM_ID, 
			bundle_id = settings.BUNDLE_ID
		):
		self.ALGORITHM = 'ES256'
		self.APNS_KEY_ID = apns_key_id
		self.APNS_AUTH_KEY = apns_key_name
		self.TEAM_ID = team_id
		self.BUNDLE_ID = bundle_id

	def send_single_push(self,device_token,title,body,badge,sound,extra):
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
		
		path = '/3/device/{0}'.format(device_token)
		
		request_headers = {
	        'apns-expiration': '0',
	        'apns-priority': '10',
	        'apns-topic': self.BUNDLE_ID,
	        'authorization': 'bearer {0}'.format(token.decode('ascii'))
		}
        
		payload = {
			'aps': {
				'alert': {
					'title'	:	title,
					'body'	: 	body
				},
				'badge': 	badge,
				'sound': 	sound,
				'extra': 	extra
			}
		}
        
		conn = HTTPConnection(settings.APNS_ENDPOINT)
		
		payload = json.dumps(payload).encode('utf-8')
		conn.request(
	        'POST',
	        path,
	        payload,
	        headers=request_headers
		)
		response = conn.get_response()
		return response