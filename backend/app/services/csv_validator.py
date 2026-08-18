from fastapi import HTTPException, UploadFile,status

from app.schemas.dataset import DatasetMetadata
import pandas as pd
import uuid

MAX_FILE_SIZE = 20 * 1024 * 1024
MAX_ROWS = 500_000
CHUNK_SIZE = 1024 * 1024
MAX_COLUMNS = 500
MAX_CELL_LENGTH = 100_000

async def validate_csv(file: UploadFile) -> DatasetMetadata:
    #Check a filename was provided
    if not file.filename:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No file part")
    #Check that it ends in csv
    if not file.filename.lower().endswith(".csv"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Not a CSV file")
    #Check file size without loading to memory
    size = 0
    while chunk := await file.read(CHUNK_SIZE):
        size += len(chunk)
        if size > MAX_FILE_SIZE:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="File is too large")
    await file.seek(0)
    #Parse and validate contents
    try:
        dataframe = pd.read_csv(file.file,chunksize = 10_000)
        total_rows = 0
        column_names = None

        for chunk in dataframe:
            if column_names is None:
                column_names = chunk.columns.tolist()
                if len(column_names) > MAX_COLUMNS:
                    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Too many columns")
            total_rows += len(chunk)
            if total_rows > MAX_ROWS:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Too many rows")
            text_columns = chunk.select_dtypes(include = ["object","string"])
            for column in text_columns.columns:
                lengths = (text_columns[column].dropna().astype(str).str.len())
                if not lengths.empty and lengths.max() > MAX_CELL_LENGTH:
                    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Too many chars in cells")
    except (pd.errors.ParserError, pd.errors.EmptyDataError, UnicodeDecodeError):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid CSV format")
    #Reject files with no actual data
    if column_names is None or total_rows == 0:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Must contain at least one row of data")
    dataset_id = str(uuid.uuid4())
    return DatasetMetadata(
        dataset_id=dataset_id,
        original_filename=file.filename,
        rows=total_rows,
        columns=len(column_names),
        column_names=column_names,
        size_bytes=size
    )