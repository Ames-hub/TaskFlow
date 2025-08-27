from webpanel.library.auth import authbook, UserLogin, autherrors
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from fastapi import APIRouter, Request
from pydantic import BaseModel
import logging
import os

router = APIRouter()
templates = Jinja2Templates(directory=os.path.join(os.path.dirname(__file__), "templates"))

class TokenData(BaseModel):
    token: str

class LoginData(BaseModel):
    username: str
    password: str

@router.get("/login", response_class=HTMLResponse)
async def show_login(request: Request):
    return templates.TemplateResponse(request, "index.html")

@router.post("/api/token/check")
async def verify_token(data: TokenData):
    verified = authbook.verify_token(data.token)
    return JSONResponse(content={'verified': verified}, status_code=200 if verified else 401)

@router.post("/api/user/login")
async def login_user(request: Request, data: LoginData):
    # Generates a key and returns it if it's okay.
    try:
        user = UserLogin(details={
            "username": data.username,
            "password": data.password,
        })
    except autherrors.UserNotFound:
        logging.info(f"Under the IP {request.client.host}, Non-Existent user {data.username} attempted to log in unsuccessfully.")
        return JSONResponse(content="An account with that username does not exist.", status_code=404)
    except (autherrors.InvalidPassword, autherrors.AccountArrested) as err:
        logging.info(f"Under the IP {request.client.host}, user {data.username} attempted to log in unsuccessfully.")
        return JSONResponse(content={'error': str(err)}, status_code=401)

    token = user.gen_token()
    user.store_token(token)
    logging.info(f"Under the IP {request.client.host}, user {data.username} successfully logged in.")

    return JSONResponse(content={'token': token}, status_code=200)