import os
import pickle
import random
import string
import uuid
from collections import defaultdict
from typing import Callable

import contractions
from nltk import pos_tag, word_tokenize
from nltk.corpus import stopwords, wordnet
from nltk.stem.wordnet import WordNetLemmatizer

import config

from .context import Context

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


def _dict_values_to_set(d: list[dict]) -> set:
    """Converts the values of a list of dictionaries to a set."""
    return set().union(*d.values())


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

        # Responses {response_uuid: {previous_uuid}}
        self.resps = resps


class Mesh(Storage):
    directory = "mesh"

    def __init__(self, data: dict[str, Link]):
        super().__init__(data)

    def _find_mesh(self, words: set[str], attr: str, ignore: set = None):

        if ignore is None:
            ignore = set()

        for _id, data in self.data.items():

            k = set(getattr(data, attr))

            # Getting shared words
            shared = k & words

            if not shared:
                continue

            resps_left = set(data.resps) - ignore

            if not resps_left:
                continue

            yield _id, data, len(k), shared, resps_left

    def find_mesh_from_resps(self, resps: set[str], ignore=None):
        return self._find_mesh(resps, attr="resps", ignore=ignore)

    def find_mesh_from_keywords(self, keywords: set[str], ignore=None):
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

    def find_elligible_meshes(
        self, meshes: list[Mesh], check: Callable, threshold: float
    ):
        # Sorting the results by the check function
        sorted_results = sorted(meshes, key=check, reverse=True)

        best_score = len(sorted_results[0][3])
        min_score = best_score * threshold

        # Picking the top responses that are within a percentage threshold of the best one
        return [r for r in sorted_results if len(r[3]) >= min_score]

    def find_resps_from_last_msg(
        self, resps_left: set, resps: dict, last_msg: str
    ) -> set:
        return {_id for _id in resps_left if last_msg in resps[_id]}

    def respond(self, ctx: Context, msg: str) -> tuple[str, list]:
        raw_tokens, keywords, stop_words = self.tokenize(msg)

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
                prev_meshes = self.get_unlinked_resps(ignore=ignore)

                if not prev_meshes:
                    # Getting all the responses if there are no unlinked responses

                    resp_ignore = ignore if len(ignore) < len(self.resps.data) else None

                    prev_meshes = self.get_all_resps(ignore=resp_ignore)

                # Picking a random response
                resp_id = random.choice(tuple(prev_meshes.keys()))

                return None, resp_id, prev_meshes[resp_id]

        # Finding elligible meshes from keywords
        results = self.find_elligible_meshes(
            results,
            lambda r: len(r[3]) / (r[2] - len(r[3]) + 1),
            config.keyword_threshold,
        )

        # Finding elligible meshes from stop words
        if keyword_query:
            results = self.find_elligible_meshes(
                results,
                lambda r: len(stop_words & set(r[1].stop_words)),
                config.stopword_threshold,
            )

        # Mesh responses from previous message
        prev_meshes = {}

        # All mesh responses
        all_meshes = {}

        # Trying to find a response by the user's previous message
        for mesh_id, link, _, _, resps_left in results:
            r = set()

            if ctx.last_msg is not None:
                # Finding the response ids that have the same previous message id
                r = self.find_resps_from_last_msg(resps_left, link.resps, ctx.last_msg)

                if r:
                    prev_meshes[mesh_id] = prev_meshes.get(mesh_id, set()) | r

            all_meshes[mesh_id] = all_meshes.get(mesh_id, set()) | resps_left

        meshes = prev_meshes if prev_meshes else all_meshes

        # Finding other meshes that share a percentage of similar responses
        initial_resps = _dict_values_to_set(meshes)
        total_resps = len(initial_resps)

        for mesh_id, link, _, shared, resps_left in self.mesh.find_mesh_from_resps(
            initial_resps, ignore=ignore
        ):
            resps = meshes.get(mesh_id, set())

            share_threshold = len(shared) * config.mesh_association

            if total_resps < share_threshold:
                continue

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

        return mesh_id, resp_id, resp

    def save_data(self):
        self.mesh.save_data()
        self.resps.save_data()

    @classmethod
    def from_file(cls):
        mesh = Mesh.from_file()
        resps = Resps.from_file()

        return cls(mesh=mesh, resps=resps)
