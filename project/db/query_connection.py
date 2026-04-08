import os
from dotenv import load_dotenv
from langchain_community.utilities import SQLDatabase

load_dotenv()
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "3306")
DB_NAME = os.getenv("DB_NAME")

def get_db():
    db_url = f"mysql+pymysql://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}@" \
             f"{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}?charset=utf8mb4"

    db = SQLDatabase.from_uri(
        db_url,
        include_tables=['school_info', 'admission_info', 'requirement_info', 'faq_info'],
        sample_rows_in_table_info=2
    )

    return db
