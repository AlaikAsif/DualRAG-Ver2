# Data Documentation

## Overview
The `data/` directory stores all data used by the chatbot system.

## Subdirectories

### documents/
- `raw/` - Original PDF/DOCX files uploaded
- `processed/` - Cleaned and extracted text
- `metadata/` - Document metadata (filename, upload date, etc.)

### vectors/
- `static/` - Chroma vector database storage
  - `chroma.sqlite3` - SQLite database file
  - `index/` - Vector index files

### database/
- `schema.sql` - SQL database schema
- `sample_data.sql` - Sample data for testing

### config/
- `static_rag.json` - Static RAG configuration
- `sql_rag.json` - SQL RAG configuration
- `reports.json` - Report templates configuration

## Usage
- Don't commit large files (documents, vectors)
- Use `.gitignore` to exclude data/ directory
- Document all schemas clearly
- Version control only configuration files
