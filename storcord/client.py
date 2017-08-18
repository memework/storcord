import random
import logging
import json

from collections import namedtuple


from .enums import DocumentType
from .collection import Collection
from .document import FullDocument

log = logging.getLogger(__name__)

InsertResult = namedtuple('InsertResult', 'inserted')
UpdateResult = namedtuple('UpdateResult', 'updated')
DeleteResult = namedtuple('DeleteResult', 'deleted')

class StorcordClient:
    def __init__(self, bot, guild_id, collections):
        self.bot = bot
        self.guild_id = guild_id
        self.collection_ids = collections

    async def ready(self):
        """To be called when your bot's cache is considered
        ready for use."""

        self.guild = self.bot.get_guild(self.guild_id)
        if self.guild is None:
            raise RuntimeError('Guild not found')

        # init collections
        self.collections = []
        for channel_id in self.collection_ids:
            chan = self.bot.get_channel(channel_id)
            if chan is None:
                log.warning('Collection ID %d not found', channel_id)
                return

            coll = Collection(self, chan)
            self.collections.append(coll)

    async def create_collection(self):
        chan_name = f'coll-{hashlib.md5(os.urandom(100)).hexdigest()[:8]}'
        chan = await self.guild.create_channel(chan_name)

        coll = Collection(self, chan)
        self.collections.append(coll)
        return True
    
    async def insert_one(self, raw_doc):
        # wrap it up in a full document, for now
        doc = Document({
            '_type': DocumentTypes.FULL,
            'raw': json.dumps(raw_doc),
        })

        # choose a random collection
        coll = random.choice(self.collections)
        doc.coll = coll
        await coll.insert(doc)

    async def simple_query(self, query):
        for coll in self.collections:
            doc = await coll.simple_query(query)
            if doc is not None:
                return doc

        return None

    async def update_one(self, query, set_on_doc):
        doc = await self.simple_query(query)
        if doc is None:
            return UpdateResult(0)
        
        newdoc = FullDocument({**doc.as_json, **set_on_doc})

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

        await doc.delete()
        return DeleteResult(1)

    async def multiple_query(self, query):
        pass


