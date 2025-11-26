# Setup Guide

## Prerequisites

- Python 3.11+
- PostgreSQL or MySQL (for SQL RAG)
- Ollama (for LLM)
- Git

## Installation

### 1. Clone Repository
```bash
git clone <repository-url>
cd chatbot-revamp
```

### 2. Create Python Environment
```bash
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure Environment
```bash
cp config/.env.example .env
# Edit .env with your settings
```

### 5. Download Models
```bash
python scripts/download_models.py
```

This downloads the BGE-Large embedding model.

### 6. Initialize Databases

#### Static RAG (Vector Store)
```bash
python scripts/init_static_db.py
```

Creates Chroma vector database at `data/vectors/static/`.

#### SQL RAG (Database)
```bash
python scripts/init_sql_db.py
```

Creates schema and sample data.

### 7. Start Ollama
```bash
ollama serve
# In another terminal:
ollama pull llama2
```

### 8. Seed Data
```bash
python scripts/seed_data.py
```

Loads sample documents and data.

### 9. Run Server
```bash
python main.py
```

Server starts at `http://localhost:8000`.

## Development Setup

### Install Dev Dependencies
```bash
pip install -r requirements-dev.txt
```

### Run Tests
```bash
pytest tests/ -v
```

### Format Code
```bash
black src/ api/ config/
flake8 src/ api/ config/
```

### Generate Documentation
```bash
pdoc src/ --html
```

## Docker Setup (Optional)

### Build Image
```bash
docker build -t chatbot-revamp .
```

### Run Container
```bash
docker run -p 8000:8000 chatbot-revamp
```

## Troubleshooting

### Ollama Connection Failed
- Ensure Ollama is running: `ollama serve`
- Check URL in `.env` matches Ollama host
- Try `curl http://localhost:11434/api/tags`

### Database Connection Failed
- Check PostgreSQL is running
- Verify credentials in `.env`
- Check firewall/network access

### Embedding Model Not Found
- Run `python scripts/download_models.py`
- Check `data/vectors/static/` directory

### Port Already in Use
- Change `API_PORT` in `.env`
- Or kill process on port 8000

## Project Structure

See `docs/ARCHITECTURE.md` for full structure overview.

## Next Steps

1. Read `docs/LLM_ORCHESTRATION.md` to understand routing
2. Read `docs/STATIC_RAG.md` to set up document search
3. Read `docs/SQL_RAG.md` to set up database queries
4. Read `docs/API.md` for API endpoints
5. Upload documents to `data/documents/raw/`
6. Test the chatbot

## Support

For issues:
1. Check logs in terminal output
2. Review `src/monitoring/logger.py` for detailed logs
3. Run tests to identify failures
4. See `docs/TROUBLESHOOTING.md`
