from chatbot import Chatbot, Context, Message


def main():
    # Creating the user's context
    ctx = Context()

    chatbot = Chatbot.from_file()

    while True:
        text = input("You: ")

        if text == "q":
            break

        msg = Message(text=text)

        r_id, r = chatbot.respond(ctx, msg)

        ctx.last_resp = r_id

        if r is not None:
            # Sending the response
            print(f"Thomas: {' '.join(r)}")

    chatbot.save_data()


if __name__ == "__main__":
    main()
