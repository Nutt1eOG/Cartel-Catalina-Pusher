# Discord Task Management Bot

A Discord bot for managing tasks within a server. Users with specific roles can create tasks, and users with the "Pusher" role can take and complete these tasks.

## Features

- Create tasks with optional price information
- Take tasks (restricted to users with the "Pusher" role)
- Mark tasks as completed
- Automatic notifications in a dedicated channel when tasks are completed

## Setup

### Prerequisites

- Python 3.8 or higher
- A Discord bot token (create one at [Discord Developer Portal](https://discord.com/developers/applications))
- Proper permissions for the bot in your Discord server

### Installation

1. Clone this repository:
   ```
   git clone <repository-url>
   cd <repository-directory>
   ```

2. Install the required dependencies:
   ```
   pip install -r requirements.txt
   ```

3. Create a `.env` file based on the provided `.env.example`:
   ```
   cp .env.example .env
   ```

4. Edit the `.env` file with your Discord bot token and channel IDs:
   ```
   DISCORD_TOKEN=your_discord_bot_token_here
   OPGAVE_KANAL_ID=your_task_channel_id
   KLAREDE_KANAL_ID=your_completed_tasks_channel_id
   ```

### Running the Bot Locally

Run the bot with:
```
python bot.py
```

### Deploying on Render

You can deploy this bot on Render for 24/7 uptime:

1. **Create a New Web Service on Render**
   - Go to [Render Dashboard](https://dashboard.render.com/)
   - Click "New" and select "Web Service"
   - Connect your GitHub repository or upload the files directly

2. **Configure the Web Service**
   - **Name**: Choose a name for your service (e.g., "discord-task-bot")
   - **Environment**: Select "Python"
   - **Region**: Choose a region close to your users
   - **Branch**: main (or your default branch)
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `python bot.py`

3. **Set Environment Variables**
   - In your service settings, go to the "Environment" tab
   - Add the following environment variables:
     - `DISCORD_TOKEN`: Your Discord bot token
     - `RENDER`: Set to "true" (this tells the bot it's running on Render)
     - `OPGAVE_KANAL_NAVN`: Name for the tasks channel (default: "opgaver")
     - `KLAREDE_KANAL_NAVN`: Name for the completed tasks channel (default: "klarede-opgaver")
     - `OPGAVE_KANAL_ID`: (Optional) ID of an existing tasks channel
     - `KLAREDE_KANAL_ID`: (Optional) ID of an existing completed tasks channel

4. **Deploy the Service**
   - Click "Create Web Service"
   - Render will automatically build and deploy your bot

## Usage

### Commands

- `/opretopgave [opgave] [pris]` - Create a new task with an optional price
  - Only users with the "Fuldgyldigt medlem" or "Ledelse" roles can create tasks

### Buttons

- **Tag opgave** - Take a task (only available to users with the "Pusher" role)
- **Marker som klaret** - Mark a task as completed (only available to the user who took the task)

## Configuration

You can customize the bot by modifying the following variables in `bot.py`:

- `FULDGYLDIG_ROLLER` - List of role names that can create tasks
- `PUSHER_ROLLE` - Role name for users who can take tasks

## License

[Specify your license here]
