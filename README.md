# Chatbot Revamp

Advanced LLM-driven chatbot with intelligent orchestration, RAG support, and report generation.

## Features

- **LLM Orchestrator**: Intelligent routing of user queries to appropriate handlers
- **Static RAG**: Vector-based document search with Chroma
- **SQL RAG**: Natural language to SQL conversion and execution
- **Report Generation**: Create structured HTML/PDF reports
- **FastAPI**: Modern HTTP API
- **Monitoring**: Comprehensive logging and metrics

## Quick Start

See `docs/SETUP.md` for detailed setup instructions.

### Basic Setup

```bash
git clone <repo>
cd chatbot-revamp
python -m venv venv
pip install -r requirements.txt
cp config/.env.example .env
python scripts/download_models.py
python scripts/init_static_db.py
python scripts/init_sql_db.py
python scripts/seed_data.py
python main.py
```

Access at `http://localhost:8000`.

## Architecture

See `docs/ARCHITECTURE.md` for system design.

## Key Modules

- `src/chains/` - LLM orchestration
- `src/rag/` - Static and SQL RAG
- `src/decision/` - Routing logic
- `src/prompts/` - LLM prompts
- `api/` - FastAPI server
- `frontend/` - Web UI

## Documentation

- `docs/ARCHITECTURE.md` - System design
- `docs/LLM_ORCHESTRATION.md` - Routing decisions
- `docs/STATIC_RAG.md` - Document search
- `docs/SQL_RAG.md` - Database queries
- `docs/REPORTS.md` - Report generation
- `docs/API.md` - API reference
- `docs/SETUP.md` - Setup guide

## Testing

```bash
pytest tests/ -v
pytest tests/unit/ -v
pytest tests/integration/ -v
```

## Development

```bash
black src/ api/ config/
flake8 src/ api/ config/
mypy src/ api/ config/
```

## API Endpoints

- `POST /api/chat` - Send query
- `GET /api/reports/{id}` - Get report
- `GET /api/health` - Health check

## Configuration

Edit `config/.env` with LLM, database, and API settings.

See `config/.env.example` for all options.

## License

MIT License

## Support

- Check `docs/` for documentation
- Review tests for examples
- Check logs for errors

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make changes
4. Add tests
5. Submit PR

---

**Status**: Active Development  
**Python**: 3.11+  
