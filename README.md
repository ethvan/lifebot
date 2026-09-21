# LifeBot

A Discord bot for creating and managing a personal to-do list, with persistent storage.

![screenshot](LifeBotFeatures.png)

## Features

- `/todo add` - Add a task to your list
- `/todo list` - Show all of your tasks with their IDs and completion status
- `/todo done` - Mark a task as completed by its ID
- `/todo delete` - Delete a task from the list by its ID
- `/ping` - Health check to confirm the bot is online
- `/remind set` - Set a reminder (`/remind set message:take a break time:30m`); the bot DMs you when time is up
- `/remind list` - Lists all upcoming reminders
- `/remind delete` - Delete an upcoming reminder
- `/weather` - Tells you the current weather for a city

All replies are ephemeral(only the user who ran the command sees them).

## Tech Stack

- **Python 3.14** - main language
- **discord.py 2.7** - Discord API wrapper and slash command framework
- **aiosqlite 0.22** - async SQLite driver for database access
- **SQLite** - local database storage (single file, no server required)
- **python-dotenv** - loads secrets from a `.env` file

## Setup

1. **Clone the repo:**

    ```
    git clone https://github.com/ethvan/lifebot.git
    cd lifebot
    ```

2. **Create and activate a virtual environment:**

    ```
    python -m venv venv
    venv\Scripts\activate.bat
    ```

3. **Install dependencies:**

    ```
    pip install -r requirements.txt
    ```

4. **Create a `.env` file** in the project root with your Discord bot token:

    ```
    DISCORD_TOKEN=your_token_here
    ```

    To get a token:

    - Go to https://discord.com/developers/applications
    - Create a new application, then a bot
    - Copy the token from the Bot tab
    - Invite the bot to a server using the OAuth2 URL Generator (scopes: `bot`, `applications.commands`; permissions: `Send Messages`, `Read Message History`)

5. **Run the bot:**

    ```
    python bot.py
    ```

    You should see `LifeBot#8795 online...`. Then type `/todo add` in Discord to test.

## What I Learned

- **SQL in practice** — Designing schemas, writing `SELECT`/`INSERT`/`UPDATE`/`DELETE` queries, and handling edge cases (like "not found" vs. "already done")
- **Async Python** — Using `async`/`await` throughout taught me why asynchronous code matters for network I/O, and how to structure a program that stays responsive while waiting on external services.
- **Background tasks** — Used `discord.ext.tasks` to run a loop every 30 seconds, querying for due reminders and sending DMs. Learned about idempotency and why fired reminders must be deleted from the DB to avoid repeat fires.
- **Discord's API model** — Slash commands, command groups, interaction responses, ephemeral replies, and the WebSocket event loop all work together in a specific way.
- **External APIs** — Chained two calls to Open-Meteo (geocoding → weather) and handled the "city not found" case where the API returns no results key.

## License

MIT — see [LICENSE](LICENSE) for details.
