import logging
import time
import json

from discord.ext import commands

import storcord
import config

logging.basicConfig(level=logging.DEBUG)
logging.getLogger('discord').setLevel(logging.INFO)
logging.getLogger('websockets').setLevel(logging.INFO)

log = logging.getLogger(__name__)

def gay_only():
    return commands.check(lambda m: m.author.id in \
        (162819866682851329, 97104885337575424, 150745989836308480))


class StorcordBot(commands.Bot):
    def __init__(self, *args, **kwargs):
        super().__init__(*args,**kwargs)

        self.storcord = storcord.StorcordClient(self, \
            config.storcord_guild, config.storcord_collections)

    async def on_ready(self):
        log.info(f'Logged in! {self.user!s}')
        await self.storcord.ready()

    async def on_message(self, message):
        author = message.author
        if author.bot: return

        try:
            guild = message.guild
        except AttributeError:
            # in a DM
            return

        ctx = await self.get_context(message)
        await self.invoke(ctx)

bot = StorcordBot(description='im shit', command_prefix='stor!')

@bot.command()
async def ping(ctx):
    """pinge!"""
    t1 = time.monotonic()
    m = await ctx.send('.')
    t2 = time.monotonic()
    delta = round((t2 - t1) * 1000, 2)
    await m.edit(content=f'{delta}ms')

@bot.command()
@gay_only()
async def insert(ctx, *, data: str):
    """Insert a document."""
    try:
        j = json.loads(data)
    except:
        return await ctx.send('Failed to parse JSON')

    res = await ctx.bot.storcord.insert_one(j)
    await ctx.send(res)

@bot.command()
async def idxdb(ctx):
    """Show IndexDB."""
    await ctx.send(repr(ctx.bot.storcord.indexdb))

@bot.command()
@gay_only()
async def saveidxdb(ctx):
    """Save IndexDB."""
    await ctx.bot.storcord.save_indexdb()
    await ctx.send('ok')

@bot.command()
async def squery(ctx, *, raw: str):
    """Make a simple query"""
    try:
        raw = json.loads(raw)
    except:
        raw = {'raw': raw}

    res = await ctx.bot.storcord.simple_query(raw)
    await ctx.send(repr(res))

@bot.command()
@gay_only()
async def sdel(ctx, *, raw: str):
    """Delete a document through simple query.
    
    Equals to deleteOne from Mongo.
    """
    try:
        raw = json.loads(raw)
    except:
        raw = {'raw': raw}

    res = await ctx.bot.storcord.delete_one(raw)
    await ctx.send(repr(res))


bot.load_extension('exec')
bot.run(config.token)

