import json
import logging

from .enums import DocumentType

log = logging.getLogger(__name__)


class FullDocument:
    """Represents a single, contained Storcord document"""
    def __init__(self, client, message):
        self.client = client
        self.message = message

        raw = json.loads(message.content)
        self.raw = raw
        self._update(raw)

    def __repr__(self):
        return f'FullDocument(type={self.type}, {self.obj!r})'

    def _update(self, raw):
        self.type = raw['_type']
        if self.type != DocumentType.FULL:
            raise TypeError('Receiving a document entry that is not a full document.')

        self.raw_obj = raw['raw']
        self.obj = json.loads(self.raw_obj)

        # yes, long, i know
        # live with it.
        self.coll = self.client.get_collection(self.message.channel.id)

    def update(self, new_data):
        # We don't really want to allow document type change
        # by updating its _type field.
        try:
            new_data.pop('_type')
        except KeyError: pass
        self.obj.update(new_data)

    async def update_on_coll(self):
        await self.coll.update(self)

    def match(self, query: 'any') -> bool:
        """See if a document matches a certain query."""
        obj_get = self.obj.get

        if isinstance(query, dict):
            return any(query.get(k) == obj_get(k) for k in query)
        elif isinstance(query, list):
            return any(bool(obj_get(key)) for key in query)
        else:
            return bool(obj_get(query))

    @property
    def to_raw(self):
        return {
            '_type': self.type,
            'raw': json.dumps(self.obj),
        }

    @property
    def to_raw_json(self):
        return json.dumps(self.to_raw)

