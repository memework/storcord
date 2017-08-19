import json

class Collection:
    def __init__(self, client, channel):
        self.chan = channel
        self.client = client

    def __repr__(self):
        return f'Collection({self.chan!r})'

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
            # search by objectID
            wanted = query['_id']
            if wanted[0] != self.chan.id:
                return

            m = await self.chan.get_message(wanted[1])
            if m is not None:
                return FullDocument(json.loads(m.content))
            return

        if 'raw' in query:
            # Search raw-y
            raw = query['raw']

            for (chan_id, message_id) in self.client.indexdb[self.chan.id]:
                m = await self.chan.get_message(message_id)
                if raw in m.content:
                    return FullDocument(json.loads(m.content))

            return

        # search by JSON, the most expensive
        for (chan_id, message_id) in self.client.indexdb[self.chan.id]:
            m = await self.chan.get_message(message_id)
            if m is not None:
                doc = FullDocument(json.loads(m.content))
                if doc.match(query):
                    return doc
        return

    async def insert(self, document):
        m = await self.chan.send(document.to_raw)
        self.client.indexdb[self.chan.id].append((self.chan.id, m.id))

