# AGENTS.md

Guidelines for AI agents working in this CodeInsight repository.

## Build/Lint/Test Commands

### Backend (Python 3.11+)

```bash
cd backend

# Format & sort imports
black . && isort .

# Type checking
mypy .

# Run all tests
pytest

# Run single test file
pytest tests/test_parsers.py

# Run single test class
pytest tests/test_parsers.py::TestPythonParser

# Run single test function
pytest tests/test_parsers.py::TestPythonParser::test_parse_simple_function

# Run tests with coverage
pytest --cov=app

# Run specific test marker
pytest -m "not slow"

# Development server
uvicorn app.main:app --reload
```

### Frontend (Node.js 18+)

```bash
cd frontend

# Install dependencies
npm install

# Development server
npm run dev

# Build (includes typecheck)
npm run build

# Lint only
npm run lint

# Type check only
npm run typecheck

# Preview production build
npm run preview
```

### Full Stack Development

```bash
# Terminal 1: Backend
cd backend && uvicorn app.main:app --reload

# Terminal 2: Frontend
cd frontend && npm run dev
```

## Code Style Guidelines

### Python (Backend)

**Imports (isort profile "black", line-length 100):**
```python
from typing import Any, Dict, List, Optional, Tuple

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.project import Project
```

**Type Annotations:**
```python
async def create_project(
    name: str,
    local_path: str,
    owner_id: Optional[str] = None,
) -> Project:
    """Create project from local directory.

    Args:
        name: Project name
        local_path: Path to local code directory
        owner_id: User ID if authenticated

    Returns:
        Created project instance

    Raises:
        ValueError: If path doesn't exist or isn't a directory
    """
    pass

def list_projects(self, page: int = 1, page_size: int = 10) -> Tuple[list, int]:
    pass
```

**Error Handling:**
```python
from fastapi import HTTPException

# Use specific status codes
raise HTTPException(status_code=404, detail="Project not found")
raise HTTPException(status_code=400, detail=str(e))
raise HTTPException(status_code=403, detail="Access denied")

# In services, use ValueError for validation
if not os.path.exists(local_path):
    raise ValueError(f"Local path does not exist: {local_path}")
```

**Naming Conventions:**
- Functions/variables: `snake_case` (`get_project`, `file_count`)
- Classes: `PascalCase` (`ProjectService`, `CreateProjectRequest`)
- Constants: `UPPER_SNAKE_CASE` (`MAX_RETRIES`, `DEFAULT_TIMEOUT`)
- Private methods: `_single_underscore` (`_validate_input`, `_count_files`)

**Database Models:**
```python
class Project(Base):
    __tablename__ = "projects"

    id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    status = Column(Enum(ProjectStatus), default=ProjectStatus.READY)

    def to_dict(self) -> dict:
        return {"id": self.id, "name": self.name, "status": self.status.value}
```

### TypeScript (Frontend)

**Imports (ES modules, `@/` alias for src):**
```typescript
import { useState, useEffect } from 'react'
import { api } from '@/services/api'
import { useProjectStore } from '@/stores/projectStore'
import type { Project, ImportData } from '@/types'
```

**Components (functional + Hooks, no class components):**
```typescript
interface ProjectCardProps {
  project: Project
  onDelete: (id: string) => void
}

export const ProjectCard: React.FC<ProjectCardProps> = ({ project, onDelete }) => {
  const [isLoading, setIsLoading] = useState(false)

  const handleDelete = async () => {
    setIsLoading(true)
    try {
      await onDelete(project.id)
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div className="p-4 border rounded">
      <h3>{project.name}</h3>
      <button onClick={handleDelete} disabled={isLoading}>
        Delete
      </button>
    </div>
  )
}
```

**Type Safety (strict mode, no `any`):**
```typescript
// Use type assertions only when necessary
const data = response.data as Project

// Prefer optional chaining and nullish coalescing
const name = user?.profile?.name ?? 'Unknown'

// Define interfaces for all data structures
interface ProjectStore {
  projects: Project[]
  isLoading: boolean
  error: string | null
  fetchProjects: () => Promise<void>
}
```

**State Management (Zustand):**
```typescript
export const useProjectStore = create<ProjectStore>((set) => ({
  projects: [],
  isLoading: false,
  error: null,

  fetchProjects: async () => {
    set({ isLoading: true, error: null })
    try {
      const res = await api.get('/projects')
      const items = res.data.items || res.data.data?.items || []
      set({ projects: items, isLoading: false })
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : 'Unknown error'
      set({ error: message, isLoading: false })
    }
  },
}))
```

**Styling (TailwindCSS):**
```typescript
// Use utility classes with responsive prefixes
<div className="p-4 md:p-6 lg:p-8 bg-white rounded-lg shadow">
  <h1 className="text-xl font-bold text-gray-900">Title</h1>
</div>
```

## Project Structure

```
code-insight/
├── backend/
│   ├── app/
│   │   ├── api/           # FastAPI routes (projects, parser, chat, etc.)
│   │   ├── core/          # Config, auth, database, websocket
│   │   ├── models/        # SQLAlchemy models (project, user, chat)
│   │   ├── parsers/       # Code parsers (Python, JS, TS, Go, Java)
│   │   ├── services/      # Business logic (project, import, rag)
│   │   ├── analysis/      # Code analysis (feature detection, API extraction)
│   │   ├── rag/           # RAG components (vector store, retriever, embedder)
│   │   ├── llm/           # LLM service integration
│   │   ├── graph/         # Call graph, dependency graph generators
│   │   └── docs/          # Documentation generators
│   └── tests/             # pytest tests (test_*.py)
├── frontend/
│   └── src/
│       ├── components/    # Reusable components (Navbar, Sidebar, etc.)
│       ├── pages/         # Page components (Projects, Chat, Analysis)
│       ├── stores/        # Zustand stores (projectStore, chatStore)
│       ├── services/      # API service (api.ts)
│       └── types/         # TypeScript interfaces (index.ts)
```

## Git Commit Format

Conventional Commits: `<type>(<scope>): <subject>`

**Types:** `feat`, `fix`, `docs`, `style`, `refactor`, `test`, `chore`

**Scopes:** `api`, `parser`, `rag`, `llm`, `ui`, `graph`, `docs`, `config`

**Examples:**
```
feat(api): add project import endpoint
fix(parser): handle empty file parsing
refactor(ui): extract ProjectCard component
test(rag): add vector store unit tests
docs(api): update endpoint documentation
```

## Pre-Commit Checklist

```bash
# Backend
cd backend && black . && isort . && mypy . && pytest

# Frontend
cd frontend && npm run lint && npm run typecheck && npm run build
```

## Key Dependencies

**Backend:** FastAPI, SQLAlchemy, Pydantic, Tree-sitter, OpenAI, pytest-asyncio

**Frontend:** React 18, Vite, TypeScript, Zustand, Axios, TailwindCSS, React Router

## Prohibitions

- **Never** use `any` type in TypeScript (use `unknown` or specific types)
- **Never** use `as any`, `@ts-ignore`, `@ts-expect-error` in TypeScript
- **Never** commit `.env` files, secrets, or API keys
- **Never** commit `node_modules/`, `__pycache__/`, `.venv/`
- **Never** use `print()` for debugging in production Python code
- **Never** push with `--force` to main branch
- **Never** skip pre-commit checks with `--no-verify`
- **Never** use \`print()\` for debugging in production Python code
- **Never** push with \`--force\` to main branch
- **Never** skip pre-commit checks with \`--no-verify\`
