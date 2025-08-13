from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .db import init_db
from .routers import mentions, ingest


app = FastAPI(title="Social Listening API")

origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def on_startup():
    init_db()


app.include_router(mentions.router, prefix="", tags=["mentions"])
app.include_router(ingest.router, prefix="/ingest", tags=["ingest"])
