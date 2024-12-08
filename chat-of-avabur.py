import discord
from discord.ext import commands
from discord import app_commands
import asyncio
import websockets
import json
from html.parser import HTMLParser
import argparse
import os
import base64

class HTMLStripper(HTMLParser):
    def __init__(self):
        super().__init__()
        self.text = []

    def handle_data(self, data):
        self.text.append(data)

    def get_data(self):
        return ''.join(self.text)
    
def strip_html(input_string):
    stripper = HTMLStripper()
    stripper.feed(input_string)
    return stripper.get_data()



def load_json_file(file_name):
    with open(file_name, 'r') as file:
        return json.load(file)

def save_json_file(file_name, data):
    with open(file_name, 'w') as file:
        json.dump(data, file, indent=4)

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(intents=intents, command_prefix="!")

TOKEN = ''

with open("token.txt", "r") as token_file:
    TOKEN = token_file.read().strip()

CLIENTS = {}

NEW_USER = {'chan_to_id': {}, 'id_to_chan': {}, 'default_channel': '2', 'guild_id': 0, 'channel_id': 0}

async def forward_to_discord(message, user):
    channel = bot.get_guild(user['guild_id']).get_channel(user['channel_id'])
    if not channel:
        return
    max_length = 1000
    while len(message) > max_length:
        split_index = message.rfind('\n', 0, max_length)
        if split_index == -1:
            split_index = max_length
        await channel.send(message[:split_index])
        message = message[split_index:]
    await channel.send(message)



@bot.event
async def on_ready():
    # global CHANNEL_ID, CHANNEL_NAME
    try:
        await bot.tree.sync()
    except Exception as e:
        print(f"Error syncing commands: {e}")

    # for guild in bot.guilds:
    #     for channel in guild.text_channels:
    #         if channel.name == CHANNEL_NAME:
    #             CHANNEL_ID = channel.id
    #             break

    print(f'Logged in as {bot.user.name} ({bot.user.id})')

def package_message(message, channel='2'):
    pack = {"type": "message", "channel": channel, "message": message.strip()}
    return json.dumps(pack)

def stage_message_variables(interaction):
    websocket_client = None
    default_channel = ''

    users = load_json_file("users.json")
    for key, user in users.items():
        if user['guild_id'] == interaction.guild.id and user['channel_id'] == interaction.channel.id:
            default_channel = user['default_channel']
            websocket_client = CLIENTS[key]
            break

    return websocket_client, default_channel

@bot.event
async def on_message(message):
    if message.author.bot:
        return

    websocket_client, default_channel = stage_message_variables(message)
    
    message_dict = package_message(message.content, default_channel)
    await send_to_websocket(message_dict, websocket_client)

    await message.delete()

@bot.tree.command(name="gen_key", description="Generates a new key for the connection")
async def generate_key(interaction: discord.Interaction):
    await interaction.response.defer()

    key = base64.urlsafe_b64encode(os.urandom(24)).decode('utf-8')
    user = NEW_USER
    user['guild_id'] = interaction.guild.id
    user['channel_id'] = interaction.channel.id

    users = load_json_file("users.json")
    users = {k: v for k, v in users.items() if not (v['guild_id'] == user['guild_id'] and v['channel_id'] == user['channel_id'])}
    users[key] = user
    save_json_file("users.json", users)

    await interaction.followup.send(f'Your key is: {key}')

