import httpx

def register(register_step):

    @register_step("weather")
    async def step_weather(step, data):
        latitude = step["latitude"]
        longitude = step["longitude"]
        store_key = step.get("store_key", "weather")

        url = (
            f"https://api.open-meteo.com/v1/forecast"
            f"?latitude={latitude}&longitude={longitude}&current_weather=true"
        )

        async with httpx.AsyncClient() as client:
            response = await client.get(url)

        try:
            weather_data = response.json()
        except Exception:
            weather_data = {"error": "Invalid response"}

        data[store_key] = weather_data
        data.setdefault("logs", []).append(
            f"Weather fetched for {latitude},{longitude}"
        )

        print(f"WEATHER: {latitude},{longitude}")

        return data
