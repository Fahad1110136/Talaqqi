"""
Main FastAPI application entry point.
Demonstrates: Dependency Injection, SOLID principles.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from config import settings
import logging

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def create_app() -> FastAPI:
    """
    Application factory pattern.
    Creates and configures the FastAPI application.
    
    Returns:
        FastAPI: Configured FastAPI application instance
    """
    app = FastAPI(
        title=settings.APP_NAME,
        version=settings.APP_VERSION,
        debug=settings.DEBUG,
        docs_url=f"{settings.API_PREFIX}/docs",
        redoc_url=f"{settings.API_PREFIX}/redoc"
    )
    
    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.ALLOWED_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Register routers (will be added as we build them)
    # from api import auth, sessions, tajweed_analysis, websocket
    # app.include_router(auth.router, prefix=f"{settings.API_PREFIX}/auth", tags=["auth"])
    # app.include_router(sessions.router, prefix=f"{settings.API_PREFIX}/sessions", tags=["sessions"])
    # app.include_router(tajweed_analysis.router, prefix=f"{settings.API_PREFIX}/analysis", tags=["analysis"])
    # app.include_router(websocket.router, prefix=f"{settings.API_PREFIX}/ws", tags=["websocket"])
    
    @app.get("/")
    async def root():
        """Root endpoint - health check."""
        return {
            "app": settings.APP_NAME,
            "version": settings.APP_VERSION,
            "status": "running"
        }
    
    @app.on_event("startup")
    async def startup_event():
        """Initialize resources on startup."""
        logger.info(f"Starting {settings.APP_NAME} v{settings.APP_VERSION}")
        # Initialize database
        from models.database import init_db
        init_db()
        logger.info("Database initialized")
        
    @app.on_event("shutdown")
    async def shutdown_event():
        """Cleanup resources on shutdown."""
        logger.info("Shutting down application")
    
    return app


# Create application instance
app = create_app()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG
    )
