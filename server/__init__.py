import os
import json
import flask

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
@app.route('/<hash>')
def hash_data(hash) : 
	app.logger.debug(hash)
	if hash[0:2] != '0x' : return ''

	app.logger.info(flask.request.method)
	if flask.request.method.lower() == 'get':
		app.logger.info(hash)
		app.logger.info(data.inquiry(hash))
		return flask.jsonify({
			'#': hash,
			'data': data.getinfo(hash),
		})
	elif flask.request.form is not None :
		return flask.jsonify({
			'#': hash, 
			'ttl': data.setinfo(hash, flask.request.form),
			'data': flask.request.form,
		})
@app.route('/', methods=('get',))
def get_list_recent() : return flask.jsonify(data.recents())


# http error routings
@app.errorhandler(404)
def error_http_404(err) : return flask.render_template('errors/404.html')

@app.errorhandler(500)
def error_http_500(err) : return flask.render_template('errors/500.html')


if __name__ == '__main__' :
	app.run()