@bot.tree.command(name="help", description="Displays all commands")
async def help_command(interaction: discord.Interaction):
    await interaction.response.defer()
    help_text_0 = """
    **General Information**
    `/help` - Displays this information.
    `/afk [reason]` - Marks you as AFK in chat and will notify anyone who whispers you that you are AFK.
    `[channel] /motd` - Displays the channel/game's Message of the Day.
    `/time` - Displays the current server time as well as your own local time.
    `/ref` - Displays your referral link.
    `/modlist` - Displays a list of moderators currently connected to the game.
    `/whois <username>` - Displays basic information about the specified user.
    `/online` - Shows how many users are connected to the game.
    `/channels [page]` - Displays a list of custom channels players have created.
    `/list [channel]` - Displays a list of people currently listening to the specified channel. If no channel is specified, shows the list of people listening to the channel your chat is set to.
    `/tips <on/off>` - Allows you to toggle gameplay tips on and off.
    """
    help_text_1 = """
    **General Chat Commands**
    `/setcolor <channel> <color>` - Changes your personal color preference for the specified channel. This only changes the channel color you see.
    `/unsetcolor <channel>` - Removes your color preference for the specified channel.
    `/quiet` - Prevents you from seeing everything except whispers and clan chat or disables quiet mode if it's already active.
    `/clear` - Clears all messages from your chat window.
    `/censor <on/off>` - Allows you to turn message censoring on and off.
    `/setchan <channelname>` - Sets your active channel to the specified channel, meaning messages you input will go there by default.
    `/w <username> <message>` - Sends a private message to the specified user.
    `/r <message>` - Sends a private message to the person who most recently whispered you.
    `/re <message>` - Sends a private message to the person you most recently whispered.
    `/me <message>` - Sends a message as an action, or "emotes," to the channel you're on.
    `/last [/channel]` - Displays the 100 most recent messages on the specified channel. If no channel is specified, displays the 100 most recent messages of the channel your chat is set to.
    `/join [channelname]` - Joins the specified channel, allowing you to receive messages sent to that channel. If no channel is specified, joins the channel your chat is set to.
    `/leave [channel]` - Leaves the specified channel, so you no will no longer receive messages sent to that channel. If no channel is specified, leaves the channel your chat is set to.
    `/nickname <username> <nickname>` - Creates a nickname for the specified user, which will display beside their messages in chat.
    `/unnickname <username>` - Removes the nickname you've created for the specified user.
    `/nicknamelist` - Displays each nickname you've created.
    """
    help_text_2 = """
    `/ignore <username>` - Prevents you from seeing any messages from the specified user.
    `/unignore <username>` - Allows you to once again see messages from a user you've previously ignored.
    `/ignorelist` - Displays a list of people you're ignoring.
    `/ignoredby [all]` - Displays a list of people who are ignoring you, aren't banned, and have logged in within the past 30 days. If you'd like to display banned users and those who have logged in within the last 30 days, add the /all parameter.
    `/m <message>` - Sends a message to the main chat channel, in case it isn't your currently selected channel.
    `/h <message>` - Sends a message to the help chat channel, in case it isn't your currently selected channel.
    `/c <message>` - Sends a message to your clan chat channel, in case it isn't your currently selected channel.
    `/t <message>` - Sends a message to the trade chat channel, in case it isn't your currently selected channel.
    `/a <message>` - Sends a message to your area chat channel, in case it isn't your currently selected channel.
    
    **Clan-related Chat Commands**
    `/c <message>` - Sends a message to your clan chat channel, in case it isn't your currently selected channel.
    `/cmotd` - Displays your clan's Message of the Day.
    `/setcmotd [<message> | /clear]` - Sets or clears your clan's Message of the Day.
    `/cann <message>` - Makes an announcement to your clan.
    `/cinvite <username>` - Invites an adventurer to your clan.
    """

    help_text_3 = """
    **Private Channel Commands**
    `/colors` - Displays a list of named colors for use with private channels. Note, however, that you may also use hex codes for channel colors.
    `/chaninfo <channel>` - Displays various information about the specified channel.
    `[/chan <channelname> create | /create <channelname>] [color] [password]` - Creates a new, private channel with the specified name. Color must be a valid html color (named colors and hex codes are allowed) - default is white. Password is optional.
    `/join <channel> [password]` - Joins the specified private channel. If a password is set, you must provide the correct one.
    `/leave <channel>` - Leaves the specified private channel.
    `/chanset <channel> <color/password/motd> <value>` - Sets the specified option to the specified value.
    `/chanmod <channel> <target>` - Gives the specified user moderation privileges on the specified channel. Only usable by the channel owner.
    `/chanunmod <channel> <target>` - Revokes moderation privileges from the specified user on the specified channel. Only usable by the channel owner.
    `/chanban <channel> <target>` - Kicks the user out of the channel and prevents them from rejoining. Only usable by the channel owner and channel moderators.
    `/chanunban <channel> <target>` - Unbans the user from the channel. Only usable by the channel owner and channel moderators.
    `/chankick <channel> <target>` - Kicks the user out of the channel. Only usable by the channel owner and channel moderators and only usable on channels with a password.
    """

    help_text_4 = """
    **Miscellaneous Chat Commands**
    `[_NOT IMPLEMENTED_] ~~/profile <username>` - Displays the specified user's profile, which contains detailed information about the user.~~
    `/calc <expression>` - Calculates the expression.
    `/roll <#dTYPE>` - Simulates a dice roll on your current channel. # specifies how many dice to roll, type specifies the number of sides per die. For example: `/diceroll 2d10` will roll 2 dice with 10 sides, generating a number between 2 and 20.
    `/roll <low> <high>` - Simulates a dice roll on your current channel. Generates a random number between <low> and <high>.
    `/tarot` - Generates a random tarot card.
    `/wire <target> <amount> <currency>` - Transfers currency from your account to the target's account. Transferable currencies: crystals, platinum, gold, food, wood, iron, stone, crafting_materials, gem_fragments
    """

    help_text_5 = """
    **Discord Integration Commands**
    `/gen_key` - Generates a new key for the connection.
    """

    await interaction.followup.send(help_text_0)
    await interaction.followup.send(help_text_1)
    await interaction.followup.send(help_text_2)
    await interaction.followup.send(help_text_3)
    await interaction.followup.send(help_text_4)
    await interaction.followup.send(help_text_5)

