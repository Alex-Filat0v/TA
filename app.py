from fastapi import FastAPI
from module_routes import module_router
import uvicorn


app = FastAPI()

app.include_router(module_router)


if __name__ == '__main__':
    uvicorn.run('app:app', reload=True)
