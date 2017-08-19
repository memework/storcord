import json
import logging

from .document import FullDocument

log = logging.getLogger(__name__)

class Collection:
    def __init__(self, client, channel):
        self.id = channel.id
        self.chan = channel
        self.client = client

    def __repr__(self):
        return f'Collection({self.chan!r})'

    async def get_single(self, message_id: int) -> 'Document':
        """Get a single document"""
        message_id = int(message_id)

        m = await self.chan.get_message(message_id)
        if m is not None:
            return FullDocument(m)

        return

    async def simple_query(self, query: dict) -> 'Document':
        """Make a Simple Query to a collection.
        
        Parameters
        ----------
        query: dict
            Query object to the collection.


        Returns
        -------
        FullDocument
            The document found.
        None
            If no documents were found.
        """
        if '_id' in query:
            return await self.get_single(query['_id'])

        if 'raw' in query:
            # Search raw-y
            raw = query['raw']

            for message_id in self.client.indexdb[self.chan.id]:
                m = await self.chan.get_message(message_id)
                if raw in m.content:
                    log.debug(m.content)
                    return FullDocument(m)

            return

        # search by JSON, the most expensive
        for message_id in self.client.indexdb[self.chan.id]:
            m = await self.chan.get_message(message_id)
            if m is not None:
                doc = FullDocument(m)
                if doc.match(query):
                    return doc
        return

    async def insert(self, document):
        m = await self.chan.send(json.dumps(document.to_raw))
        self.client.indexdb[self.chan.id].append(m.id)

    async def delete(self, document):
        try:
            self.client.indexdb[self.id].pop(document.message.id)
        except IndexError:
            pass

        return await document.message.delete()

