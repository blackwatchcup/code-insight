from app.core.database import engine
from sqlalchemy import text

with engine.connect() as conn:
    result = conn.execute(text('PRAGMA table_info(chat_messages)'))
    columns = [row[1] for row in result]
    print('Current columns:', columns)
