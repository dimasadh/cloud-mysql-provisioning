from flask import Flask,current_app, jsonify, make_response, Response,  Blueprint, abort,render_template, request, redirect,render_template_string, url_for, send_from_directory
from flask_restful import Api, Resource, reqparse,wraps
import uuid
import json
from container_model import *

class PhpmyadminsAPI(Resource):
    def __init__(self):
        self.cp = PhpmyadminProvisioning()
    def post(self):
        try:
            self.datakirim = request.get_json()
        except:
            self.datakirim = dict()
        try:
            s = self.cp.create(username=self.datakirim['username'], mem_limit=self.datakirim['mem_limit'])
            return jsonify(s)
        except:
            return jsonify(dict(status='ERROR'))
    def get(self,username):
        s = self.cp.get_stats(username=username)
        return jsonify(s)

class PhpmyadminAPI(Resource):
    def __init__(self):
        self.cp = PhpmyadminProvisioning()
    def get(self,username):
        s = self.cp.get(username=username)
        return jsonify(s)
    def delete(self,username):
        s = self.cp.delete(username=username)
        return jsonify(s)

def get_flask(name):
    app = Flask(name)
    app.secret_key = b'781231casda9871293812h3'
    return app

def get_blueprint(nama):
    app = get_flask(__name__)
    api = Api(app)
    api.add_resource(PhpmyadminsAPI,'/pmas',endpoint='pmas')
    api.add_resource(PhpmyadminsAPI,'/stats/<username>',endpoint='stats')
    api.add_resource(PhpmyadminAPI,'/pma/<username>',endpoint='pma')
    return app

app = get_blueprint(__name__)
if __name__=='__main__':
    app.run(host='0.0.0.0', port=32111, debug=True)