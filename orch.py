from flask import Flask, request, make_response, jsonify
from flask_restful import reqparse, abort, Api, Resource
import datetime
from pymongo import MongoClient
from flask_cors import CORS, cross_origin
import xml.etree.cElementTree as ET
import jxmlease
import threading

""" *************************************************
Initial configuration.

Some of the parameters contain sensitive information,
therefore it would be optimal to pass these params via
the console during initialization of the Python app.

To keep data private, use the os.environ library to
access to this info passed by flags.
************************************************* """
app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*", "methods": ["GET", "POST"]}})

# The mongodb conection URL
app.config['MONGO_CONN_URL'] = 'your-mongo-db-connection-info'

# Initializes the API app
api = Api(app)

# Initializes MongoDB configuration
MONGO_CLIENT = MongoClient(app.config['MONGO_CONN_URL'])
MONGO_DB = MONGO_CLIENT['galacticsearchengine']

""" *************************************************
Generates a response message with a code number.
************************************************* """
def message_gen(message, code=200):
    return {'message': message}, code


""" *************************************************
MongoDB interaction
************************************************* """
def mongo_format_doc(payload):
    timestamp = str(datetime.datetime.utcnow())

    return {
        'timestamp': timestamp,
        'payload': payload
    }

def mongo_store_doc(**kwargs):
    collection = MONGO_DB[kwargs['namespace']]
    collection.insert_one(kwargs['doc'])


""" *************************************************
The log endpoint
************************************************* """
xml_parser = jxmlease.Parser()
class Log(Resource):
    def post(self):
        namespace = request.args.get('namespace')
        if not namespace:
            return message_gen('namespace query param missing', 400)

        try:
            payload = xml_parser(request.data)
        except Exception as e:
            return message_gen('Unabled to transform XML into dict', 403)

        try:
            mongo_log = mongo_format_doc(payload)
            t = threading.Thread(target=mongo_store_doc, kwargs={'namespace':namespace, 'doc':mongo_log})
            t.start()
        except Exception as e:
            return message_gen('Unabled to store log in MongoDB', 403)

        return message_gen('Message received by server')


""" *************************************************
************************************************* """
api.add_resource(Log, '/log')

if __name__ == '__main__':
    app.run(debug=True, port=5000)
