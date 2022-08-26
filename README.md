<div align="center">
    <img src="https://i.imgur.com/1qHopDH.png" alt="Thomas" width="220" height="220">
    <h1>Thomas the Chatbot</h1>
</div>

# How does Thomas work?

Thomas has no hard-coded responses and is designed to “learn” as he is spoken to.

Note: I created this approach based on my intuition and not a proven method.

## Data Storage

Thomas does not come up with his own responses, he reiterates those that he has seen before.

### Responses

Previous responses are stored in `storage/resps.thomas` as a dictionary where the key is a generated [UUID](https://docs.python.org/3/library/uuid.html) and the value is the tokenized response.

### Mesh

Prompts are associated with responses through a "mesh" which is stored in `storage/mesh.thomas`. The mesh consists of a dictionary where the key is the UUID of the prompt and the value is a "link". Links are used to associate responses to patterns of words, they have the following structure:

`stop_words: set`
Stop words separated from the tokenized prompt

`keywords: set`
The remaining words which are lemmatized by their part of speech

`resps: dict[str, set]`
Responses to the prompt where the key is the response UUID and the value is a set of mesh ids from the previous prompt.

## Querying Responses

### Tokenizing Prompts

Before tokenization, prompts are lowercased, contractions are expanded and punctuation is removed. Prompts are tokenized by word and split into key words and stop words.

### Ignoring Responses

The user's prompt and bot's previous response are ignored to prevent repetition.

### Key Words

Meshes are initially queried by the number of shared key words with the prompt. The results are sorted and the meshes that aren't within a percentage threshold (configurable) of the best mesh's score are discarded.

### Stop Words

Stop words are queried in the same way as key words but with a different percentage threshold.

### Mesh Association

Meshes are associated with each other by the percentage of shared responses (configurable). Associated meshes for each queried mesh are found and added to the list.

### Choosing a Response

If responses are found to share the same previous message UUID as the prompt, all non-sharing responses are moved. Responses are chosen at random from the remaining responses.

# Running

### CLI

**Python 3.9+ is required**

1. Install [Poetry](https://python-poetry.org/) using `pip install poetry`

2. Install the necessary dependencies using `poetry install`

3. Activate the poetry virtual environment using `poetry shell`

4. Type `python run ttc` to run

# Formatting

[Black](https://github.com/psf/black), [isort](https://github.com/PyCQA/isort) and [Prettier](https://prettier.io/) are used for formatting
