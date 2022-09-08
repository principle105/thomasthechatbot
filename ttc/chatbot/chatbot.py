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

import json
import os
import random
import string
import uuid
from collections import defaultdict
from typing import TYPE_CHECKING, Callable

import contractions
from nltk import pos_tag, word_tokenize
from nltk.corpus import stopwords, wordnet
from nltk.stem.wordnet import WordNetLemmatizer

if TYPE_CHECKING:
    from .context import Context

# Constants
DEFAULT_STORAGE_PATH = "storage"
STOP_WORDS = set(stopwords.words("english"))


def _load_json_file(path: str, name: str) -> dict:
    directory = f"{path}/{name}.json"

    if not os.path.exists(directory):
        return {}

    with open(directory, "r") as f:
        return json.load(f)


def _save_json_file(path: str, name: str, data: dict):
    directory = f"{path}/{name}.json"

    if not os.path.exists(path):
        os.makedirs(path)

    with open(directory, "w") as f:
        return json.dump(data, f)


def _generate_uuid():
    return str(uuid.uuid1())


def _dict_values_to_set(d: list[dict]) -> set:
    """Converts the values of a list of dictionaries to a set."""
    return set().union(*d.values())


class Storage:
    file_name: str = ...

    def __init__(self, data: dict):
        self.data = data

    def to_json(self) -> dict:
        ...

    @classmethod
    def from_json(cls, data: dict):
        ...

    def save_data(self, path: str):
        json_data = self.to_json()

        _save_json_file(path, self.file_name, json_data)

    @classmethod
    def from_file(cls, path: str):
        json_data = _load_json_file(path, cls.file_name)

        return cls.from_json(json_data)


class Link:
    def __init__(self, keywords: set, stop_words: set, resps: dict[str, set] = None):
        if resps is None:
            resps = {}

        # Query data
        self.keywords = keywords
        self.stop_words = stop_words

        # Responses {response_uuid: {previous_uuid}}
        self.resps = resps

    def to_json(self) -> dict:
        return {
            "keywords": list(self.keywords),
            "stop_words": list(self.stop_words),
            "resps": {v: list(k) for v, k in self.resps.items()},
        }

    @classmethod
    def from_json(cls, data: dict):
        return cls(
            keywords=set(data["keywords"]),
            stop_words=set(data["stop_words"]),
            resps={v: set(k) for v, k in data["resps"].items()},
        )


class Mesh(Storage):
    file_name = "mesh"

    def __init__(self, data: dict[str, Link]):
        super().__init__(data)

    def to_json(self) -> dict:
        return {k: v.to_json() for k, v in self.data.items()}

    @classmethod
    def from_json(cls, data: dict):
        return cls({k: Link.from_json(v) for k, v in data.items()})

    def find_mesh(
        self, score_callback: Callable[[Link], int], min_score: int, ignore: set = None
    ):

        if ignore is None:
            ignore = set()

        for _id, data in self.data.items():

            score = score_callback(data)

            if score < min_score:
                continue

            resps_left = set(data.resps) - ignore

            if not resps_left:
                continue

            yield _id, data, resps_left, score

    def add_new_mesh(self, _id: str, keywords: set, stop_words: set):
        if _id is None:
            _id = _generate_uuid()

        link = Link(keywords, stop_words)

        self.data[_id] = link

    def add_mesh_resp(self, _id: str, resp: str, prev_resp: str = None):
        if resp not in self.data[_id].resps:
            self.data[_id].resps[resp] = set()

        if prev_resp is not None:
            self.data[_id].resps[resp].add(prev_resp)

    def resp_id_in_mesh(self, _id: str) -> bool:
        return _id in self.data

    def resp_id_in_mesh_resp(self, _id: str, resp: str) -> bool:
        return resp in self.data[_id].resps

    def get_mesh_from_id(self, _id: str) -> Link:
        return self.data.get(_id, None)


