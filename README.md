# CodeInsight

Local code repository intelligent analysis and knowledge Q&A system.

## Requirements

- **Python >= 3.11** (3.11+ required)
- Node.js >= 18
- Docker (optional)

## Quick Start

```bash
# Start services
docker-compose up -d

# Access
# Frontend: http://localhost:3000
# Backend API: http://localhost:8000/docs
```

## Development

```bash
# Backend (Python 3.11+)
cd backend

# Create virtual environment
python -m venv .venv

# Activate (Windows)
.\.venv\Scripts\activate
# Activate (Linux/Mac)
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run development server
uvicorn app.main:app --reload

# Frontend
cd frontend
npm install
npm run dev
```
