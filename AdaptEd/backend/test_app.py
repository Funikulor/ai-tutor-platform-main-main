from fastapi import FastAPI

app = FastAPI()

@app.get("/")
def read_root():
    return {"message": "Test server works!"}

@app.get("/test")
def test():
    return {"status": "OK"}

