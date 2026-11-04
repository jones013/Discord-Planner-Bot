import discord
from database import (
    init_db,
    add_event,
    get_events,
    get_due_events,
    delete_event,
    mark_reminded,
)
from datetime import datetime
from discord import app_commands
import os
from discord.ext import tasks
from dotenv import load_dotenv
load_dotenv()

token  = os.environ.get("DISCORD_TOKEN")

if not token:
    raise RuntimeError("DISCORD_TOKEN is not set")


client = discord.Client(intents=discord.Intents.default())
tree = app_commands.CommandTree(client)

def parse_date(date_str: str):
    #function to not double the strptime for due and reminders
    for fmt in ("%m/%d/%Y %H:%M", "%m/%d/%Y"):
        try:
            return datetime.strptime(date_str.strip(), fmt)
        except ValueError:
            continue
    return None

@tasks.loop(seconds=30)
async def check_due_dates():
    for item in get_due_events():
        channel = client.get_channel(item["channel_id"])

        if channel is None:
            try:
                channel = await client.fetch_channel(item["channel_id"])
            except discord.HTTPException:
                continue


        if not isinstance(channel, discord.abc.Messageable):
            continue
        due_date = datetime.fromisoformat(item["due"])

        try:
            await channel.send(
                f"<@{item['user_id']}> **Reminder:** "
                f"Assignment `{item['title']}` is due now!\n"
                f"Final deadline is: {due_date:%m/%d/%Y %H:%M}"
            )
            mark_reminded(item["id"])
        except discord.HTTPException:
            pass




@tree.command(name="add", description="Add an assignment with a custom reminder alert date")
@app_commands.describe(
    title="Assignment title",
    due="Final due date (MM/DD/YYYY or MM/DD/YYYY HH:MM)",
    remind_at="Set reminder with (MM/DD/YYYY or MM/DD/YYYY HH:MM)")

async def add(
    interaction: discord.Interaction,
    title: str,
    due: str,
    remind_at: str
):
    print ("Add command")
    
    # %Y = 4-digit year, %m = 2-digit month, %d = 2-digit day
    due_date = parse_date(due)
    reminder_time = parse_date(remind_at)   

    if not due_date or not reminder_time:
        await interaction.response.send_message("Invalid date format. Use MM/DD/YYYY HH:MM", ephemeral = True)
        return

    add_event(
        interaction.guild_id,
        title,
        due_date,
        reminder_time,
        interaction.channel_id,
        interaction.user.id,
    )


    due_str = due_date.strftime("%m/%d/%Y %H:%M")
    remind_str = reminder_time.strftime("%m/%d/%Y %H:%M")

    await interaction.response.send_message(
        f"Added: {title}\nDue: {due_str}\n Reminder Set For: {remind_str}"
    )


@tree.command(name="schedule", description="See all added assignments")
async def schedule(interaction: discord.Interaction):
    print ("Schedule command")

    message = "**Assignment Queue**\n"



    events = get_events(interaction.guild_id)

    if not events:
        await interaction.response.send_message(
        "No assignments yet.",
        ephemeral=True,
        )
        return


    for number, event in enumerate(events, start=1):
        due_date = datetime.fromisoformat(event["due"])
        reminder_time = datetime.fromisoformat(event["reminder_time"])

        status = "(Reminder Sent)" if event["reminded"] else "(Pending)"

        message += (
            f"**{number}.** {event['title']} {status}\n"
            f"   • Due: `{due_date:%m/%d/%Y %H:%M}`\n"
            f"   • Alert at: `{reminder_time:%m/%d/%Y %H:%M}`\n"
        )

    await interaction.response.send_message(message)


@tree.command(name="delete", description="Delete an assignment by queue number")
async def delete(interaction: discord.Interaction, number: int):
    events = get_events(interaction.guild_id)

    if number < 1 or number > len(events):
        await interaction.response.send_message(
            "Invalid number. Use /schedule to see the queue."
        )
        return

    event = events[number - 1]
    delete_event(event["id"], interaction.guild_id)

    await interaction.response.send_message(
        f"Deleted: {event['title']}"
    )



@client.event
async def on_ready():
    if not check_due_dates.is_running():
        check_due_dates.start()
    
    await tree.sync()
    print("Bot is ready")

init_db()
client.run(token)