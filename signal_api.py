import asyncio
import datetime
import json
import logging
import traceback
from typing import Any, Callable, Dict, Optional

import aiohttp

JSONType = Dict[str, Any]  # don't look


class SignalAPI:
    def __init__(self, phone_number: str, message_handler: Callable, host: str = "localhost:8080") -> None:
        self.phone_number = phone_number
        self.message_handler = message_handler
        self.host = host
        self.session: Optional[aiohttp.ClientSession] = None

        # Map group internal id to id
        self.groups: Dict[str, str] = {}

    async def async_init(self) -> None:
        # Session must be created in a coroutine
        self.session = aiohttp.ClientSession(raise_for_status=True)

    async def get_group_id(self, internal_id: str) -> str:
        if internal_id not in self.groups:
            async with self.session.get(f"http://{self.host}/v1/groups/{self.phone_number}") as resp:
                data = await resp.json()
                for group in data:
                    self.groups[group["internal_id"]] = group["id"]

        return self.groups[internal_id]

    async def send_message(self, recipient: str, message: str) -> None:
        data = {
            "number": self.phone_number,
            "recipients": [recipient],
            "message": message
        }
        await self.session.post(f"http://{self.host}/v2/send", json=data)

    async def react(self, recipient: str, target_author: str, timestamp: int, reaction: str) -> None:
        data = {
            "recipient": recipient,
            "target_author": target_author,
            "timestamp": timestamp,
            "reaction": reaction
        }
        await self.session.post(f"http://{self.host}/v1/reactions/{self.phone_number}", json=data)

    async def receive_messages(self) -> None:
        await self.async_init()
        async with self.session.ws_connect(f"ws://{self.host}/v1/receive/{self.phone_number}") as ws:
            async for line in ws:
                data = json.loads(line.data)
                if "dataMessage" in data["envelope"] and data["envelope"]["dataMessage"]["message"]:
                    # This message contains text
                    message = Message(self, data["envelope"])
                    try:
                        await self.message_handler(message)
                    except Exception as e:
                        logging.error(
                            "".join(traceback.format_exception(type(e), e, e.__traceback__))
                        )

    def run(self) -> None:
        try:
            asyncio.run(self.receive_messages())
        except KeyboardInterrupt:
            print("Oof")
            asyncio.run(self.session.close())


class Message:
    def __init__(self, client: SignalAPI, data: JSONType) -> None:
        self.client = client
        self._timestamp = data["dataMessage"]["timestamp"]
        self.time = datetime.datetime.fromtimestamp(self._timestamp / 1000)
        self.sender_number = data["sourceNumber"]
        self.sender_name = data["sourceName"]
        self.text = data["dataMessage"]["message"]

        if "groupInfo" in data["dataMessage"]:
            self.is_group = True
            self.group_internal_id = data["dataMessage"]["groupInfo"]["groupId"]
        else:
            self.is_group = False
            self.group_internal_id = None

    async def _get_recipient(self) -> str:
        if self.is_group:
            return await self.client.get_group_id(self.group_internal_id)
        else:
            return self.sender_number

    async def reply(self, message: str) -> None:
        await self.client.send_message(await self._get_recipient(), message)

    async def react(self, reaction: str) -> None:
        await self.client.react(await self._get_recipient(), self.sender_number, self._timestamp, reaction)
