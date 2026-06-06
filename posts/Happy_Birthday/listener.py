import json
import requests
from flask import Flask, request

app = Flask(__name__)

@app.route('/<path:path>', methods=['POST'])
def webhook(path):
    try:
        msg = json.loads(request.data)

        if request.headers.get('x-amz-sns-message-type') == 'SubscriptionConfirmation':
            print("[+] Subscription confirmation received")
            print(msg['SubscribeURL'])
            requests.get(msg['SubscribeURL'])

        elif request.headers.get('x-amz-sns-message-type') == 'Notification':
            print("[+] Notification received")
            print(msg["Message"])

        else:
            print(request.data.decode())

    except Exception as e:
        print(f"Error: {e}")
        print(request.data)

    return "OK"

app.run(host="0.0.0.0", port=8080)
