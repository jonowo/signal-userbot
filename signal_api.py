import asyncio
import datetime
import json
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

    async def receive_messages(self) -> None:
        await self.async_init()
        async with self.session.ws_connect(f"ws://{self.host}/v1/receive/{self.phone_number}") as ws:
            async for line in ws:
                data = json.loads(line.data)
                if "dataMessage" in data["envelope"] and data["envelope"]["dataMessage"]["message"]:
                    # This message contains text
                    message = Message(self, data["envelope"])
                    await self.message_handler(message)

    def run(self) -> None:
        try:
            asyncio.run(self.receive_messages())
        except KeyboardInterrupt:
            print("Oof")
            asyncio.run(self.session.close())


class Message:
    def __init__(self, client: SignalAPI, data: JSONType) -> None:
        self.client = client
        self.time = datetime.datetime.fromtimestamp(data["dataMessage"]["timestamp"] / 1000)
        self.sender_number = data["sourceNumber"]
        self.sender_name = data["sourceName"]
        self.text = data["dataMessage"]["message"]

        if "groupInfo" in data["dataMessage"]:
            self.group_internal_id = data["dataMessage"]["groupInfo"]["groupId"]
        else:
            self.group_internal_id = None

    async def reply(self, message: str) -> None:
        if self.group_internal_id:
            recipient = await self.client.get_group_id(self.group_internal_id)
        else:
            recipient = self.sender_number
        await self.client.send_message(recipient, message)

    async def react(self, emoji: str) -> None:
        pass
