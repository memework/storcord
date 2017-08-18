import logging

from discord.ext import commands

import storcord
import config

logging.basicConfig(level=logging.DEBUG)
logging.getLogger('discord').setLevel(logging.INFO)
logging.getLogger('websockets').setLevel(logging.INFO)

class StorcordBot(commands.Bot):
    def __init__(self, *args, **kwargs):
        super().__init__(*args,**kwargs)

        self.storcord = storcord.StorcordManager(self, \
            config.storcord_guild, config.storcord_collections)

    async def on_ready(self):
        log.info(f'Logged in! {self.user!s}')
        self.loop.create_task(self.storcord.ready())

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
    t1 = time.monotonic()
    m = await ctx.send('.')
    t2 = time.monotonic()
    delta = round((t2 - t1) * 1000, 2)
    await m.edit(content=f'{delta}ms')

@bot.command()
@bot.is_owner()
async def insert(ctx, *, data: str):
    try:
        j = json.loads(data)
    except:
        return await ctx.send('Failed to parse JSON')

    res = await ctx.bot.storcord.insert_one(j)
    await ctx.send(res)

bot.run(config.token)

