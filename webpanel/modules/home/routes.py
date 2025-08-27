from webpanel.library.auth import require_valid_token, authbook
from fastapi import APIRouter, Request, Depends
from fastapi.templating import Jinja2Templates
import logging
import os

router = APIRouter()
templates = Jinja2Templates(directory=os.path.join(os.path.dirname(__file__), "templates"))

@router.get("/")
async def load_index(request: Request, token: str = Depends(require_valid_token)):
    logging.info(f"IP {request.client.host} ({authbook.token_owner(token)}) Has accessed the home page.")

    return templates.TemplateResponse(request, "index.html")