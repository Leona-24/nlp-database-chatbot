from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .db.database import init_db, init_auth_db
from .api.endpoints import auth, query, feedback, schema

app = FastAPI(
    title="NLP Chatbot API",
    description="Industry-style structured NLP-to-SQL backend.",
    version="1.0.0"
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize DBs on startup
@app.on_event("startup")
def on_startup():
    init_db()
    init_auth_db()

# Include Routers
app.include_router(auth.router, prefix="/api", tags=["authentication"])
app.include_router(query.router, prefix="/api", tags=["query"])
app.include_router(feedback.router, prefix="/api", tags=["feedback"])
app.include_router(schema.router, prefix="/api", tags=["schema"])

@app.get("/")
def root():
    return {"message": "NLP Chatbot API is running.", "docs": "/docs"}
