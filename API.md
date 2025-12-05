# DualRAG API Documentation

## Overview

The DualRAG API is a FastAPI-based REST API that provides access to a dual Retrieval-Augmented Generation (RAG) system, combining both static document retrieval and SQL database querying.

## Base URL

```
http://localhost:8000
```

## API Documentation

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## Endpoints

### Health & Status

#### Check Server Health
```
GET /health
```

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2025-12-05T15:10:27.123456",
  "service": "DualRAG API"
}
```

#### Check Server Readiness
```
GET /health/ready
```

**Response:**
```json
{
  "ready": true,
  "timestamp": "2025-12-05T15:10:27.123456"
}
```

### SQL RAG Endpoints

#### Query SQL Database
```
POST /api/sql-rag
```

**Request Body:**
```json
{
  "query": "How many users are in the database?",
  "database_context": "Optional context about the database",
  "schema_summary": "Optional schema description",
  "previous_queries": []
}
```

**Response:**
```json
{
  "original_query": "How many users are in the database?",
  "generated_sql": "SELECT COUNT(*) FROM users",
  "sql_explanation": "Count the total number of user records",
  "query_result": {
    "query": "SELECT COUNT(*) FROM users",
    "rows": [{"count": 1234}],
    "column_names": ["count"],
    "row_count": 1,
    "execution_time_ms": 45.2,
    "status": "success"
  },
  "interpretation": "There are 1234 users in the database",
  "confidence": 0.95
}
```

#### Get Database Schema Summary
```
GET /api/schema-summary
```

**Response:**
```json
{
  "schema_summary": "Database contains tables: users, orders, products..."
}
```

#### Refresh Database Schema Cache
```
POST /api/schema-refresh
```

**Response:**
```json
{
  "status": "success",
  "message": "Schema refreshed"
}
```

#### Get Query Execution History
```
GET /api/execution-history?limit=10
```

**Query Parameters:**
- `limit` (int, optional): Number of recent executions to return (default: 10)

**Response:**
```json
{
  "history": [
    {
      "query": "SELECT COUNT(*) FROM users",
      "status": "success",
      "row_count": 1,
      "execution_time_ms": 45.2,
      "timestamp": 1733407827.123,
      "error": null
    }
  ]
}
```

### Chat Endpoints

#### Send Chat Message
```
POST /api/chat
```

**Request Body:**
```json
{
  "message": "What is the total revenue this year?",
  "session_id": "session-123",
  "context": {}
}
```

**Response:**
```json
{
  "message": "What is the total revenue this year?",
  "reply": "Based on the database, the total revenue this year is...",
  "session_id": "session-123",
  "confidence": 0.85,
  "source": "chat",
  "requires_clarification": false
}
```

#### Get Conversation History
```
GET /api/conversation/{session_id}
```

**Response:**
```json
{
  "session_id": "session-123",
  "messages": [],
  "created_at": "2025-12-05T15:10:27.123456"
}
```

#### Delete Conversation
```
DELETE /api/conversation/{session_id}
```

**Response:**
```json
{
  "status": "success",
  "message": "Session session-123 deleted"
}
```

### Report Endpoints

#### Generate Report
```
POST /api/reports
```

**Request Body:**
```json
{
  "title": "Q4 Sales Report",
  "content": "Sales data summary...",
  "format": "html"
}
```

**Response:**
```json
{
  "report_id": "rep_a1b2c3d4e5",
  "title": "Q4 Sales Report",
  "content": "Sales data summary...",
  "status": "completed",
  "generated_at": "2025-12-05T15:10:27.123456",
  "format": "html"
}
```

#### Get Report
```
GET /api/reports/{report_id}
```

**Response:**
```json
{
  "report_id": "rep_a1b2c3d4e5",
  "title": "Q4 Sales Report",
  "content": "Sales data summary...",
  "generated_at": "2025-12-05T15:10:27.123456"
}
```

#### Delete Report
```
DELETE /api/reports/{report_id}
```

**Response:**
```json
{
  "status": "success",
  "message": "Report rep_a1b2c3d4e5 deleted"
}
```

## Error Handling

All errors follow a consistent format:

```json
{
  "error": "Error Type",
  "message": "Description of what went wrong",
  "path": "/api/endpoint",
  "method": "POST"
}
```

### Status Codes

- `200 OK`: Request successful
- `400 Bad Request`: Invalid request parameters
- `401 Unauthorized`: Missing or invalid authentication
- `404 Not Found`: Resource not found
- `500 Internal Server Error`: Server-side error
- `503 Service Unavailable`: Service temporarily unavailable

## Authentication

Currently, the API does not require authentication. In production, implement JWT-based authentication.

## Rate Limiting

Not yet implemented. Recommended for production deployment.

## Configuration

Configure the API using environment variables in `.env`:

```
DATABASE_CONNECTION_STRING=postgresql://user:pass@host:5432/db
PORT=8000
DEBUG=false
LOG_LEVEL=info
```

## Running the Server

### Development

```bash
python main.py
```

### Production

```bash
uvicorn api.server:app --host 0.0.0.0 --port 8000 --workers 4
```

## Example Requests

### Using curl

```bash
# Health check
curl http://localhost:8000/health

# SQL RAG query
curl -X POST http://localhost:8000/api/sql-rag \
  -H "Content-Type: application/json" \
  -d '{
    "query": "How many users are active?",
    "database_context": "Users table has active_status field",
    "schema_summary": "",
    "previous_queries": []
  }'

# Chat message
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "What is our top product?",
    "session_id": "session-123",
    "context": {}
  }'
```

### Using Python

```python
import requests

# SQL RAG query
response = requests.post(
    "http://localhost:8000/api/sql-rag",
    json={
        "query": "How many users are active?",
        "database_context": "",
        "schema_summary": "",
        "previous_queries": []
    }
)

print(response.json())
```

## Support

For issues or questions, please refer to the project documentation.
