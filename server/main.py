from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.requests import Request

app = FastAPI()

# Static files (JS/CSS)
app.mount("/static", StaticFiles(directory="web/static"), name="static")

# Templates (HTML)
templates = Jinja2Templates(directory="web/templates")


@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})