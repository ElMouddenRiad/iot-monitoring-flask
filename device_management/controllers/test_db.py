from sqlalchemy import create_engine
from sqlalchemy_utils import database_exists, create_database

def test_db_connection():
    DATABASE_URL = "postgresql://admin:admin123@localhost:5432/iot_platform"
    
    try:
        engine = create_engine(DATABASE_URL)
        if not database_exists(engine.url):
            create_database(engine.url)
        
        # Test the connection
        connection = engine.connect()
        connection.close()
        print("Database connection successful!")
        return True
    except Exception as e:
        print(f"Error connecting to database: {e}")
        return False

if __name__ == "__main__":
    test_db_connection()