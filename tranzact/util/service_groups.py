from typing import KeysView, Generator

SERVICES_FOR_GROUP = {
    "all": "tranzact_harvester tranzact_timelord_launcher tranzact_timelord tranzact_farmer tranzact_full_node tranzact_wallet".split(),
    "node": "tranzact_full_node".split(),
    "harvester": "tranzact_harvester".split(),
    "farmer": "tranzact_harvester tranzact_farmer tranzact_full_node tranzact_wallet".split(),
    "farmer-no-wallet": "tranzact_harvester tranzact_farmer tranzact_full_node".split(),
    "farmer-only": "tranzact_farmer".split(),
    "timelord": "tranzact_timelord_launcher tranzact_timelord tranzact_full_node".split(),
    "timelord-only": "tranzact_timelord".split(),
    "timelord-launcher-only": "tranzact_timelord_launcher".split(),
    "wallet": "tranzact_wallet tranzact_full_node".split(),
    "wallet-only": "tranzact_wallet".split(),
    "introducer": "tranzact_introducer".split(),
    "simulator": "tranzact_full_node_simulator".split(),
}


def all_groups() -> KeysView[str]:
    return SERVICES_FOR_GROUP.keys()


def services_for_groups(groups) -> Generator[str, None, None]:
    for group in groups:
        for service in SERVICES_FOR_GROUP[group]:
            yield service


def validate_service(service: str) -> bool:
    return any(service in _ for _ in SERVICES_FOR_GROUP.values())
