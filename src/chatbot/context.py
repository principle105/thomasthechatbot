import time


class Context:
    def __init__(
        self, last_resp: str = None, last_msg: str = None, last_timestamp: float = None
    ):
        # The last response's id from the chatbot
        self.last_resp = last_resp

        # The mesh id of the last response from the chatbot
        self.last_msg = last_msg

        self.last_timestamp = last_timestamp

    def save_message(self, last_resp: str = None, last_msg: str = None):
        self.last_resp = last_resp
        self.last_msg = last_msg

        self.last_timestamp = time.time()
