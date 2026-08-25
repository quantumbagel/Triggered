# Triggered

Triggered is a self-hostable Discord **if-this-then-that** bot. You create a **trigger** (something that happens in a server) and attach one or more **dos** (actions the bot should take). Example: if a message contains `hello`, send a notification embed to `#alerts`.

This repository is at **v1.0 RC1**. The public branch is [`main`](https://github.com/quantumbagel/Triggered/tree/main). Development happens on [`dev`](https://github.com/quantumbagel/Triggered/tree/dev).

[Invite the hosted bot](https://discord.com/api/oauth2/authorize?client_id=1181338133204307968&permissions=268454912&response_type=code&redirect_uri=https%3A%2F%2Fgithub.com%2Fquantumbagel&scope=bot+applications.commands.permissions.update+applications.commands) · [Author](https://github.com/quantumbagel)

---

## Features

- Slash-command workflow for creating, attaching, viewing, and deleting automations
- Built-in triggers for messages, reactions, voice channels, and member join/leave
- Built-in dos for sending a channel message or a DM
- Server-wide permission role plus channel/role white/blacklists
- Per-user white/blacklists so people can opt in or out of being targeted
- MongoDB storage, per-guild data isolation, and cleanup when the bot is kicked
- Optional git auto-update against `main`, `stable`, or `dev`

## Requirements

- Python **3.10+**
- A running **MongoDB** instance (local is strongly recommended; this bot talks to the database a lot)
- A Discord application/bot with these **Privileged Gateway Intents** enabled:
  - Server Members Intent
  - Message Content Intent
  - Presence Intent (the client currently requests all intents)

## Quick start (self-host)

```bash
git clone https://github.com/quantumbagel/Triggered.git
cd Triggered
git checkout main
python3 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

1. Create a Discord application at [https://discord.com/developers/applications](https://discord.com/developers/applications).
2. Create a bot user, copy the token, and enable the privileged intents listed above.
3. Invite the bot with `applications.commands` and permission to view channels, send messages, and embed links.
4. Start MongoDB. The default URI is `mongodb://localhost:27017`.
5. Edit `configuration/config.json` (see below).
6. Run the bot:

```bash
python bot.py
```

7. In a server the bot can see, send `triggered/sync` as the configured owner to register slash commands. After that, use `/triggered`.

---

## Configuration

All runtime settings live in `configuration/config.json`.

| Key | Type | Meaning |
| --- | --- | --- |
| `bot_secret` | string | Discord bot token. Keep this private. |
| `mongodb_uri` | string | MongoDB connection string. |
| `owner_id` | int | Discord user ID allowed to run owner text commands (`triggered/sync`, enable/disable). |
| `max_dos_per_trigger` | int | Maximum actions that can be attached to one trigger. Default: `3`. |
| `argument_length_limit` | int | Max length for names, descriptions, and text arguments. Default: `128`. |
| `allowed_execution` | int | Reserved for execution limits. |
| `check_for_updates` | bool | On startup, fetch the remote and warn if a newer commit exists. |
| `auto_update` | bool | If an update is available, check out the configured stream, pull, and exit so a process manager can restart you. |
| `update_to` | string | Git branch to follow: `main`, `stable`, or `dev`. |

`configuration/requirements.json` is **not** server config. It maps trigger/do IDs to Python classes so the bot can load them dynamically.

---

## How it works

A **trigger** is a named rule in a guild ("when X happens"). A **do** is an action attached to that trigger ("then do Y"). Only the trigger's author or the guild owner can add or delete dos / delete the trigger.

Typical flow:

1. `/triggered new` — create the trigger
2. `/triggered add` — attach a do
3. `/triggered view` — inspect it
4. Let Discord events fire it

Slash commands only work in guilds, not DMs.

### Slash commands

| Command | What it does |
| --- | --- |
| `/triggered new` | Create a trigger. Required: `name`, `trigger`. Optional: `description` plus the argument that trigger needs (`trigger_text`, `trigger_role`, `trigger_emoji`, `trigger_vc`, …). |
| `/triggered add` | Attach a do to an existing trigger. Required: `trigger_name`, `do`, `do_name`. Optional: `description` plus the argument that do needs (`do_channel`, `do_member`, …). |
| `/triggered delete` | Delete a trigger (and its dos) or a single do. |
| `/triggered view` | `List all`, `View` one trigger by name, or `Search` by name / author / type. |
| `/triggered server-configure` | Guild permission settings. Requires Discord Administrator. |
| `/triggered user-configure` | Your personal white/blacklist of other members. |

### Owner text commands

These only work if your Discord user ID matches `owner_id`.

| Message | What it does |
| --- | --- |
| `triggered/sync` | Sync slash commands globally. |
| `triggered/sync this` | Sync slash commands to the current guild. |
| `triggered/sync <guild_id>` | Sync slash commands to that guild. |
| `triggered/disable` | Disable command handling without shutting the process down. |
| `triggered/enable` | Re-enable command handling. |
| `triggered/toggle` | Flip enabled/disabled. |

---

## Built-in triggers

Pass the matching `/triggered new` argument for each type.

| Dropdown name | ID | Event | Required argument |
| --- | --- | --- | --- |
| Contains Text | `contains-text` | Message sent | `trigger_text` — substring match |
| Contains Word | `contains-word` | Message sent | `trigger_text` — whole-word match |
| Role Mentioned | `role-mentioned` | Message sent | `trigger_role` |
| Reaction Added | `reaction-added` | Reaction added | `trigger_emoji` |
| Reaction Removed | `reaction-removed` | Reaction removed | `trigger_emoji` |
| Joined VC Channel | `join-vc` | Member joins voice | `trigger_vc` |
| Left VC Channel | `left-vc` | Member leaves voice | `trigger_vc` |
| Member Joined | `member-joined` | Member joins the guild | none |
| Member Left | `member-left` | Member leaves the guild | none |

## Built-in dos

| Dropdown name | ID | Required argument | Effect |
| --- | --- | --- | --- |
| Send Message | `send-message` | `do_channel` | Posts an embed in that channel describing what fired. |
| Send DM | `send-dm` | `do_member` | DMs that member the same kind of embed. |

Bots never fire triggers. If a do targets a member, that member's user-configure lists are checked first.

---

## Permissions

### Who can use `/triggered`

If the guild has a **Required Role** set (`/triggered server-configure`), only members with that role can use commands.

If no role is set, your highest role must sit **above** the bot's role (the guild owner always can).

### Server lists

Admins can white/blacklist channels and roles for triggers and for dos separately:

- Channel whitelist/blacklist (Trigger)
- Channel whitelist/blacklist (Do)
- Role whitelist/blacklist (Trigger)
- Role whitelist/blacklist (Do)

Each list starts as a blacklist (everything allowed except listed items). Use `Switch Whitelist/Blacklist` to invert it.

### User lists

`/triggered user-configure` controls whether other people can write rules that target you. User lists default to **whitelist** (nobody can target you until you add them).

---

## Adding a custom trigger or do

The bot loads everything listed in `configuration/requirements.json`.

1. Subclass `actions.triggers.Trigger.Trigger` or `actions.dos.Do.Do`.
2. Implement `dropdown_name()`, `human()`, and `is_valid()` (triggers) or `execute()` (dos).
3. Put the file in `actions/triggers/` or `actions/dos/`.
4. Register it in `configuration/requirements.json` with an ID, `class` name, `type` (triggers only), and `params`.

Trigger `type` must be one of: `send_msg`, `vc_join`, `vc_leave`, `reaction_add`, `reaction_remove`, `member_join`, `member_leave`.

Open a pull request against `dev` if you want it in the public bot.

---

## Project layout

```
bot.py                      # Discord client, slash commands, event routing
actions/triggers/           # Trigger implementations
actions/dos/                # Do implementations
backend/                   # Mongo encoding, validation, pagination, git updates
configuration/config.json   # Runtime settings (token, MongoDB, owner)
configuration/requirements.json  # Trigger/do registry
```

## Branches

| Branch | Role |
| --- | --- |
| `main` | Public stable snapshot (v1.0 RC1 plus docs). Clone this. |
| `stable` | Auto-update stream. Kept in sync with `main` for existing configs that still set `update_to` to `"stable"`. |
| `dev` | Active development. May be ahead of `main`. |

If you enable `auto_update`, run the process under systemd, Docker, or another supervisor — the bot exits after a successful pull so it can be restarted on the new commit.

## Known limits

- Slash commands do not work in DMs.
- There is no periodic / scheduled trigger yet.
- The hosted invite is a small personal bot, not a high-availability service. Self-host if you need it reliable.
- `config.json` is required at `configuration/config.json`; there is no environment-variable override.

## License

No license file is published in this repository. Contact [quantumbagel](https://github.com/quantumbagel) if you want to use it beyond personal self-hosting.
