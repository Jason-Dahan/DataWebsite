from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_uploaded_csv():
    csv_content = b"name,age\n,30\nSarah,28\n"
    response = client.post("/datasets/upload", files={"file":("people.csv",csv_content,"text/csv")})
    assert response.status_code == 200
    data = response.json()
    assert data["original_filename"] == "people.csv"
    assert data["rows"] == 2
    assert data["columns"] == 2
    assert data["column_names"] == ["name", "age"]
    assert data["size_bytes"] == len(csv_content)
    assert "dataset_id" in data

def test_reject_non_csv():
    response = client.post(
        "/datasets/upload",
        files = {
            "file": (
                "people.txt",
                b"name,age\nJason,30\n",
                "text/plain"
            )
        }
    )
    assert response.status_code == 400
    data = response.json() == {"detail": "Only csv format is supported"}

def test_empty_csv():
    response = client.post(
        "/datasets/upload",
        files = {"file": (
            "empty.csv",
            b"",
            "text/csv"
        )
        }
    )
    assert response.status_code == 400
    assert response.json() == {"detail": "Invalid CSV format"}

def test_invalid_content():
    response = client.post(
        "/datasets/upload",
        files = {"file": (
            "fake.csv",
            b"\xff\xfe\x00\x00",
            "text/csv"
        )
    }
)
    assert response.status_code == 400
    assert response.json() == {"detail": "Invalid CSV format"}

def test_over_columns():
    columns = [f"column_{i}" for i in range(501)]
    csv_content = (
        ",".join(columns)
        +"/n"
        +",".join(["1"]*501)
        +"\n"
    ).encode()

    response = client.post(
        "/datasets/upload",
        files = {"file": (
            "wide.csv",
            csv_content,
            "text/csv"
        )
        }
    )
    assert response.status_code == 400
    assert response.json() == {"detail": "Too many columns"}

def test_reject_large(monkeypatch):
    monkeypatch.setattr(
        "app.services.csv_validator.MAX_FILE_SIZE",10
    )
    csv_content = b"name,age\nJason,30\n"
    response = client.post(
        "/datasets/upload",
        files = {"file": (
            "people.csv",
            csv_content,
            "text/csv"
        )}
    )
    assert response.status_code == 400
    assert response.json() == {"detail": "File is too large"}

def test_over_rows(monkeypatch):
    monkeypatch.setattr(
        "app.services.csv_validator.MAX_ROWS",
        2
    )
    csv_content = (
        b"name,age\n"
        b"Jason,30\n"
        b"Sarah,28\n"
        b"David,35\n"
    )
    response = client.post(
        "/datasets/upload",
        files = {"file": (
            "people.csv",
            csv_content,
            "text/csv"
        )}
    )
    assert response.status_code == 400
    assert response.json() == {"detail": "Too many rows"}

def test_over_cell(monkeypatch):
    monkeypatch.setattr("app.services.csv_validator.MAX_CELL_LENGTH", 4)
    csv_content = (
        b"name,age\n"
        b"Jason,30\n"
        b"Sarah,28\n"
    )
    response = client.post(
        "/datasets/upload",
        files = {"file": (
            "people.csv",
            csv_content,
            "text/csv"
        )}
    )
    assert response.status_code == 400
    assert response.json() == {"detail": "Too many chars in cells"}