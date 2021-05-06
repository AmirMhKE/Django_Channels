import json
from channels.generic.websocket import WebsocketConsumer

class ChatConsumer(WebsocketConsumer):
    def connect(self):
        self.accept()

    def disconnect(self, close_code):
        pass

    def receive(self, text_data):
        text_data_dict = json.loads(text_data)
        message = text_data_dict["message"]
        print(message)

        self.send(json.dumps({
            "message": message
        }))