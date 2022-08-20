import typer
from InquirerPy import inquirer
from InquirerPy.utils import color_print
from InquirerPy.validator import EmptyInputValidator
from yaspin import yaspin

from chatbot import Chatbot, Context, Message, download_nltk_data

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
def start():
    with yaspin(text="Loading", color="cyan") as sp:
        download_nltk_data()
        sp.write("- Downloaded data")

        chatbot = Chatbot.from_file()
        sp.write("- Brain loaded")

        sp.ok("✔")

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

        msg = Message(text=text)

        with yaspin(color="yellow") as spinner:
            mesh_id, r_id, r = chatbot.respond(ctx, msg)

            ctx.last_resp = r_id
            ctx.last_msg = mesh_id

            spinner.stop()

            if r is not None:
                # Sending the response
                Sender.thomas(f"Thomas: {' '.join(r)}")


if __name__ == "__main__":
    app()
