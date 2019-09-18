import datetime
from chatterbot.trainers import ListTrainer
from chatterbot import ChatBot
#import os
import sqlite3
import os
from textblob import TextBlob
from flask import Flask
from flask import request, jsonify
from flask_socketio import SocketIO, send
from word2number import w2n
import random
import requests
import json
import re
# from requests.auth import HTTPProxyAuth
import urllib3
from flask_cors import CORS, cross_origin
from bs4 import BeautifulSoup
# from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

app = Flask(__name__)
app.config['DEBUG'] = True
app.config['SECRET_KEY'] = "abcd"
socketio = SocketIO(app)
CORS(app)  # , resources={r"/api/*": {"origins":"*"}})


@app.route('/', methods=['GET', 'POST'])
def index():
    print(request.get_json())
    if request.is_json:
        inp = request.json['msg']
        user = request.json['user']
        print('user is {}'.format(user))
        bot = ChatBot('Joe', logic_adapters=[{
            'import_path': 'chatterbot.logic.BestMatch'
        },
        {
            'import_path': 'approve.MyLogicAdapter'
        },
        {
            'import_path': 'requests.MyLogicAdapter'
        },
            {
            'import_path': 'chatterbot.logic.LowConfidenceAdapter',
            'threshold': 0.60,
            'default_response': "Sorry! I didn't get it"
        }
        ],
        user = '{}'.format(user)
        )
        # bot.storage.drop()
        bot.set_trainer(ListTrainer)

        # cwd = os.getcwd()
        # cwd = cwd.replace('\\', '/')
        # path = cwd + "/training_data/"
        # bot.train("chatterbot.corpus.english.greetings")
        # bot.train("chatterbot.corpus.english.conversations")
        # try:

        #     for files in os.listdir(path):
        #         data = open(path + files, 'r').readlines()
        #         bot.train(data)
        # except Exception as e:
        #     return jsonify("Error while opening file due to {}".format(e))
        response = bot.get_response(inp)
        return jsonify("{}".format(response))


@app.route('/temp', methods=['GET'])
def random1():
    return "/temp"


if __name__ == "__main__":
    app.run(port=5050)
