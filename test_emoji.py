from emoji import emojize
from emoji import EMOJI_DATA as EMOJIS





new_emoji = {}
for emoji in EMOJIS.keys():
    if 'alias' in EMOJIS[emoji].keys():
        new_emoji.update({EMOJIS[emoji]['alias'][0]: emoji})
    else:
        new_emoji.update({EMOJIS[emoji]['en']: emoji})
print(EMOJI)
