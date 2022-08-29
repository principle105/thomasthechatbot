import discord

import config
from chatbot import download_nltk_data


def main():
    download_nltk_data()

    from .client import ThomasClient

    intents = discord.Intents.none()

    # Privileged intents
    intents.message_content = True
    intents.messages = True

    thomas = ThomasClient(intents=intents)
    thomas.run(config.token)
