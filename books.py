import os
from fastapi import FastAPI, HTTPException, Depends, Security
from fastapi.security import APIKeyHeader
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from dotenv import load_dotenv

import models
from database import engine, SessionLocal

# ----- Cargar variables de entorno (.env) -----
load_dotenv()
API_KEY = os.getenv("API_KEY")

# ----- Iniciar app -----
app = FastAPI(title="Books API", version="1.0.0")

# ----- Crear tablas -----
models.Base.metadata.create_all(bind=engine)

# ----- Dependencia DB -----
def get_db():
    try:
        db = SessionLocal()
        yield db
    finally:
        db.close()

# ----- Seguridad por header -----
api_key_header = APIKeyHeader(name="X-API-Key", description="API key por header", auto_error=True)

async def get_api_key(api_key: str = Security(api_key_header)) -> str:
    if API_KEY and api_key == API_KEY:
        return api_key
    raise HTTPException(status_code=403, detail="Could not validate credentials")

# ----- Esquema Pydantic -----
class Book(BaseModel):
    title: str = Field(min_length=1)
    author: str = Field(min_length=1, max_length=100)
    description: str = Field(min_length=1, max_length=100)
    rating: int = Field(gt=-1, lt=101)

# ----- Endpoints -----
@app.get("/")
def root():
    return {"message": "Books API up. See /docs"}

@app.get("/api/v1/books/", tags=["books"])
def list_books(db: Session = Depends(get_db), api_key: str = Depends(get_api_key)):
    return db.query(models.Books).all()

@app.post("/api/v1/books/", tags=["books"])
def create_book(book: Book, db: Session = Depends(get_db), api_key: str = Depends(get_api_key)):
    book_model = models.Books(
        title=book.title,
        author=book.author,
        description=book.description,
        rating=book.rating
    )
    db.add(book_model)
    db.commit()
    db.refresh(book_model)
    return book_model

@app.put("/api/v1/books/{book_id}", tags=["books"])
def update_book(book_id: int, book: Book, db: Session = Depends(get_db), api_key: str = Depends(get_api_key)):
    book_model = db.query(models.Books).filter(models.Books.id == book_id).first()
    if book_model is None:
        raise HTTPException(status_code=404, detail=f"ID {book_id} : Does not exist")

    book_model.title = book.title
    book_model.author = book.author
    book_model.description = book.description
    book_model.rating = book.rating

    db.add(book_model)
    db.commit()
    db.refresh(book_model)
    return book_model

@app.delete("/api/v1/books/{book_id}", tags=["books"])
def delete_book(book_id: int, db: Session = Depends(get_db), api_key: str = Depends(get_api_key)):
    book_model = db.query(models.Books).filter(models.Books.id == book_id).first()
    if book_model is None:
        raise HTTPException(status_code=404, detail=f"ID {book_id} : Does not exist")

    db.query(models.Books).filter(models.Books.id == book_id).delete()
    db.commit()
    return {"deleted_id": book_id}