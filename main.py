import os
import random

from dotenv import load_dotenv

from constants import poems, silence
from signal_api import Message, SignalAPI

load_dotenv()


def message_handler(message: Message) -> None:
    if message.text == "!poem":
        message.reply(random.choice(poems))
    elif message.text == "今天發生了一件事情":
        message.reply(silence)


def main():
    client = SignalAPI(os.environ["PHONE_NUMBER"], message_handler)
    print("Starting...")
    client.run()


if __name__ == "__main__":
    main()
