from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    from models import create_db_and_tables
    create_db_and_tables()
    yield

app = FastAPI(lifespan=lifespan, title="Country Data Service", version="2.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


from views import *

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, reload=True)