from typing import Dict

# The rest of the codebase uses zactos everywhere.
# Only use these units for user facing interfaces.
units: Dict[str, int] = {
    "tranzact": 10 ** 12,  # 1 tranzact (TRZ) is 1,000,000,000,000 zacto (1 trillion)
    "zacto:": 1,
    "colouredcoin": 10 ** 3,  # 1 coloured coin is 1000 colouredcoin zactos
}
