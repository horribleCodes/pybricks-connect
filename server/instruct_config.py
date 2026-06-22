from pathlib import Path

import yaml

from models import InstructDefinition
from server_data.hub_commands import _VALID_COMMANDS


def load_instructs(
    path: str, valid_handlers: set[str] | None = None
) -> dict[str, InstructDefinition]:
    config_path = Path(path)
    if not config_path.is_file():
        raise FileNotFoundError("Instruct config not found: %s" % path)

    with config_path.open() as f:
        data = yaml.safe_load(f)

    if not isinstance(data, dict) or "instructs" not in data:
        raise ValueError("Instruct config must contain an 'instructs' key")

    instructs_raw = data["instructs"]
    if not isinstance(instructs_raw, list) or not instructs_raw:
        raise ValueError("'instructs' must be a non-empty list")

    instructs: dict[str, InstructDefinition] = {}
    for entry in instructs_raw:
        instruct = InstructDefinition(**entry)
        if instruct.port not in range(0, 6):
            raise ValueError(
                "Invalid port for instruct %s: %s" % (instruct.id, instruct.port)
            )
        if not instruct.function:
            raise ValueError("Empty function for instruct %s" % instruct.id)
        valid_hub_function = _VALID_COMMANDS.index(instruct.function) != -1
        valid_server_function = (
            valid_handlers is not None and instruct.function in valid_handlers
        )
        if not valid_hub_function and not valid_server_function:
            raise ValueError(
                "Unknown function '%s' for instruct %s"
                % (instruct.function, instruct.id)
            )
        if instruct.id in instructs:
            raise ValueError("Duplicate instruct id: %s" % instruct.id)
        instructs[instruct.id] = instruct
