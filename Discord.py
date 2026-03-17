import discord
import requests
import os
import asyncio
from discord.ext import commands, tasks
from datetime import datetime, timedelta
from urllib.parse import urlencode

# ================= CONFIGURATION =================
BOT_TOKEN = "(Your bot token
CLIENT_ID = "(Your client id)
CLIENT_SECRET = "(Your Client secret)
MAIN_SERVER_ID = 1480957214733893792
REDIRECT_URI = "https://parrotgames.free.nf/discord-redirect.html"
# =================================================

print("🚀 Starting Bot...")

intents = discord.Intents.all()
intents.message_content = True

bot = commands.Bot(command_prefix='!', intents=intents)
bot.remove_command("help")

server_join_times = {}

@bot.event
async def on_ready():
    print(f'✅ Bot is online as: {bot.user}')
    print(f'🏠 Registered Main Server: {MAIN_SERVER_ID}')
    for guild in bot.guilds:
        if guild.id != MAIN_SERVER_ID:
            server_join_times[guild.id] = datetime.now()
    if not check_server_ages.is_running():
        check_server_ages.start()

@tasks.loop(hours=24)
async def check_server_ages():
    for guild in bot.guilds:
        if guild.id == MAIN_SERVER_ID:
            continue
        join_time = server_join_times.get(guild.id, datetime.now())
        if datetime.now() - join_time >= timedelta(days=14):
            try:
                await guild.leave()
                print(f"🚪 Auto-left server: {guild.name}")
            except:
                pass

@bot.command()
async def help(ctx):
    embed = discord.Embed(title="🤖 Bot Control Panel", color=0x00ff00)
    embed.add_field(name="!get_token", value="Generate the authentication link", inline=False)
    embed.add_field(name="!auth <code>", value="Verify yourself using the provided code", inline=False)
    embed.add_field(name="!djoin <server_id>", value="Make all verified users join a server", inline=False)
    embed.add_field(name="!servers", value="List all servers the bot is currently in", inline=False)
    await ctx.send(embed=embed)

@bot.command()
async def get_token(ctx):
    scopes = "identify guilds.join"
    params = {
        'client_id': CLIENT_ID,
        'response_type': 'code',
        'redirect_uri': REDIRECT_URI,
        'scope': scopes,
        'prompt': 'consent'
    }
    url = f"https://discord.com/oauth2/authorize?{urlencode(params)}"
    await ctx.send(f"🔐 **Verification Link:** [CLICK HERE TO AUTHENTICATE]({url})")

@bot.command()
async def auth(ctx, code: str):
    data = {
        'client_id': CLIENT_ID,
        'client_secret': CLIENT_SECRET,
        'grant_type': 'authorization_code',
        'code': code.strip(),
        'redirect_uri': REDIRECT_URI
    }
    r = requests.post('https://discord.com/api/v10/oauth2/token', data=data)
    if r.status_code == 200:
        res = r.json()
        with open("auths.txt", "a") as f:
            f.write(f"{ctx.author.id},{res['access_token']},{res['refresh_token']}\n")
        await ctx.send(f"✅ {ctx.author.name}, you have been successfully verified!")
    else:
        await ctx.send("❌ Authentication failed. Please check your code or Client Secret.")

@bot.command()
async def djoin(ctx, server_id: str):
    if not os.path.exists('auths.txt'):
        return await ctx.send("❌ No verified users found in the database.")
    
    await ctx.send(f"🚀 Starting mass join for Server ID: `{server_id}`...")
    count = 0
    with open('auths.txt', 'r') as f:
        for line in f:
            parts = line.strip().split(',')
            if len(parts) >= 2:
                uid, token = parts[0], parts[1]
                url = f"https://discord.com/api/v10/guilds/{server_id}/members/{uid}"
                headers = {"Authorization": f"Bot {BOT_TOKEN}"}
                res = requests.put(url, headers=headers, json={"access_token": token})
                if res.status_code in [201, 204]:
                    count += 1
                await asyncio.sleep(1)
    await ctx.send(f"🎯 Operation complete. {count} users joined successfully.")

@bot.command()
async def servers(ctx):
    list_s = "\n".join([f"• {g.name} ({g.id})" for g in bot.guilds])
    await ctx.send(f"🏠 **Current Servers:**\n{list_s if list_s else 'None'}")

if __name__ == "__main__":
    try:
        bot.run(BOT_TOKEN)
    except Exception as e:
        print(f"❌ Critical Error: {e}")

@bot.event
async def on_message(message):
    if message.author == bot.user:
        return
    print(f"📩 Message received: {message.content} from {message.author}")
    await bot.process_commands(message)