class Resps(Storage):
    file_name = "resps"

    def __init__(self, data: dict[str, list]):
        super().__init__(data)

    def to_json(self) -> dict:
        return self.data

    @classmethod
    def from_json(cls, data: dict):
        return cls(data)

    def add_new_resp(self, msg_tokens: list) -> str:
        _id = _generate_uuid()

        self.data[_id] = msg_tokens

        return _id

    def get_resp_from_tokens(self, msg_tokens: list) -> str:
        resp_values = tuple(self.data.values())

        if msg_tokens not in resp_values:
            return None

        resp_index = resp_values.index(msg_tokens)

        return tuple(self.data.keys())[resp_index]

    def get_resp_from_id(self, _id: str):
        return self.data.get(_id, None)


class Response:
    def __init__(self, resp: str, resp_id: str, mesh_id: str = None):
        self.resp = resp
        self.resp_id = resp_id
        self.mesh_id = mesh_id

    def __str__(self) -> str:
        return self.resp


class Chatbot:
    def __init__(
        self,
        *,
        path: str = None,
        learn: bool = True,
        min_score: float = 0.7,
        score_threshold: float = 0.7,
        mesh_association: float = 0.6,
    ):

        # The path to the storage directory
        self.path = path or DEFAULT_STORAGE_PATH

        # The states conrolling thomas' memory
        self.mesh = Mesh.from_file(self.path)
        self.resps = Resps.from_file(self.path)

        # Configurations
        self.learn = learn
        self.min_score = min_score
        self.score_threshold = score_threshold
        self.mesh_association = mesh_association

        # Responsible for lemmatizing words
        self.tag_map = self.create_tag_map()
        self.wl = WordNetLemmatizer()

    def create_tag_map(self):
        tag_map = defaultdict(lambda: wordnet.NOUN)
        tag_map["J"] = wordnet.ADJ
        tag_map["V"] = wordnet.VERB
        tag_map["R"] = wordnet.ADV

        return tag_map

    def tokenize_msg(self, msg: str) -> tuple[set]:
        text = msg.lower()

        # Removing contrations
        text = contractions.fix(text)

        # Removing punctuation
        text = text.translate(str.maketrans("", "", string.punctuation))

        return word_tokenize(text)

    def lemmatize_tokens(self, tokens: list):
        for token, tag in pos_tag(tokens):
            yield self.wl.lemmatize(token, self.tag_map[tag[0]])

    def separate_tokens(self, raw_tokens: list):
        stop_words = set()
        tokens = set()

        # Separating stop words
        for w in self.lemmatize_tokens(raw_tokens):
            if w in STOP_WORDS:
                stop_words.add(w)
            else:
                # Stemming helps with matching key words
                tokens.add(w)

        return tokens, stop_words

    def _parse_resps(self, resps, ignore: set = None) -> dict[str, list]:
        if ignore is None:
            ignore = set()

        return {d: self.resps.data[d] for d in resps if d not in ignore}

    def get_unlinked_resps(self, ignore: set = None):
        """Finds responses that do not have a response in the mesh"""
        if ignore is None:
            ignore = set()

        resp_ids = set(self.resps.data)
        mesh_ids = set(self.mesh.data)

        no_mesh_resp = resp_ids - mesh_ids

        return self._parse_resps(no_mesh_resp, ignore)

    def get_all_resps(self, ignore: set = None):
        return self._parse_resps(self.resps.data, ignore)

    def tokenize(self, text: str):
        # Tokenizing the input
        raw_tokens = self.tokenize_msg(text)

        # Separating the stop words from the key words
        keywords, stop_words = self.separate_tokens(raw_tokens)

        return raw_tokens, keywords, stop_words

    def find_elligible_meshes(self, meshes: list, threshold: float):
        # Sorting the results by the check function
        sorted_results = sorted(meshes, key=lambda x: x[3], reverse=True)

        best_score = sorted_results[0][3]
        min_score = best_score * threshold

        # Picking the top responses that are within a percentage threshold of the best one
        return [r for r in sorted_results if r[3] >= min_score]

    def find_resps_from_last_msg(
        self, resps_left: set, resps: dict, last_msg: str
    ) -> set:
        return {_id for _id in resps_left if last_msg in resps[_id]}

    def respond(self, ctx: "Context", msg: str) -> Response:
        raw_tokens, keywords, stop_words = self.tokenize(msg)

        msg_id = self.resps.get_resp_from_tokens(raw_tokens)

        if self.learn:
            # Saving the user's message
            if msg_id is None:
                msg_id = self.resps.add_new_resp(msg_tokens=raw_tokens)

            save_resp = True

            # Saving the user's mesasge as if it was a response to the bot
            if ctx.last_resp is not None:
                if not self.mesh.resp_id_in_mesh(ctx.last_resp):
                    resp = self.resps.get_resp_from_id(ctx.last_resp)

                    k, s = self.separate_tokens(resp)

                    self.mesh.add_new_mesh(ctx.last_resp, k, s)

                # Checking if the response is already in the mesh
                elif self.mesh.resp_id_in_mesh_resp(ctx.last_resp, msg_id):
                    save_resp = False

                if save_resp:
                    self.mesh.add_mesh_resp(ctx.last_resp, msg_id, ctx.last_msg)

        ignore = set()

        # Prevents the bot from responding with the same message twice
        if ctx.last_resp is not None:
            ignore.add(ctx.last_resp)

        # Prevents the bot from saying the same thing as the user
        if msg_id is not None:
            ignore.add(msg_id)

        def _filter(r: Link):
            t = len(stop_words & r.stop_words) / 2 + len(r.keywords & keywords)

            return t / (len(r.stop_words) / 2 + len(r.keywords) - t + 1)

        results = [
            k
            for k in self.mesh.find_mesh(
                _filter, min_score=self.min_score, ignore=ignore
            )
        ]

        if results == []:
            # Trying the query just using stop words
            _filter = lambda r: len(stop_words & r.stop_words)

            results = [
                k for k in self.mesh.find_mesh(_filter, min_score=1, ignore=ignore)
            ]

            # Picking a random response if there are still no results
            if results == []:
                prev_meshes = self.get_unlinked_resps(ignore=ignore)

                if not prev_meshes:
                    # Getting all the responses if there are no unlinked responses

                    resp_ignore = ignore if len(ignore) < len(self.resps.data) else None

                    prev_meshes = self.get_all_resps(ignore=resp_ignore)

                resp_ids = tuple(prev_meshes.keys())

                if not resp_ids:
                    raise Exception("No responses found, configure learning to True")

                # Picking a random response
                resp_id = random.choice(resp_ids)

                resp = " ".join(prev_meshes[resp_id])

                return Response(resp=resp, resp_id=resp_id)

        # Finding elligible meshes from keywords
        results = self.find_elligible_meshes(results, self.score_threshold)

        # Mesh responses from previous message
        prev_meshes = {}

        # All mesh responses
        all_meshes = {}

        # Trying to find a response by the user's previous message
        for mesh_id, link, resps_left, _ in results:
            r = set()

            if ctx.last_msg is not None:
                # Finding the response ids that have the same previous message id
                r = self.find_resps_from_last_msg(resps_left, link.resps, ctx.last_msg)

                if r:
                    prev_meshes[mesh_id] = prev_meshes.get(mesh_id, set()) | r

            all_meshes[mesh_id] = all_meshes.get(mesh_id, set()) | resps_left

        meshes = prev_meshes if prev_meshes else all_meshes

        initial_resps = _dict_values_to_set(meshes)
        share_threshold = len(initial_resps) * self.mesh_association

        _filter = lambda x: len(set(x.resps) & initial_resps)

        # Finding other meshes that share a percentage of similar responses
        for mesh_id, link, resps_left, _ in self.mesh.find_mesh(
            _filter, min_score=share_threshold, ignore=ignore
        ):
            resps = meshes.get(mesh_id, set())

            if ctx.last_msg is not None:
                r = self.find_resps_from_last_msg(resps_left, link.resps, ctx.last_msg)

                if r:
                    resps |= r

            if not prev_meshes:
                resps |= set(resps_left)

            meshes[mesh_id] = resps

        # Converting to list of responses to allow for random selection
        resps = _dict_values_to_set(meshes)

        # Choosing a random mesh from the elligible mesh responses
        resp_id = random.choice(tuple(resps))

        # Getting the mesh id
        mesh_id = next((_id for _id, r in meshes.items() if resp_id in r), None)

        resp = self.resps.get_resp_from_id(resp_id)

        resp = " ".join(resp)

        return Response(resp=resp, resp_id=resp_id, mesh_id=mesh_id)

    def save_data(self):
        self.mesh.save_data(self.path)
        self.resps.save_data(self.path)
