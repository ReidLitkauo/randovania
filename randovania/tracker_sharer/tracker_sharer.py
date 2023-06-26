import dataclasses
import json

from PySide6 import QtCore, QtWidgets
from randovania.interface_common.options import Options
from randovania.network_client.game_session import User

class TrackerSharer(QtCore.QObject):

	_app: QtWidgets.QApplication
	_options: Options
	_user: User = None

	def __init__(self, app: QtWidgets.QApplication, options: Options):
		self._app = app
		self._options = options
		self.subscribe_to_relevant_updates()

	def subscribe_to_relevant_updates(self):
		self._app.game_connection.Updated.connect(self.on_game_state_updated)
		self._app.network_client.UserChanged.connect(self.on_user_changed)

	def on_game_state_updated(self):
		print("="*80)
		print(self._app.game_connection.get_current_inventory())
		print(self._user.as_json if self._user else '')
		print("-"*80)

	def on_user_changed(self, user: User):
		self._user = user

	def build_tracker_info_dict(self) -> dict:
		return {
			'user': self._user.as_json if self._user else None,
			'game_name': state.source.game.game.value,
			'inventory': { item.long_name: state.current_inventory[item].capacity for item in state.current_inventory },
		}

