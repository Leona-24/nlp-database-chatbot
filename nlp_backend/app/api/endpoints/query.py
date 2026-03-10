from fastapi import APIRouter, HTTPException
from ...db.database import get_schema, get_engine, execute_query
from ...services.nlp import NLPEngine
from ...services.visualization import generate_chart
from ...schemas.query import QueryRequest, QueryResponse

router = APIRouter()
nlp_engine = NLPEngine()

@router.post("/query", response_model=QueryResponse)
async def handle_query(request: QueryRequest):
    try:
        schema = get_schema()
        engine = get_engine()
        dialect = engine.dialect.name
        
        nlp_response = nlp_engine.generate_sql(
            request.query, 
            schema, 
            dialect=dialect, 
            history=request.history
        )
        suggested_chart = nlp_response.get("suggested_chart", "none")
        sql_query = nlp_response["sql"]
        thought = nlp_response["thought"]

        if sql_query == "-- Not Found":
             return {
                "sql_query": "",
                "results": [],
                "message": thought,
                "thought": thought,
                "confidence": 0
            }
        
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
