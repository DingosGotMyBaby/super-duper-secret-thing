from typing import Optional

import discord
from discord import app_commands
import dotenv
import os
import logging

dotenv.load_dotenv()


MY_GUILD = discord.Object(id=os.environ["GUILD"])  # replace with your guild id
TOKEN = os.environ["TOKEN"]
PINNED_MESSAGE = os.environ["PINNED_MESSAGE"]
CHANNEL = os.environ["CHANNEL"]

class MyClient(discord.Client):
    def __init__(self, *, intents: discord.Intents):
        super().__init__(intents=intents)

        self.tree = app_commands.CommandTree(self)

    # In this basic example, we just synchronize the app commands to one guild.
    # Instead of specifying a guild to every command, we copy over our global commands instead.
    # By doing so, we don't have to wait up to an hour until they are shown to the end-user.
    async def setup_hook(self):
        # This copies the global commands over to your guild.
        self.tree.copy_global_to(guild=MY_GUILD)
        await self.tree.sync(guild=MY_GUILD)


intents = discord.Intents.default()
client = MyClient(intents=intents)


@client.event
async def on_ready():
    print(f'Logged in as {client.user} (ID: {client.user.id})')
    print('------')
    print(f'Guilds: {len(client.guilds)}')
    print(f'Invite URL: {discord.utils.oauth_url(client.user.id, permissions=discord.Permissions.all())}')


# Game Submission command
@client.tree.command()
@app_commands.describe(url='The Steam URL of the game you want to submit')
async def submit_game(interaction: discord.Interaction, url: str):
    """Submits a game to be played then edits a message with the games app id.
    This command is only available in the #game-submissions channel.
    URL format is https://james.spinthe.games/?share={list-title:[]}
    """
    # Check if the command is being run in the #game-submissions channel
    if interaction.channel.id != CHANNEL:
        await interaction.response.send_message(
            f'This command can only be run in the #game-submissions channel.', ephemeral=True
        )
        logging.info(f'User {interaction.user} tried to run the submit_game command in the wrong channel.')

        return
    # We're sending this response message with ephemeral=True, so only the command executor can see it
    await interaction.response.send_message(f'Submitted {url} to be played.', ephemeral=True)
    logging.info(f'User {interaction.user} submitted {url} to be played.')

    # extract the app id from the url
    app_id = url.split('/')[-1]
    # get current pinned message from the channel
    pinned_message = await interaction.channel.fetch_message(PINNED_MESSAGE)
    # pull out the current app ids from the url in the pinned message
    current_app_ids = pinned_message.content.split('=')[-1].strip(']').strip('}').strip('[').strip('{').split(',')
    # add the new app id to the list
    current_app_ids.append(app_id)
    # create a new url with the updated app ids
    new_url = f'https://james.spinthe.games/?share={{list-title:[{",".join(current_app_ids)}]}}'
    # edit the pinned message with the new url
    await pinned_message.edit(content=new_url)


client.run('token')