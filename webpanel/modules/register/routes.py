from fastapi.responses import HTMLResponse, JSONResponse
from webpanel.library.auth import authbook, autherrors
from fastapi.templating import Jinja2Templates
from fastapi import APIRouter, Request
from pydantic import BaseModel
import logging
import os

router = APIRouter()
templates = Jinja2Templates(directory=os.path.join(os.path.dirname(__file__), "templates"))

class RegisterData(BaseModel):
    username: str
    password: str

@router.get("/register", response_class=HTMLResponse)
async def show_reg(request: Request):
    return templates.TemplateResponse(request, "index.html")

@router.post("/api/authbook/register")
async def register(request: Request, data: RegisterData):
    try:
        success = authbook.create_account(
            data.username,
            data.password,
        )
    except autherrors.ExistingUser:
        return JSONResponse({"success": False, "error": "That username is taken."}, status_code=400)

    logging.info(f"User {data.username} registered successfully by {request.client.host}")
    return JSONResponse(content={'success': success}, status_code=201 if success is True else 500)
