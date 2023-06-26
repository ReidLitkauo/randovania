import json
from randovania.server.server_app import ServerApp

def setup_app(sio: ServerApp):
	sio.on("tracker_info", tracker_info_received)

def tracker_info_received(sio: ServerApp, info: str):
	print("X"*80*2)
	print(json.loads(info))