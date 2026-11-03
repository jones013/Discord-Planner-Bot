import discord
from datetime import datetime
from discord import app_commands
import os
from discord.ext import tasks
from dotenv import load_dotenv
load_dotenv()

token  = os.environ.get("DISCORD_TOKEN")

client = discord.Client(intents=discord.Intents.default())
tree = app_commands.CommandTree(client)

assignments = []

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
    #Checks every 30 seconds for the assignments that are due
    now = datetime.now()

    for item in assignments:
        if item["reminder_time"] <= now and not item["reminded"]:
            channel = client.get_channel(item["channel_id"])
            if channel is None:
                try:
                    channel = await client.fetch_channel(item["channel_id"])
                except discord.HTTPException:
                    continue

            if channel:
                due_str = item["due"].strftime("%m/%d/%Y %H:%M")
                try:
                    await channel.send(f"<@{item['user_id']}> **Reminder:** Assignment `{item['title']}` is due now!" 
                                       f"Final deadline is: {due_str}")
                except discord.HTTPException:
                    pass

            # It will prevent the bot to keep "reminding" every 30 seconds
            item["reminded"] = True 




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

    assignments.append({"title": title,
                        "due": due_date,
                        "reminder_time": reminder_time,
                        "channel_id": interaction.channel_id,
                        "user_id": interaction.user.id,
                        "reminded": False})

    assignments.sort(key=lambda x: x["due"])

    due_str = due_date.strftime("%m/%d/%Y %H:%M")
    remind_str = reminder_time.strftime("%m/%d/%Y %H:%M")

    await interaction.response.send_message(
        f"Added: {title}\nDue: {due_str}\n Reminder Set For: {remind_str}"
    )


@tree.command(name="schedule", description="See all added assignments")
async def schedule(interaction: discord.Interaction):
    print ("Schedule command")
    if len(assignments) == 0:
        await interaction.response.send_message("No assignments yet.", ephemeral=True)
        return

    message = "**Assignment Queue**\n"
    number = 1

    for a in assignments:
        due_str = a["due"].strftime("%m/%d/%Y %H:%M")
        remind_str = a["reminder_time"].strftime("%m/%d/%Y %H:%M")
        status = "(Reminder Sent)"  if a["reminded"] else "(Pending)"
        message += (f"**{number}.** {a['title']} {status}\n"
            f"   • Due: `{due_str}`\n"
            f"   • Alert at: `{remind_str}`\n")
        number += 1

    await interaction.response.send_message(message)


@tree.command(name="delete", description="Delete an assignment by queue number")
async def delete(interaction: discord.Interaction, number: int):
    if number < 1 or number > len(assignments):
        await interaction.response.send_message(
            "Invalid number. Use /schedule to see the queue."
        )
        return

    removed = assignments.pop(number - 1)

    await interaction.response.send_message(
        f"Deleted: {removed['title']}"
    )



@client.event
async def on_ready():
    if not check_due_dates.is_running():
        check_due_dates.start()
    
    await tree.sync()
    print("Bot is ready")


client.run(token)