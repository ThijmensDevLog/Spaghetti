import httpx

# Discord webhook (single message)
def register(register_step):
    @register_step("discord_webhook")
    async def step_discord_webhook(step, data):
        webhook_url = step["webhook_url"]
        content = step["content"]
        data_path = step.get("data_path")

        if data_path:
            value = data
            for key in data_path.split("."):
                value = value.get(key, "")
            content = content.replace("{{value}}", str(value))

        async with httpx.AsyncClient() as client:
            await client.post(webhook_url, json={"content": content})

        data.setdefault("logs", []).append(f"Discord webhook: {content}")
        print(f"Discord webhook: {content}")
        return data