@bot.tree.command(name="afk", description="Marks you as AFK in chat and will notify anyone who whispers you that you are AFK.")
async def afk_command(interaction: discord.Interaction, reason: str = ""):
    await interaction.response.defer()

    websocket_client, default_channel = stage_message_variables(interaction)

    message_dict = package_message(f"/afk {reason}", default_channel)

    await send_to_websocket(message_dict, websocket_client)
    await interaction.followup.send("Command sent")

@bot.tree.command(name="time", description="Displays the current server time as well as your own local time.")
async def time_command(interaction: discord.Interaction):
    await interaction.response.defer()

    websocket_client, default_channel = stage_message_variables(interaction)

    message_dict = package_message("/time", default_channel)

    await send_to_websocket(message_dict, websocket_client)
    await interaction.followup.send("Command sent")

@bot.tree.command(name="ref", description="Displays your referral link.")
async def ref_command(interaction: discord.Interaction):
    await interaction.response.defer()

    websocket_client, default_channel = stage_message_variables(interaction)

    message_dict = package_message("/ref", default_channel)

    await send_to_websocket(message_dict, websocket_client)
    await interaction.followup.send("Command sent")

@bot.tree.command(name="modlist", description="Displays a list of moderators currently connected to the game.")
async def modlist_command(interaction: discord.Interaction):
    await interaction.response.defer()

    websocket_client, default_channel = stage_message_variables(interaction)

    message_dict = json.dumps({"type": "modlist"})

    await send_to_websocket(message_dict, websocket_client)
    await interaction.followup.send("Command sent")

@bot.tree.command(name="whois", description="Displays basic information about the specified user.")
async def whois_command(interaction: discord.Interaction, username: str):
    await interaction.response.defer()

    websocket_client, default_channel = stage_message_variables(interaction)

    message_dict = package_message(f"/whois {username}", default_channel)

    await send_to_websocket(message_dict, websocket_client)
    await interaction.followup.send("Command sent")

@bot.tree.command(name="online", description="Shows how many users are connected to the game.")
async def online_command(interaction: discord.Interaction):
    await interaction.response.defer()

    websocket_client, default_channel = stage_message_variables(interaction)

    message_dict = package_message("/online", default_channel)

    await send_to_websocket(message_dict, websocket_client)
    await interaction.followup.send("Command sent")

@bot.tree.command(name="channels", description="Displays a list of custom channels players have created.")
async def channels_command(interaction: discord.Interaction, page: int = 1):
    await interaction.response.defer()

    websocket_client, default_channel = stage_message_variables(interaction)

    message_dict = package_message(f"/channels {page}", default_channel)

    await send_to_websocket(message_dict, websocket_client)
    await interaction.followup.send("Command sent")

@bot.tree.command(name="list", description="Displays a list of people currently listening to the specified channel.")
async def list_command(interaction: discord.Interaction, channel: str = None):
    await interaction.response.defer()

    websocket_client, default_channel = stage_message_variables(interaction)

    if not channel:
        channel = default_channel
    message_dict = package_message(f"/list {channel}", default_channel)

    await send_to_websocket(message_dict, websocket_client)
    await interaction.followup.send("Command sent")

@bot.tree.command(name="tips", description="Allows you to toggle gameplay tips on and off.")
async def tips_command(interaction: discord.Interaction, toggle: str):
    await interaction.response.defer()

    websocket_client, default_channel = stage_message_variables(interaction)

    message_dict = package_message(f"/tips {toggle}", default_channel)

    await send_to_websocket(message_dict, websocket_client)
    await interaction.followup.send("Command sent")

@bot.tree.command(name="setcolor", description="Changes your personal color preference for the specified channel.")
async def set_color(interaction: discord.Interaction, channel: str, color: str):
    await interaction.response.defer()

    websocket_client, default_channel = stage_message_variables(interaction)

    message_dict = package_message(f"/setcolor {channel} {color}", default_channel)

    await send_to_websocket(message_dict, websocket_client)
    await interaction.followup.send("Command sent")

@bot.tree.command(name="unsetcolor", description="Removes your color preference for the specified channel.")
async def unset_color(interaction: discord.Interaction, channel: str):
    await interaction.response.defer()

    websocket_client, default_channel = stage_message_variables(interaction)

    message_dict = package_message(f"/unsetcolor {channel}", default_channel)

    await send_to_websocket(message_dict, websocket_client)
    await interaction.followup.send("Command sent")

@bot.tree.command(name="quiet", description="Prevents you from seeing everything except whispers and clan chat.")
async def quiet_mode(interaction: discord.Interaction):
    await interaction.response.defer()

    websocket_client, default_channel = stage_message_variables(interaction)

    message_dict = package_message("/quiet", default_channel)

    await send_to_websocket(message_dict, websocket_client)
    await interaction.followup.send("Command sent")

