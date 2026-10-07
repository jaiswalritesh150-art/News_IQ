from database import Base, engine
from models import Article, Summary

print("Creating database tables...")

Base.metadata.create_all(bind=engine)

print("Database tables created successfully.")