"""
数据库迁移脚本 - 添加项目上下文字段

添加以下字段到projects表：
- readme_content: README文件内容
- project_summary: LLM生成的项目摘要
- tech_stack: 技术栈（JSON数组字符串）

运行方式：
    python backend/scripts/migrate_add_project_context.py
"""

import sys
from pathlib import Path

# 添加项目根目录到路径
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from sqlalchemy import text
from app.core.database import engine, Base
from app.models.project import Project


def migrate():
    """执行数据库迁移"""
    print("开始迁移：添加项目上下文字段...")
    
    with engine.connect() as conn:
        # 检查字段是否已存在
        def column_exists(table_name: str, column_name: str) -> bool:
            result = conn.execute(text(f"PRAGMA table_info({table_name})"))
            columns = [row[1] for row in result]
            return column_name in columns
        
        # 添加 readme_content 字段
        if not column_exists("projects", "readme_content"):
            print("添加 readme_content 字段...")
            conn.execute(text("ALTER TABLE projects ADD COLUMN readme_content TEXT"))
            conn.commit()
        else:
            print("readme_content 字段已存在，跳过")
        
        # 添加 project_summary 字段
        if not column_exists("projects", "project_summary"):
            print("添加 project_summary 字段...")
            conn.execute(text("ALTER TABLE projects ADD COLUMN project_summary TEXT"))
            conn.commit()
        else:
            print("project_summary 字段已存在，跳过")
        
        # 添加 tech_stack 字段
        if not column_exists("projects", "tech_stack"):
            print("添加 tech_stack 字段...")
            conn.execute(text("ALTER TABLE projects ADD COLUMN tech_stack TEXT"))
            conn.commit()
        else:
            print("tech_stack 字段已存在，跳过")
    
    print("迁移完成！")


if __name__ == "__main__":
    migrate()
