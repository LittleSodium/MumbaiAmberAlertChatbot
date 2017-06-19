import os
import sys
import json
import requests
from flask import Flask, request, url_for

app = Flask(__name__)

# Get started button request:
#
# curl -X POST -H "Content-Type: application/json" -d '{
#   "get_started":{
#     "payload":"GET_STARTED_PAYLOAD"
#   }
# }' "https://graph.facebook.com/v2.6/me/messenger_profile?access_token=PAGE_ACCESS_TOKEN"

# <div>Icons made by <a href="http://www.flaticon.com/authors/madebyoliver" title="Madebyoliver">Madebyoliver</a> from <a href="http://www.flaticon.com" title="Flaticon">www.flaticon.com</a> is licensed by <a href="http://creativecommons.org/licenses/by/3.0/" title="Creative Commons BY 3.0" target="_blank">CC 3.0 BY</a></div>
# <div>Icons made by <a href="http://www.flaticon.com/authors/maxim-basinski" title="Maxim Basinski">Maxim Basinski</a> from <a href="http://www.flaticon.com" title="Flaticon">www.flaticon.com</a> is licensed by <a href="http://creativecommons.org/licenses/by/3.0/" title="Creative Commons BY 3.0" target="_blank">CC 3.0 BY</a></div>

@app.route('/webhook', methods=['GET'])
def verify():
    # when the endpoint is registered as a webhook, it must echo back
    # the 'hub.challenge' value it receives in the query arguments
    if request.args.get("hub.mode") == "subscribe" and request.args.get("hub.challenge"):
        if not request.args.get("hub.verify_token") == os.environ["VERIFY_TOKEN"]:
            return "Verification token mismatch", 403
        return request.args["hub.challenge"], 200

    return "Hello world", 200

    # Register the Get Started Button
    params = {
        "access_token": os.environ["PAGE_ACCESS_TOKEN"]
    }
    headers = {
        "Content-Type": "application/json"
    }
    data = json.dumps({
            "get_started": {
            "payload":"GET_STARTED_PAYLOAD"
            }
        })
    r = requests.post("https://graph.facebook.com/v2.6/me/messages", params=params, headers=headers, data=data)

@app.route('/webhook', methods=['POST'])
def webhook():

    # endpoint for processing incoming messaging events

    data = request.get_json()
    log(data) # log message contents

    if data["object"] == "page":

        for entry in data["entry"]:
            for messaging_event in entry["messaging"]:

                if messaging_event.get("message"):  # someone sent us a message

                    sender_id = messaging_event["sender"]["id"]        # the facebook ID of the person sending the message
                    recipient_id = messaging_event["recipient"]["id"]  # the recipient's ID, i.e our page's facebook ID
                    if messaging_event["message"].get("text"):
                        message_text = messaging_event["message"]["text"]  # the message's text

                    if messaging_event["message"].get("quick_reply"):
                        if messaging_event["message"]["quick_reply"]["payload"] == 'found':
                            send_message_call_button(sender_id, "That is great! Please contact the nearest police station, or call the Missing Person helpline at 02222621549.")

                        else:
                            if messaging_event["message"]["quick_reply"]["payload"] == 'missing':
                                response_text = "Please tell us more about the person."
                                send_message_webview(sender_id, response_text)

                    else:
                        send_message_quick_reply(sender_id, "I am sorry, I don't understand that. Did you want to report a missing/found person?")

                if messaging_event.get("postback"):  # user clicked/tapped "postback" button in earlier message
                    sender_id = messaging_event["sender"]["id"]

                    if messaging_event["postback"]["payload"] == "GET_STARTED_PAYLOAD":
                        send_subscriber_id(sender_id)
                        send_message_quick_reply(sender_id, "Welcome to Mumbai Amber Alert. Would you like to report a missing person or report that you may have found a missing person?")

    return "ok", 200

