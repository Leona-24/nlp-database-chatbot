from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel
from typing import Dict, Any, List, Optional
import textwrap
from datetime import datetime, timedelta
from jose import JWTError, jwt
import bcrypt
import csv
import os

from .database import execute_query, init_db, init_auth_db, get_user, create_user
from .nlp_service import nlp_engine
from .rag_service import rag_service
from .visualization_service import generate_chart

print("\n" + "="*50)
print("SERVER IS STARTING WITH LATEST AUTH CODE")
print("="*50 + "\n")

# Security Config
SECRET_KEY = "super-secret-key-for-prototype" # In production, use environment variable
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 # 1 day

# Removed pwd_context due to passlib/bcrypt4.0 compatibility bug
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/login")

app = FastAPI(title="Text-to-SQL Bot", description="Convert natural language to SQL and retrieve database results.")

# CORS Middleware for frontend access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize DBs on startup
init_db()
init_auth_db()

class QueryRequest(BaseModel):
    query: str
    history: List[Dict[str, str]] = []

class QueryResponse(BaseModel):
    sql_query: str
    results: List[Dict[str, Any]]
    message: str = "Success"
    thought: Optional[str] = None
    confidence: float = 0.0
    chart_image: Optional[str] = None  # base64-encoded PNG from Matplotlib
    chart_spec: Optional[Dict[str, Any]] = None  # Vega-Lite JSON spec

class UserRegister(BaseModel):
    username: str
    email: str
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str
    username: str

class FeedbackRequest(BaseModel):
    message_id: str
    status: str
    how: Optional[str] = None

# Helper functions
def verify_password(plain_password: str, hashed_password: str):
    try:
        return bcrypt.checkpw(
            plain_password.encode('utf-8'), 
            hashed_password.encode('utf-8')
        )
    except Exception:
        return False

def get_password_hash(password: str):
    # Bcrypt has a 72-byte limit. We truncate to ensure stability.
    pwd_bytes = password.encode('utf-8')[:72]
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(pwd_bytes, salt)
    return hashed.decode('utf-8')


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

# Endpoints
@app.post("/api/register")
def register(user: UserRegister):
    print(f"REGISTER REQUEST: {user.username}")
    try:
        # Fix 1: Bcrypt has a 72-character/byte limit
        if len(user.password.encode("utf-8")) > 72:
            print(f"REGISTER FAILED: Password too long for {user.username}")
            raise HTTPException(status_code=400, detail="Password too long (max 72 characters)")

        existing = get_user(user.username)
        if existing:
            print(f"REGISTER FAILED: Username already exists: {user.username}")
            raise HTTPException(status_code=400, detail="Account already exists")
        
        existing_email = get_user(user.email)
        if existing_email:
            print(f"REGISTER FAILED: Email already exists: {user.email}")
            raise HTTPException(status_code=400, detail="Account already exists")
        
        hashed_password = get_password_hash(user.password)
        success = create_user(user.username, user.email, hashed_password)
        if not success:
            print(f"REGISTER FAILED: Database error for {user.username}")
            raise HTTPException(status_code=500, detail="Could not create user in database")
        
        print(f"REGISTER SUCCESS: {user.username}")
        return {"message": "User registered successfully"}
    except HTTPException as he:
        raise he
    except Exception as e:
        print(f"REGISTER ERROR: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/login", response_model=Token)
def login(form_data: OAuth2PasswordRequestForm = Depends()):
    print(f"LOGIN REQUEST: {form_data.username}")
    user = get_user(form_data.username)
    if not user or not verify_password(form_data.password, user["password_hash"]):
        print(f"LOGIN FAILED: Invalid credentials for {form_data.username}")
        raise HTTPException(status_code=401, detail="Incorrect username or password")
    
    print(f"LOGIN SUCCESS: {form_data.username}")
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user["username"]}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer", "username": user["username"]}