@bot.tree.command(name="clear", description="Clears all messages from your chat window.")
async def clear_chat(interaction: discord.Interaction):
    await interaction.response.defer()

    websocket_client, default_channel = stage_message_variables(interaction)

    old_channel = interaction.channel
    new_channel = await interaction.channel.clone(reason="Clearing messages")
    await old_channel.delete()
    await new_channel.send("Chat cleared")

    users = load_json_file("users.json")
    for key, user in users.items():
        if user['guild_id'] == interaction.guild.id and user['channel_id'] == old_channel.id:
            user['channel_id'] = new_channel.id
            user['default_channel'] = default_channel
    save_json_file("users.json", users)

    await interaction.followup.send("Command sent")

@bot.tree.command(name="censor", description="Allows you to turn message censoring on and off.")
@app_commands.describe(toggle="Choose to toggle censoring on or off")
@app_commands.choices(toggle=[
    discord.app_commands.Choice(name="on", value="on"),
    discord.app_commands.Choice(name="off", value="off")
])
async def censor_mode(interaction: discord.Interaction, toggle: app_commands.Choice[str]):
    await interaction.response.defer()

    websocket_client, default_channel = stage_message_variables(interaction)

    message_dict = package_message(f"/censor {toggle.value}", default_channel)

    await send_to_websocket(message_dict, websocket_client)
    await interaction.followup.send("Command sent")

@bot.tree.command(name="setchan", description="Sets your active channel to the specified channel.")
async def set_channel(interaction: discord.Interaction, channel: str):
    await interaction.response.defer()
    channel_id = ""
    channel_name = ""

    users = load_json_file("users.json")

    for key, user in users.items():
        if user['guild_id'] == interaction.guild.id and user['channel_id'] == interaction.channel.id:
            print(user)
            id_to_chan = user['id_to_chan']
            chan_to_id = user['chan_to_id']

            try:
                channel_id = chan_to_id[channel]
                channel_name = channel
            except KeyError:
                try:
                    channel_name = id_to_chan[channel]
                    channel_id = channel
                except KeyError:
                    await interaction.followup.send("Invalid channel")
                    return

            user['default_channel'] = channel_id

            break
    
    save_json_file("users.json", users)

    await interaction.followup.send(f"Default channel set to {channel_name}")

@bot.tree.command(name="w", description="Sends a private message to the specified user.")
async def send_private_message(interaction: discord.Interaction, username: str, message: str):
    await interaction.response.defer()

    websocket_client, default_channel = stage_message_variables(interaction)

    message_dict = package_message(f"/w {username} {message}", default_channel)

    await send_to_websocket(message_dict, websocket_client)
    await interaction.followup.send("Command sent")

@bot.tree.command(name="r", description="Sends a private message to the person who most recently whispered you.")
async def send_private_message(interaction: discord.Interaction, message: str):
    await interaction.response.defer()

    websocket_client, default_channel = stage_message_variables(interaction)

    message_dict = package_message(f"/r {message}", default_channel)

    await send_to_websocket(message_dict, websocket_client)
    await interaction.followup.send("Command sent")

@bot.tree.command(name="re", description="Sends a private message to the person you most recently whispered.")
async def send_private_message(interaction: discord.Interaction, message: str):
    send_private_message(interaction, message)

@bot.tree.command(name="me", description="Sends a message as an action, or 'emotes,' to the channel you're on.")
async def send_action(interaction: discord.Interaction, message: str):
    await interaction.response.defer()

    websocket_client, default_channel = stage_message_variables(interaction)

    message_dict = json.dumps({"type": "emote", "channel": default_channel, "message": message})

    await send_to_websocket(message_dict, websocket_client)
    await interaction.followup.send("Command sent")

@bot.tree.command(name="last", description="Displays the 100 most recent messages on the specified channel.")
async def last_messages(interaction: discord.Interaction, channel: str = None):
    await interaction.response.defer()

    websocket_client, default_channel = stage_message_variables(interaction)

    if not channel:
        channel = default_channel
    message_dict = json.dumps({"type": "history", "channel": channel})

    await send_to_websocket(message_dict, websocket_client)
    await interaction.followup.send("Command sent")

@bot.tree.command(name="join", description="Joins the specified channel, allowing you to receive messages sent to that channel.")
async def join_channel(interaction: discord.Interaction, channel: str = None):
    await interaction.response.defer()

    websocket_client, default_channel = stage_message_variables(interaction)

    if not channel:
        channel = default_channel
    message_dict = package_message(f"/join {channel}", default_channel)

    await send_to_websocket(message_dict, websocket_client)
    await interaction.followup.send("Command sent")

@bot.tree.command(name="leave", description="Leaves the specified channel, so you will no longer receive messages sent to that channel.")
async def leave_channel(interaction: discord.Interaction, channel: str = None):
    await interaction.response.defer()

    websocket_client, default_channel = stage_message_variables(interaction)

    if not channel:
        channel = default_channel
    message_dict = package_message(f"/leave {channel}", default_channel)

    await send_to_websocket(message_dict, websocket_client)
    await interaction.followup.send("Command sent")

