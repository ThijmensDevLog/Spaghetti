import httpx
import re

# Discord webhook (single message)
def register(register_step):
    @register_step("discord_webhook")
    async def step_discord_webhook(step, data):
        webhook_url = step["webhook_url"]
        content = step["content"]

        placeholders = re.findall(r"{{(.*?)}}", content)

        for ph in placeholders:
            value = data
            for part in ph.strip().split("."):
                value = value.get(part, "")
            content = content.replace(f"{{{{{ph}}}}}", str(value))

        async with httpx.AsyncClient() as client:
            await client.post(webhook_url, json={"content": content})

        data.setdefault("logs", []).append(f"{content}")
        print(f"DISCORD WEBHOOK: {content}")
        return data