def send_message(recipient_id, message_text):

    log("sending message to {recipient}: {text}".format(recipient=recipient_id, text=message_text))

    params = {
        "access_token": os.environ["PAGE_ACCESS_TOKEN"]
    }
    headers = {
        "Content-Type": "application/json"
    }
    data = json.dumps({
        "recipient": {
            "id": recipient_id
        },
        "message": {
            "text": message_text
        }
    })
    r = requests.post("https://graph.facebook.com/v2.6/me/messages", params=params, headers=headers, data=data)
    if r.status_code != 200:
        log(r.status_code)
        log(r.text)

def send_message_quick_reply(recipient_id, message_text):

    log("sending message to {recipient}: {text}".format(recipient=recipient_id, text=message_text))

    params = {
        "access_token": os.environ["PAGE_ACCESS_TOKEN"]
    }
    headers = {
        "Content-Type": "application/json"
    }
    data = json.dumps({
        "recipient": {
            "id": recipient_id
        },
        "message": {
            "text": message_text,
            "quick_replies":[
                  {
                    "content_type":"text",
                    "title":"Report Missing",
                    "payload":"missing",
                    "image_url": os.environ["DOMAIN"] + "/static/error.svg"
                  },
                  {
                    "content_type":"text",
                    "title":"I found a person!",
                    "payload":"found",
                    "image_url": os.environ["DOMAIN"] + "/static/success.svg"
                  }
                ]
        }
    })
    r = requests.post("https://graph.facebook.com/v2.6/me/messages", params=params, headers=headers, data=data)
    if r.status_code != 200:
        log(r.status_code)
        log(r.text)

def send_message_webview(recipient_id, message_text):
    # Send URL Button that opens webview containing form for registering missing person.
    log("sending message to {recipient}: {text}".format(recipient=recipient_id, text=message_text))

    params = {
        "access_token": os.environ["PAGE_ACCESS_TOKEN"]
    }
    headers = {
        "Content-Type": "application/json"
    }
    data = json.dumps({
        "recipient": {
            "id": recipient_id
        },
        "message":{
            "attachment":{
              "type":"template",
              "payload":{
                "template_type":"button",
                "text": message_text,
                "buttons":[
                  {
                    "type":"web_url",
                    "url":"https://d5cd3cf4.ngrok.io/people/new?user=" + recipient_id,
                    "title":"Enter Details",
                    "webview_height_ratio": "full",
                    "messenger_extensions": "true"
                  }
                ]
              }
            }
          }
        })
    r = requests.post("https://graph.facebook.com/v2.6/me/messages", params=params, headers=headers, data=data)
    if r.status_code != 200:
        log(r.status_code)
        log(r.text)

def send_message_call_button(recipient_id, message_text):
    # Send URL Button that opens webview containing form for registering missing person.
    log("sending message to {recipient}: {text}".format(recipient=recipient_id, text=message_text))

    params = {
        "access_token": os.environ["PAGE_ACCESS_TOKEN"]
    }
    headers = {
        "Content-Type": "application/json"
    }
    data = json.dumps({
        "recipient": {
            "id": recipient_id
        },
        "message":{
            "attachment":{
              "type":"template",
              "payload":{
                "template_type":"button",
                "text": message_text,
                "buttons":[
                  {
                    "type":"phone_number",
                    "title":"Call Police Helpline",
                    "payload": "02222621549"
                  },
                  {
                    "type":"web_url",
                    "url":"https://d5cd3cf4.ngrok.io",
                    "title":"Show Person Database",
                    "webview_height_ratio": "full"
                  }
                ]
              }
            }
          }
        })
    r = requests.post("https://graph.facebook.com/v2.6/me/messages", params=params, headers=headers, data=data)
    if r.status_code != 200:
        log(r.status_code)
        log(r.text)

def send_subscriber_id(sender_id):
    headers = {
        "Content-Type": "application/json"
    }
    data = json.dumps({
        "subscriber_id": sender_id,
        "key": os.environ["SUBSCRIBER_REG_KEY"]
    })
    r = requests.post("https://d5cd3cf4.ngrok.io/subscribe", headers=headers, data=data)
    if r.status_code != 200:
        log(r.status_code)

def log(message):  # simple wrapper for logging to stdout on heroku
    print(str(message))
    sys.stdout.flush()


if __name__ == '__main__':
    app.run(debug=True)
