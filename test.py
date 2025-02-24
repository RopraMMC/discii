import os
import asyncio
import discii

from dotenv import load_dotenv

client = discii.Client()


@client.on("READY")
async def bot_ready() -> None:
    print(f"The client is ready. The client's latency is {round(client.latency * 1000)}s")


@client.on("MESSAGE_CREATE")
async def on_message(message: discii.Message):
    print(f"Message detected. Content: {message.content}")

    embed = discii.Embed(
        title="Hello, this is the TITLE.", timestamp=message.timestamp, colour=0xFFFFF
    )
    embed.add_field(name="Hello, I am a field!", value="I am a field value!")
    embed.set_author(name="My name is Discii!")

    if message.author.bot:
        return

    if message.content.lower() == "hi":
        await message.reply(embeds=[embed])

    test_channel = client.get_channel(953049224516370493)
    if test_channel is not None:
        await test_channel.send("Heyo!")
    
    await message.author.send("hello...")
    


if __name__ == "__main__":
    load_dotenv()
    asyncio.run(client.start(os.environ["BOT_TOKEN"]))
