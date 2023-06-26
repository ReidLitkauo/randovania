import asyncio
import dataclasses
import json

from PySide6 import QtCore, QtWidgets
from randovania.game_connection.game_connection import ConnectedGameState
from randovania.interface_common.options import Options
from randovania.network_common.game_connection_status import GameConnectionStatus
from randovania.network_common.multiplayer_session import User

class TrackerSharer(QtCore.QObject):

	_app: QtWidgets.QApplication

	def __init__(self, app: QtWidgets.QApplication, options: Options):
		self._app = app
		self._options = options
		self.subscribe_to_relevant_updates()

	def subscribe_to_relevant_updates(self):
		self._app.game_connection.GameStateUpdated.connect(self.on_game_state_updated, QtCore.Qt.QueuedConnection)

	def on_game_state_updated(self, state: ConnectedGameState):
		print("GAME STATE UPDATE " * 20)
		if not self.allowed_to_proceed_with_sharing(state):
			return
		self.share_tracker_info_with_server( self.build_tracker_info_json(state) )

	def allowed_to_proceed_with_sharing(self, state: ConnectedGameState) -> bool:
		return self._options.share_tracker_with_server \
			and self._app.network_client.current_user \
			and state.status is GameConnectionStatus.InGame \
			and hasattr(state.source, 'game') \
			and state.current_inventory != {}

	def build_tracker_info_json(self, state: ConnectedGameState) -> str:
		return json.dumps( {
			'game_name': state.source.game.game.value,
			'inventory': { item.long_name: state.current_inventory[item].capacity for item in state.current_inventory },
		} )

	def share_tracker_info_with_server(self, info: str):
		# https://docs.python.org/3/library/asyncio-task.html#asyncio.create_task
		server_call_task_persistance = set()
		server_call_task = asyncio.create_task( self._app.network_client.server_call('tracker_info', info) )
		server_call_task.add_done_callback(server_call_task_persistance.discard)

