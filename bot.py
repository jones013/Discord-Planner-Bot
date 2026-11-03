import discord
from discord import app_commands
import os
from dotenv import load_dotenv
load_dotenv()

token  = os.environ.get("DISCORD_TOKEN")

client = discord.Client(intents=discord.Intents.default())
tree = app_commands.CommandTree(client)

assignments = []


@tree.command(name="add", description="Add an assignment")
async def add(
    interaction: discord.Interaction,
    title: str,
    due: str
):
    print ("Add command")
    assignments.append({"title": title, "due": due})
    await interaction.response.send_message(
        f"Added: {title} (due {due})"
    )


@tree.command(name="schedule", description="See all added assignments")
async def schedule(interaction: discord.Interaction):
    print ("Schedule command")
    if len(assignments) == 0:
        await interaction.response.send_message("No assignments yet.")
        return

    message = "**Assignment Queue**\n"
    number = 1

    for a in assignments:
        message += f"{number}. {a['title']} - due {a['due']}\n"
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
    await tree.sync()
    print("Bot is ready")


client.run(token)