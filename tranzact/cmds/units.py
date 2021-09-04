from typing import Dict

# The rest of the codebase uses totos everywhere.
# Only use these units for user facing interfaces.
units: Dict[str, int] = {
    "tranzact": 10 ** 12,  # 1 tranzact (TRZ) is 1,000,000,000,000 toto (1 trillion)
    "toto:": 1,
    "colouredcoin": 10 ** 3,  # 1 coloured coin is 1000 colouredcoin totos
}
