import json
import logging
import os
import random
import re
from typing import List

import aiofiles
from dotenv import load_dotenv

logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)

from constants import chinese, silence
from signal_api import Message, SignalAPI

load_dotenv()

logger = logging.getLogger(__name__)


async def load_poems() -> List[str]:
    async with aiofiles.open("poems.json", encoding="utf-8") as f:
        return json.loads(await f.read())


async def write_poems(poems: List[str]) -> None:
    async with aiofiles.open("poems.json", "w", encoding="utf-8") as f:
        await f.write(json.dumps(poems, indent=4))


def is_poem(text: str) -> str or bool:
    if re.match(fr"^[{chinese}\s]+$", text) and len(clist := re.findall(f"[{chinese}]", text)) == 14:
        return "".join(clist[:7]) + "\n" + "".join(clist[7:])
    else:
        return False


async def message_handler(message: Message) -> None:
    args = message.text.partition(" ")[2]
    if message.text == "!poem":
        poems = await load_poems()
        await message.reply(random.choice(poems))
    elif message.text.startswith("!addpoem "):
        poems = await load_poems()
        poem = is_poem(args)
        if poem and poem not in poems:
            poems.append(poem)
            await write_poems(poems)
            await message.reply("Poem added.")
        else:
            await message.reply("no")
    elif message.text.startswith("!delpoem "):
        poems = await load_poems()
        poem = is_poem(args)
        if poem and poem in poems:
            poems.remove(poem)
            await write_poems(poems)
            await message.reply("Poem removed.")
        else:
            await message.reply("no")

    elif message.text == "今天發生了一件事情":
        await message.reply(silence)

    elif "forgor" in message.text.lower().split():
        await message.react("💀")
    elif "rember" in message.text.lower().split():
        await message.react("😃")


def main():
    client = SignalAPI(os.environ["PHONE_NUMBER"], message_handler)
    logger.info("Starting...")
    client.run()


if __name__ == "__main__":
    main()