@bot.tree.command(name="nickname", description="Creates a nickname for the specified user, which will display beside their messages in chat.")
async def nickname_user(interaction: discord.Interaction, username: str, nickname: str):
    await interaction.response.defer()

    websocket_client, default_channel = stage_message_variables(interaction)

    message_dict = package_message(f"/nickname {username} {nickname}", default_channel)

    await send_to_websocket(message_dict, websocket_client)
    await interaction.followup.send("Command sent")

@bot.tree.command(name="unnickname", description="Removes the nickname you've created for the specified user.")
async def unnickname_user(interaction: discord.Interaction, username: str):
    await interaction.response.defer()

    websocket_client, default_channel = stage_message_variables(interaction)

    message_dict = package_message(f"/unnickname {username}", default_channel)

    await send_to_websocket(message_dict, websocket_client)
    await interaction.followup.send("Command sent")

@bot.tree.command(name="nicknamelist", description="Displays each nickname you've created.")
async def nickname_list(interaction: discord.Interaction):
    await interaction.response.defer()

    websocket_client, default_channel = stage_message_variables(interaction)

    message_dict = package_message("/nicknamelist", default_channel)

    await send_to_websocket(message_dict, websocket_client)
    await interaction.followup.send("Command sent")

@bot.tree.command(name="ignore", description="Prevents you from seeing any messages from the specified user.")
async def ignore_user(interaction: discord.Interaction, username: str):
    await interaction.response.defer()

    websocket_client, default_channel = stage_message_variables(interaction)

    message_dict = json.dumps({"type": "ignore", "target": username})

    await send_to_websocket(message_dict, websocket_client)
    await interaction.followup.send("Command sent")

@bot.tree.command(name="unignore", description="Allows you to once again see messages from a user you've previously ignored.")
async def unignore_user(interaction: discord.Interaction, username: str):
    await interaction.response.defer()

    websocket_client, default_channel = stage_message_variables(interaction)

    message_dict = json.dumps({"type": "unignore", "target": username})

    await send_to_websocket(message_dict, websocket_client)
    await interaction.followup.send("Command sent")

@bot.tree.command(name="ignorelist", description="Displays a list of people you're ignoring.")
async def ignore_list(interaction: discord.Interaction):
    await interaction.response.defer()

    websocket_client, default_channel = stage_message_variables(interaction)

    message_dict = package_message("/ignorelist", default_channel)

    await send_to_websocket(message_dict, websocket_client)
    await interaction.followup.send("Command sent")

@bot.tree.command(name="ignoredby", description="Displays a list of people who are ignoring you.")
@app_commands.describe(all="Display all users, including banned users and those who have logged in within the last 30 days")
@app_commands.choices(all=[
    discord.app_commands.Choice(name="all", value="all")
])
async def ignored_by(interaction: discord.Interaction, all: app_commands.Choice[str] = ""):
    await interaction.response.defer()

    websocket_client, default_channel = stage_message_variables(interaction)

    message_dict = package_message(f"/ignoredby {all.value}", default_channel)

    await send_to_websocket(message_dict, websocket_client)
    await interaction.followup.send("Command sent")

@bot.tree.command(name="m", description="Sends a message to the main chat channel.")
async def main_chat(interaction: discord.Interaction, message: str):
    await interaction.response.defer()

    websocket_client, default_channel = stage_message_variables(interaction)

    message_dict = package_message(f"/m {message}", default_channel)

    await send_to_websocket(message_dict, websocket_client)
    await interaction.followup.send("Command sent")

@bot.tree.command(name="h", description="Sends a message to the help chat channel.")
async def help_chat(interaction: discord.Interaction, message: str):
    await interaction.response.defer()

    websocket_client, default_channel = stage_message_variables(interaction)

    message_dict = package_message(f"/h {message}", default_channel)

    await send_to_websocket(message_dict, websocket_client)
    await interaction.followup.send("Command sent")

@bot.tree.command(name="c", description="Sends a message to your clan chat channel.")
async def clan_chat(interaction: discord.Interaction, message: str):
    await interaction.response.defer()

    websocket_client, default_channel = stage_message_variables(interaction)

    message_dict = package_message(f"/c {message}", default_channel)

    await send_to_websocket(message_dict, websocket_client)
    await interaction.followup.send("Command sent")

@bot.tree.command(name="t", description="Sends a message to the trade chat channel.")
async def trade_chat(interaction: discord.Interaction, message: str):
    await interaction.response.defer()

    websocket_client, default_channel = stage_message_variables(interaction)

    message_dict = package_message(f"/t {message}", default_channel)

    await send_to_websocket(message_dict, websocket_client)
    await interaction.followup.send("Command sent")

