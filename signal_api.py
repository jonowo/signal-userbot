import datetime
import json
import subprocess
import time

from typing import Any, Callable, Dict

JSONType = Dict[str, Any]


class SignalAPI:
    def __init__(self, phone_number: str, message_handler: Callable[["Message"], None]) -> None:
        self.username = phone_number
        self.message_handler = message_handler

    def send_message(self, recipient: str, message: str, is_group=False) -> None:
        args = ["signal-cli", "-a", self.username, "send", "-m", message]
        if is_group:
            args += ["-g", recipient]
        else:
            args.append(recipient)

        subprocess.run(args, stdout=subprocess.DEVNULL)

    def process_updates(self) -> None:
        with subprocess.Popen(["signal-cli", "--output=json", "-a", self.username, "receive"],
                              stdout=subprocess.PIPE,
                              bufsize=1,
                              text=True) as proc:
            for line in proc.stdout:
                if not line:
                    continue
                data = json.loads(line)
                if (data["account"] == self.username
                    and "dataMessage" in data["envelope"]
                    and data["envelope"]["dataMessage"]["message"]):
                    # Handle regular text message
                    self.message_handler(Message(self, data["envelope"]))

    def run(self) -> None:
        try:
            while True:
                self.process_updates()
                time.sleep(0.2)
        except KeyboardInterrupt:
            print("Oof.")


class Message:
    def __init__(self, client: SignalAPI, data: JSONType) -> None:
        self.client = client
        self.time = datetime.datetime.fromtimestamp(data["dataMessage"]["timestamp"] / 1000)
        self.sender_number = data["sourceNumber"]
        self.sender_name = data["sourceName"]
        self.text = data["dataMessage"]["message"]

        if "groupInfo" in data["dataMessage"]:
            self.group_id = data["dataMessage"]["groupInfo"]["groupId"]
        else:
            self.group_id = None

    def reply(self, message: str) -> None:
        if self.group_id:
            self.client.send_message(self.group_id, message, is_group=True)
        else:
            self.client.send_message(self.sender_number, message)
