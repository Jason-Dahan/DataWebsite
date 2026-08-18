from pydantic import BaseModel

class DatasetMetadata(BaseModel):
    dataset_id: str
    original_filename: str
    rows: int
    columns: int
    column_names: list[str]
    size_bytes: int