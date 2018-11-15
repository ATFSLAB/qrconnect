import os
import json
import Flask as flask

from . import datalayer

def _configure(path) :
	ret = {}
	if os.path.exists(path) :
		with open(path, 'r', encoding='utf8') as fp :
			ret = json.load(fp)
	return ret



# init flask server
app = flask.Flask(__name__)
configure = _configure('./settings.json')
app.config.from_object(configure['server'] if 'server' in configure else {})
api_token = configure['etherscan'] if 'etherscan' in configure else ''
redis_conf = configure['redis'] if 'redis' in configure else {}
redis_conf['decode_responses'] = True
app.logger.info('[SETTINGS] ' + str(configure))
data = datalayer.DataLayer(redis_conf, api_token)

# app routings
@app.route('/<hash>', methods=('GET',))
def hash_data(hash) : 
	app.logger.debug(hash)
	if hash[0:2] != '0x' : return ''

	return flask.jsonify({
		'#': hash,
		'data': data.getinfo(hash),
	})
		

@app.route('/+/<hash>', methods=('GET',))
def hash_set(hash) :
	app.logger.debug(hash)
	if hash[0:2] != '0x' : return ''

	vals = data.inquiry(hash)
	if vals is not None :
		return flask.jsonify({
			'#': hash,
			'ttl': data.setinfo(hash, vals),
			'data': vals,
		})
	else :
		return flask.jsonify({
			'#': hash, 
			'ttl': 0
		})

@app.route('/', methods=('get',))
def get_list_recent() : return flask.jsonify(data.recents())


# http error routings
@app.errorhandler(404)
def error_http_404(err) : return flask.render_template('errors/404.html')

@app.errorhandler(500)
def error_http_500(err) : return flask.render_template('errors/500.html')
