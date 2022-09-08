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

import config
import discord

from ttc import Chatbot, Context


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

        # Checking if the configured guild id matches
        if config.guild_id and msg.guild.id != config.guild_id:
            return

        # Checking if the configured channel id matches
        if config.channel_id and msg.channel.id != config.channel_id:
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
