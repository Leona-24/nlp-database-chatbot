import os
import csv
from datetime import datetime
from fastapi import APIRouter
from ...schemas.query import FeedbackRequest

router = APIRouter()

@router.post("/feedback")
async def submit_feedback(feedback: FeedbackRequest):
    feedback_file = os.path.join(os.path.dirname(__file__), "..", "..", "..", "data", "feedback.csv")
    file_exists = os.path.isfile(feedback_file)
    
    try:
        os.makedirs(os.path.dirname(feedback_file), exist_ok=True)
        with open(feedback_file, mode='a', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
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
        
    return {"message": "Feedback submitted successfully"}
