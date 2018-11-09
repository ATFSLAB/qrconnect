import re
import redis
import requests
from time import time

'''
<prefix>://				ZSET (score: unix timestamp, value: hash)
<prefix>://<hash>		HSET (data dict), expires in a day
'''
REDIS_PREFIX = 'qrscan'
REDIS_INDEX_THRESHOLD = 1000
REDIS_CONFIG = {}

class DataLayer() :
	def __init__(self, configure, api_token) :
		self.redis = redis.Redis(**configure)
		self.api_token = api_token

	def __valid(self, hash=None) :
		return hash is not None and 0<len(hash)

	def __key(self, hash=None):
		return '%s://%s'%(REDIS_PREFIX, hash if self.__valid(hash) else '')

	def __trim(self, rk) :
		if REDIS_INDEX_THRESHOLD < self.redis.zcard(rk) :
			rems = self.redis.zrange(REDIS_INDEX_THRESHOLD/2, -1)
			tx = self.redis.pipeline()
			# delete indices
			for rrk in rems :
				tx.zrem(rrk)
			# 
			tx.execute()

	
	def recents(self, starts=0, paged=100) :
		rk  = self.__key()

		# trim older indices
		self.__trim(rk)

		return [rv for rv in self.redis.zrange(rk, starts, paged, withscores=True)]

	def getinfo(self, hash) :
		if not self.__valid(hash) :
			return None
		rk = self.__key(hash)
		if not self.redis.exists(rk) :
			# for debug; inquiry
			data = self.inquiry(hash)
			if data is None : 
				return {}
			
			self.setinfo(hash, data)
			
		return self.redis.hgetall(rk)

	def setinfo(self, hash, data) :
		ik = self.__key()
		if self.__valid(hash) and data is not None :
			rk = self.__key(hash)
			pipe = self.redis.pipeline()
			pipe.hmset(rk, data)
			pipe.expire(rk, 24*3600)
			pipe.zadd(ik, hash, time())
			pipe.execute()
			return self.redis.ttl(rk)
		else :
			return 0

	def inquiry(self, hash):
		# query url
		api_host = 'https://api.etherscan.io/api'
		api_params = 'module=proxy&action=eth_getTransactionByHash&txhash=%s&apikey=%s'%(hash, self.api_token)
		api = '%s?%s'%(api_host, api_params)

		rs = requests.get(api)
		try :
			rss = rs.json()
			data = rss['result']
			text = data['input']
			body = bytes.fromhex(text[2:]).decode('utf8') if text[0:2] == '0x' else ''
			
			data['input'] = body
			return data
		except :
			return None



