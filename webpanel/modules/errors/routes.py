from webpanel.library.auth import require_valid_token, authbook
from fastapi import APIRouter, Request, Depends
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from library.storage import dataMan
from library.botapp import botapp
from pydantic import BaseModel
import datetime
import logging
import hikari
import os

router = APIRouter()
templates = Jinja2Templates(directory=os.path.join(os.path.dirname(__file__), "templates"))

@router.get("/bot/errors")
async def load_index(request: Request, token: str = Depends(require_valid_token)):
    logging.info(f"IP {request.client.host} ({authbook.token_owner(token)}) Has accessed the error reports page.")

    total_reports = 0
    open_bug_reports = []
    closed_bug_reports = []
    for report in dataMan().list_bug_reports():
        if bool(report["resolved"]) is False:
            open_bug_reports.append(report)
        else:
            # Only show reports that were closed less than 30 days ago.
            if datetime.datetime.strptime(report["received_date"], "%Y-%m-%d %H:%M:%S") > datetime.datetime.now() - datetime.timedelta(days=30):
                closed_bug_reports.append(report)
        total_reports += 1

    return templates.TemplateResponse(request, "index.html", {
        "open": len(open_bug_reports),
        "closed": len(closed_bug_reports),
        "total_reports": total_reports,
    })

@router.get("/bot/errors/{error_id}")
async def load_error(request: Request, error_id: int, token: str = Depends(require_valid_token)):
    logging.info(f"IP {request.client.host} ({authbook.token_owner(token)}) Has accessed the error report {error_id}.")
    report = dataMan().list_bug_reports(ticket_id=error_id)[0]
    status = "open" if bool(report['resolved']) is False else "closed"

    return templates.TemplateResponse(request, "error.html", {
        "bug": {
            "id": error_id,
            "title": report['stated_bug'],
            "status": status,
            "severity": "low",
            "reported_by": report['reporter_id'],
            "date_reported": report['received_date'],
            "reproduction": report['stated_reproduction'],
            "additional_info": report['additional_info']
        }
    })

@router.get("/api/errors/list")
async def list_errors(request: Request, token: str = Depends(require_valid_token)):
    logging.info(f"IP {request.client.host} ({authbook.token_owner(token)}) Is listing the error reports.")

    all_errors = dataMan().list_bug_reports()

    parsed_data = []
    for error in all_errors:
        parsed_data.append({
            "id": error["ticket_id"],
            "title": error["stated_bug"],
            "status": "open" if bool(error["resolved"]) is False else "closed",
            "severity": "low"
        })

    return parsed_data

class ResolveData(BaseModel):
    bug_id: int
    response: str

@router.post("/api/errors/resolve")
async def resolve_error(request: Request, data: ResolveData, token: str = Depends(require_valid_token)):
    logging.info(f"IP {request.client.host} ({authbook.token_owner(token)}) Is closing the error report {data.bug_id}.")
    success = dataMan().mark_bugreport_resolved(data.bug_id)

    # DMs the user that their bug is resolved IF it is.
    if success:
        report = dataMan().list_bug_reports(ticket_id=data.bug_id)[0]
        reporter_id = report['reporter_id']
        if reporter_id is None:
            return HTMLResponse(content="Unable to message user", status_code=200)
        user = await botapp.rest.fetch_user(reporter_id)
        if user is not None:
            embed = (hikari.Embed(
                    title="Bug report result",
                    description=f"This is regarding a bug report you filed a while ago with Ticket ID {data.bug_id}.\n\n",
                    color=0x00ff00,
                    timestamp=datetime.datetime.now().astimezone()
                )
                .add_field(
                    name=f"Bug Report {data.bug_id}",
                    value=f"Status: RESOLVED\n"
                          f"Stated Bug: {report['stated_bug']}"
                )
                .add_field(
                    name="Message",
                    value=data.response if data.response is not None else "The bug has been resolved and will not cause more trouble. Thank you for reporting it!")
            )
            try:
                await user.send(embed)
            except (hikari.errors.ForbiddenError, hikari.errors.NotFoundError, hikari.errors.BadRequestError, hikari.errors.UnauthorizedError):
                logging.info(f"User {reporter_id} cannot be DM'd.")
                return HTMLResponse(content="Unable to message user, but bug resolved successfully!", status_code=200)

    return HTMLResponse(
        content="Successfully resolved bug and notified user!" if success else "Error resolving bug and notifying user!",
        status_code=200 if success else 500
    )

class UnresolveData(BaseModel):
    bug_id: int

@router.post("/api/errors/unresolve")
async def resolve_error(request: Request, data: UnresolveData, token: str = Depends(require_valid_token)):
    logging.info(f"IP {request.client.host} ({authbook.token_owner(token)}) Is re-opening the error report {data.bug_id}.")
    success = dataMan().mark_bugreport_unresolved(data.bug_id)
    return HTMLResponse(content="Success" if success else "Error", status_code=200 if success else 500)