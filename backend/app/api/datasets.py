from fastapi import APIRouter,File,UploadFile

from app.schemas.dataset import DatasetMetadata
from app.services.csv_validator import validate_csv

router = APIRouter(prefix="/datasets", tags=["datasets"])

@router.post("/upload", response_model=DatasetMetadata)
async def upload_dataset(file: UploadFile = File(...)):
    return await validate_csv(file)