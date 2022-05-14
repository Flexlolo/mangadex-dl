from typing import Dict
import requests

class API:

	BASE_URL = 'https://api.mangadex.org/'

	def request(method: str, api: str, params: Dict = {}, data: Dict = {}) -> Dict:
		url = API.BASE_URL + api

		match method:
			case 'GET':
				r = requests.get(url, params=params, json=data)

			case 'POST':
				r = requests.post(url, params=params, json=data)

			case 'PATCH':
				r = requests.patch(url, params=params, json=data)

			case 'DELETE':
				r = requests.delete(url, params=params, json=data)

			case _:
				raise ValueError('Not supported requests method')

		j = r.json()

		if r.status_code != 200:
			print(r)
			print(j)
			raise ValueError('Recieved unexpected status code.')

		if j['result'] != 'ok':
			print(j)
			raise ValueError('Recieved unexpected result status.')

		return j