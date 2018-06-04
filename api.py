# -*- coding: utf-8 -*-

from flask import Flask, jsonify, abort, make_response
from flask_restful import Api, Resource, reqparse, fields, marshal
from instagram import main


app = Flask(__name__, static_url_path="")
api = Api(app)

class InstAPI(Resource):
    def __init__(self):
        self.reqparse = reqparse.RequestParser()
        self.reqparse.add_argument('f', type=str, required=True, help='Fan Username',location='json')
        self.reqparse.add_argument('b', type=str, help="Brand Username", required=True, location='json')
        super(InstAPI, self).__init__()

    def get(self):
        args = self.reqparse.parse_args()
        return main(args.f, args.b), 200

    def post(self):
        args = self.reqparse.parse_args()
        print (args)
        return main(args.f, args.b), 200


api.add_resource(InstAPI, '/api/v1/follow', endpoint='follow')

if __name__ == '__main__':
    app.run(debug=True)
