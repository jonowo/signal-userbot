# Signal Userbot
Python 3.9+ required.

## signal-cli-rest-api Installation
In `docker-compose.yml`, change `MODE=json-rpc` to `MODE=normal`.
```bash
docker compose up -d
```

Register your phone number
```bash
curl -X POST -H "Content-Type: application/json" 'http://127.0.0.1:8080/v1/register/<phone number>'
```

or link a device.
```bash
curl -X GET -H "Content-Type: application/json" 'http://127.0.0.1:8080/v1/qrcodelink?device_name=<device name>'
```

In `docker-compose.yml`, change `MODE=normal` to `MODE=json-rpc`.
```bash
docker compose up -d
```


## Running the bot
```bash
pip install -Ur requirements.txt
export PHONE_NUMBER='+CCXXXXXXXX'  # Or store in .env
python main.py
```
