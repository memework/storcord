# Storcord

Storcord is a document-oriented NoSQL manager that uses
Discord as its "main" storage.

## Setting up a database

Creating databases are like creating Discord guilds.
Every guild represents a database and every Discord channel
acts as a "collection"(from Mongo).

## Adding documents

When adding documents, an entry is generated for that document.
A document has to be in JSON(no BSON bullshit from mongo).

A document entry is the document object with metadata about the document.
Those metadata are included in the following fields:
 - `_type`[int]: The type of this entry
   - `0` for an actual document.
   - `1` for a document shard.

### Document Sharding

For documents that their total JSON(plus metadata) gets bigger than 2000 characters,
the document becomes sharded across document shards, each shard has chunks of the actual
JSON encoded document but they have metadata on how to find the other shards so you can
rebuild the entire document witn only one of the shards.

## Querying documents

**TODO: think about it**

## Updating documents

If the document to be updated is a single unsharded document, updating
is easy: edit the message the document is contained in with a new version of it.

 - If the edited version of the document goes over 2000 characters we will have to
 delete the old document and write a new sharded document.

If the document is a sharded document, you can:
 - Easy: Delete all document shards and recreate them.
 - Hard: Edit existing shards and create new shards as required by the document's size.

## Deleting documents

Deleting documents is straightforward.
 - If the document is not sharded, deleting the message the document is contained
 is enough.
 - If the document is sharded, all document shards have to be deleted from their respective channels.

