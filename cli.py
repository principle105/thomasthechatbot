import typer
from InquirerPy import inquirer
from InquirerPy.utils import color_print
from InquirerPy.validator import EmptyInputValidator

from chatbot import Chatbot, Context, Message

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
    # Creating the user's context
    ctx = Context()

    chatbot = Chatbot.from_file()

    while True:
        text = inquirer.text(
            message="You: ",
            validate=EmptyInputValidator(),
            amark="",
        ).execute()

        if text == "q":
            break

        msg = Message(text=text)

        mesh_id, r_id, r = chatbot.respond(ctx, msg)

        ctx.last_resp = r_id
        ctx.last_msg = mesh_id

        if r is not None:
            # Sending the response
            Sender.thomas(f"Thomas: {' '.join(r)}")

    chatbot.save_data()


if __name__ == "__main__":
    app()
