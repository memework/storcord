from discord.ext import commands

import config

class StorcordBot(commands.Bot):
    async def query(self, query):
        pass

    async def write(self, data):
        pass

bot = StorcordBot(description='im shit', command_prefix='stor!')

@bot.command()
async def ping(ctx):
    t1 = time.monotonic()
    m = await ctx.send('.')
    t2 = time.monotonic()
    delta = round((t2 - t1) * 1000, 2)
    await m.edit(content=f'{delta}ms')

bot.run(config.token)

