from setuptools import setup

dependencies = [
    "blspy==1.0.6",  # Signature library
    "chiavdf==1.0.3",  # timelord and vdf verification
    "chiabip158==1.0",  # bip158-style wallet filters
    "chiapos==1.0.4",  # proof of space
    "clvm==0.9.7",
    "clvm_rs==0.1.11",
    "clvm_tools==0.4.3",
    "aiohttp==3.7.4",  # HTTP server for full node rpc
    "aiosqlite==0.17.0",  # asyncio wrapper for sqlite, to store blocks
    "bitstring==3.1.9",  # Binary data management library
    "colorama==0.4.4",  # Colorizes terminal output
    "colorlog==5.0.1",  # Adds color to logs
    "concurrent-log-handler==0.9.19",  # Concurrently log and rotate logs
    "cryptography==3.4.7",  # Python cryptography library for TLS - keyring conflict
    "fasteners==0.16.3",  # For interprocess file locking
    "keyring==23.0.1",  # Store keys in MacOS Keychain, Windows Credential Locker
    "keyrings.cryptfile==1.3.4",  # Secure storage for keys on Linux (Will be replaced)
    #  "keyrings.cryptfile==1.3.8",  # Secure storage for keys on Linux (Will be replaced)
    #  See https://github.com/frispete/keyrings.cryptfile/issues/15
    "PyYAML==5.4.1",  # Used for config file format
    "setproctitle==1.2.2",  # Gives the tranzact processes readable names
    "sortedcontainers==2.3.0",  # For maintaining sorted mempools
    "websockets==8.1.0",  # For use in wallet RPC and electron UI
    "click==7.1.2",  # For the CLI
    "dnspython==2.1.0",  # Query DNS seeds
    "watchdog==2.1.3",  # Filesystem event watching - watches keyring.yaml
]

upnp_dependencies = [
    "miniupnpc==2.2.2",  # Allows users to open ports on their router
]

dev_dependencies = [
    "pytest",
    "pytest-asyncio",
    "flake8",
    "mypy",
    "black",
    "aiohttp_cors",  # For blackd
    "ipython",  # For asyncio debugging
]

kwargs = dict(
    name="tranzact-blockchain",
    author="Archiviz",
    author_email="tranzact.network@gmail.com",
    description="Tranzact blockchain full node, farmer, timelord, and wallet.",
    url="https://tranzact.cash/",
    license="Apache License",
    python_requires=">=3.7, <4",
    keywords="tranzact blockchain node",
    install_requires=dependencies,
    setup_requires=["setuptools_scm"],
    extras_require=dict(
        uvloop=["uvloop"],
        dev=dev_dependencies,
        upnp=upnp_dependencies,
    ),
    packages=[
        "build_scripts",
        "tranzact",
        "tranzact.cmds",
        "tranzact.clvm",
        "tranzact.consensus",
        "tranzact.daemon",
        "tranzact.full_node",
        "tranzact.timelord",
        "tranzact.farmer",
        "tranzact.harvester",
        "tranzact.introducer",
        "tranzact.plotting",
        "tranzact.pools",
        "tranzact.protocols",
        "tranzact.rpc",
        "tranzact.server",
        "tranzact.simulator",
        "tranzact.types.blockchain_format",
        "tranzact.types",
        "tranzact.util",
        "tranzact.wallet",
        "tranzact.wallet.puzzles",
        "tranzact.wallet.rl_wallet",
        "tranzact.wallet.cc_wallet",
        "tranzact.wallet.did_wallet",
        "tranzact.wallet.settings",
        "tranzact.wallet.trading",
        "tranzact.wallet.util",
        "tranzact.ssl",
        "mozilla-ca",
    ],
    entry_points={
        "console_scripts": [
            "tranzact = tranzact.cmds.tranzact:main",
            "tranzact_wallet = tranzact.server.start_wallet:main",
            "tranzact_full_node = tranzact.server.start_full_node:main",
            "tranzact_harvester = tranzact.server.start_harvester:main",
            "tranzact_farmer = tranzact.server.start_farmer:main",
            "tranzact_introducer = tranzact.server.start_introducer:main",
            "tranzact_timelord = tranzact.server.start_timelord:main",
            "tranzact_timelord_launcher = tranzact.timelord.timelord_launcher:main",
            "tranzact_full_node_simulator = tranzact.simulator.start_simulator:main",
        ]
    },
    package_data={
        "tranzact": ["pyinstaller.spec"],
        "": ["*.clvm", "*.clvm.hex", "*.clib", "*.clinc", "*.clsp", "py.typed"],
        "tranzact.util": ["initial-*.yaml", "english.txt"],
        "tranzact.ssl": ["tranzact_ca.crt", "tranzact_ca.key", "dst_root_ca.pem"],
        "mozilla-ca": ["cacert.pem"],
    },
    use_scm_version={"fallback_version": "unknown-no-.git-directory"},
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    zip_safe=False,
)


if __name__ == "__main__":
    setup(**kwargs)
