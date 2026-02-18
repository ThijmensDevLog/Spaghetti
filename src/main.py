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

# Build-in workflow
workflow = {
    "start": "1",
    "steps": {
        "1": {"type": "log", "message": "Start", "next": ["2", "3"]},
        "2": {"type": "delay", "seconds": 10, "next": ["5"]},
        "3": {"type": "log", "message": "Branch 3", "next": ["4"]},
        "4": {"type": "log", "message": "End branch 3", "next": []},
        "5": {"type": "log", "message": "End branch 2", "next": []}
    }
}

data = {}

# Api endpoints
@app.get("/")
def root():
    asyncio.run(execute_step(workflow["start"], workflow, data))
    return {"message": "Spaghetti is up and running"}