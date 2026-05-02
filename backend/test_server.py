from fastapi import FastAPI
import uvicorn

app = FastAPI()

@app.get("/")
def read_root():
    return {"Hello": "World"}

@app.get("/allotment/test")
def test_allotment():
    return {"message": "allotment test success"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8005)
