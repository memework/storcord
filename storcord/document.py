from .enums import DocumentType

class Document:
    """Represents a single, contained Storcord document"""
    def __init__(self, raw):
        self.raw = raw

    def update(self, raw):
        self.id = raw['id']
        self.type = raw['type']

    @property
    def to_raw(self):
        return {
            '_id': self.id,
            '_type': self.type,
        }

