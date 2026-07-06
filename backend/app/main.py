from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.config import settings
from app.routers import auth, candidates, jobs, applications, uploads, resumes, matching, templates, interview, analytics, assistant, search
from app.services.event_listeners import register_event_listeners

# Register database event listeners transparently
register_event_listeners()

app = FastAPI(
    title=settings.PROJECT_NAME,
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Set up CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routes
app.include_router(auth.router, prefix=settings.API_V1_STR)
app.include_router(candidates.router, prefix=settings.API_V1_STR)
app.include_router(jobs.router, prefix=settings.API_V1_STR)
app.include_router(applications.router, prefix=settings.API_V1_STR)
app.include_router(uploads.router, prefix=settings.API_V1_STR)
app.include_router(resumes.router, prefix=settings.API_V1_STR)
app.include_router(matching.router, prefix=settings.API_V1_STR)
app.include_router(templates.router, prefix=settings.API_V1_STR)
app.include_router(interview.router, prefix=settings.API_V1_STR)
app.include_router(analytics.router, prefix=settings.API_V1_STR)
app.include_router(assistant.router, prefix=settings.API_V1_STR)
app.include_router(search.router, prefix=settings.API_V1_STR)

# Global Exception Handlers
@app.exception_handler(RequestValidationError)
def validation_exception_handler(request: Request, exc: RequestValidationError):
    """
    Standardize validation errors to return a clean client response.
    """
    errors = []
    for error in exc.errors():
        errors.append({
            "field": " -> ".join(map(str, error["loc"][1:])),
            "message": error["msg"],
            "type": error["type"]
        })
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "success": False,
            "error_type": "ValidationError",
            "message": "Input validation failed",
            "details": errors
        }
    )

@app.exception_handler(StarletteHTTPException)
def http_exception_handler(request: Request, exc: StarletteHTTPException):
    """
    Standardize HTTP exceptions.
    """
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "error_type": "HTTPException",
            "message": exc.detail
        }
    )

@app.exception_handler(Exception)
def general_exception_handler(request: Request, exc: Exception):
    """
    Catch-all for internal server errors.
    """
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "success": False,
            "error_type": "ServerError",
            "message": "An unexpected error occurred on the server.",
            "details": str(exc)
        }
    )

@app.get("/")
def health_check():
    return {
        "status": "healthy",
        "service": settings.PROJECT_NAME,
        "version": "1.0.0"
    }
