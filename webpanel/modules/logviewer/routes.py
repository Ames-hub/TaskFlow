from webpanel.library.auth import authbook, require_valid_token
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi import APIRouter, Request, Depends, Query
from fastapi.templating import Jinja2Templates
import logging
import os

router = APIRouter()
templates = Jinja2Templates(directory=os.path.join(os.path.dirname(__file__), "templates"))

@router.get("/bot/logs", response_class=HTMLResponse)
async def show_login(request: Request, token: str = Depends(require_valid_token)):
    logging.info(f"IP {request.client.host} (user: {authbook.token_owner(token)}) has accessed the bot logs page.")
    return templates.TemplateResponse(
        request,
        "loglist.html",
    )

@router.get("/api/bot/logs/list")
async def list_logs(
        request: Request,
        search: str = Query(None, description="String to search for in logs"),
        token: str = Depends(require_valid_token)
):
    logging.info(f"IP {request.client.host} (user: {authbook.token_owner(token)}) is listing the bot logs.")

    logs_dir = "logs"
    if not os.path.isdir(logs_dir):
        return JSONResponse(
            content={"success": False, "error": f"Logs directory '{logs_dir}' not found."},
            status_code=404
        )

    logs_data = {}

    for log_file in os.listdir(logs_dir):
        full_path = os.path.join(logs_dir, log_file)
        if not os.path.isfile(full_path):
            continue

        try:
            size = os.path.getsize(full_path)
            mtime = os.path.getmtime(full_path)  # last modified
        except OSError as e:
            logging.warning(f"Failed to stat log file '{full_path}': {e}")
            continue

        # If searching, check contents for a match
        if search:
            try:
                with open(full_path, "r", encoding="utf-8", errors="ignore") as f:
                    found = False
                    for line in f:
                        if search.lower() in line.lower():
                            found = True
                            break
                if not found:
                    continue
            except OSError as e:
                logging.warning(f"Failed to read log file '{full_path}': {e}")
                continue

        logs_data[log_file] = {
            "size": size,
            "mtime": mtime
        }

    return JSONResponse(
        content={"success": True, "logs": logs_data},
        status_code=200
    )

@router.get("/bot/logs/{log_name}")
async def get_log(request: Request, log_name: str, token: str = Depends(require_valid_token)):
    logging.info(f"IP {request.client.host} (user: {authbook.token_owner(token)}) is getting the bot log {log_name}.")

    logs_dir = "logs"
    # Safe path prevents file traversing.
    safe_path = os.path.join(os.path.abspath(logs_dir), log_name)
    if not os.path.exists(safe_path) or not os.path.isfile(safe_path):
        return HTMLResponse(content="Log not found", status_code=404)

    try:
        with open(safe_path, "r", encoding="utf-8", errors="replace") as f:
            log_content = f.read()
    except OSError as e:
        logging.error(f"Failed to read log file '{safe_path}': {e}")
        return HTMLResponse(content="Unable to read log", status_code=500)

    lines = list(enumerate(log_content.splitlines(), start=1))

    return templates.TemplateResponse(
        request,
        "logview.html",
        {
            "log_name": log_name,
            "log_lines": lines,  # send numbered lines
        }
    )