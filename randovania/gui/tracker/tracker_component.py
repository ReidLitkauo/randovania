from abc import ABC
from typing import Optional

from randovania.resolver.state import State


class TrackerComponent(ABC):
    def reset(self):
        raise NotImplementedError()

    def apply_previous_state(self, previous_state: dict) -> bool:
        raise NotImplementedError()

    def persist_current_state(self) -> dict:
        raise NotImplementedError()

    def fill_into_state(self, state: State) -> Optional[State]:
        raise NotImplementedError()
