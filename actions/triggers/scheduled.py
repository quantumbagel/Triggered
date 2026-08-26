from actions.triggers.trigger import Trigger


class ScheduledTrigger(Trigger):
    async def human(variables: dict):
        interval = variables.get("trigger_text") or "an interval"
        return f"Scheduled clock fired (every {interval})."

    async def is_valid(variables: dict, _other=None):
        return True

    def dropdown_name(self):
        return "Scheduled"
