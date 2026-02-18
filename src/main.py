from fastapi import FastAPI
import asyncio

app = FastAPI()

async def execute_step(step_id, workflow, data):
    step = workflow["steps"][step_id]

    if step["type"] == "log":
        print(f"LOGGING: {step["message"]}")
    elif step["type"] == "delay":
        await asyncio.sleep(step.get("seconds", 1))
    elif step["type"] == "set":
        data[step["key"]] = step["value"]

    next_steps = step.get("next", [])
    if next_steps:
        await asyncio.gather(*[
            execute_step(next_id, workflow, data) for next_id in next_steps
        ])

    return data

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

@app.get("/")
def root():
    asyncio.run(execute_step(workflow["start"], workflow, data))
    return {"message": "Spaghetti is up and running"}