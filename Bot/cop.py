# Importing Required Dependencies
import discord
from discord.ext import commands, tasks
import json
import asyncio
from datetime import timedelta
from itertools import cycle
import random as rand


# Getting the bot's token from the env variable

TOKEN = "PUT_YOUR_TOKEN_HERE"

# Setup
client = commands.Bot(command_prefix='.', intents=discord.Intents.all())
client.remove_command("help")

#########################
# THE COMMANDS
#########################

# Check if the member running the command has the required permission
def has_permission(ctx):
    return ctx.author.guild_permissions.kick_members

# Command check decorator
def has_permissions_check():
    def predicate(ctx):
        return has_permission(ctx)
    return commands.check(predicate)

status = cycle(['You!', "Everyone!"])

@client.event
async def on_ready():
  change_status.start()
  print("Your bot is ready")

@tasks.loop(seconds=30)
async def change_status():
  await client.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name=next(status)))

@client.command(name="ping")
async def ping(ctx):
    await ctx.send("Pong!")

# Warn Command
@client.command()
@has_permissions_check()
async def warn(ctx, member: discord.Member, intensity: str, *, reason: str = "No reason provided."):
    intensity_levels = ['low', 'med', 'high']
    if intensity.lower() not in intensity_levels:
        await ctx.send(f"Invalid intensity level. Please choose from: {', '.join(intensity_levels)}.")
        return

    # Get the warns data
    user_id = str(member.id)
    username = member.name
    warns_data = load_warns_from_json()

    # Increment the warn count for the specified intensity level
    user_warns = warns_data.setdefault(user_id, {}).setdefault(username, {}).get('warns', {})
    user_warns[intensity.lower()] = user_warns.get(intensity.lower(), 0) + 1

    # Save the updated warns to the JSON file
    warns_data[user_id][username]['warns'] = user_warns
    save_warns_to_json(warns_data)

    await ctx.send(f"Warned: {member.mention}, intensity: {intensity}, for: {reason}!")

    # Apply the time-out based on intensity level
    if intensity.lower() == "med":
        timeout_role = discord.utils.get(ctx.guild.roles, name="Timeout")
        await member.add_roles(timeout_role)
        await asyncio.sleep(600)  # 10 minutes timeout
        await member.remove_roles(timeout_role)
    elif intensity.lower() == "high":
        timeout_role = discord.utils.get(ctx.guild.roles, name="Timeout")
        await member.add_roles(timeout_role)
        await asyncio.sleep(timedelta(days=1).total_seconds())  # 1-day timeout
        await member.remove_roles(timeout_role)

# Warns Command
@client.command()
@has_permissions_check()
async def warns(ctx, member: discord.Member):
    # Get the warns data
    user_id = str(member.id)
    username = member.name
    warns_data = load_warns_from_json()
    user_warns = warns_data.get(user_id, {}).get(username, {}).get('warns', {})

    if not user_warns:
        await ctx.send(f"{member.mention} has no warns.")
        return

    # Prepare the warns message
    warns_message = f"{member.name}'s Warns:\n"
    for intensity, count in user_warns.items():
        warns_message += f"> {intensity.capitalize()}: {count}\n"

    await ctx.send(warns_message)

# JSON helper functions
def save_warns_to_json(data):
    with open('warns.json', 'w') as f:
        json.dump(data, f, indent=4)

def load_warns_from_json():
    try:
        with open('warns.json', 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

# Kick Command
@client.command()
@has_permissions_check()
async def kick(ctx, member: discord.Member, reason=None):
    await member.kick(reason=reason)
    await ctx.send(f"Kicked {member.name}. Reason: {reason}")

# Ban Command
@client.command()
@has_permissions_check()
async def ban(ctx, member: discord.Member, *, reason=None):
    await member.ban(reason=reason)
    await ctx.send(f"Banned {member.name}. Reason: {reason}")

# Purge Command
@client.command()
@has_permissions_check()
async def purge(ctx, amount: int):
    if amount <= 0:
        await ctx.send("Please provide a positive non-zero number to purge.")
        return

    # Fetch the messages to delete
    messages = [msg async for msg in ctx.channel.history(limit=amount + 1)]

    # Delete the messages
    await ctx.channel.delete_messages(messages)

    # Send the "Purged by" message and delete it after 5 seconds
    purged_by_message = await ctx.send(f"Purged by {ctx.author.mention}")
    await asyncio.sleep(5)
    await purged_by_message.delete()

@client.command()
@commands.has_permissions(manage_channels = True)
async def lock(ctx):
    await ctx.channel.set_permissions(ctx.guild.default_role, send_messages=False)
    await ctx.send( ctx.channel.mention + " ***is now in lockdown.***")

@client.command()
@commands.has_permissions(manage_channels=True)
async def unlock(ctx):
    await ctx.channel.set_permissions(ctx.guild.default_role, send_messages=True)
    await ctx.send(ctx.channel.mention + " ***has been unlocked.***")
    

@client.command(name="peppo")
async def peppo(ctx):
  emojis = ["<:peepoSad:1132647291849822270>", "<:Heyge:1132647418240958484>", "<:peepo_mean:1132647457067651082>", "<:PepeChadge:1132647537187242124>", "<:peepoBlush:1132647637410136064>"]
  emoji = rand.choice(emojis)
  await ctx.send("Here ya go:")
  await ctx.send(emoji)

@client.group(invoke_without_command=True)
async def help(ctx, *, type=None):
    if type is None:
        em = discord.Embed(title="Help", description="Type '.<category>' to see all the commands!", color=ctx.author.color)
        em.add_field(name='Categories:', value='Fun\nModeration')
    elif type.lower() == 'fun':
        em = discord.Embed(title='Fun Commands', description="Some random funish commands", color=ctx.author.color)
        em.add_field(name='.peppo', value='Sends a random pepe emoji\n**Syntax:** .peppo')
    elif type.lower() == 'moderation':
        em = discord.Embed(title="Moderation Commands", description="Server moderation tools", color=ctx.author.color)
        em.add_field(name='.warn', value='Warns a member\n**Syntax:** .warn <member> [intensity: low/med/high] [reason]', inline=False)
        em.add_field(name='.kick', value='Kicks a member\n**Syntax:** .kick <member> [reason]', inline=False)
        em.add_field(name='.ban', value='Bans a member\n**Syntax:** .ban <member> [reason]', inline=False)
        em.add_field(name='.purge', value='Deletes specified amount of messages\n**Syntax:** .purge <amount>', inline=False)
        em.add_field(name='.lock', value='Locks the requested channel\n**Syntax:** .lock', inline=False)
        em.add_field(name='.unlock', value='Unlocks a currently locked channel\n**Syntax:** .unlock', inline=False)
    else:
        em = discord.Embed(title="Invalid Category", description="The specified category is not recognized.", color=discord.Color.red())
    
    em.set_footer(text=":]")
    await ctx.send(embed=em)


    
    
# Run The Bot!!!!
try:
  client.run(TOKEN)
except Exception as e:
  print(e)
