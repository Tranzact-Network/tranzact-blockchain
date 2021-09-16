from typing import List, Optional

import aiosqlite

from tranzact.types.blockchain_format.coin import Coin
from tranzact.types.blockchain_format.sized_bytes import bytes32
from tranzact.types.coin_record import CoinRecord
from tranzact.types.full_block import FullBlock
from tranzact.util.db_wrapper import DBWrapper
from tranzact.util.ints import uint32, uint64
from tranzact.util.lru_cache import LRUCache

#tranzact additional imports
from tranzact.types.blockchain_format.program import Program, SerializedProgram
import aiohttp
import asyncio
import ssl

class CoinStore:
    """
    This object handles CoinRecords in DB.
    A cache is maintained for quicker access to recent coins.
    """

    coin_record_db: aiosqlite.Connection
    coin_record_cache: LRUCache
    cache_size: uint32
    db_wrapper: DBWrapper

    @classmethod
    async def create(cls, db_wrapper: DBWrapper, cache_size: uint32 = uint32(60000)):
        self = cls()

        self.cache_size = cache_size
        self.db_wrapper = db_wrapper
        self.coin_record_db = db_wrapper.db
        await self.coin_record_db.execute("pragma journal_mode=wal")
        await self.coin_record_db.execute("pragma synchronous=2")
        await self.coin_record_db.execute(
            (
                "CREATE TABLE IF NOT EXISTS coin_record("
                "coin_name text PRIMARY KEY,"
                " confirmed_index bigint,"
                " spent_index bigint,"
                " spent int,"
                " coinbase int,"
                " puzzle_hash text,"
                " coin_parent text,"
                " amount blob,"
                " timestamp bigint)"
            )
        )

        # Useful for reorg lookups
        await self.coin_record_db.execute(
            "CREATE INDEX IF NOT EXISTS coin_confirmed_index on coin_record(confirmed_index)"
        )

        await self.coin_record_db.execute("CREATE INDEX IF NOT EXISTS coin_spent_index on coin_record(spent_index)")

        await self.coin_record_db.execute("CREATE INDEX IF NOT EXISTS coin_spent on coin_record(spent)")

        await self.coin_record_db.execute("CREATE INDEX IF NOT EXISTS coin_puzzle_hash on coin_record(puzzle_hash)")

        await self.coin_record_db.commit()
        self.coin_record_cache = LRUCache(cache_size)
        return self

    async def new_block(self, block: FullBlock, tx_additions: List[Coin], tx_removals: List[bytes32]):
        """
        Only called for blocks which are blocks (and thus have rewards and transactions)
        """
        if block.is_transaction_block() is False:
            return None
        assert block.foliage_transaction_block is not None

        for coin in tx_additions:
            record: CoinRecord = CoinRecord(
                coin,
                block.height,
                uint32(0),
                False,
                False,
                block.foliage_transaction_block.timestamp,
            )
            await self._add_coin_record(record, False)

        included_reward_coins = block.get_included_reward_coins()
        if block.height == 0:
            assert len(included_reward_coins) == 0
        else:
            assert len(included_reward_coins) >= 2

        for coin in included_reward_coins:
            reward_coin_r: CoinRecord = CoinRecord(
                coin,
                block.height,
                uint32(0),
                False,
                True,
                block.foliage_transaction_block.timestamp,
            )
            await self._add_coin_record(reward_coin_r, False)

        total_amount_spent: int = 0
        for coin_name in tx_removals:
            total_amount_spent += await self._set_spent(coin_name, block.height)

        # Sanity check, already checked in block_body_validation
        assert sum([a.amount for a in tx_additions]) <= total_amount_spent

    # Checks DB and DiffStores for CoinRecord with coin_name and returns it
    async def get_coin_record(self, coin_name: bytes32) -> Optional[CoinRecord]:
        cached = self.coin_record_cache.get(coin_name)
        if cached is not None:
            return cached
        cursor = await self.coin_record_db.execute("SELECT * from coin_record WHERE coin_name=?", (coin_name.hex(),))
        row = await cursor.fetchone()
        await cursor.close()
        if row is not None:
            coin = Coin(bytes32(bytes.fromhex(row[6])), bytes32(bytes.fromhex(row[5])), uint64.from_bytes(row[7]))
            record = CoinRecord(coin, row[1], row[2], row[3], row[4], row[8])
            self.coin_record_cache.put(record.coin.name(), record)
            return record
        return None

    async def get_coins_added_at_height(self, height: uint32) -> List[CoinRecord]:
        cursor = await self.coin_record_db.execute("SELECT * from coin_record WHERE confirmed_index=?", (height,))
        rows = await cursor.fetchall()
        await cursor.close()
        coins = []
        for row in rows:
            coin = Coin(bytes32(bytes.fromhex(row[6])), bytes32(bytes.fromhex(row[5])), uint64.from_bytes(row[7]))
            coins.append(CoinRecord(coin, row[1], row[2], row[3], row[4], row[8]))
        return coins

    async def get_coins_removed_at_height(self, height: uint32) -> List[CoinRecord]:
        cursor = await self.coin_record_db.execute("SELECT * from coin_record WHERE spent_index=?", (height,))
        rows = await cursor.fetchall()
        await cursor.close()
        coins = []
        for row in rows:
            spent: bool = bool(row[3])
            if spent:
                coin = Coin(bytes32(bytes.fromhex(row[6])), bytes32(bytes.fromhex(row[5])), uint64.from_bytes(row[7]))
                coin_record = CoinRecord(coin, row[1], row[2], spent, row[4], row[8])
                coins.append(coin_record)
        return coins

    # Checks DB and DiffStores for CoinRecords with puzzle_hash and returns them
    async def get_coin_records_by_puzzle_hash(
        self,
        include_spent_coins: bool,
        puzzle_hash: bytes32,
        start_height: uint32 = uint32(0),
        end_height: uint32 = uint32((2 ** 32) - 1),
    ) -> List[CoinRecord]:

        coins = set()
        cursor = await self.coin_record_db.execute(
            f"SELECT * from coin_record INDEXED BY coin_puzzle_hash WHERE puzzle_hash=? "
            f"AND confirmed_index>=? AND confirmed_index<? "
            f"{'' if include_spent_coins else 'AND spent=0'}",
            (puzzle_hash.hex(), start_height, end_height),
        )
        rows = await cursor.fetchall()

        await cursor.close()
        for row in rows:
            coin = Coin(bytes32(bytes.fromhex(row[6])), bytes32(bytes.fromhex(row[5])), uint64.from_bytes(row[7]))
            coins.add(CoinRecord(coin, row[1], row[2], row[3], row[4], row[8]))
        return list(coins)

    async def get_coin_records_by_puzzle_hashes(
        self,
        include_spent_coins: bool,
        puzzle_hashes: List[bytes32],
        start_height: uint32 = uint32(0),
        end_height: uint32 = uint32((2 ** 32) - 1),
    ) -> List[CoinRecord]:
        if len(puzzle_hashes) == 0:
            return []

        coins = set()
        puzzle_hashes_db = tuple([ph.hex() for ph in puzzle_hashes])
        cursor = await self.coin_record_db.execute(
            f"SELECT * from coin_record INDEXED BY coin_puzzle_hash "
            f'WHERE puzzle_hash in ({"?," * (len(puzzle_hashes_db) - 1)}?) '
            f"AND confirmed_index>=? AND confirmed_index<? "
            f"{'' if include_spent_coins else 'AND spent=0'}",
            puzzle_hashes_db + (start_height, end_height),
        )

        rows = await cursor.fetchall()

        await cursor.close()
        for row in rows:
            coin = Coin(bytes32(bytes.fromhex(row[6])), bytes32(bytes.fromhex(row[5])), uint64.from_bytes(row[7]))
            coins.add(CoinRecord(coin, row[1], row[2], row[3], row[4], row[8]))
        return list(coins)

    async def get_coin_records_by_names(
        self,
        include_spent_coins: bool,
        names: List[bytes32],
        start_height: uint32 = uint32(0),
        end_height: uint32 = uint32((2 ** 32) - 1),
    ) -> List[CoinRecord]:
        if len(names) == 0:
            return []

        coins = set()
        names_db = tuple([name.hex() for name in names])
        cursor = await self.coin_record_db.execute(
            f'SELECT * from coin_record WHERE coin_name in ({"?," * (len(names_db) - 1)}?) '
            f"AND confirmed_index>=? AND confirmed_index<? "
            f"{'' if include_spent_coins else 'AND spent=0'}",
            names_db + (start_height, end_height),
        )

        rows = await cursor.fetchall()

        await cursor.close()
        for row in rows:
            coin = Coin(bytes32(bytes.fromhex(row[6])), bytes32(bytes.fromhex(row[5])), uint64.from_bytes(row[7]))
            coins.add(CoinRecord(coin, row[1], row[2], row[3], row[4], row[8]))
        return list(coins)

    async def get_coin_records_by_parent_ids(
        self,
        include_spent_coins: bool,
        parent_ids: List[bytes32],
        start_height: uint32 = uint32(0),
        end_height: uint32 = uint32((2 ** 32) - 1),
    ) -> List[CoinRecord]:
        if len(parent_ids) == 0:
            return []

        coins = set()
        parent_ids_db = tuple([pid.hex() for pid in parent_ids])
        cursor = await self.coin_record_db.execute(
            f'SELECT * from coin_record WHERE coin_parent in ({"?," * (len(parent_ids_db) - 1)}?) '
            f"AND confirmed_index>=? AND confirmed_index<? "
            f"{'' if include_spent_coins else 'AND spent=0'}",
            parent_ids_db + (start_height, end_height),
        )

        rows = await cursor.fetchall()

        await cursor.close()
        for row in rows:
            coin = Coin(bytes32(bytes.fromhex(row[6])), bytes32(bytes.fromhex(row[5])), uint64.from_bytes(row[7]))
            coins.add(CoinRecord(coin, row[1], row[2], row[3], row[4], row[8]))
        return list(coins)

    async def rollback_to_block(self, block_index: int):
        """
        Note that block_index can be negative, in which case everything is rolled back
        """
        # Update memory cache
        delete_queue: bytes32 = []
        for coin_name, coin_record in list(self.coin_record_cache.cache.items()):
            if int(coin_record.spent_block_index) > block_index:
                new_record = CoinRecord(
                    coin_record.coin,
                    coin_record.confirmed_block_index,
                    uint32(0),
                    False,
                    coin_record.coinbase,
                    coin_record.timestamp,
                )
                self.coin_record_cache.put(coin_record.coin.name(), new_record)
            if int(coin_record.confirmed_block_index) > block_index:
                delete_queue.append(coin_name)

        for coin_name in delete_queue:
            self.coin_record_cache.remove(coin_name)

        # Delete from storage
        c1 = await self.coin_record_db.execute("DELETE FROM coin_record WHERE confirmed_index>?", (block_index,))
        await c1.close()
        c2 = await self.coin_record_db.execute(
            "UPDATE coin_record SET spent_index = 0, spent = 0 WHERE spent_index>?",
            (block_index,),
        )
        await c2.close()

    # Store CoinRecord in DB and ram cache
    async def _add_coin_record(self, record: CoinRecord, allow_replace: bool) -> None:
        if self.coin_record_cache.get(record.coin.name()) is not None:
            self.coin_record_cache.remove(record.coin.name())

        cursor = await self.coin_record_db.execute(
            f"INSERT {'OR REPLACE ' if allow_replace else ''}INTO coin_record VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                record.coin.name().hex(),
                record.confirmed_block_index,
                record.spent_block_index,
                int(record.spent),
                int(record.coinbase),
                str(record.coin.puzzle_hash.hex()),
                str(record.coin.parent_coin_info.hex()),
                bytes(record.coin.amount),
                record.timestamp,
            ),
        )
        await cursor.close()

    # Update coin_record to be spent in DB
    async def _set_spent(self, coin_name: bytes32, index: uint32) -> uint64:
        current: Optional[CoinRecord] = await self.get_coin_record(coin_name)
        if current is None:
            raise ValueError(f"Cannot spend a coin that does not exist in db: {coin_name}")

        assert not current.spent  # Redundant sanity check, already checked in block_body_validation
        spent: CoinRecord = CoinRecord(
            current.coin,
            current.confirmed_block_index,
            index,
            True,
            current.coinbase,
            current.timestamp,
        )  # type: ignore # noqa
        await self._add_coin_record(spent, True)
        return current.coin.amount

    #tranzact code below
    async def get_nft_coins(self, contract_hash_hex: str, delay:uint64) -> list:
        cursor = await self.coin_record_db.execute(f"SELECT *, CASE WHEN timestamp <= (strftime('%s', 'now') - {delay}) THEN true ELSE false END eligible FROM coin_record WHERE spent == 0 AND puzzle_hash LIKE '{contract_hash_hex}' ORDER BY timestamp DESC")
        coin_records: list = []
        rows = await cursor.fetchall()
        for coin in rows:
            coin_amount: int = int.from_bytes(coin[7], byteorder='big', signed=False)
            if coin_amount > 0:
                coin_records.append(coin)

        await cursor.close()
        return coin_records

    async def fetchData(url, coin_solutions_b, session):
        try:
            async with session.post(
                url, 
                ssl=False,
                json={
                        'spend_bundle': {
                            'aggregated_signature': '0xc00000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000',
                            'coin_solutions': coin_solutions_b
                }}
             ) as response:
                content = await response.read()
                return (url, 'OK', content)
        except Exception as e:
            print(e)
            return (url, 'ERROR', str(e))

    async def rundata(self,coin_solutions, cert_path, cert_key_path, node_host, node_port):
        ssl_ctx = ssl.create_default_context()
        ssl_ctx.check_hostname = False
        ssl_ctx.verify_mode = ssl.CERT_NONE
        ssl_ctx.load_cert_chain(cert_path, cert_key_path)
        conn = aiohttp.TCPConnector(ssl_context=ssl_ctx)
        tasks = []
        async with aiohttp.ClientSession(connector=conn, raise_for_status=True) as session:
            for coin_solutions_b in coin_solutions:
                balance_batch: int = 0
                for coin_solution in coin_solutions_b:
                    balance_batch += coin_solution['coin']['amount']

                task = asyncio.ensure_future(self.fetchData(f'https://{node_host}:{node_port}/push_tx', coin_solutions_b, session))
                tasks.append(task)
                responses = asyncio.gather(*tasks)
                await responses
        return responses

    async def claim_nft_coins(self, contract_hash_hex: str, program_puzzle_hex: str, cert_path:str, cert_key_path:str, node_host:str, node_port:str, delay:uint64) -> dict:
        cursor = await self.coin_record_db.execute(f"SELECT * FROM coin_record WHERE spent == 0 AND timestamp <= (strftime('%s', 'now') - {delay} AND puzzle_hash LIKE '{contract_hash_hex}' ORDER BY timestamp DESC")
        coin_records: list = []
        rows = await cursor.fetchall()
        for coin in rows:
            coin_amount: int = int.from_bytes(coin[7], byteorder='big', signed=False)
            if coin_amount > 0:
                coin_records.append(coin)

        await cursor.close()

        coin_solutions: list[dict] = []
        
        for coin in coin_records:
            coin_parent: str = coin[6]
            coin_amount: int = int.from_bytes(coin[7], byteorder='big', signed=False)

            coin_solution_hex: str = bytes(SerializedProgram.from_program(
                Program.to([uint64(coin_amount), 0])
            )).hex()

            coin_solutions.append({
                'coin': {
                    'amount': coin_amount,
                    'parent_coin_info': coin_parent,
                    'puzzle_hash': contract_hash_hex
                },
                'puzzle_reveal': program_puzzle_hex,
                'solution': coin_solution_hex
            })

        balance_recovered: int = 0

        loop = asyncio.get_event_loop()
        asyncio.set_event_loop(loop)
        task = asyncio.ensure_future(self.rundata(coin_solutions, cert_path, cert_key_path, node_host, node_port))
        loop.run_until_complete(task)
        result = task.result().result()

        return {
                    "success": True,
                    "msg": f'Recovered a total of {balance_recovered / (10 ** 12):.12f} coins.'
                }
