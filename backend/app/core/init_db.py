from sqlalchemy import text

from app.core.database import engine, Base
from app.models import Base


def init_db():
    """Initialize database tables and add missing columns."""
    # Create all tables (won't modify existing ones)
    Base.metadata.create_all(bind=engine)
    
    # Add missing columns for existing tables
    _add_missing_columns()


def _add_missing_columns():
    """Add missing columns to existing tables."""
    missing_columns = [
        # Project table - new analysis fields
        ("projects", "architecture", "TEXT"),  # 项目架构描述
        ("projects", "data_flow", "TEXT"),
        ("projects", "features_detail", "TEXT"),
        ("projects", "api_info", "TEXT"),
        ("projects", "key_modules", "TEXT"),
    ]
    
    for table_name, column_name, column_type in missing_columns:
        try:
            with engine.connect() as conn:
                # Check if column exists
                result = conn.execute(text(f"""
                    SELECT name FROM pragma_table_info('{table_name}') 
                    WHERE name='{column_name}'
                """))
                if not result.fetchone():
                    # Column doesn't exist, add it
                    conn.execute(text(f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_type}"))
                    conn.commit()
                    print(f"Added column {column_name} to {table_name}")
        except Exception as e:
            # If it fails (e.g., table doesn't exist or column already exists), ignore
            print(f"Note: Could not add column {column_name} to {table_name}: {e}")
