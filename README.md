<div align="center">
    <img src="https://i.imgur.com/1qHopDH.png" alt="Thomas" width="220" height="220">
    <h1>Thomas the Chatbot</h1>
</div>

![Demo](https://i.imgur.com/Jet4UGh.gif)

# Installation

**Python 3.9+ is required**

This package can be installed from [PyPi](https://pypi.org/project/thomasthechatbot/) with:

```
pip install thomasthechatbot
```

# Usage

## Basic Usage

```py
from ttc import Chatbot, Context
from ttc.utils import download_nltk_data

# Only needs to be run once
download_nltk_data()

ctx = Context()

chatbot = Chatbot()

talk = True

while talk:
    msg = input("You: ")

    if msg == "s":
        talk = False
    else:
        # Getting the response
        resp = chatbot.respond(ctx, msg)

        # Saving the response to the context
        ctx.save_resp(resp)

        print(resp)

# Saving the chatbot data
chatbot.save_data()
```

## Configurations

```py
chatbot = Chatbot(
    path="brain",
    learn=False,
    min_score=0.5,
    score_threshold=0.5,
    mesh_association=0.5,
)
```

## CLI

Type `ttc` to begin talking to Thomas.

# How does Thomas work?

Thomas has no hard-coded responses and is designed to “learn” as he is spoken to.

Note: I created this approach based on my intuition and not a proven method.

## Data Storage

Thomas does not come up with his own responses, he reiterates those that he has seen before.

### Responses

Previous responses are stored in `resps.json` as a dictionary where the key is a generated [UUID](https://docs.python.org/3/library/uuid.html) and the value is the tokenized response.

### Mesh

Prompts are associated with responses through a "mesh" which is stored in `mesh.thomas`. The mesh consists of a dictionary where the key is the UUID of the prompt and the value is a "link". Links associate responses to patterns of words, they have the following attributes:

`stop_words: set`
Stop words separated from the tokenized prompt.

`keywords: set`
The remaining words which are lemmatized by their part of speech.

`resps: dict[str, set]`
Responses to the prompt where the key is the response UUID and the value is a set of mesh ids from the previous prompt.

## Querying Responses

### Tokenizing Prompts

Before tokenization, prompts are lowercased, contractions are expanded and punctuation is removed. This aids in improving the consistency and accuracy of queries. Prompts are tokenized by word and split into key words and stop words.

### Ignoring Responses

The user's prompt and chatbot's previous response are ignored to prevent the chatbot from appearing repetitive.

### Initial Query

Meshes are initially queried by their score which can be calculated with:

`(ss / 2 + sk) / (ts / 2 + tk - ss / 2 - sk + 1)`

`ss` = shared stop words

`sk` = shared key words

`ts` = total stop words

`tk` = total key words

This formula weighs shared key words 2 times more heavily than stop words by dividing `ss` and `sk` by 2. It also takes into account the total number of words resulting in more precise meshes being favoured.

### First Discard

Meshes with scores below a threshold (`min_score`) are discarded.

### No Results Queried

If no results remain, meshes are queried by the number of shared stop words.

### Second Discard

The remaining meshes are sorted and meshes that fall below a percentage threshold (`score_threshold`) of the best score are discarded. Considering multiple meshes increases the variety of responses.

### Mesh Association

Meshes are associated with each other by the percentage of shared responses (`mesh_association`). Associated meshes for each queried mesh are found and added to the list. This process prevents less trained prompts from having a small response pool.

### Choosing a Response

If responses are found to share the same previous message UUID as the prompt, all non-sharing responses are moved. Responses are chosen at random from the remaining responses. Random selection prevents the chatbot from being predictable.

# Contributing

Open to contributions, please create an issue if you want to do so.

# Formatting

[Black](https://github.com/psf/black), [isort](https://github.com/PyCQA/isort) and [Prettier](https://prettier.io/) are used for formatting
