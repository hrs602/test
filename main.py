#!/usr/bin/env python
# coding: utf-8
from gae_http_client import RequestsHttpClient
from google.appengine.api import taskqueue
from flask import Flask, request, abort
from linebot import (
    LineBotApi, WebhookHandler, WebhookParser
)
from linebot.exceptions import (
    InvalidSignatureError, LineBotApiError
)
from linebot.models import (
    MessageEvent, TextMessage, TextSendMessage,
)

import requests
import config
import doco.client
import httplib
import urllib
import logging

app = Flask(__name__)


# Line Messaging API
line_bot_api = LineBotApi(config.CHANNEL_ACCESS_TOKEN, http_client=RequestsHttpClient)
handler = WebhookHandler(config.CHANNEL_SECRET)
parser = WebhookParser(config.CHANNEL_SECRET)

# Docomo API
ENDPOINT_URI = 'https://api.apigw.smt.docomo.ne.jp/dialogue/v1/dialogue?API_KEY='
DOCOMO_API_KEY = '62353054416e576e4851436c6244733366316b44726f6d66522f7271492e577353717368316d4d634e5537'

# Vision API
image_url = ''
headers = {
    # Request headers
    'Content-Type': 'application/json',
    # 'Content-Type': 'application/octet-stream',
    'Ocp-Apim-Subscription-Key': 'Your key',
}
params = urllib.urlencode({
    # Request parameters
    'visualFeatures': 'Description',
    # 'visualFeatures': 'Categories,Tags, Description, Faces, ImageType, Color, Adult',
    # 'details': 'Celebrities'
})

logging.getLogger().setLevel(logging.DEBUG)

@app.route("/callback", methods=['POST'])
def callback():
    signature = request.headers['X-Line-Signature']

    #body = request.get_data(as_text=True)
    body = request.get_data()
    logging.debug("Request body: " + body)

    user = {'t': 20}  # 20:kansai character
    docomo_client = doco.client.Client(apikey=DOCOMO_API_KEY, user=user)


    events = parser.parse(body, signature)
    for event in events:
        if event.message.type == 'text':
            docomo_res = docomo_client.send(utt=event.message.text,apiname='Dialogue')
            line_bot_api.reply_message(
                event.reply_token,
               TextSendMessage(text=docomo_res['utt'])
            )
        elif event.message.type = 'image':
            line_bot_api.reply_message(
                event.reply_token,
               TextSendMessage(text='image')
            )
    return ''


if __name__ == "__main__":
    app.run()
