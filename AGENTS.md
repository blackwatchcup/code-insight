# AGENTS.md

This file contains guidelines for AI agents working in this CodeInsight repository.

## Build/Lint/Test Commands

### Backend (Python 3.11+)

```bash
cd backend

# Format code
black .

# Sort imports
isort .

# Type checking
mypy .

# Run all tests
pytest

# Run single test file
pytest tests/test_parsers.py

# Run single test function
pytest tests/test_parsers.py::TestPythonParser::test_parse_simple_function

# Run tests with coverage
pytest --cov=app

# Run development server
uvicorn app.main:app --reload
```

### Frontend (Node.js 18+)

```bash
cd frontend

# Install dependencies
npm install

# Build
npm run build

# Lint
npm run lint

# Type check
npm run typecheck

# Dev server
npm run dev

# Preview build
npm run preview
```

### Full Stack Development

```bash
# Backend
cd backend && uvicorn app.main:app --reload

# Frontend (separate terminal)
cd frontend && npm run dev
```

## Code Style Guidelines

### Python (Backend)

**Imports:**
- Use `isort` profile "black" with line-length 100
- Standard library imports first, third-party, then local
- From imports preferred over direct imports

```python
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db
```

**Type Annotations:**
- Complete type annotations required for all function parameters and returns
- Use `Optional[T]` instead of `T | None` for backward compatibility
- Use `Dict[str, Any]` for flexible data structures

```python
async def create_project(
    name: str,
    owner_id: Optional[str] = None
) -> Project:
    """Create a new project.
    
    Args:
        name: Project name
        owner_id: User ID if authenticated
        
    Returns:
        Created project instance
    """
    pass
```

**Error Handling:**
- Raise HTTPException for API errors (400, 404, 403, 500)
- Use try-except with specific exception types
- Log errors appropriately

```python
try:
    project = await service.create_project(name, owner_id)
except ValueError as e:
    raise HTTPException(status_code=400, detail=str(e))
except Exception as e:
    raise HTTPException(status_code=500, detail="Internal server error")
```

**Naming Conventions:**
- Functions: snake_case (e.g., `get_project`, `create_user`)
- Classes: PascalCase (e.g., `ProjectService`, `CreateProjectRequest`)
- Constants: UPPER_SNAKE_CASE (e.g., `MAX_RETRIES`, `DEFAULT_TIMEOUT`)
- Private methods: single underscore prefix (e.g., `_validate_input`)

**Database Models:**
- Use SQLAlchemy with declarative base
- Include `to_dict()` method for JSON serialization
- Use enums for status fields
- Define relationships explicitly

**Async Patterns:**
- Use `async def` for all async functions
- Use `await` for async operations
- Prefer `async for` when iterating async generators

### TypeScript (Frontend)

**Imports:**
- Use ES module syntax
- Import type-only imports with `import type`
- Group imports: external, then internal with `@/` alias

```typescript
import { useState } from 'react'
import { useProjectStore } from '@/stores/projectStore'
import type { Project } from '@/types'
```

**Components:**
- Functional components with Hooks only
- Define props interface for all components
- Use destructuring for props

```typescript
interface ProjectCardProps {
  project: Project
  onDelete: (id: string) => void
}

export const ProjectCard: React.FC<ProjectCardProps> = ({ project, onDelete }) => {
  return <div>{project.name}</div>
}
```

**Type Safety:**
- No `any` types - use `unknown` or specific types
- Use union types for alternatives
- Use optional chaining `?.` and nullish coalescing `??`

```typescript
// Avoid
const data: any = response.data

// Use
const data = response.data as Project
const name = user?.profile?.name ?? 'Unknown'
```

**State Management:**
- Use Zustand for global state
- Interface for store shape
- Async actions with error handling

```typescript
interface ProjectStore {
  projects: Project[]
  isLoading: boolean
  error: string | null
  fetchProjects: () => Promise<void>
}
```

**API Calls:**
- Use axios with configured base URL
- Centralized API service in `src/services/api.ts`
- Handle errors with try-catch

**Styling:**
- TailwindCSS utility classes
- Responsive design with `md:`, `lg:` prefixes
- Use shadcn/ui components when available

## General Guidelines

### Project Structure

```
code-insight/
├── backend/
│   ├── app/
│   │   ├── api/          # FastAPI routes
│   │   ├── core/         # Config, auth, database
│   │   ├── models/       # SQLAlchemy models
│   │   ├── parsers/      # Code parsers (Python, JS, TS)
│   │   ├── services/     # Business logic
│   │   ├── analysis/     # Code analysis
│   │   ├── rag/          # RAG components
│   │   └── llm/          # LLM service
│   └── tests/            # pytest tests
├── frontend/
│   └── src/
│       ├── components/   # React components
│       ├── pages/        # Page components
│       ├── stores/       # Zustand stores
│       ├── services/     # API service
│       └── types/        # TypeScript types
```

### Security

- Never commit `.env` files or secrets
- Use environment variables for configuration
- Validate all inputs
- Implement proper authentication/authorization

### Git Commit Format

Follow Conventional Commits: `<type>(<scope>): <subject>`

Types: `feat`, `fix`, `docs`, `style`, `refactor`, `test`, `chore`
Scopes: `api`, `parser`, `rag`, `llm`, `ui`, `config`

Examples:
- `feat(api): add project import endpoint`
- `fix(parser): handle empty file parsing`
- `refactor(ui): extract common button component`

### Before Committing

Always run:
```bash
# Backend
cd backend && black . && isort . && mypy . && pytest

# Frontend
cd frontend && npm run lint && npm run typecheck && npm run build
```

### Key Dependencies

**Backend:**
- FastAPI (web framework)
- SQLAlchemy (ORM)
- Pydantic (validation)
- ChromaDB (vector store)
- OpenAI (LLM)
- Tree-sitter (parsing)
- pytest (testing)

**Frontend:**
- React 18 (UI framework)
- Vite (build tool)
- TypeScript (type safety)
- Zustand (state management)
- Axios (HTTP client)
- TailwindCSS (styling)
- React Router (routing)
