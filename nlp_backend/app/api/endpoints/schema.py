from fastapi import APIRouter, HTTPException
from typing import Dict, Any
from ...db.database import connect_db, get_schema
from ...services.rag import rag_service

router = APIRouter()

@router.post("/connect")
async def connect_database(config: Dict[str, Any]):
    result = connect_db(config)
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    
    schema = get_schema()
    rag_service.index_schema(schema)
    rag_status = rag_service.get_status()
    
    return {
        "message": "Connected", 
        "schema": schema, 
        "details": result,
        "rag": {
            "indexed": True if rag_status["initialized"] else False,
            "tables_indexed": rag_status["indexed_tables"],
            "available": rag_status["available"]
        }
    }

@router.get("/schema")
async def get_current_schema():
    schema = get_schema()
    rag_service.index_schema(schema)
    return {"schema": schema}

@router.get("/rag-status")
async def get_rag_status():
    return rag_service.get_status()
