import datetime
from unittest.mock import patch, AsyncMock, MagicMock

from PySide6.QtWidgets import QDialog

from randovania.gui.dialog.online_game_list_dialog import OnlineGameListDialog
from randovania.network_common.multiplayer_session import MultiplayerSessionListEntry
from randovania.network_common.session_state import MultiplayerSessionState


@patch("randovania.gui.lib.async_dialog.execute_dialog", new_callable=AsyncMock)
async def test_attempt_join(mock_execute_dialog: AsyncMock,
                            skip_qtbot):
    # Setup
    utc = datetime.timezone.utc
    mock_execute_dialog.return_value = QDialog.DialogCode.Accepted
    network_client = MagicMock()
    network_client.join_multiplayer_session = AsyncMock()

    session_a = MultiplayerSessionListEntry(
        id=1, name="A Game", has_password=True, state=MultiplayerSessionState.FINISHED,
        num_players=1, creator="You",
        creation_date=datetime.datetime(year=2015, month=5, day=1, tzinfo=utc),
    )
    session_b = MultiplayerSessionListEntry(
        id=2, name="B Game", has_password=True,
        state=MultiplayerSessionState.IN_PROGRESS,
        num_players=1, creator="You",
        creation_date=datetime.datetime.now(utc) - datetime.timedelta(days=4),
    )

    dialog = OnlineGameListDialog(network_client)
    dialog.sessions = [session_a, session_b]
    dialog.update_list()
    dialog.table_widget.selectRow(0)

    # Run
    await dialog.attempt_join()

    # Assert
    mock_execute_dialog.assert_awaited_once()
    network_client.join_multiplayer_session.assert_awaited_once_with(session_b, "")
