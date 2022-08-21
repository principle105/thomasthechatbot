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

Prompts are split up into keywords and stop words.

### Key Words

Meshes are initially by the number of shared keywords with the prompt. The results are sorted and the meshes that aren't within a percentage threshold (configurable) of the best mesh are discarded.

### Stop Words

Eligible meshes are weighed by their prevalence of stop words with the prompt. A mesh is selected with a weighted random choice.

### Choosing a Response

Responses are chosen at random from the response UUIDs in the selected mesh. If responses share the same previous message mesh UUID as the prompt, all responses that don't are removed.

# Formatting

[Black](https://github.com/psf/black), [isort](https://github.com/PyCQA/isort) and [Prettier](https://prettier.io/) are used for formatting
