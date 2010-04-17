# -*- coding: utf-8 -*-

__all__ = ('Client', )

import urllib
import json

class ClientException(Exception): pass
class ConnectionException(ClientException): pass
class RemoteException(ClientException): pass
class Client(object):
	
	def __init__(self, ns, transport_type='json'):
		self.ns = ns
		self.transport_type = transport_type
	
	def _handle_remote_call(self, fname):
		def do_call(**kwargs):
			data = {
				'_call': fname,
				'_type': self.transport_type,
			}
			data.update(kwargs)
			print data
			try:
				response = urllib.urlopen(self.ns, urllib.urlencode(data)).read()
			except IOError, e:
				raise ConnectionException(e)
			
			try:
				response = json.loads(response)
			except ValueError, e:
				raise ConnectionException, e
			
			if response.get('success'):
				return response.get('result')
			else:
				raise RemoteException(". ".join(response.get('errors')))
			
		return do_call
	
	def __getattr__(self, name):
		return self._handle_remote_call(name)