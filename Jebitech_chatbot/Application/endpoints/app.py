from fastapi import FastAPI, HTTPException

from Application.endpoints.chat_transfer import chat_transfer_router
from Application.endpoints.user_endpoints import guest_router,initial
from Application.endpoints.db_onboarding import db_router
from fastapi.middleware.cors import CORSMiddleware

app=FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(guest_router, tags=["Guest/Registered_user"])
app.include_router(db_router,tags=["Database"])
app.include_router(chat_transfer_router, prefix="/chat")
@app.on_event("startup")
async def startup_event():
    await initial()





#uvicorn Application.endpoints.app:app 
