# Existing imports
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import asyncio
import httpx
import os
import dotenv

# Custom nodes
from steps import discord as dc_node

# Envirement
dotenv.load_dotenv()

DISCORD_WEBHOOK = os.getenv("DISCORD_WEBHOOK")

# Create app
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Registering steps
step_handlers = {}

def register_step(step_type):
    def decorator(func):
        step_handlers[step_type] = func
        return func
    return decorator

@register_step("log")
async def step_log(step, data):
    msg = step["message"]
    print(f"LOGGING: {msg}")
    data.setdefault("logs", []).append(msg)
    return data

@register_step("set")
async def step_set(step, data):
    data[step["key"]] = step["value"]
    return data

@register_step("delay")
async def step_delay(step, data):
    await asyncio.sleep(step.get("seconds", 1))
    return data

@register_step("if")
async def step_if(step, data):
    condition = step["condition"]
    result = eval(condition)

    next_steps = step["true_next"] if result else step.get("false_next", [])

    await asyncio.gather(*[
            execute_step(next_id, workflow, data) for next_id in next_steps
        ])

    return data

@register_step("http")
async def step_http(step, data):
    url = step["url"]
    method = step.get("method", "GET").upper()
    body = step.get("body", None)
    store_key = step.get("store_key", "http_response")

    async with httpx.AsyncClient() as client:
        response = await client.request(method, url)

    try:
        data[store_key] = response.json()
    except ValueError:
        data[store_key] = response.text
    
    data.setdefault("logs", []).append(f"HTTP: {method} {url} -> {response.status_code}")
    print(f"HTTP: {method} {url} -> {response.status_code}")

dc_node.register(register_step)

# Executing steps
async def execute_step(step_id, workflow, data):
    step = workflow["steps"][step_id]
    step_type = step["type"]

    if step_type not in step_handlers:
        raise Exception(f"Unknown step type: {step_type}")

    data = await step_handlers[step_type](step, data)

    next_steps = step.get("next", [])
    if next_steps:
        await asyncio.gather(*[
            execute_step(next_id, workflow, data) for next_id in next_steps
        ])

    return data

# Build-in workflow (for testing and development purpose)
workflow = {
    "start": "1",
    "steps": {
        "1": {"type": "set", "key": "temperature", "value": 22, "next": ["2"]},
        "2": {
            "type": "if",
            "condition": 'data.get("temperature", 0) < 25',
            "true_next": ["3"],
            "false_next": []
        },
        "3": {"type": "set", "key": "humidity", "value": "80%", "next": ["4"]},
        "4": {
            "type": "discord_webhook",
            "webhook_url": DISCORD_WEBHOOK,
            "content": "Temperature is {{temperature}}\nHumidity is {{humidity}}",
            "next": ["5"]
        },
        "5": {"type": "log", "message": "Finished execution", "next": []},

    }
}

data = {}

# Api endpoints
@app.get("/")
async def root():
    global data
    await execute_step(workflow["start"], workflow, data)
    return {"Data": data}

@app.get("/debug/steps")
async def debug_steps():
    global step_handlers
    return step_handlers

@app.post("/run/workflow")
async def run_workflow(request: Request):
    payload = await request.json()
    workflow = payload.get("workflow")
    if not workflow:
        return JSONResponse({"error": "No workflow provided"}, status_code=400)

    data = {}
    try:
        await execute_step(workflow["start"], workflow, data)
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)

    return {"data": data, "execution_order": data.get("execution_order", [])}