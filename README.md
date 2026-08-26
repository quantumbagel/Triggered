# Triggered

Triggered is a self-hostable Discord **if-this-then-that** bot. You create a **trigger** (something that happens in a server) and attach one or more **dos** (actions the bot should take). Example: if a message contains `hello`, send a notification embed to `#alerts`.

[Invite the hosted bot](https://discord.com/api/oauth2/authorize?client_id=1181338133204307968&permissions=268454912&response_type=code&redirect_uri=https%3A%2F%2Fgithub.com%2Fquantumbagel&scope=bot+applications.commands.permissions.update+applications.commands) · [Author](https://github.com/quantumbagel)

---

## Features

- Slash-command workflow for creating, attaching, viewing, and deleting automations
- Autocomplete for trigger/do types and existing names (type to search; not limited to Discord's 25-choice dropdown)
- Built-in triggers for messages, edits, deletes, reactions, voice, roles, nicknames, boosts, and a timed clock
- Built-in dos for messages, DMs, replies, reactions, roles, voice moves, and moderation
- Server-wide permission role plus channel/role white/blacklists
- Per-user white/blacklists so people can opt in or out of being targeted
- MongoDB storage, per-guild data isolation, and cleanup when the bot is kicked

## Requirements

- Python 3.10+
- A running **MongoDB** instance (local is strongly recommended; this bot talks to the database a lot :D)
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
pip install -e .
```

1. Create a Discord application at [https://discord.com/developers/applications](https://discord.com/developers/applications).
2. Create a bot user, copy the token, and enable the privileged intents listed above.
3. Invite the bot with `applications.commands` and permission to view channels, send messages, embed links, add reactions, manage roles, move members, kick, ban, and moderate members (the extra permissions are only required for those dos).
4. Start MongoDB. The default URI is `mongodb://localhost:27017`.
5. Copy `configuration/config.example.json` to `configuration/config.json` and fill in your bot token, owner ID, and MongoDB URI.
6. Run the bot:

```bash
python bot.py
```

7. In a server the bot can see, send `triggered/sync` as the configured owner to register slash commands. After that, use `/triggered`.

---

## Configuration

All runtime settings live in `configuration/config.json`. Any of them can be overridden with a matching `TRIGGERED_*` environment variable (useful for Docker).

| Key                     | Type   | Meaning                                                                                            |
|-------------------------|--------|----------------------------------------------------------------------------------------------------|
| `bot_secret`            | string | Discord bot token.                                                                                 |
| `mongodb_uri`           | string | MongoDB connection string.                                                                         |
| `owner_id`              | int    | Discord user ID allowed to run owner text commands (`triggered/sync`, enable/disable).             |
| `max_dos_per_trigger`   | int    | Maximum actions that can be attached to one trigger. Default: `3`.                                 |
| `argument_length_limit` | int    | Max length for names, descriptions, and text arguments. Default: `128`.                            |
| `allowed_execution`     | int    | Reserved for execution limits.                                                                     |

Environment overrides use the same names in uppercase with a `TRIGGERED_` prefix, for example `TRIGGERED_BOT_SECRET`, `TRIGGERED_MONGODB_URI`, `TRIGGERED_OWNER_ID`.

`configuration/requirements.json` is **not** server config. It maps trigger/do IDs to Python classes so the bot can load them dynamically. The module file is inferred from the ID (`contains-text` → `actions/triggers/contains_text.py`) unless you set `"module"` on the entry.

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
| `/triggered new` | Create a trigger. Required: `name`, `trigger`. Type in `trigger` to search types (autocomplete, not a 25-item dropdown). Optional: `description` plus the argument that trigger needs (`trigger_text`, `trigger_role`, `trigger_member`, `trigger_emoji`, `trigger_vc`, `trigger_channel`, …). Durations use seconds or shorthand (`60s`, `5m`, `1h`, `1d`). |
| `/triggered add` | Attach a do to an existing trigger. Required: `trigger_name`, `do`, `do_name`. Type in `do` and `trigger_name` to search. Optional: `description` plus the argument that do needs (`do_channel`, `do_member`, `do_role`, `do_emoji`, `do_text`, `do_vc`, …). |
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

| Dropdown name     | ID                   | Event                   | Required argument                 |
|-------------------|----------------------|-------------------------|-----------------------------------|
| Contains Text     | `contains-text`      | Message sent            | `trigger_text` — substring match  |
| Contains Word     | `contains-word`      | Message sent            | `trigger_text` — whole-word match |
| Role Mentioned    | `role-mentioned`     | Message sent            | `trigger_role`                    |
| User Mentioned    | `user-mentioned`     | Message sent            | `trigger_member`                  |
| Sent By           | `sent-by`            | Message sent            | `trigger_member`                  |
| In Channel        | `in-channel`         | Message sent            | `trigger_channel`                 |
| Has Attachment    | `has-attachment`     | Message sent            | none                              |
| Everyone Mentioned| `everyone-mentioned` | Message sent            | none — `@everyone` or `@here`     |
| Starts With       | `starts-with`        | Message sent            | `trigger_text` — prefix match     |
| Message Edited    | `message-edited`     | Message edited          | optional `trigger_channel`        |
| Message Deleted   | `message-deleted`    | Message deleted         | optional `trigger_channel`        |
| Reaction Added    | `reaction-added`     | Reaction added          | `trigger_emoji`                   |
| Reaction Removed  | `reaction-removed`   | Reaction removed        | `trigger_emoji`                   |
| Joined VC Channel | `join-vc`            | Member joins voice      | `trigger_vc`                      |
| Left VC Channel   | `left-vc`            | Member leaves voice     | `trigger_vc`                      |
| Role Added        | `role-added`         | Member gained a role    | `trigger_role`                    |
| Role Removed      | `role-removed`       | Member lost a role      | `trigger_role`                    |
| Nickname Changed  | `nickname-changed`   | Guild nickname changed  | none                              |
| Member Boosted    | `member-boosted`     | Member boosted the guild| none                              |
| Member Joined     | `member-joined`      | Member joins the guild  | none                              |
| Member Left       | `member-left`        | Member leaves the guild | none                              |
| Scheduled         | `scheduled`          | Interval clock          | `trigger_text` — duration (`5m`)  |

## Built-in dos

| Dropdown name | ID | Required argument | Effect |
| --- | --- | --- | --- |
| Send Message | `send-message` | `do_channel` | Posts an embed in that channel describing what fired. |
| Send DM | `send-dm` | `do_member` | DMs that member the same kind of embed. |
| Send Text | `send-text` | `do_channel`, `do_text` | Posts your custom text in that channel. |
| Reply | `reply` | `do_text` | Replies to the triggering message. Message send/edit triggers only. |
| Add Reaction | `add-reaction` | `do_emoji` | Reacts to the triggering message. Message send/edit triggers only. |
| Delete Message | `delete-message` | none | Deletes the triggering message. Message send/edit triggers only. |
| Add Role | `add-role` | `do_role` | Gives that role to the member who fired the trigger. |
| Remove Role | `remove-role` | `do_role` | Removes that role from the member who fired the trigger. |
| Move to VC | `move-to-vc` | `do_vc` | Moves the member who fired the trigger into that voice channel. They must already be in voice. |
| Kick Member | `kick-member` | none | Kicks the member who fired the trigger. |
| Timeout Member | `timeout-member` | `do_text` | Times out the member who fired the trigger. Duration like `10m` (max 28d). |
| Ban Member | `ban-member` | none | Bans the member who fired the trigger. |

Bots never fire triggers. If a do targets a member, that member's user-configure lists are checked first.

`add-role` and `remove-role` need **Manage Roles**, and the bot's role must sit above the role being granted or removed. `add-reaction` needs **Add Reactions**. `move-to-vc` needs **Move Members**. `kick-member`, `timeout-member`, and `ban-member` need **Kick Members**, **Moderate Members**, and **Ban Members** respectively. Those three skip the guild owner and the bot itself.

Scheduled triggers wait one interval after creation before the first fire. Message-deleted only runs if Discord still had the message cached.

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

1. Subclass `actions.triggers.trigger.Trigger` or `actions.dos.do.Do`.
2. Implement `dropdown_name()`, `human()`, and `is_valid()` (triggers) or `execute()` (dos).
3. Put the file in `actions/triggers/` or `actions/dos/`, named after the ID (`contains-text` → `contains_text.py`).
4. Register it in `configuration/requirements.json` with an ID, `class` name, `type` (triggers only), and `params`.

Trigger `type` must be one of: `send_msg`, `vc_join`, `vc_leave`, `reaction_add`, `reaction_remove`, `member_join`, `member_leave`, `message_edit`, `message_delete`, `role_add`, `role_remove`, `nickname_change`, `member_boost`, `scheduled`.

Open a pull request against `dev` if you want it in the public bot.

---

## Project layout

```
bot.py                         # Discord client, slash commands, event routing
actions/triggers/              # Trigger implementations (snake_case modules)
actions/dos/                   # Do implementations
backend/                      # Encoding, validation, pagination
configuration/config.json      # Runtime settings (token, MongoDB, owner)
configuration/requirements.json
pyproject.toml                 # Package metadata and dependencies
Dockerfile / docker-compose.yml
```

## Branches

| Branch | Role |
| --- | --- |
| `main` | Public stable snapshot (v1.0). Clone this. |
| `stable` | Kept in sync with `main`. |
| `dev` | Active development. May be ahead of `main`. |

## Tests

```bash
pip install -e ".[dev]"
pytest
```

## Docker

Copy `.env.example` to `.env` and set your bot token and owner ID. Then:

```bash
docker compose up --build
```

Compose starts MongoDB and the bot. The bot reads `configuration/config.example.json` inside the image and applies `TRIGGERED_*` environment variables from Compose (Mongo URI, token, owner).

To use a local `configuration/config.json` instead, bind-mount it onto `/app/configuration/config.json`. Environment variables still win when set.

## Known limits

- Slash commands do not work in DMs.
- Autocomplete still shows at most 25 matches at a time; type more of the name or id to narrow the list.
- Scheduled triggers cannot run more often than every 15 seconds.
- The hosted invite is a small personal bot, not a high-availability service. Self-host if you need it reliable.
- `config.json` is required at `configuration/config.json` (copy it from `configuration/config.example.json`). Keep that file private — it is gitignored. Docker can skip a local config file and use `TRIGGERED_*` environment variables instead.
