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
import re
import config
import doco.client
import httplib
import urllib
import logging
import base64
import json

app = Flask(__name__)


# Line Messaging API
line_bot_api = LineBotApi(config.CHANNEL_ACCESS_TOKEN, http_client=RequestsHttpClient)
line_bot_api_nc = LineBotApi(config.CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(config.CHANNEL_SECRET)
parser = WebhookParser(config.CHANNEL_SECRET)

# Docomo API
ENDPOINT_URI = 'https://api.apigw.smt.docomo.ne.jp/dialogue/v1/dialogue?API_KEY='
DOCOMO_API_KEY = '62353054416e576e4851436c6244733366316b44726f6d66522f7271492e577353717368316d4d634e5537'

# Translate API
TRANSLATE_API_ENDPOINT = 'https://api.cognitive.microsoft.com/sts/v1.0'
TRANSLATE_API_KEY = 'f4c2e8baea4744068d4dcb010eb813e2'

# Vision API
VISION_API_ENDPOINT = 'https://southeastasia.api.cognitive.microsoft.com/vision/v1.0'
image_url = ''
headers = {
    # Request headers
    'Content-Type': 'application/octet-stream',
    # 'Content-Type': 'application/octet-stream',
    'Ocp-Apim-Subscription-Key': '61bb79be31ee4405bc6d347a89743dd2',
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
    token = get_access_token(TRANSLATE_API_KEY)
    user = {'t': 20}  # 20:kansai character
    docomo_client = doco.client.Client(apikey=DOCOMO_API_KEY, user=user)
    events = parser.parse(body.decode('utf-8'), signature)
#    if body['type'] == 'text' :
#        events = parser.parse(body.decode('utf-8'), signature)
#    else:
#        events = parser.parse(body, signature)


    for event in events:
        if event.message.type == 'text':

            msg = event.message.text
            logging.debug(type(msg))
            docomo_res = docomo_client.send(utt=msg,apiname='Dialogue')
            line_bot_api.reply_message(
                event.reply_token,
               TextSendMessage(text=docomo_res['utt'])
            )
        elif event.message.type == 'image':
            message_content = line_bot_api.get_message_content(event.message.id)
 #           logging.debug(message_content.content)
            conn = httplib.HTTPSConnection('api.projectoxford.ai')
            conn.request("POST","https://southeastasia.api.cognitive.microsoft.com/vision/v1.0/analyze?%s" % params, message_content.content, headers)
            response = conn.getresponse()
            res_data = response.read()
            conn.close()
            logging.debug("result data :" + res_data)
            res = json.loads(res_data)
            caption = translator(res['description']['captions'][0]['text'], 'ja', token)
            logging.debug("caption_xml :" + caption_xml)
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text='「' + caption + '」 の写真やね。')
            )
#            line_bot_api.reply_message(
#                event.reply_token,
#                TextSendMessage(text=','.join(res['description']['tags']))
#            )
    return ''

# トークン発行
def get_access_token(key):
    headers = {
        'Ocp-Apim-Subscription-Key': key
    };

    response = requests.request('POST', 'https://api.cognitive.microsoft.com/sts/v1.0/issueToken', headers=headers)

    return response.text

# 翻訳実行
def translator(text, lang, token):
    headers = {
        'Authorization': 'Bearer ' + token
    }

    query = {
        'to': lang,
        'text': text
    }

    response = requests.request('GET', 'https://api.microsofttranslator.com/V2/Http.svc/Translate', headers=headers, params=query)
    traslated = re.sub("<.*?>", '', response.text)
    return traslated






if __name__ == "__main__":
    app.run()
