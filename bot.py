import os
import discord
from discord import app_commands
from discord.ext import commands
from dotenv import load_dotenv
from db import init_db, add_todo, list_todos, complete_todo, delete_todo, add_reminder
from datetime import datetime, timedelta

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
    print(f"{bot.user} online...")

# Ping
@bot.tree.command(name="ping", description = "Check to see if the bot is online")
async def ping(interaction: discord.Interaction):
    await interaction.response.send_message("I'm alive!")

# Add Item or Create Todo List
@bot.tree.command(name="todo_add", description = "Adds an item to the todo list")
@app_commands.describe(task = "Task you want to add to the list")
async def todo_add(interaction: discord.Interaction, task: str):
    await add_todo(str(interaction.user.id), task)
    await interaction.response.send_message(f"Added {task} to the list.", ephemeral = True)

# Print Todo List
@bot.tree.command(name="todo_list", description = "Prints your current todo list")
async def todo_list(interaction: discord.Interaction):
    rows = await list_todos(str(interaction.user.id))

    if not rows:
        await interaction.response.send_message("Use /todo_add to add tasks to your list!", ephemeral=True)
        return

    lines = []
    for tid, task, done in rows:
        mark = "✅" if done else "❌"
        lines.append(f"{mark} [#{tid}] {task}")

    await interaction.response.send_message("\n".join(lines), ephemeral=True)

# Marks Task as Done
@bot.tree.command(name="mark_done", description = "Mark your task as complete")
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
@bot.tree.command(name="delete_task", description = "Delete a task")
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
        f"⏰ Reminder set: **{message}** for **{amount}{time}** from now",
        ephemeral=True
    )

bot.run(TOKEN)