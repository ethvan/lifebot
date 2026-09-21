import os
import discord
from discord import app_commands
from discord.ext import commands
from dotenv import load_dotenv
from db import init_db, add_todo, list_todos, complete_todo, delete_todo, add_reminder, get_due_reminders, delete_reminder
from datetime import datetime, timedelta
from discord.ext import tasks
import aiohttp

load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")

# Creates Bot Object
intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents = intents)

# Bot Entry Message
@bot.event
async def on_ready():
    await init_db()
    await bot.tree.sync()
    if not reminder_loop.is_running():
        reminder_loop.start()
    print(f"{bot.user} online...")

# Ping
@bot.tree.command(name="ping", description = "Check to see if the bot is online")
async def ping(interaction: discord.Interaction):
    await interaction.response.send_message("I'm alive!")

# Todo Commands
todo_group = app_commands.Group(name="todo", description = "Manage your todo list")

# Add Item or Create Todo List
@todo_group.command(name="add", description = "Adds an item to the todo list")
@app_commands.describe(task = "Task you want to add to the list")
async def todo_add(interaction: discord.Interaction, task: str):
    await add_todo(str(interaction.user.id), task)
    await interaction.response.send_message(f"Added {task} to the list.", ephemeral = True)

# Print Todo List
@todo_group.command(name="todo_list", description = "Prints your current todo list")
async def todo_list(interaction: discord.Interaction):
    rows = await list_todos(str(interaction.user.id))

    if not rows:
        await interaction.response.send_message("Use /todo add to add tasks to your list!", ephemeral=True)
        return

    lines = []
    for tid, task, done in rows:
        mark = "✅" if done else "❌"
        lines.append(f"{mark} [#{tid}] {task}")

    await interaction.response.send_message("\n".join(lines), ephemeral=True)

# Marks Task as Done
@todo_group.command(name="mark_done", description = "Mark your task as complete")
@app_commands.describe(todo_id = "Task ID you want to mark as complete")
async def mark_done(interaction: discord.Interaction, todo_id: int):
    status = await complete_todo(str(interaction.user.id), todo_id)

    if status == "complete":
        await interaction.response.send_message(f"✅ Task #{todo_id} marked as complete!", ephemeral=True)

    elif status == "already_done":
        await interaction.response.send_message(f"⚠️ Task #{todo_id} is already complete!", ephemeral=True)

    else:
        await interaction.response.send_message(f"❌ No task found with ID #{todo_id}!", ephemeral=True)

# Deletes a Task
@todo_group.command(name="delete_task", description = "Delete a task")
@app_commands.describe(todo_id = "Task ID you want to delete")
async def delete_task(interaction:discord.Interaction, todo_id: int):
    task = await delete_todo(str(interaction.user.id), todo_id)
    if task is None:
        await interaction.response.send_message(f"❌ No task found with ID #{todo_id}!", ephemeral=True)
    else:
        await interaction.response.send_message(f"🗑️ Deleted Task #{todo_id}: {task}!", ephemeral = True)

# Sets a Reminder
@bot.tree.command(name="remind", description = "⏰ Set a reminder")
@app_commands.describe(
    message = "What to remind you about",
    time = "When send reminder e.g. 30m, 2h, 1d"
)
async def remind(interaction:discord.Interaction, message: str, time: str):
    # Validate and parse time string
    units = {"m": "minutes", "h": "hours", "d": "days"}

    if len(time) < 2 or time[-1] not in units:
        await interaction.response.send_message(
            "⚠️ Invalid time format. Please format like '30m', '2h' or '1d'.", 
            ephemeral = True
            )
        return
    try:
        amount = int(time[:-1])
    except ValueError:
        await interaction.response.send_message(
            "⚠️ Invalid time format. Please format like '30m', '2h' or '1d'.", 
        )
        return

    # Build timedelta
    unit_key = units[time[-1]]
    delta = timedelta(**{unit_key: amount})

    # Computes as a formatted UTC time
    remind_at = (datetime.utcnow() + delta).strftime("%Y-%m-%d %H:%M:%S")

    # Save and confirm
    reminder_id = await add_reminder(str(interaction.user.id), message, remind_at)
    await interaction.response.send_message(
        f"⏰ Reminder set: **{message}** for **{time}** from now",
        ephemeral=True
    )

# Every 30 seconds, check reminders and send user DM if needed
@tasks.loop(seconds = 30)
async def reminder_loop():
    due = await get_due_reminders()
    for reminder_id, user_id, message in due:
        try:
            user = await bot.fetch_user(int(user_id))
            await user.send(f"⏰ Reminder: {message}")
        except Exception as e:
            print(f"Failed to message {user_id}: {e}")

        await delete_reminder(reminder_id)

# Weather
@bot.tree.command(name = "weather", description = "🌤️ Get current weather for a city")
@app_commands.describe(city="City name, e.g. Chicago")
async def weather(interaction: discord.Interaction, city: str):
    await interaction.response.defer()

    try:
        async with aiohttp.ClientSession() as session:
            # Geocode City
            geo_url = "https://geocoding-api.open-meteo.com/v1/search"
            async with session.get(geo_url, params={"name": city, "count": 1}) as resp:
                geo_data = await resp.json()

                if "results" not in geo_data:
                    await interaction.followup.send(f"❌ Couldn't find a city called **{city}**.")
                    return

                city_info = geo_data["results"][0]
                lat,lon = city_info["latitude"], city_info["longitude"]
                country = city_info.get("country", "")

            # Get Weather in City
            weather_url = "https://api.open-meteo.com/v1/forecast"
            params = {"latitude": lat, "longitude": lon, "current": "temperature_2m"}
            async with session.get(weather_url, params=params) as resp:
                weather_data = await resp.json()

                temp = weather_data["current"]["temperature_2m"]

                await interaction.followup.send(
                    f"🌤️ **{city_info['name']}, {country}** — {temp}°C"
                )
    except Exception as e:
        print(f"Weather error: {e}")
        await interaction.followup.send("❌ Something went wrong fetching the weather.")
    

bot.run(TOKEN)