from fastapi import FastAPI
import asyncio

app = FastAPI()

# Registering steps
step_handlers = {}

def register_step(step_type):
    def decorator(func):
        step_handlers[step_type] = func
        return func
    return decorator

@register_step("log")
async def step_log(step, data):
    print(f"LOGGING: {step["message"]}")
    return data

@register_step("set")
async def step_set(step, data):
    data[step["key"]] = step["value"]
    return data

@register_step("delay")
async def step_delay(step, data):
    await asyncio.sleep(step.get("seconds", 1))

@register_step("if")
async def step_if(step, data):
    condition = step["condition"]
    result = eval(condition)

    next_steps = step["true_next"] if result else step.get("false_next", [])

    await asyncio.gather(*[
            execute_step(next_id, workflow, data) for next_id in next_steps
        ])

    return data

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
            "condition": 'data.get("temperature", 0) > 25',
            "true_next": ["3"],
            "false_next": ["4"]
        },
        "3": {"type": "log", "message": "It's hot!", "next": []},
        "4": {"type": "log", "message": "It's cool!", "next": []}
    }
}

data = {}

# Api endpoints
@app.get("/")
async def root():
    global data
    await execute_step(workflow["start"], workflow, data)
    return {"Data": data}