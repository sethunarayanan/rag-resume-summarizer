from fastapi import FastAPI
from app.api.routes import router
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(
    title="Resume processing api",
    version="1.0.0",
    docs_url="/swagger",
    redoc_url="/redoc"         
)

app.include_router(router)