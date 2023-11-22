from typing import Optional, Literal, Union, NamedTuple
from enum import Enum

import discord
from discord import app_commands
import dotenv
import os
import logging
import re
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import Base, User, Submission, Category, Settings


logging.basicConfig(level=logging.DEBUG)
logging.getLogger("sqlalchemy.engine").setLevel(logging.INFO)
dotenv.load_dotenv()


MY_GUILD = discord.Object(id=os.environ["GUILD"])  # replace with your guild id
TOKEN = os.environ["TOKEN"]
CHANNEL = int(os.environ["CHANNEL"])
OWNER = int(os.environ["OWNER"])

database_url = "sqlite:///data/games.db"
# database_url = "postgresql://postgres:postgres@localhost:5432/games"

engine = create_engine(database_url)


Session = sessionmaker(bind=engine)
session = Session()


Base.metadata.create_all(engine)


# database functions
def get_user(userid):
    return session.query(User).filter(User.userid == userid).first()


def get_submission(submissionid):
    return (
        session.query(Submission)
        .filter(Submission.submissionid == submissionid)
        .first()
    )


def get_submission_by_category(categoryid):
    return session.query(Submission).filter(Submission.categoryid == categoryid).all()


def get_category(categoryid):
    return session.query(Category).filter(Category.categoryid == categoryid).first()


def get_category_by_name(categoryname):
    return session.query(Category).filter(Category.categoryname == categoryname).first()


def get_setting(settingname):
    return session.query(Settings).filter(Settings.settingname == settingname).first()


def get_all_users():
    return session.query(User).all()


def get_all_submissions():
    return session.query(Submission).all()


def get_all_categories():
    return session.query(Category).all()


def get_all_settings():
    return session.query(Settings).all()


def add_user(userid, username):
    user = User(userid=userid, username=username)
    session.add(user)
    session.commit()
    return user


def add_submission(userid, url, categoryid, appid):
    submission = Submission(userid=userid, url=url, categoryid=categoryid, appid=appid)
    session.add(submission)
    session.commit()
    return submission


def add_category(categoryname):
    category = Category(categoryname=categoryname)
    session.add(category)
    session.commit()
    return category


def add_setting(settingname, settingvalue):
    setting = Settings(settingname=settingname, settingvalue=settingvalue)
    session.add(setting)
    session.commit()
    return setting


def update_user(userid, username):
    user = get_user(userid)
    user.username = username
    session.commit()
    return user


def make_mod(userid):
    user = get_user(userid)
    user.mod = True
    session.commit()
    return user


def make_admin(userid):
    user = get_user(userid)
    user.admin = True
    session.commit()
    return user


def remove_submission(submissionid):
    submission = get_submission(submissionid)
    session.delete(submission)
    session.commit()
    return submission


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
        # seed database before running bot
        to_seed_categories = get_all_categories()
        # compare to Categories enum
        for category in Categories:
            # if category is not in the database, add it
            if category.name not in [
                category.categoryname for category in to_seed_categories
            ]:
                add_category(category.name)
                logging.info(
                    f"Category {category.name} was not in the database. Adding it now."
                )
        logging.info(f"Categories in the database: {get_all_categories()}")


intents = discord.Intents.default()
client = MyClient(intents=intents)


@client.event
async def on_ready():
    logging.info(f"Logged in as {client.user} (ID: {client.user.id})")
    # print('------')
    logging.info(f"Guilds: {len(client.guilds)}")
    logging.info(
        f"Invite URL: {discord.utils.oauth_url(client.user.id, permissions=discord.Permissions(permissions=139653810176))}"
    )
    # logging.info(
    #     "Environment variables loaded. " + str(CHANNEL)
    # )
    # print("Environment variables loaded." + str(MY_GUILD) + str(PINNED_MESSAGE) + str(CHANNEL))


