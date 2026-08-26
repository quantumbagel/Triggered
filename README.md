# Triggered - A IFTTT discord bot

Triggered is a Discord bot that you can configure to take an input action
(like a message being sent with certain text, or a member joining a certain voice channel) and perform output actions
(like sending a DM with information on what happened).
I have tried to make this bot extensible (so it's very easy to add your own input and output actions).

[Invite the hosted bot](https://discord.com/api/oauth2/authorize?client_id=1181338133204307968&permissions=268454912&response_type=code&redirect_uri=https%3A%2F%2Fgithub.com%2Fquantumbagel&scope=bot+applications.commands.permissions.update+applications.commands) · [Author](https://github.com/quantumbagel)

The invite is just my personal instance (not fully hosted yet). If you actually need this to stay up, self-host it.

Alright, let's get started!

## How do I set it up locally?

You need:

- Python 3.10+
- MongoDB running locally (please don't use Atlas — this bot talks to the database a *lot* :D)
- A Discord bot with the privileged intents turned on: Server Members, Message Content, and Presence

1. Go to [Discord's developer website](https://discord.com/developers/applications) and create a bot. [Official tutorial](https://discord.com/developers/docs/getting-started)
2. Enable those intents, copy the token.
3. Invite the bot with `applications.commands` plus send messages / embed links / add reactions. Manage roles, move members, kick, timeout, and ban are only needed if you actually use those dos.
4. Clone this repo:

```bash
git clone https://github.com/quantumbagel/Triggered.git
cd Triggered
git checkout main
python3 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -e .
```

5. Copy `configuration/config.example.json` to `configuration/config.json` and fill in your token, owner ID, and Mongo URI (`mongodb://localhost:27017` is the default). Don't commit that file, it's gitignored for a reason.
6. Start MongoDB, then `python bot.py`.
7. In a server the bot can see, send `triggered/sync` as the owner. After that, `/triggered` should show up.

Please open an issue if you're having any trouble setting this up.

### Config

Everything lives in `configuration/config.json`. You can also override keys with `TRIGGERED_*` env vars (that's what Docker does).

| Key | What it is |
| --- | --- |
| `bot_secret` | Bot token |
| `mongodb_uri` | Mongo connection string |
| `owner_id` | Your Discord user ID (`triggered/sync` etc) |
| `max_dos_per_trigger` | Cap on dos per trigger (default 3) |
| `argument_length_limit` | Max length for names/text (default 128) |
| `allowed_execution` | leftover, unused |

`configuration/requirements.json` is **not** server config. It tells the bot which trigger/do classes to load (`contains-text` → `actions/triggers/contains_text.py` unless you set `"module"`).

## How do you actually use the bot?

A trigger is "when X happens". A do is "then do Y". Only the person who made the trigger (or the server owner) can add/delete dos or delete the trigger.

Slash commands don't work in DMs. Autocomplete only shows 25 things at a time — type more to narrow it down.

NB: `[]` = required, `{}` = optional

### Slash commands

| Command | What it does |
| --- | --- |
| `/triggered new [name] [trigger] {description} {trigger_*}` | Make a trigger. Type in `trigger` to search types. Extra args depend on the type (`trigger_text`, `trigger_role`, `trigger_member`, `trigger_emoji`, `trigger_vc`, `trigger_channel`, …). Durations are `60s` / `5m` / `1h` / `1d` (or just seconds). |
| `/triggered add [trigger_name] [do] [do_name] {description} {do_*}` | Attach a do. Same deal with extra args (`do_channel`, `do_member`, `do_role`, `do_emoji`, `do_text`, `do_vc`, …). |
| `/triggered delete [to_delete] [trigger_name] {do_name}` | Delete a trigger (and its dos) or one do. |
| `/triggered view [mode] {query}` | `List all`, `View` one by name, or `Search` by name / author / type. |
| `/triggered server-configure` | Server permission settings. Needs Discord Administrator. |
| `/triggered user-configure` | Your personal white/blacklist of other people. |
| `/triggered about` | About the project. This one works in DMs. |

### Owner text commands

These only work if your Discord ID matches `owner_id`.

| Message | What it does |
| --- | --- |
| `triggered/sync` | Sync slash commands globally |
| `triggered/sync this` | Sync to this server |
| `triggered/sync <guild_id>` | Sync to that server |
| `triggered/disable` | Stop handling commands without killing the process |
| `triggered/enable` | Turn them back on |
| `triggered/toggle` | Flip it |
| `triggered/emoji-upload` | Upload missing custom emojis from `assets/emoji` |

### Built-in triggers

| Name | ID | Fires on | Argument |
| --- | --- | --- | --- |
| Contains Text | `contains-text` | message sent | `trigger_text` (substring) |
| Contains Word | `contains-word` | message sent | `trigger_text` (whole word) |
| Role Mentioned | `role-mentioned` | message sent | `trigger_role` |
| User Mentioned | `user-mentioned` | message sent | `trigger_member` |
| Sent By | `sent-by` | message sent | `trigger_member` |
| In Channel | `in-channel` | message sent | `trigger_channel` |
| Has Attachment | `has-attachment` | message sent | none |
| Everyone Mentioned | `everyone-mentioned` | message sent | none (`@everyone` / `@here`) |
| Starts With | `starts-with` | message sent | `trigger_text` (prefix) |
| Message Edited | `message-edited` | message edited | optional `trigger_channel` |
| Message Deleted | `message-deleted` | message deleted | optional `trigger_channel` |
| Reaction Added | `reaction-added` | reaction added | `trigger_emoji` |
| Reaction Removed | `reaction-removed` | reaction removed | `trigger_emoji` |
| Joined VC Channel | `join-vc` | join voice | `trigger_vc` |
| Left VC Channel | `left-vc` | leave voice | `trigger_vc` |
| Role Added | `role-added` | gained a role | `trigger_role` |
| Role Removed | `role-removed` | lost a role | `trigger_role` |
| Nickname Changed | `nickname-changed` | nick changed | none |
| Member Boosted | `member-boosted` | boosted the server | none |
| Member Joined | `member-joined` | joined the server | none |
| Member Left | `member-left` | left the server | none |
| Scheduled | `scheduled` | timer | `trigger_text` like `5m` (min 15s) |

### Built-in dos

| Name | ID | Argument | What it does |
| --- | --- | --- | --- |
| Send Message | `send-message` | `do_channel` | Posts a "this rule fired" panel in that channel |
| Send DM | `send-dm` | `do_member` | Same panel, but as a DM |
| Send Text | `send-text` | `do_channel`, `do_text` | Posts your text in that channel |
| Reply | `reply` | `do_text` | Replies to the message (send/edit triggers only) |
| Add Reaction | `add-reaction` | `do_emoji` | Reacts to the message (send/edit only) |
| Delete Message | `delete-message` | none | Deletes the message (send/edit only) |
| Add Role | `add-role` | `do_role` | Gives that role to whoever fired it |
| Remove Role | `remove-role` | `do_role` | Takes that role away |
| Move to VC | `move-to-vc` | `do_vc` | Moves them into that VC (they have to already be in voice) |
| Kick Member | `kick-member` | none | Kicks them |
| Timeout Member | `timeout-member` | `do_text` | Times them out (`10m`, max 28d) |
| Ban Member | `ban-member` | none | Bans them |

Bots never fire triggers. If a do targets someone, their user-configure lists get checked first.

`add-role` / `remove-role` need **Manage Roles**, and the bot's role has to sit above the role you're giving/taking. `add-reaction` needs **Add Reactions**. `move-to-vc` needs **Move Members**. Kick / timeout / ban need the matching Discord permissions, and they skip the server owner and the bot itself.

Scheduled triggers wait one interval after you create them before they fire the first time. Message-deleted only works if Discord still had the message cached.

## Permissions

If a **Required Role** is set (`/triggered server-configure`), you need that role to use commands. If it isn't, your highest role has to sit above the bot's (the server owner can always use it).

Admins can white/blacklist channels and roles for triggers and dos separately. They start as blacklists (everything allowed except listed stuff). Hit `Switch Whitelist/Blacklist` to flip them.

`/triggered user-configure` is whether other people can write rules that target *you*. Those default to whitelist, so nobody can target you until you add them.

## Adding a custom trigger or do

The bot loads everything in `configuration/requirements.json`.

1. Subclass `actions.triggers.trigger.Trigger` or `actions.dos.do.Do`.
2. Implement `dropdown_name()`, `human()`, and `is_valid()` (triggers) or `execute()` (dos).
3. Drop the file in `actions/triggers/` or `actions/dos/`, named after the ID (`contains-text` → `contains_text.py`).
4. Register it in `configuration/requirements.json` with an ID, `class` name, `type` (triggers only), and `params`.

Trigger `type` has to be one of: `send_msg`, `vc_join`, `vc_leave`, `reaction_add`, `reaction_remove`, `member_join`, `member_leave`, `message_edit`, `message_delete`, `role_add`, `role_remove`, `nickname_change`, `member_boost`, `scheduled`.

Open a pull request if you want it in the public bot. Your contribution is appreciated!

## Docker

Copy `.env.example` to `.env`, put your token and owner ID in it, then:

```bash
docker compose up --build
```

That starts Mongo and the bot. Env vars from Compose override the example config inside the image.

If you'd rather use a local `configuration/config.json`, mount it onto `/app/configuration/config.json`. Env vars still win if they're set.

## Tests

```bash
pip install -e ".[dev]"
pytest
```