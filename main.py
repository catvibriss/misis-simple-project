from fastapi import FastAPI
from routers import all_routers

app = FastAPI(title="nah bro")

for r in all_routers:
    app.include_router(r)
