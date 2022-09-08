"""
MIT License

Copyright (c) 2022 Principle

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE."""

import time
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .chatbot import Response


class Context:
    def __init__(
        self, last_resp: str = None, last_msg: str = None, last_timestamp: float = None
    ):
        # The last response's id from the chatbot
        self.last_resp = last_resp

        # The mesh id of the last response from the chatbot
        self.last_msg = last_msg

        self.last_timestamp = last_timestamp

    def save_resp(self, resp: "Response"):
        self.last_resp = resp.resp_id
        self.last_msg = resp.mesh_id

        self.last_timestamp = time.time()
