import discord

import config
from chatbot import Chatbot, Context


class ThomasClient(discord.Client):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        # The instance of the chatbot
        self.chatbot = Chatbot.from_file()

        # The context of each user
        self.ctxs: dict[str, Context] = {}

    async def on_ready(self):
        print("Thomas is ready!")

    async def on_message(self, msg: discord.Message):
        # Prevents the bot from responding to itself
        if msg.author.id == self.user.id:
            return

        # Checking if the channel_id is not configured
        if config.channel_id is None:
            return

        if msg.channel.id != config.channel_id:
            return

        # Getting the user's context
        ctx = self.ctxs.get(msg.author.id, Context())

        async with msg.channel.typing():
            mesh_id, r_id, r = self.chatbot.respond(ctx, msg.content)

            ctx.save_message(r_id, mesh_id)

            # Saving the updated context
            self.ctxs[msg.author.id] = ctx

        if r is not None:
            await msg.reply(" ".join(r), mention_author=False)
