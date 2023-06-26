from randovania.server.tracker_sharer import tracker_bridge
from randovania.server.server_app import ServerApp

def setup_app(sio: ServerApp):
	tracker_bridge.setup_app(sio)

