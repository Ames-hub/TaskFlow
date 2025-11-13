from webpanel.library.auth import require_valid_token, authbook
from library.storage import dataMan, get_traceback
from fastapi import APIRouter, Request, Depends
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from library.botapp import botapp
from fastapi import HTTPException
from pydantic import BaseModel
import datetime
import logging
import hikari
import os

async def update_user_on_bug(bug_id:int, message:str=None):
    report = dataMan().list_bug_reports(ticket_id=bug_id)[0]
    if not report:
        raise ValueError("Bug report not found.")

    dmc = await botapp.rest.create_dm_channel(report["reporter_id"])

    embed = (
        hikari.Embed(
            title="Bug report result",
            description=f"This is regarding a bug report you filed a while ago with Ticket ID {bug_id}.\n\n",
            color=0x00ff00,
            timestamp=datetime.datetime.now().astimezone()
        )
        .add_field(
            name=f"Bug Report {bug_id}",
            value=f"Status: {"RESOLVED" if bool(report['resolved']) else "Still unresolved."}\n"
        )
        .add_field(
            name="Stated Bug",
            value=f"\"{report['stated_bug']}\""
        )
    )

    if message is not None:
        embed.add_field(name="Message From Maintainers", value=message)
    else:
        embed.add_field(
            name="Extra Info",
            value=f"{report['extra_info']}"
        )

    await dmc.send(embed)

router = APIRouter()
templates = Jinja2Templates(directory=os.path.join(os.path.dirname(__file__), "templates"))

@router.get("/bot/errors")
async def load_index(request: Request, token: str = Depends(require_valid_token)):
    logging.info(f"IP {request.client.host} ({authbook.token_owner(token)}) Has accessed the error reports page.")

    all_reports = dataMan().list_bug_reports()

    open_bug_reports = []
    closed_bug_reports = []
    for report in all_reports:
        if report["resolved"] is False:
            open_bug_reports.append(report)
        else:
            # Only show reports that were closed less than 30 days ago.
            if report["resolved_date"] is None:
                if report["resolved"] is True:
                    logging.warning(f"Bug report {report['ticket_id']} is marked as resolved but has no resolved date!")
                    continue
                else:
                    closed_bug_reports.append(report)
                    continue
            if datetime.datetime.strptime(report["resolved_date"], "%Y-%m-%d %H:%M:%S") > datetime.datetime.now() - datetime.timedelta(days=30):
                closed_bug_reports.append(report)

    return templates.TemplateResponse(request, "index.html", {
        "open": len(open_bug_reports),
        "closed": len(closed_bug_reports),
        "total_reports": len(all_reports),
    })

@router.get("/bot/errors/{error_id}")
async def load_error(request: Request, error_id: int, token: str = Depends(require_valid_token)):
    logging.info(f"IP {request.client.host} ({authbook.token_owner(token)}) Has accessed the error report {error_id}.")
    report = dataMan().list_bug_reports(ticket_id=error_id)[0]

    if not report:
        raise HTTPException(status_code=404)

    status = "open" if bool(report['resolved']) is False else "closed"

    tb = get_traceback(error_id)

    return templates.TemplateResponse(request, "error.html", {
        "bug": {
            "id": error_id,
            "title": report['stated_bug'],
            "status": status,
            "severity": report['severity'],
            "reported_by": report['reporter_id'],
            "date_reported": report['received_date'],
            "reproduction": report['stated_reproduction'],
            "additional_info": report['additional_info'],
            "problem_section": report['problem_section'],
            "expected_result": report['expected_result'],
            "traceback": tb['traceback'] if tb else False,
            "exc_type": tb['exc_type'] if tb else False
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
            "severity": error['severity']
        })

    return parsed_data

class ResolveData(BaseModel):
    bug_id: int
    response: str

class UnresolveData(BaseModel):
    bug_id: int

@router.post("/api/errors/resolve")
async def resolve_error(request: Request, data: ResolveData, token: str = Depends(require_valid_token)):
    logging.info(f"IP {request.client.host} ({authbook.token_owner(token)}) Is closing the error report {data.bug_id}.")
    success = dataMan().mark_bug_report_resolved(data.bug_id)

    if success and data.response != "<NO_CONTENT>":
        await update_user_on_bug(data.bug_id, data.response)
        logging.info(
            f"IP {request.client.host} ({authbook.token_owner(token)}) Has resolved the error report {data.bug_id} and notified the user with the response: {data.response}"
        )

    return HTMLResponse(
        content="Successfully resolved bug and notified user!" if success else "Error resolving bug and notifying user!",
        status_code=200 if success else 500
    )

@router.post("/api/errors/ignore")
async def ignore_error(request: Request, data: UnresolveData, token: str = Depends(require_valid_token)):
    logging.info(f"IP {request.client.host} ({authbook.token_owner(token)}) Is deleting the error report {data.bug_id}.")
    success = dataMan().mark_bug_report_resolved(data.bug_id)
    return HTMLResponse(content="Success" if success else "Error", status_code=200 if success else 500)

@router.post("/api/errors/unresolve")
async def resolve_error(request: Request, data: UnresolveData, token: str = Depends(require_valid_token)):
    logging.info(f"IP {request.client.host} ({authbook.token_owner(token)}) Is re-opening the error report {data.bug_id}.")
    success = dataMan().mark_bug_report_unresolved(data.bug_id)
    return HTMLResponse(content="Success" if success else "Error", status_code=200 if success else 500)

class Msg_Data(BaseModel):
    bug_id: int
    response: str

@router.post("/api/errors/message")
async def message_user(request: Request, data: Msg_Data, token: str = Depends(require_valid_token)):
    logging.info(f"IP {request.client.host} ({authbook.token_owner(token)}) Is messaging the reporter of error report {data.bug_id}.")
    try:
        await update_user_on_bug(data.bug_id, data.response)
        return HTMLResponse(content="Success", status_code=200)
    except Exception as e:
        logging.error(f"Error messaging user regarding bug report {data.bug_id}: {e}", exc_info=e)
        return HTMLResponse(content="Error", status_code=500)