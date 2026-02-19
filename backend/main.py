from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import asyncio
import httpx

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
async def step_log(step, workflow, data):
    msg = step["message"]
    print(f"LOGGING: {msg}")
    data.setdefault("logs", []).append(msg)
    return data

@register_step("set")
async def step_set(step, workflow, data):
    data[step["key"]] = step["value"]
    return data

@register_step("delay")
async def step_delay(step, workflow, data):
    await asyncio.sleep(step.get("seconds", 1))

@register_step("if")
async def step_if(step, workflow, data):
    condition = step["condition"]
    result = eval(condition)

    next_steps = step["true_next"] if result else step.get("false_next", [])

    await asyncio.gather(*[
            execute_step(next_id, workflow, data) for next_id in next_steps
        ])

    return data

@register_step("http")
async def step_http(step, workflow, data):
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

# Executing steps
async def execute_step(step_id, workflow, data):
    step = workflow["steps"][step_id]
    step_type = step["type"]

    if step_type not in step_handlers:
        raise Exception(f"Unknown step type: {step_type}")

    data = await step_handlers[step_type](step, workflow, data)

    next_steps = step.get("next", [])
    if next_steps:
        await asyncio.gather(*[
            execute_step(next_id, workflow, data) for next_id in next_steps
        ])

    return data

data = {}

# Api endpoints
@app.post("/run")
async def run_workflow(workflow: dict):
    global data
    global workflow_global
    workflow_global = workflow
    await execute_step(workflow["start"], workflow, data)
    return data