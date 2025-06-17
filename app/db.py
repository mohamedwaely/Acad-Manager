from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from dotenv import load_dotenv
import urllib.parse
import os

load_dotenv()

db_password = urllib.parse.quote_plus(os.getenv('db_password'))
dbURL = (
    f"mysql+pymysql://"
    f"{os.getenv('db_user')}:{db_password}@"
    f"{os.getenv('db_host')}:{os.getenv('db_port', '3306')}/"
    f"{os.getenv('db_name')}?charset=utf8mb4"
)

# MySQL specific engine configuration
engine = create_engine(
    dbURL,
    pool_pre_ping=True,
    pool_recycle=300,
    echo=False  # Set to True for debugging SQL queries
)

try:
    with engine.connect() as connection:
        print("MySQL Connection successful!")
except Exception as e:
    print(f"MySQL Connection failed: {e}")

sessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = sessionLocal()
    try:
        yield db
    finally:
        db.close()