import json
import logging

from .enums import DocumentType

log = logging.getLogger(__name__)


class FullDocument:
    """Represents a single, contained Storcord document"""
    def __init__(self, raw):
        self.raw = raw
        self.update(raw)

    def update(self, raw):
        self.type = raw['_type']
        if self.type != DocumentType.FULL:
            raise TypeError('Receiving a document entry that is not a full document.')

        self.raw_obj = raw['raw']
        self.obj = json.loads(self.raw_obj)

    @property
    def to_raw(self):
        return {
            '_type': self.type,
            'raw': json.dumps(self.obj),
        }