@client.tree.error
async def on_app_command_error(
    interaction: discord.Interaction, exception: app_commands.AppCommandError
):
    if isinstance(exception, app_commands.CommandOnCooldown):
        await interaction.response.send_message(
            f"You are on cooldown, try again later!", ephemeral=True
        )
        logging.info(
            f"{interaction.user.name} tried to use a command on cooldown. They have {round(exception.retry_after, 2)} seconds left."
        )
        return
    else:
        logging.error(f"{interaction.command} raised an exception: {exception}")
        followup = interaction.followup
        await followup.send(
            f"Something went wrong! Tell Dingo to fucking fix it <:Madge:786617980103688262>",
            ephemeral=True,
        )
        return


# # Add category command
# @client.tree.command()
# @app_commands.describe(category_name='The name of the category you want to add')
# async def add_category(interaction: discord.Interaction, category_name: str):
#     """Adds a category to the database.
#     """
#     # Make sure the user is a mod
#     user_check = get_user(interaction.user.id)
#     if not user_check.mod or not user_check.admin:
#         await interaction.response.send_message(
#             f'You must be a mod to run this command.', ephemeral=True
#         )
#         logging.info(f'User {interaction.user} tried to run the add_category command but is not a mod.')

#         return

#     # We're sending this response message with ephemeral=True, so only the command executor can see it
#     await interaction.response.send_message(f'Added {category_name} to the database.', ephemeral=True)
#     logging.info(f'User {interaction.user} added {category_name} to the database.')

#     # add the category to the database
#     add_category(category_name)


# categories enum
class Categories(Enum):
    """Categories to choose from when submitting a game."""

    action = 1
    adventure = 2
    casual = 3
    horror = 4
    multiplayer = 5
    platformer = 6
    puzzle = 7
    racing = 8
    rpg = 9
    shooter = 10
    simulation = 11
    sports = 12
    strategy = 13
    other = 14


# Game Submission command
@client.tree.command()
@app_commands.checks.cooldown(1, 600, key=lambda i: (i.guild_id, i.user.id))
@app_commands.describe(url="The Steam URL of the game you want to submit")
@app_commands.describe(category="The category you want to submit the game to")
async def submit_game(interaction: discord.Interaction, url: str, category: Categories):
    """Submits a game to be played by James"""
    # Check if the command is being run in the #game-submissions channel
    if interaction.channel.id != CHANNEL:
        await interaction.response.send_message(
            f"This command can only be run in the #game-submissions channel.",
            ephemeral=True,
        )
        logging.info(
            f"User {interaction.user} tried to run the submit_game command in the wrong channel."
        )
        logging.debug(
            f"They ran it in {interaction.channel} which has an id of {(interaction.channel.id)}. Run it in {CHANNEL} instead."
        )

        return
    # check if submitted URL is a steam URL
    if "store.steampowered.com/app/" not in url:
        await interaction.response.send_message(
            f"This command can only be run with a Steam URL.", ephemeral=True
        )
        logging.info(
            f"User {interaction.user} tried to run the submit_game command with a non-steam URL. They submitted {url}"
        )

        return

    # app_id = url.split('/')[-2]
    app_id = (
        re.search(r"/app/(\d+)/", url).group(1)
        if re.search(r"/app/(\d+)/", url)
        else None
    )
    if not app_id:
        await interaction.response.send_message(
            f"This command can only be run with a Steam URL.", ephemeral=True
        )
        logging.info(
            f"User {interaction.user} tried to run the submit_game command with a non-steam URL. They submitted {url}"
        )

        return
    # We're sending this response message with ephemeral=True, so only the command executor can see it
    await interaction.response.send_message(
        f"Submitted {url} to be played.", ephemeral=True
    )

    logging.info(
        f"User {interaction.user} submitted {url} to be played. App ID is: {app_id}"
    )

    # make sure user is in the database
    user = get_user(interaction.user.id)
    if not user:
        add_user(interaction.user.id, interaction.user.name)
        logging.info(
            f"User {interaction.user} was not in the database. Adding them now."
        )
    # make sure app is not already submitted
    submission = session.query(Submission).filter(Submission.appid == app_id).first()
    if submission:
        # silently fail
        logging.info(
            f"User {interaction.user} tried to submit {url} but it was already submitted."
        )
        return
    # check and see if the category is in the database
    category_check = get_category_by_name(category.name)
    if not category_check:
        # add category to database just in case
        add_category(category.name)
        logging.info(f"{category.name} was not in the category table. Adding it now.")

    # add the submission to the database
    add_submission(interaction.user.id, url, category.value, app_id)


