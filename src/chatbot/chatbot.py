import os
import pickle
import random
import string
import uuid
from collections import defaultdict

from nltk import pos_tag, word_tokenize
from nltk.corpus import stopwords, wordnet
from nltk.stem.wordnet import WordNetLemmatizer

import config

from .context import Context, Message

# Constants
STOP_WORDS = set(stopwords.words("english"))
EXTENSION = "thomas"


def _load_storage_file(name: str):
    directory = f"{config.storage_dir}/{name}.{EXTENSION}"

    if not os.path.exists(directory):
        return None

    with open(directory, "rb") as f:
        return pickle.load(f)


def _save_storage_file(name: str, data: dict):
    directory = f"{config.storage_dir}/{name}.{EXTENSION}"

    with open(directory, "wb") as f:
        return pickle.dump(data, f)


def _generate_uuid():
    return str(uuid.uuid1())


class Storage:
    directory: str = ...

    def __init__(self, data: dict):
        self.data = data

    def save_data(self):
        _save_storage_file(self.directory, self.data)

    @classmethod
    def from_file(cls):
        data = _load_storage_file(cls.directory) or {}

        return cls(data)


class Link:
    def __init__(self, keywords: set, stop_words: set, resps: dict[str, set] = None):
        if resps is None:
            resps = {}

        # Query data
        self.keywords = keywords
        self.stop_words = stop_words

        # Responses
        self.resps = resps


class Mesh(Storage):
    directory = "mesh"

    def __init__(self, data: dict[str, Link]):
        super().__init__(data)

    def _find_mesh(
        self, words: set[str], attr: str, ignore: set = set()
    ) -> tuple[str, set]:

        for _id, data in self.data.items():

            k = getattr(data, attr)

            # Getting shared words
            shared = set(k) & words

            if not shared:
                continue

            resps_left = set(data.resps) - ignore

            if not resps_left:
                continue

            yield _id, data, shared, resps_left

    def find_mesh_from_keywords(self, keywords: set[str], ignore=None):
        # TODO: take into account synonyms
        return self._find_mesh(keywords, attr="keywords", ignore=ignore)

    def find_mesh_from_stop_words(self, stop_words: set[str], ignore=None):
        return self._find_mesh(stop_words, attr="stop_words", ignore=ignore)

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
    directory = "resps"

    def __init__(self, data: dict[str, list]):
        super().__init__(data)

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


class Chatbot:
    def __init__(self, mesh: Mesh, resps: Resps):
        # The states conrolling thomas' memory
        self.mesh = mesh
        self.resps = resps

        self.tag_map = self.create_tag_map()
        self.wl = WordNetLemmatizer()

    def create_tag_map(self):
        tag_map = defaultdict(lambda: wordnet.NOUN)
        tag_map["J"] = wordnet.ADJ
        tag_map["V"] = wordnet.VERB
        tag_map["R"] = wordnet.ADV

        return tag_map

    def tokenize_msg(self, msg: str) -> tuple[set]:
        msg = msg.lower()

        # Removing punctuation
        msg = msg.translate(str.maketrans("", "", string.punctuation))

        return word_tokenize(msg)

    def lemmatize_tokens(self, tokens: list):
        for token, tag in pos_tag(tokens):
            yield self.wl.lemmatize(token, self.tag_map[tag[0]])

    def separate_tokens(self, raw_tokens: list) -> str:
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

    def respond(self, ctx: Context, msg: Message) -> tuple[str, list]:
        raw_tokens, keywords, stop_words = self.tokenize(msg.text)

        msg_id = self.resps.get_resp_from_tokens(raw_tokens)

        if config.learn:
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

        results = [
            k for k in self.mesh.find_mesh_from_keywords(keywords, ignore=ignore)
        ]

        keyword_query = bool(results)

        if keyword_query is False:
            # Trying the query using stop words
            results = [
                w
                for w in self.mesh.find_mesh_from_stop_words(stop_words, ignore=ignore)
            ]

            # Picking a random response if there are still no results
            if results == []:
                resps = self.get_unlinked_resps(ignore=ignore)

                if not resps:
                    # Getting all the responses if there are no unlinked responses

                    resp_ignore = ignore if len(ignore) < len(self.resps.data) else None

                    resps = self.get_all_resps(ignore=resp_ignore)

                # Picking a random response
                resp_id = random.choice(tuple(resps.keys()))

                return None, resp_id, resps[resp_id]

        # Weighing and sorting the results
        sorted_results = sorted(results, key=lambda x: len(x[2]), reverse=True)

        # Picking the top responses that are within a percentage threshold of the best one
        best_score = len(sorted_results[0][2])
        min_score = best_score * config.response_threshold

        elligible_results = [r for r in sorted_results if len(r[2]) >= min_score]

        weights = []

        for r in sorted_results[: len(elligible_results)]:

            if keyword_query:
                # Adding weight with prevelance of shared stop words
                stop_words = stop_words & set(r[1].stop_words)

            weights.append(len(r[2]) + len(stop_words))

        # Weighted random choice to pick the response
        (link,) = random.choices(elligible_results, weights=weights, k=1)

        mesh_id, link, _, resps_left = link

        resps = set()

        # Trying to find a response based on what the user previously said
        if ctx.last_msg is not None:
            # Finding the response ids that have the same previous message id
            common_resps = {
                _id for _id in resps_left if ctx.last_msg in link.resps[_id]
            }

            resps.update(common_resps)

        resps = tuple(resps if resps else link.resps)

        # Choosing a random response from the link
        resp_id = random.choice(resps)

        resp = self.resps.get_resp_from_id(resp_id)

        return mesh_id, resp_id, resp

    def save_data(self):
        self.mesh.save_data()
        self.resps.save_data()

    @classmethod
    def from_file(cls):
        mesh = Mesh.from_file()
        resps = Resps.from_file()

        return cls(mesh=mesh, resps=resps)
