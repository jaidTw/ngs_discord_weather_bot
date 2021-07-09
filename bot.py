#!/usr/bin/env python3

import os
from enum import IntEnum
from datetime import datetime, timezone, timedelta, date
from dotenv import load_dotenv
from discord.ext import commands, tasks

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
CHANNEL = int(os.getenv('DISCORD_CHANNEL'))
TZ_TOKYO = timezone(timedelta(hours=9))
TZ_TAIPEI = timezone(timedelta(hours=8))

NEXT_STORM_COUNT = 3
DATASET_FILE = './predicted_dataset'
INPUT_TZ = TZ_TOKYO
OUTPUT_TZ = TZ_TAIPEI
NOTIFY_BEFORE = 10 # minutes
LANG = 'tc'
DEBUG = True


notification_msg = {
    'tc': [
        f"{NOTIFY_BEFORE} 分鐘後エアリオ地區即將發生雷雨！時間為：\n",
        f"本次之後的後 {NEXT_STORM_COUNT - 1} 次雷雨時間為：\n>>> " ],
    'en': [
        f"Storm is about to happen in Aelio region after {NOTIFY_BEFORE} minutes\n",
        f"Following {NEXT_STORM_COUNT - 1} storms would be at\n>>> " ],
    'jp': [
        f"{NOTIFY_BEFORE} 分後、エアリオリージョンで雷雨の発生が予想されています\n", 
        f"今回以降 {NEXT_STORM_COUNT - 1} 回の雷雨予想時間は以下となります\n>> "]
}

class WeatherType(IntEnum):
    CLEAR = 0
    CLOUDY = 1
    RAIN = 2
    STORM = 3

weather_table = {
    'clear': WeatherType.CLEAR,
    'cloudy': WeatherType.CLOUDY,
    'rain': WeatherType.RAIN,
    'storm': WeatherType.STORM
}

weather_emoji = {
    WeatherType.CLEAR: ":sunny:",
    WeatherType.CLOUDY: ":cloud:",
    WeatherType.RAIN: ":cloud_rain:",
    WeatherType.STORM: ":thunder_cloud_rain:"
}

class Weather:
    def __init__(self, weather, time, length):
        self.weather = weather_table[weather]
        self.time = datetime.fromisoformat(time)
        self.len = length

    def isclear(self):
        return self.weather == WeatherType.CLEAR

    def iscloudy(self):
        return self.weather == WeatherType.CLOUDY

    def israin(self):
        return self.weather == WeatherType.RAIN

    def isstorm(self):
        return self.weather == WeatherType.STORM

    def __str__(self):
        e = f'{weather_emoji[self.weather]}\t'
        s = f"{to_HrMin(self.time, OUTPUT_TZ)} ~ {to_HrMin(self.time + timedelta(minutes=self.len), OUTPUT_TZ)}"
        if self.len > 6 and self.isstorm():
            s = '**' + s + '**'
        return e + s

    def __repr__(self):
        return str(self)

    def __len__(self):
        return self.len


def to_HrMin(time, tz):
    return time.astimezone(tz).strftime('%H:%M')


def normalize_data(line):
    weather, time, length, rerolls = line.split()
    h, m = map(int, length.split(':'))
    return Weather(weather, time, h * 60 + m)


with open(DATASET_FILE, 'r') as f:
    dataset = list(map(normalize_data, f.readlines()))


bot = commands.Bot("s!")

"""
Event Loop:
Notify storm before NOTIFY_BEFORE minute(s)
"""
@tasks.loop(minutes=1)
async def check_storm():
    now = datetime.now(tz=INPUT_TZ)
    storms = list(filter(lambda x: x.time > now and x.isstorm(), dataset))

    if any(storms):
        next_time = storms[0].time
        print(f"[DEBUG] next_storm={next_time}, delta={next_time - now}")

    candidate = list(filter(
        lambda x: timedelta(minutes=NOTIFY_BEFORE + 1) > x[1].time - now >= timedelta(minutes=NOTIFY_BEFORE)
    , enumerate(storms)))

    if any(candidate):
        idx, next_storm = candidate[0]
        msg = notification_msg[LANG][0]
        msg += '> ' + str(next_storm) + '\n'
        msg += notification_msg[LANG][1]
        if len(storms) > 1:
            msg += '\n'.join(map(str, storms[idx + 1:idx + NEXT_STORM_COUNT]))
        else:
            msg += '暫無資料'
        await bot.get_channel(CHANNEL).send(msg)

@check_storm.before_loop
async def before():
    await bot.wait_until_ready()
    print("Finished waiting")


"""
List all today's storms
"""
@bot.command()
async def today(ctx):
    storms = list(filter(
        lambda x: x.time.astimezone(OUTPUT_TZ).date() == datetime.now(OUTPUT_TZ).date() and x.isstorm()
    , dataset))

    msg = '\n'.join(map(str, storms)) if any(storms) else '暫無資料'
    await ctx.send('今日所有雷雨：\n>>> ' + msg)

"""
List next n storms
"""
@bot.command()
async def next(ctx, arg='3'):
    try:
        n = 10 if int(arg) > 10 else int(arg)
    except ValueError:
        return

    storms = list(filter(lambda x: x.time > datetime.now(tz=INPUT_TZ) and x.isstorm(), dataset))

    msg = '\n'.join(map(str, storms[:n]))
    if len(storms) < n:
        msg += '\n暫無資料'
    await ctx.send(f"後 {n} 次雷雨時間為\n>>> " + msg)


"""
List near future weather
"""
@bot.command()
async def weather(ctx):
    COUNT = 3
    msg = ''
    current = list(filter(
        lambda x: (
            lambda idx, data:
            data.time + timedelta(minutes=len(data)) > datetime.now(INPUT_TZ) >= data.time
        )(*x),
        enumerate(dataset)))

    msg += f'エアリオ　　\t'
    if any(current):
        idx, _ = current[0]
        msg += '\n　　　　　　\t'.join(map(str, dataset[idx:idx + COUNT]))
    else:
        msg += ':question:\t暫無資料'
        
    await ctx.send("即時天氣\n>>> " + msg)

check_storm.start()
bot.run(TOKEN)
