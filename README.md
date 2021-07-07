# ngs_discord_weather_bot

A discord bot for forecasting the weather in Phantom Star Online 2: New Genesis

## Features
* List today's storms
* List next N weather changes
* List next N storms
* Send notification when storms are going to happen

## Setup

Create an `.env` file.
Then, set `DISCORD_TOKEN` to your bot's token and set `DISCORD_CHANNEL` to the channel's id where notifications are going to be sent.

You should provide a predicted weather dataset, which could be inferred from previous weather record as of now.
A sample dataset based on [@liruk's work](https://docs.google.com/spreadsheets/d/1Nf4NSSUhhX4EcsIFzdRYJSsJXWAH4_8Rg7b58oaTwag/edit#gid=18583798) is included in the project and your own dataset should follow the format

## Configuration
Set `INPUT_TZ` to the timezone of the dataset and `OUTPUT_TZ` to the timezone for results to show.

## License
MIT
