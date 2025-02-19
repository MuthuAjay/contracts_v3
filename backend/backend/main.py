from fastapi import FastAPI, UploadFile, File, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, Response
from pydantic import BaseModel
from typing import Optional, Dict, Any
import json
import os
from analyze import perform_analysis as analyze_func
from process_document import process_document as process_func
from contract_analyzer.config import Config, ModelType

app = FastAPI()

# Configure CORS
origins = [
    "http://localhost:4200",
    "http://127.0.0.1:4200"
]

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # You can restrict this to specific origins like ["http://localhost:4200"]
    allow_credentials=True,
    allow_methods=["*"],  # Allow specific methods like ["GET", "POST"]
    allow_headers=["*"],  # Allow specific headers
)

class SetModelTypeRequest(BaseModel):
    model_type: str

# Request/Response Models
class AnalysisRequest(BaseModel):
    content: str
    type: str
    collection_name: Optional[str] = None
    custom_query: Optional[str] = None

class AnalysisResponse(BaseModel):
    content: str
    collection_name: str

class ErrorResponse(BaseModel):
    detail: str

# File size limit (10MB)
MAX_FILE_SIZE = 10 * 1024 * 1024

# Allowed file types
ALLOWED_FILE_TYPES = {
    '.txt': 'text/plain',
    '.pdf': 'application/pdf',
    '.doc': 'application/msword',
    '.docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
}

async def save_upload_file(file: UploadFile) -> str:
    """Save uploaded file and return the file path."""
    # Check file size
    contents = await file.read()
    if len(contents) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=413,
            detail="File size exceeds the 10MB limit"
        )
    
    # Check file type
    file_ext = os.path.splitext(file.filename)[1].lower()
    if file_ext not in ALLOWED_FILE_TYPES:
        raise HTTPException(
            status_code=415,
            detail=f"Unsupported file type. Allowed types: {', '.join(ALLOWED_FILE_TYPES.keys())}"
        )

    temp_path = f"temp_{file.filename}"
    try:
        with open(temp_path, "wb") as buffer:
            buffer.write(contents)
        return temp_path
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to save uploaded file: {str(e)}"
        )

@app.post("/api/upload")
async def upload_file(file: UploadFile = File(...)):
    # UploadFile = File(...)
    temp_path = None
    try:
        # Save and validate file
        temp_path = await save_upload_file(file)
        
        # Process document
        content, collection_name = process_func(temp_path)
        
        if not content or not collection_name:
            raise HTTPException(
                status_code=500,
                detail="Failed to process document"
            )
        
        
       
        return {
            "content": content,
            "collection_name": collection_name
        }
        
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Document processing failed: {str(e)}"
        )
    finally:
        if temp_path and os.path.exists(temp_path):
            os.remove(temp_path)

@app.post("/api/analyze")
async def analyze_document(request: AnalysisRequest) -> Dict[str, Any]:
    try:
        # Convert frontend analysis type to backend format
        analysis_type_mapping = {
            'contract_review': 'Contract Review',
            'information_extraction': 'Information Extraction',
            'legal_research': 'Legal Research',
            'risk_assessment': 'Risk Assessment',
            'contract_summary': 'Contract Summary',
            'custom_analysis': 'Custom Analysis'
        }
        
        analysis_type = analysis_type_mapping.get(request.type)
        if not analysis_type:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid analysis type: {request.type}"
            )
        
        # Perform analysis
        result = analyze_func(
            content=request.content,
            analysis_type=analysis_type,
            collection_name=request.collection_name,
            custom_query=request.custom_query
        )
        
        if not result:
            raise HTTPException(
                status_code=500,
                detail="Analysis failed to produce results"
            )
            
        return result
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Analysis failed: {str(e)}"
        )

@app.post("/api/set_model_type")
async def set_model_type(request: SetModelTypeRequest):
    try:
        model_type = ModelType[request.model_type.upper().replace(" ", "_")]
        print(f"Setting model type to: {model_type}")
        Config.set_model_type(model_type)
        return {"detail": f"Model type set to {request.model_type}"}
    except KeyError:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid model type --- : {request.model_type}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to set model type: {str(e)}"
        )

# Error handler for generic exceptions
@app.exception_handler(Exception)
async def generic_exception_handler(request, exc):
    return JSONResponse(
        status_code=500,
        content={"detail": str(exc)}
    )

# Health check endpoint
@app.get("/api/health")
async def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)