@bot.tree.command(name="a", description="Sends a message to your area chat channel.")
async def area_chat(interaction: discord.Interaction, message: str):
    await interaction.response.defer()

    websocket_client, default_channel = stage_message_variables(interaction)

    message_dict = package_message(f"/a {message}", default_channel)

    await send_to_websocket(message_dict, websocket_client)
    await interaction.followup.send("Command sent")

@bot.tree.command(name="cmotd", description="Displays your clan's Message of the Day.")
async def clan_motd(interaction: discord.Interaction):
    await interaction.response.defer()

    websocket_client, default_channel = stage_message_variables(interaction)

    message_dict = package_message("/cmotd", default_channel)

    await send_to_websocket(message_dict, websocket_client)
    await interaction.followup.send("Command sent")

@bot.tree.command(name="cann", description="Makes an announcement to your clan.")
async def clan_announcement(interaction: discord.Interaction, message: str):
    await interaction.response.defer()

    websocket_client, default_channel = stage_message_variables(interaction)

    message_dict = package_message(f"/cann {message}", default_channel)

    await send_to_websocket(message_dict, websocket_client)
    await interaction.followup.send("Command sent")

@bot.tree.command(name="cinvite", description="Invites an adventurer to your clan.")
async def clan_invite(interaction: discord.Interaction, username: str):
    await interaction.response.defer()

    websocket_client, default_channel = stage_message_variables(interaction)

    message_dict = package_message(f"/cinvite {username}", default_channel)

    await send_to_websocket(message_dict, websocket_client)
    await interaction.followup.send("Command sent")

@bot.tree.command(name="colors", description="Displays a list of named colors for use with private channels.")
async def color_list(interaction: discord.Interaction):
    await interaction.response.defer()

    websocket_client, default_channel = stage_message_variables(interaction)

    message_dict = package_message("/colors", default_channel)

    await send_to_websocket(message_dict, websocket_client)
    await interaction.followup.send("Command sent")

@bot.tree.command(name="chaninfo", description="Displays various information about the specified channel.")
async def channel_info(interaction: discord.Interaction, channel: str):
    await interaction.response.defer()

    websocket_client, default_channel = stage_message_variables(interaction)

    message_dict = package_message(f"/chaninfo {channel}", default_channel)

    await send_to_websocket(message_dict, websocket_client)
    await interaction.followup.send("Command sent")

@bot.tree.command(name="create", description="Creates a new, private channel with the specified name.")
async def create_channel(interaction: discord.Interaction, channel: str, color: str = "white", password: str = ""):
    await interaction.response.defer()

    websocket_client, default_channel = stage_message_variables(interaction)

    message_dict = package_message(f"/chan {channel} create {color} {password}", default_channel)

    await send_to_websocket(message_dict, websocket_client)
    await interaction.followup.send("Command sent")

@bot.tree.command(name="chanset", description="Sets the specified option to the specified value.")
@app_commands.describe(option="The option to set", value="The value to set the option to")
@app_commands.choices(option=[
    discord.app_commands.Choice(name="color", value="color"),
    discord.app_commands.Choice(name="password", value="password"),
    discord.app_commands.Choice(name="motd", value="motd")
])
async def set_channel_option(interaction: discord.Interaction, channel: str, option: app_commands.Choice[str], value: str):
    await interaction.response.defer()

    websocket_client, default_channel = stage_message_variables(interaction)

    message_dict = package_message(f"/chanset {channel} {option.value} {value}", default_channel)

    await send_to_websocket(message_dict, websocket_client)
    await interaction.followup.send("Command sent")

@bot.tree.command(name="setcmotd", description="Sets or clears your clan's Message of the Day.")
async def set_clan_motd(interaction: discord.Interaction, message: str = ""):
    await interaction.response.defer()

    websocket_client, default_channel = stage_message_variables(interaction)

    message_dict = package_message(f"/setcmotd {message}", default_channel)

    await send_to_websocket(message_dict, websocket_client)
    await interaction.followup.send("Command sent")

@bot.tree.command(name="chanmod", description="Gives the specified user moderation privileges on the specified channel.")
async def channel_mod(interaction: discord.Interaction, channel: str, target: str):
    await interaction.response.defer()

    websocket_client, default_channel = stage_message_variables(interaction)

    message_dict = package_message(f"/chanmod {channel} {target}", default_channel)

    await send_to_websocket(message_dict, websocket_client)
    await interaction.followup.send("Command sent")

@bot.tree.command(name="chanunmod", description="Revokes moderation privileges from the specified user on the specified channel.")
async def channel_unmod(interaction: discord.Interaction, channel: str, target: str):
    await interaction.response.defer()

    websocket_client, default_channel = stage_message_variables(interaction)

    message_dict = package_message(f"/chanunmod {channel} {target}", default_channel)

    await send_to_websocket(message_dict, websocket_client)
    await interaction.followup.send("Command sent")

