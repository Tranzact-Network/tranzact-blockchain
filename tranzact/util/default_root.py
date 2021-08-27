import os
from pathlib import Path

DEFAULT_ROOT_PATH = Path(os.path.expanduser(os.getenv("TRANZACT_ROOT", "~/.tranzact/mainnet"))).resolve()

DEFAULT_KEYS_ROOT_PATH = Path(os.path.expanduser(os.getenv("TRANZACT_KEYS_ROOT", "~/.tranzact_keys"))).resolve()
