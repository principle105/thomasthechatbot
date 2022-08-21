import discord


class ThomasClient(discord.Client):
    def __init__(self):
        super().__init__()

    async def on_ready(self):
        print("Thomas is ready!")

    async def on_message(self, msg: discord.Message):
        ...