@bot.tree.command(name="chanban", description="Kicks the user out of the channel and prevents them from rejoining.")
async def channel_ban(interaction: discord.Interaction, channel: str, target: str):
    await interaction.response.defer()

    websocket_client, default_channel = stage_message_variables(interaction)

    message_dict = package_message(f"/chanban {channel} {target}", default_channel)

    await send_to_websocket(message_dict, websocket_client)
    await interaction.followup.send("Command sent")

@bot.tree.command(name="chanunban", description="Unbans the user from the channel.")
async def channel_unban(interaction: discord.Interaction, channel: str, target: str):
    await interaction.response.defer()

    websocket_client, default_channel = stage_message_variables(interaction)

    message_dict = package_message(f"/chanunban {channel} {target}", default_channel)

    await send_to_websocket(message_dict, websocket_client)
    await interaction.followup.send("Command sent")

@bot.tree.command(name="chankick", description="Kicks the user out of the channel.")
async def channel_kick(interaction: discord.Interaction, channel: str, target: str):
    await interaction.response.defer()

    websocket_client, default_channel = stage_message_variables(interaction)

    message_dict = package_message(f"/chankick {channel} {target}", default_channel)

    await send_to_websocket(message_dict, websocket_client)
    await interaction.followup.send("Command sent")

# @bot.tree.command(name="profile", description="Displays the specified user's profile.")
# async def user_profile(interaction: discord.Interaction, username: str):
#     await interaction.response.defer()

#     message_dict = package_message(f"/profile {username}", default_channel)

#     await send_to_websocket(message_dict)
#     await interaction.followup.send("Command sent")

@bot.tree.command(name="calc", description="Calculates the expression.")
async def calculate_expression(interaction: discord.Interaction, expression: str):
    await interaction.response.defer()

    try:
        result = eval(expression)
        await interaction.followup.send(f"Calculation: {expression} = {result}")
    except Exception as e:
        await interaction.followup.send(f"Error calculating expression: {e}")

@bot.tree.command(name="roll", description="Simulates a dice roll on your current channel.")
async def dice_roll(interaction: discord.Interaction, amount_d_faces_or_low: str, high: str = ""):
    await interaction.response.defer()

    websocket_client, default_channel = stage_message_variables(interaction)

    message_dict = package_message(f"/roll {amount_d_faces_or_low} {high}", default_channel)

    await send_to_websocket(message_dict, websocket_client)
    await interaction.followup.send("Command sent")


@bot.tree.command(name="tarot", description="Generates a random tarot card.")
async def tarot_card(interaction: discord.Interaction):
    await interaction.response.defer()

    websocket_client, default_channel = stage_message_variables(interaction)

    message_dict = package_message("/tarot", default_channel)

    await send_to_websocket(message_dict, websocket_client)
    await interaction.followup.send("Command sent")

@bot.tree.command(name="wire", description="Transfers currency from your account to the target's account.")
async def currency_transfer(interaction: discord.Interaction, target: str, amount: str, currency: str):
    await interaction.response.defer()

    websocket_client, default_channel = stage_message_variables(interaction)

    message_dict = package_message(f"/wire {target} {amount} {currency}", default_channel)

    await send_to_websocket(message_dict, websocket_client)
    await interaction.followup.send("Command sent")

# @bot.tree.command(name="pc", description="Specify a private channel to send messages to")
# async def discord_to_websocket(interaction: discord.Interaction, channel_id: str, message: str):
#     await interaction.response.defer()

#     websocket_client = None

#     users = load_json_file("users.json")
#     for key, user in users.items():
#         if user['guild_id'] == interaction.guild.id and user['channel_id'] == interaction.channel.id:
#             websocket_client = user['websocket_client']
#             break

#     if not channel_id.isdigit():
#         try:
#             channel_id = chan_to_id[channel_id]
#         except KeyError:
#             await interaction.followup.send("Invalid channel ID")
#             return

#     message_dict = package_message(message, channel_id)
#     await send_to_websocket(message_dict, websocket_client)
#     await interaction.followup.send("Message sent")



async def send_to_websocket(message, websocket_client):
    if websocket_client:
        await websocket_client.send(message)

