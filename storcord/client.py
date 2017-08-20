import random
import logging
import json
import hashlib
import os

import collections
import json

from collections import namedtuple

import discord

from .enums import DocumentType
from .collection import Collection
from .document import FullDocument

log = logging.getLogger(__name__)

InsertResult = namedtuple('InsertResult', 'inserted doc')
UpdateResult = namedtuple('UpdateResult', 'updated')
DeleteResult = namedtuple('DeleteResult', 'deleted')

IDX_SIZE = 5
IDX_EMPTY_CHUNK = '\N{CJK UNIFIED IDEOGRAPH-6969}'

def yield_chunks(l, n):
    """Yield successive n-sized chunks from l."""
    for i in range(0, len(l), n):
        yield l[i:i + n]

class StorcordClient:
    """Main storcord client class.
    
    Attributes
    ----------
    bot: `bot instance`
        Bot instance to be used by the client.
    guild_id: int
        Guild that is used by the client to store its data.
    idx_message: List[int]
        List of IndexDB messages to edit.
    config_total_colls: int
        Total amount of collections to create by default when running
        :meth:`StorcordClient.init`.
    """
    def __init__(self, bot, guild_id, total_colls):
        self.bot = bot
        self.guild_id = guild_id

        self.idx_messages = []
        self.config_total_colls = total_colls

    async def create_indexdb(self):
        """Create an empty IndexDB."""
        self.indexdb = {}
        idxdb = await self.guild.create_text_channel('indexdb')

        start = await idxdb.send('{}')
        self.idx_messages.append(start)

        for i in range(IDX_SIZE - 1):
            m = await idxdb.send(IDX_EMPTY_CHUNK)
            self.idx_messages.append(m)

        for coll in self.collections:
            self.indexdb[coll.id] = []

        log.info('Created IndexDB')

    async def load_indexdb(self):
        """Load the IndexDB with data from its channel."""
        self.indexdb = collections.defaultdict(list)

        for coll in self.collections:
            self.indexdb[coll.id] = []

        indexdb_chan = discord.utils.get(self.guild.channels, name='indexdb')
        indexdb_data = []

        async for message in indexdb_chan.history(limit=IDX_SIZE, reverse=True):
            if message.content.startswith(IDX_EMPTY_CHUNK):
                continue

            indexdb_data.append(message.content)
            self.idx_messages.append(message)

        log.debug('%d chunks', len(indexdb_data))
        indexdb_data = ''.join(indexdb_data)

        log.debug('raw indexdb %r', indexdb_data)
        indexdb_raw = json.loads(indexdb_data)

        for chan_id, msgs in indexdb_raw.items():
            chan_id = int(chan_id)
            self.indexdb[chan_id] = msgs

        log.info('Loaded IndexDB')

    async def save_indexdb(self):
        """Save the IndexDB to its respective channel."""
        indexdb_json = json.dumps(self.indexdb)
        indexdb_chan = discord.utils.get(self.guild.channels, name='indexdb')

        cur = 0
        for chunk in yield_chunks(indexdb_json, 2000):
            if cur > IDX_SIZE:
                log.warning('INDEXDB TOO BIG')

            try:
                chunk_msg = self.idx_messages[cur]
                await chunk_msg.edit(content=chunk)
            except IndexError:
                chunk_msg = await indexdb_chan.send(chunk)
                self.idx_messages.append(chunk_msg)

            cur += 1

        log.info('Saved indexDB')

    async def ready(self):
        """To be called when your bot's cache is considered
        ready for use."""

        log.info('READYing...')

        self.guild = self.bot.get_guild(self.guild_id)
        if self.guild is None:
            raise RuntimeError('Guild not found')

        # init collections
        self.collections = []
        collections = list(filter(lambda c: c.name.startswith('collection'), self.guild.channels))

        if len(collections) < 1:
            log.debug('Initializing DB from %r', collections)
            await self.init()
            return

        for chan in collections:
            coll = Collection(self, chan)
            self.collections.append(coll)

        await self.load_indexdb()
        log.info('Finished READY')

    async def create_collection(self):
        """Create a collection."""
        chan_name = f'collection-{hashlib.md5(os.urandom(100)).hexdigest()[:10]}'
        chan = await self.guild.create_text_channel(chan_name)

        coll = Collection(self, chan)
        self.collections.append(coll)
        return True

    async def init(self):
        """Used for DB initialization."""
        self.guild = self.bot.get_guild(self.guild_id)

        colls = self.collections
        self.collections = []
        for i in range(self.config_total_colls):
            await self.create_collection()

        await self.create_indexdb()

    async def insert_one(self, raw_doc):
        """Insert a document in a random collection.
        
        Parameters
        ----------
        raw_doc: dict
            Raw document data to be inserted.

        """
        # wrap it up in a full document, for now
        m_content = json.dumps({
            '_type': DocumentType.FULL,
            'raw': json.dumps(raw_doc),
        })
        doc = FullDocument(namedtuple('NotAMessage', 'content id')(m_content, -1))

        # choose a random collection
        coll = random.choice(self.collections)
        doc.coll = coll

        try:
            await coll.insert(doc)
            return InsertResult(1, doc)
        except:
            log.exception('shit')
            return InsertResult(0, None)

    async def simple_query(self, query: dict) -> 'Document':
        """Query all the collections for a document matching
        the data described in ``query``.
        
        Paremeters
        ----------
        query: dict
            Query object.
            If it has an ``_id`` field, it checks in `IndexDB` if
                an ID exists and gets it through :meth:`Collection.get_single`.

            If not, gets passed to :meth:`Collection.simple_query`.
        """
        if '_id' in query:
            wanted = int(query['_id'])

            for chan_id, msgs in self.indexdb.items():
                try:
                    msgs.index(wanted)

                    # TODO: not be lazy and do _get or something
                    coll = [c for c in self.collections if c.id == chan_id][0]
                    return await coll.get_single(wanted)
                except ValueError:
                    pass

            return

        for coll in self.collections:
            doc = await coll.simple_query(query)
            if doc is not None:
                return doc

        return None

    async def multiple_query(self, query: dict) -> list:
        """Query multiple documents."""
        results = []
        for coll in self.collections:
            docs = await coll.multiple_query(query)
            results += docs

        return results

    async def update_one(self, query, set_on_doc):
        doc = await self.simple_query(query)
        if doc is None:
            return UpdateResult(0)
        
        doc.update(set_on_doc)

        if len(newdoc.to_raw_json) > 2000:
            return UpdateResult(0, 'New document cant be sharded, yet.')
            #shard = ShardedDocument(newdoc.raw)
            #await self.insert_shard(shard)
            #await doc.delete()
            #return UpdateResult(!)

        await doc.update(set_on_doc)
        return UpdateResult(1)

    async def delete_one(self, query):
        doc = await self.simple_query(query)
        if doc is None:
            return DeleteResult(0)

        coll = [c for c in self.collections if c.id == doc.message.channel.id][0]
        await coll.delete(doc)
        return DeleteResult(1)



