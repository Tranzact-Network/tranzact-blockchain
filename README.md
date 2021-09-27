# tranzact-blockchain

![Alt text](https://tranzact.network/images/logo.png)

Current Release/tranzact
        :---:          
[![Windows Installer on Windows 10 and Python 3.7](https://github.com/Tranzact-Network/tranzact-blockchain/actions/workflows/build-windows-installer.yml/badge.svg)](https://github.com/Tranzact-Network/tranzact-blockchain/actions/workflows/build-windows-installer.yml)  


Tranzact is a modern cryptocurrency forked from Chia&reg;, designed to be efficient, decentralized, and secure. Here are some of the features and benefits:
* [Proof of space and time](https://docs.google.com/document/d/1tmRIb7lgi4QfKkNaxuKOBHRmwbVlGL4f7EsBDr_5xZE/edit) based consensus which allows anyone to farm with commodity hardware
* Very easy to use full node and farmer GUI and cli (thousands of nodes active on mainnet)
* Simplified UTXO based transaction model, with small on-chain state
* Lisp-style Turing-complete functional [programming language](https://chialisp.com/) for money related use cases
* BLS keys and aggregate signatures (only one signature per block)
* [Pooling protocol](https://github.com/Tranzact-Network/tranzact-blockchain/wiki/Pooling-User-Guide) that allows farmers to have control of making blocks
* Support for light clients with fast, objective syncing
* A growing community of farmers and developers around the world

Please check out the [wiki](https://github.com/Tranzact-Network/tranzact-blockchain/wiki)
and [FAQ](https://github.com/Tranzact-Network/tranzact-blockchain/wiki/FAQ) for
information on this project.

Python 3.7+ is required. Make sure your default python version is >=3.7
by typing `python3`.

If you are behind a NAT, it can be difficult for peers outside your subnet to
reach you when they start up. You can enable
[UPnP](https://www.homenethowto.com/ports-and-nat/upnp-automatic-port-forward/)
on your router or add a NAT (for IPv4 but not IPv6) and firewall rules to allow
TCP port 8655 access to your peer.
These methods tend to be router make/model specific.

Most users should only install harvesters, farmers, plotter, full nodes, and wallets.
Building Timelords and VDFs is for sophisticated users, in most environments.
Tranzact Network and additional volunteers are running sufficient Timelords
for consensus.

## Installing

Install instructions are available in the
[INSTALL](https://github.com/Tranzact-Network/tranzact-blockchain/wiki/INSTALL)
section of the
[tranzact-blockchain repository wiki](https://github.com/Tranzact-Network/tranzact-blockchain/wiki).

## Running

Once installed, a
[Quick Start Guide](https://github.com/Tranzact-Network/tranzact-blockchain/wiki/Quick-Start-Guide)
is available from the repository
[wiki](https://github.com/Tranzact-Network/tranzact-blockchain/wiki).

## For Chia Farmers that want to join us

You can farm Tranzact using OG anf NFT Chia&reg; plots. And we would love to have you! 

However, in order to farm your Chia&reg; plots on this or any other fork, you are required to enter the mnemonic seed of the private key that you created those Chia&reg; plots with.

If you have been farming to the same wallet of the private key that your plots were created with, as a precaution, and before farming any Chia&reg; fork, you should do the following. 

1. Create a new Chia&reg; private key (which will create a new wallet).
2. Move the XCH in the old wallet to the newly created wallet.
3. Set the farming reward address in (home)/.chia/mainnet/config/config.yaml to the new wallet address and restart your Chia&reg; services.

This will ensure that even if someone gets your mnemonic seed they would have no XCH to steal, and technically could only use it to farm your plots.

We suggest anyone that is farming other forks do the same with those wallets.

We support Off Chain NFT plots in the same manner as Flax and other forks, in that if you win a block with an NFT plot, you will get the .25 reward immediately.  The .75 remaining reward will be able to be claimed after a 7 day waiting period.  This waiting period is baked into the pooling contract.

We are currently working on a GUI and CLI addition that will show pending and claimable rewards from NFT plots.  Until that is complete we will most likely be using the [alltheblocks.net](https://alltheblocks.net/) online NFT claiming service.

# If you are farming the Maize fork:

We were informed by a user that we had some internal colliding ports with the Maize fork.  Unfortunately one of those collisions was with our full node port 8655 and Maize's rpc port. This collision will not allow you to connect to tranzact peers while running the Maize full node.  

Therefore, if you want to mine Maize alongside our fork, please use the following workaround.

1. Make sure you have updated Tranzact to the newest version.
2. Stop all Tranzact and Maize services "pkill tranzact && pkill maize"
3. Open the Maize config file (home)/.maize/mainnet/config/config.yaml
4. Find and replace 8655 with 8677 in the config.yaml file
5. Start all Tranzact services "tranzact start all".
6. Start all Maize services "maize start all".