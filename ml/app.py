from fastapi import FastAPI 


app = FastAPI()


@app.post('/')
async def timepass(data):
    print(data)

    return {'status' : "OK"}