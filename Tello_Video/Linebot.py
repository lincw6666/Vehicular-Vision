# -*- coding: UTF-8 -*-

#Python module requirement: line-bot-sdk, flask
from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError 
from linebot.models import MessageEvent, TextMessage, TextSendMessage

line_bot_api = LineBotApi('') #LineBot's Channel access token
handler = WebhookHandler('')        #LineBot's Channel secret
user_id_set=set()                                         #LineBot's Friend's user id 
app = Flask(__name__)

def loadUserId():
    try:
        idFile = open('idfile', 'r')
        idList = idFile.readlines()
        idFile.close()
        idList = idList[0].split(';')
        idList.pop()
        return idList
    except Exception as e:
        print(e)
        return None


def saveUserId(userId):
        idFile = open('idfile', 'a')
        idFile.write(userId+';')
        idFile.close()

def Initialize():
	idList = loadUserId()
	if idList: 
		global user_id_set 
		user_id_set = set(idList)

def SendMessage(message):
	try:
		for userId in user_id_set:
			line_bot_api.push_message(userId, TextSendMessage(text=message))  # Push API example
	except Exception as e:
		print(e)

	
@app.route("/", methods=['GET'])
def hello():
    return "HTTPS Test OK."

@app.route("/", methods=['POST'])
def callback():
    signature = request.headers['X-Line-Signature']    # get X-Line-Signature header value
    body = request.get_data(as_text=True)              # get request body as text
    print("Request body: " + body, "Signature: " + signature)
    try:
        handler.handle(body, signature)                # handle webhook body
    except InvalidSignatureError:
        abort(400)
    return 'OK'


@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    Msg = event.message.text
    if Msg == 'Hello, world': return
    print('GotMsg:{}'.format(Msg))

    line_bot_api.reply_message(event.reply_token,TextSendMessage(text="收到訊息!!"))   # Reply API example
    
    userId = event.source.user_id
    if not userId in user_id_set:
        user_id_set.add(userId)
        saveUserId(userId)

 
def Active():
    Initialize() 

    SendMessage("LineBot is ready for you!")
    
    app.run('127.0.0.1', port=32768, threaded=True, use_reloader=False)

    

