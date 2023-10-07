# super-duper-secret-thing

heh

This is a bot for a thing, it does the things for some peoples 🙂

## Installation

Copy the `.env.example` to `.env` and replace the values with your values.
Then you can run the bot using the `docker-compose.yml`

## Usage

The bot exposes several commands,

* submit_game
  * Can be used by anyone
  * Submits a game to be played
* get_games
  * Can only be used by admins, mods and the owner
  * Gets the games to be played
* set_user
  * Can only be used by admins, mods and the owner
  * Sets a user to a specified user level
  * Owner can make admins and mods, admins can make mods

## Development

The only thing I care about is consistent formatting, therefore the Black formatter in VSCode is used
