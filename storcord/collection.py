
class Collection:
    def __init__(self, client, channel):
        self.chan = channel
        self.client = client

    async def insert(self, document):
        await self.chan.send(document.to_raw)

