# Discord EmbedBuilder

[![PyPI version](https://img.shields.io/pypi/v/py-embedbuilder.svg)](https://pypi.org/project/py-embedbuilder/)
[![Python Versions](https://img.shields.io/pypi/pyversions/py-embedbuilder.svg)](https://pypi.org/project/py-embedbuilder/)
[![License](https://img.shields.io/github/license/Ypuf/embedbuilder.svg)](https://github.com/Ypuf/embedbuilder/blob/main/LICENSE)

Does a lot of shit and simplifies discord's annoying and lengthy embed creation process.

This does NOT *require* 3.11+ necessarily, it just hasn't been TESTED for anything older.

If you CAN confirm that it works for 3.9/3.10 create an issue on the GitHub and I'll update accordingly.


## Installation
```bash
pip install py-embedbuilder
```
From there you can just..

## Example
```py
import discord
from discord.ext import commands
from embedbuilder import EmbedBuilder

@bot.command(name="example")
async def example(ctx):
    msg = await EmbedBuilder(ctx) \
        .set_title("Welcome!") \
        .set_description("This is a basic embed") \
        .set_color(discord.Color.blue()) \
        .send()
```

or

```py
@bot.command(name="example")
async def example(ctx):
    builder = EmbedBuilder(ctx)
    messages = await (builder
                     .set_title("Welcome!")
                     .set_description("This is a basic embed")
                     .set_color(discord.Color.blue())
                     .send())
```

These both do the exact same thing it's just a matter of preference.

## "Quick" explanation of everything you can do

`?` denotes optional inputs and **SHOULD NOT** be included in the actual function. If there is no `?` it's a required field.
`|` at the end denotes aliases you can use as shorthand or valid alternative spellings.

### Basic stuff
```py
.set_title("Your title here") # | .title()
.set_description("Whatever you want to say") # | .description() | .desc()
.set_color(discord.Color.red())  # or any color | .set_colour | .color() | .colour()
.set_url("https://example.com")  # makes the title clickable | .url()
```

### Author details
Author details (author name, author icon url, author url) are incredibly simple.
```py
await EmbedBuilder(ctx).set_author("Cheap Credits", ?icon_url="https://example.com/img.png", ?url="https://cheap.ypuf.xyz") # | .author()
```

### Footer details
```py
await EmbedBuilder(ctx).set_footer("Visit my site!", ?icon_url="https://example.com/img.png") # .footer()
```

### Fields
These are just normal field inputs so it's title, description and then inline: true/false
```py
.add_field("Look at this number", "17", inline=True) # | .field()
.add_field("Another field", "Some value", inline=False)
.add_field("Woah another field", "with a value") # Inline is false by default
```

Optionally, you can also add multiple fields at once with a tuple

```py
fields = [
    ("Look at this number", "17", True),
    ("Another field", "Some value", False)
    ("Woah another field", "with a value") # Inline is false by default
]
await EmbedBuilder(ctx).add_fields(fields) # | .fields()
```

### Images and thumbnails
```py
.set_thumbnail("https://example.com/small_image.png")  # small image in top right | .thumb()
.set_image("https://example.com/big_image.png")       # big image at bottom | .image() | .img()
```

### Files and attachments
```py
.set_file_path("./my_image.png")  # attach a local file | .file_path() | .f_path()
.add_file(discord.File("another_file.txt"))  # or add discord files directly | .file() | .f()
```

### Message content (outside the embed)
```py
await EmbedBuilder(ctx).set_content("This text appears above the embed") # | .content()
```

### Timestamps
```py
.set_timestamp()  # uses current time | .timestamp()
.set_timestamp(some_datetime_object)  # or your own time
.set_timezone('America/New_York')  # change timezone if needed
```

## For slash commands
Works exactly the same but pass the interaction instead of ctx:
```py
@bot.slash_command()
async def slash_example(interaction):
    await EmbedBuilder(interaction) \
        .set_title("Slash command embed") \
        .set_ephemeral(True) \ # | .ephemeral()
        .send()  # only the user who ran the command can see it due to ephemeral being True
```

## Long descriptions? No problem
If your description is too long, it'll automatically split it into multiple embeds:
```py
really_long_text = "Lorem ipsum..." * 5000

await EmbedBuilder(ctx) \
    .set_title("Long ass message") \
    .set_description(really_long_text) \
    .send()  # automatically creates multiple embeds
```

## Pagination for fancy stuff
Want actual page navigation? Enable pagination:
```py
builder = EmbedBuilder(ctx).enable_pagination()

# Add custom pages
builder.add_page(title="Page 1", description="First page content") # | .page()
builder.add_page(title="Page 2", description="Second page content")
builder.add_page(title="Page 3", description="Third page content")

await builder.send()  # creates navigation buttons
```

## Other useful shit

### Reply to messages
```py
# | .reply()
.set_reply(True)   # default behavior (if you're sending to a specific channel it won't reply to the user anyway)
.set_reply(False)  # don't reply, just send normally
```

### Auto-delete messages
```py
await EmbedBuilder(ctx).set_delete_after(30)  # deletes after 30 seconds | .delete_after() .delete()
```

### Edit existing messages instead of sending new ones
```py
old_message = await EmbedBuilder().... # any old embedbuilder function or any old embed at all
await EmbedBuilder(ctx) \
    .edit_message(old_message) \ # | .edit()
    .set_title("Done!") \
    .send()
```

### Forums and threads
(IF YOURE CREATING A FORUM) Forums are a little bit "complicated" with a specific call being required.

If the forum already exists, it acts as a normal channel.
```py
await EmbedBuilder(forum_channel) \
    .create_forum_thread( # | .forum() | .forum_thread() | .create_forum
        name="Bug report 2077!",
        ?content="Pls help johnny silverhand is in my head." # Optional, defaults to embed content.
    ) \
    .set_title("Please patch!!") \
    .set_description("So this would actually appear as embedded text") \
    .send()
```
(IF YOU'RE CREATING A THREAD) You have a lot of input options for this.

If the thread already exists, it acts as a normal channel.
```py
await EmbedBuilder(ctx) \
    .set_title("Any embed title") \
    .set_description("Any embed description") \
    # | .thread()
    .create_thread("New thread!", ?auto_archive_duration=10080, ?reason="I felt like creating one lol xd") \ # Duration is in minutes.
    .send()
```
I'm pretty sure auto_archive_duration has to be very rigid times but I'm not entirely sure of that.

Don't pass in `None` to auto_archive_duration.

## Testing
Currently 64 different tests are run every update to ensure quality however this does not GUARANTEE quality as I am still human.

## That's basically it
The library handles all the annoying Discord limits and validation for you. Just chain the methods you want and call `.send()` at the end.

If something breaks, it'll probably tell you what went wrong instead of just dying silently like Discord's API likes to do.


## Instructions to self-build
Install the source code from https://github.com/Ypuf/EmbedBuilder/releases

(If you're willing to self build I'm going to assume you know what most of this means)

```pwsh
pip install build
```

cd into whatever directory you've installed the source code

```ps1
python -m build
```

then, to install it

```powershell
pip install .
```
