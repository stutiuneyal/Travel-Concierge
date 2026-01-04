from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.requests import Request
from pydantic import BaseModel

from workflow import build_workflow  # must expose `workflow` object

app = FastAPI(title="Travel Concierge Demo")

# Serve static assets
app.mount("/static", StaticFiles(directory="static"), name="static")

# Serve HTML templates
templates = Jinja2Templates(directory="templates")

workflow = build_workflow()


class AskRequest(BaseModel):
    query: str


class AskResponse(BaseModel):
    final_answer: str
    classifications: list = []
    results: list = []


@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.post("/ask", response_model=AskResponse)
def ask(req: AskRequest):
    # Your workflow state contract
    out = workflow.invoke(
        {
            "query": req.query,
            "classifications": [],
            "results": [],
            "final_answer": "",
        }
    )

    return {
        "final_answer": out.get("final_answer", ""),
        "classifications": out.get("classifications", []),
        "results": out.get("results", []),
    }
