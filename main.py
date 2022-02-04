import os
import random

from dotenv import load_dotenv

from constants import poems, silence
from signal_api import Message, SignalAPI

load_dotenv()


async def message_handler(message: Message) -> None:
    if message.text == "!poem":
        await message.reply(random.choice(poems))
    elif message.text == "今天發生了一件事情":
        await message.reply(silence)

    if "forgor" in message.text.lower().split():
        await message.react("💀")
    elif "rember" in message.text.lower().split():
        await message.react("😃")


def main():
    client = SignalAPI(os.environ["PHONE_NUMBER"], message_handler)
    print("Starting...")
    client.run()


if __name__ == "__main__":
    main()
