from app.core.database import engine
from sqlalchemy import text

with engine.connect() as conn:
    result = conn.execute(text('PRAGMA table_info(chat_messages)'))
    columns = [row[1] for row in result]
    print('Current columns:', columns)
    
    if 'chat_mode' not in columns:
        print('Adding chat_mode column...')
        conn.execute(text('ALTER TABLE chat_messages ADD COLUMN chat_mode VARCHAR DEFAULT "project"'))
        conn.commit()
        print('chat_mode column added!')
    else:
        print('chat_mode column already exists')
