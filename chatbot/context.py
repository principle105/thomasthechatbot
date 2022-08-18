import time


class Message:
    def __init__(self, text: str, timestamp: int = None):
        self.text = text

        if timestamp is None:
            timestamp = time.time()

        self.timestamp = timestamp


class Context:
    def __init__(self, last_resp: str = None, last_msg: Message = None):
        # The last response's id from the chatbot
        self.last_resp = last_resp

        # The last message from the user
        self.last_msg = last_msg

    def update(self, msg: str):
        self.last_resp = msg