@app.get("/api/me")
def read_users_me(token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise HTTPException(status_code=401, detail="Invalid token")
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    user = get_user(username)
    if user is None:
        raise HTTPException(status_code=401, detail="User not found")
    
    return {"username": user["username"]}


@app.post("/api/feedback")
def submit_feedback(feedback: FeedbackRequest):
    """
    Submits user feedback and saves it to a CSV file.
    """
    print(f"FEEDBACK RECEIVED: ID={feedback.message_id}, Status={feedback.status}, How={feedback.how}")
    
    # Save to CSV
    feedback_file = os.path.join(os.path.dirname(__file__), "..", "data", "feedback.csv")
    file_exists = os.path.isfile(feedback_file)
    
    try:
        with open(feedback_file, mode='a', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            # Write header if new file
            if not file_exists:
                writer.writerow(["timestamp", "message_id", "status", "comment"])
            
            writer.writerow([
                datetime.utcnow().isoformat(),
                feedback.message_id,
                feedback.status,
                feedback.how or ""
            ])
    except Exception as e:
        print(f"ERROR SAVING FEEDBACK: {str(e)}")
        # We don't raise an exception here as it shouldn't break the user experience
        
    return {"message": "Feedback submitted successfully"}


@app.get("/")
def root():
    return {"message": "Text-to-SQL API is running."}

@app.post("/api/connect")
def connect_database(config: Dict[str, Any]):
    """
    Connects to the specified database.
    """
    from .database import connect_db, get_schema
    
    result = connect_db(config)
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    
    # Return schema upon successful connection
    schema = get_schema()
    
    # Auto-index schema into RAG vector store
    rag_indexed = rag_service.index_schema(schema)
    rag_status = rag_service.get_status()
    
    return {
        "message": "Connected", 
        "schema": schema, 
        "details": result,
        "rag": {
            "indexed": rag_indexed,
            "tables_indexed": rag_status["indexed_tables"],
            "available": rag_status["available"]
        }
    }

@app.get("/api/schema")
def get_current_schema():
    """
    Get the schema of the currently connected database.
    """
    from .database import get_schema
    schema = get_schema()
    
    # Ensure RAG index is up to date
    rag_service.index_schema(schema)
    
    return {"schema": schema}

@app.get("/api/rag-status")
def get_rag_status():
    """
    Get the current status of the RAG (Retrieval-Augmented Generation) system.
    """
    return rag_service.get_status()

@app.post("/api/query", response_model=QueryResponse)
def handle_query(request: QueryRequest):
    """
    Receives natural text query, converts to SQL via NLP, runs on DB, returns results.
    """
    try:
        # 1. Fetch Current Schema and Dialect for dynamic NLP
        from .database import get_schema, get_engine
        schema = get_schema()
        engine = get_engine()
        dialect = engine.dialect.name
        
        # 2. NLP Processing with dynamic schema, dialect, and history
        nlp_response = nlp_engine.generate_sql(
            request.query, 
            schema, 
            dialect=dialect, 
            history=request.history
        )
        suggested_chart = nlp_response.get("suggested_chart", "none")

        sql_query = nlp_response["sql"]
        thought = nlp_response["thought"]

        # 2.5 Quick Check for Incomplete Query
        if sql_query == "-- Not Found":
             return {
                "sql_query": "",
                "results": [],
                "message": thought,
                "thought": thought,
                "confidence": 0
            }
        
        # 3. Database Execution
        execution_result = execute_query(sql_query)
        
        if "error" in execution_result:
            return {
                "sql_query": sql_query,
                "results": [],
                "message": execution_result["error"],
                "thought": thought,
                "confidence": nlp_response.get("confidence", 0)
            }
            
        columns = execution_result["columns"]
        data = execution_result["data"]

        # Generate chart from results
        # Now returns both a static PNG and an interactive spec
        chart_image, chart_spec = generate_chart(
             columns=columns,
             data=data,
             query=request.query,
             chart_type=suggested_chart if suggested_chart != "none" else None
        )

        return {
            "sql_query": sql_query,
            "results": data,
            "message": f"Found {len(data)} results.",
            "thought": thought,
            "confidence": nlp_response.get("confidence", 0),
            "execution_time": execution_result.get("execution_time", 0.1),
            "chart_image": chart_image,
            "chart_spec": chart_spec,
        }
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))