def process_message(dict_data, user):
    id_to_chan = user['id_to_chan']
    chan_to_id = user['chan_to_id']
    default_channel = user['default_channel']

    message_type = dict_data['type']
    output = None

    if message_type == "message" or message_type == "diceroll":
        channel_id = default_channel
        try:
            channel_id = id_to_chan[f"{dict_data['c_id']}"]
        except KeyError:
            if 'c_id' in dict_data:
                channel_id = dict_data['c_id']
        output = f"[{dict_data['ts']}] [{channel_id}] {dict_data['u']}: {dict_data['m']}"
    elif message_type == "you_are_afk":
        output = f"You are now AFK. Reason: {dict_data['r']}"
    elif message_type == "you_not_are_afk":
        pass
    elif message_type == "motd":
        output = f"[{dict_data['mts']}] **Message of the day: {dict_data['m']}**"
    elif message_type == "announcement":
        output = f"[{dict_data['ts']}] **Announcement: {dict_data['m']}**"
    elif message_type == "notification":
        output = f"[{dict_data['ts']}] {dict_data['m']}"
    elif message_type == "mychans":
        for chan in dict_data['channels']:
            id_to_chan[f"{chan['id']}"] = chan['name']
            chan_to_id[chan['name']] = f"{chan['id']}"
    elif message_type == "pmfrom":
        output = f"[{dict_data['ts']}] Whisper from {dict_data['u']}: {dict_data['m']}"
    elif message_type == "history":
        output = "**History:**\n"
        for message in dict_data['ml']:
            output += "\t" + process_message(message) + "\n"
    elif message_type == "nicknamelist":
        output = "**Nicknames:**\n"
        for nickname, nick_value in dict_data['nicknames'].items():
            output += f"\t{nickname}: {nick_value}\n"
    elif message_type == "all_channels":
        output = f"**Channels ({dict_data['c']} results):**\n"
        for channel in dict_data['list']:
            output += f"\tChannel __{channel['n']}__ is owned by __{channel['o']}__\n"
    elif message_type == "chanlist":
        output = f"[{dict_data['ts']}] **Users connected on this channel:**\n"
        for user in dict_data['list']:
            if user['a']:
                output += f"\t{user['n']} (AFK)\n"
            else:
                output += f"\t{user['n']}\n"
    elif message_type == "modlist":
        output = f"[{dict_data['ts']}] **The following moderators are currently available:**\n"
        for user in dict_data['list']:
            if user['a']:
                output += f"\t{user['n']} (AFK)\n"
            else:
                output += f"\t{user['n']}\n"
    elif message_type == "emote":
        channel_id = default_channel
        try:
            channel_id = id_to_chan[f"{dict_data['c_id']}"]
        except KeyError:
            if 'c_id' in dict_data:
                channel_id = dict_data['c_id']
        output = f"[{dict_data['ts']}] [{channel_id}] * _{dict_data['u']} {dict_data['m']}_"
    elif message_type == "colorlist":
        output = "**Colors:**\n"
        for color in dict_data['list']:
            output += f"\t{color}\n"
    elif message_type == "tarot":
        channel_id = default_channel
        try:
            channel_id = id_to_chan[f"{dict_data['c_id']}"]
        except KeyError:
            if 'c_id' in dict_data:
                channel_id = dict_data['c_id']
        output = f"[{dict_data['ts']}] [{channel_id}] _{dict_data['u']} {dict_data['m']}_"
    elif message_type == "clanannouncement":
        output = f"[{dict_data['ts']}] **Clan Announcement: {dict_data['m']}**"
    elif message_type == "timestamp":
        output = f"[{dict_data['m']}] The current server time is {dict_data['m']}."
    else:
        print(f"Unsupported message type: {message_type}")
        
    return output, id_to_chan, chan_to_id

async def socket_server(websocket):
    global CLIENTS
    try:
        async for message in websocket:
            message = json.loads(message)
            message_dict = json.loads(message['roa_message'])
            key = message['key']

            users = load_json_file("users.json")
            user = None

            if key in users.keys():
                user = users[key]
            else:
                print(f"Invalid key: {key}")
                continue

            if key not in CLIENTS:
                CLIENTS[key] = websocket

            if type(message_dict) is not list:
                continue
                
            message_string, id_to_chan, chan_to_id = process_message(message_dict[0], user)
            users[key]['id_to_chan'] = id_to_chan
            users[key]['chan_to_id'] = chan_to_id
            save_json_file("users.json", users)

            if message_string:
                plain_message_string = strip_html(message_string)
                await forward_to_discord(plain_message_string, user)
    except websockets.exceptions.ConnectionClosedError as e:
        print(f"Connection closed with error: {e}")

async def main():
    if not os.path.exists("users.json"):
        with open("users.json", "w") as f:
            json.dump({}, f)

    parser = argparse.ArgumentParser(description="Discord bot for Avabur")
    parser.add_argument('--self-host', action='store_true', help='Run the bot in self-hosting mode')
    args = parser.parse_args()

    if args.self_host:
        websocket_server = await websockets.serve(socket_server, "127.0.0.1", 8765)
        print("WebSocket server started at ws://localhost:8765")
    else:
        websocket_server = await websockets.serve(socket_server, "0.0.0.0", 8765)
        print("WebSocket server started at ws://0.0.0.0:8765")

    # Start Discord bot
    await bot.start(TOKEN)

    # Wait for WebSocket server to close
    await websocket_server.wait_closed()

if __name__ == '__main__':
    asyncio.run(main())