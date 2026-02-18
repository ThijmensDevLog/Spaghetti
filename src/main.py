from fastapi import FastAPI

app = FastAPI()



@app.get("/")
def root():
    return {"message": "Spaghetti is up and running"}