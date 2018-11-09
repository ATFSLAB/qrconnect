import redis

with redis.Redis() as redis :
	print(redis.ping())