# send message to the channel to be pinned
@client.tree.command()
@app_commands.describe()
async def get_games(
    interaction: discord.Interaction, category: Optional[Categories] = None
):
    """Sends the message to be pinned to the channel."""
    # Check if the command is being run in the #game-submissions channel
    if interaction.channel.id != CHANNEL:
        await interaction.response.send_message(
            f"This command can only be run in the #game-submissions channel.",
            ephemeral=True,
        )
        logging.info(
            f"User {interaction.user} tried to run the pin_message command in the wrong channel."
        )

        return
    # make sure user is admin or mod
    user = get_user(interaction.user.id)
    if not user.admin and not user.mod and interaction.user.id != OWNER:
        await interaction.response.send_message(
            f"You must be an admin or mod to run this command.", ephemeral=True
        )
        logging.info(
            f"User {interaction.user} tried to run the get_games command but is not an admin or mod."
        )

        return

    if category:
        # get all submissions in that category
        submissions = get_submission_by_category(category.value)
    else:
        # get all submissions
        submissions = get_all_submissions()

    # if submissions are empty, send a message saying so
    if not submissions:
        await interaction.response.send_message(
            f'No submissions in {category.name if category else "games"}',
            ephemeral=True,
        )
        logging.info(
            f"User {interaction.user} tried to pin a message but there were no submissions."
        )
        return

    stringed_submissions = (
        str([str(submission.appid) for submission in submissions])
        .replace("'", "")
        .replace("[", "")
        .replace("]", "")
        .replace(" ", "")
    )

    # send the message to the channel and get the message id
    list_title = (category.name if category else "games").capitalize()
    # NOTES: 7B is {, 7D is }, 3A is :, %5B is [, %5D is ]
    await interaction.response.send_message(
        f"https://james.spinthe.games/?share=%7B{list_title}%3A%5B{stringed_submissions}%5D%7D",
        ephemeral=True,
    )


# dev use only Uncomment to enable
# @client.tree.command()
# @app_commands.describe()
# async def edit_message(interaction: discord.Interaction, message_id: str, message: str):
#     """Edits a message."""
#     # We're sending this response message with ephemeral=True, so only the command executor can see it
#     await interaction.response.send_message(f"Editing message.", ephemeral=True)
#     message_to_edit_id = int(message_id)

#     # get the message to be edited
#     message_to_edit = await interaction.channel.fetch_message(message_to_edit_id)
#     logging.info(
#         f"User {interaction.user} edited the message. Before edit: {message_to_edit.content} After edit: {message}"
#     )
#     # edit the message
#     await message_to_edit.edit(content=message)


@client.tree.command()
@app_commands.describe()
async def set_user(
    interaction: discord.Interaction,
    member: discord.Member,
    user_level: Literal["admin", "mod"],
):
    # Owner and admin only command
    if interaction.user.id != OWNER or not get_user(interaction.user.id).admin:
        await interaction.response.send_message(
            f"This command can only be run by the owner.", ephemeral=True
        )
        logging.info(
            f"User {interaction.user} tried to run the set_user command but is not the owner."
        )

        return
    logging.info(f"User {interaction.user} set {member} to {user_level}.")
    # set the user level
    if user_level == "admin":
        # check that user is owner
        if interaction.user.id != OWNER:
            await interaction.response.send_message(
                f"This command can only be run by the owner.", ephemeral=True
            )
            logging.info(
                f"User {interaction.user} tried to set {member} to {user_level} but is not the owner."
            )

            return

        make_admin(member.id)
        await interaction.response.send_message(
            f"Setting user to {user_level}.", ephemeral=True
        )
    elif user_level == "mod":
        make_mod(member.id)
        await interaction.response.send_message(
            f"Setting user to {user_level}.", ephemeral=True
        )
    else:
        await interaction.response.send_message(
            f"User level must be admin or mod.", ephemeral=True
        )
        logging.info(
            f"User {interaction.user} tried to set {member} to {user_level} but user level must be admin or mod."
        )

        return


client.run(TOKEN)
