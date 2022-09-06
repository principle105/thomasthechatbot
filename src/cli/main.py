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

import typer
from InquirerPy import inquirer
from InquirerPy.utils import color_print
from InquirerPy.validator import EmptyInputValidator
from yaspin import yaspin

from utils import download_nltk_data

# Initializing the CLI
app = typer.Typer()


class Sender:
    @staticmethod
    def success(text: str):
        color_print([("green", text)])

    @staticmethod
    def fail(text: str):
        color_print([("red", text)])

    @staticmethod
    def thomas(text: str):
        color_print([("#f6ca44", text)])

    @staticmethod
    def regular(text: str):
        color_print([("", text)])


@app.command()
def info():
    ...


@app.command()
def start():
    with yaspin(text="Loading", color="cyan") as sp:
        # quiet=True prevents the download progress from being displayed
        download_nltk_data(quiet=True)
        sp.write("- Downloaded data")

        # Importing chatbot after downloading nltk data to prevent error
        from chatbot import Chatbot, Context

        chatbot = Chatbot.from_file()
        sp.write("- Brain loaded")

        sp.ok("✔")

    if chatbot.new_data:
        Sender.success(
            "Thomas learns as you speak to him.\n" "Save his brain by typing 's'."
        )

    # Creating the user's context
    ctx = Context()

    while True:
        text = inquirer.text(
            message="You:",
            validate=EmptyInputValidator(),
            amark="",
        ).execute()

        if text == "s":
            save = inquirer.confirm(
                message="Are you sure you want to save the new brain?", default=False
            ).execute()

            if save:
                chatbot.save_data()

                Sender.success("Saving data...")
                return

            continue

        with yaspin(color="yellow") as spinner:
            mesh_id, r_id, r = chatbot.respond(ctx, text)

            ctx.save_message(r_id, mesh_id)

            spinner.stop()

            if r is not None:
                # Sending the response
                Sender.thomas(f"Thomas: {' '.join(r)}")
