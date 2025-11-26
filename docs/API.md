# API Documentation

## Overview

The chatbot API provides HTTP endpoints for chat queries, report retrieval, and system health checks.

## Base URL
```
http://localhost:8000
```

## Endpoints

### 1. Chat Endpoint

**POST** `/api/chat`

Send a user query to the chatbot.

**Request:**
```json
{
  "message": "What is machine learning?",
  "conversation_id": "optional-conversation-uuid",
  "context": {
    "user_id": "optional-user-id",
    "session_id": "optional-session-id"
  }
}
```

**Response:**
```json
{
  "response": "Machine learning is...",
  "action": "chat",
  "confidence": 0.95,
  "sources": ["internal_knowledge"],
  "conversation_id": "uuid",
  "timestamp": "2024-01-01T12:00:00Z",
  "execution_time_ms": 1234
}
```

**Status Codes:**
- `200` - Success
- `400` - Invalid request
- `500` - Server error

### 2. Reports Endpoint

**GET** `/api/reports/{report_id}`

Retrieve a generated report.

**Response:**
```json
{
  "id": "report-uuid",
  "title": "Q4 Sales Report",
  "html": "<html>...</html>",
  "created_at": "2024-01-01T12:00:00Z",
  "data_source": ["sql_rag"],
  "query": "Create Q4 sales report"
}
```

**Status Codes:**
- `200` - Success
- `404` - Report not found

### 3. Health Check

**GET** `/api/health`

Check system status.

**Response:**
```json
{
  "status": "healthy",
  "components": {
    "llm": "connected",
    "database": "connected",
    "vector_store": "connected"
  },
  "timestamp": "2024-01-01T12:00:00Z"
}
```

## Request/Response Format

All requests/responses are JSON.

### Headers

```
Content-Type: application/json
Accept: application/json
```

### Error Response

```json
{
  "error": "Error message",
  "error_code": "INVALID_REQUEST",
  "details": {},
  "timestamp": "2024-01-01T12:00:00Z"
}
```

## Rate Limiting

- 100 requests per minute per IP
- 1000 requests per hour per user_id

Headers:
```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1704124800
```

## Authentication (Optional)

If enabled, include Bearer token:
```
Authorization: Bearer <token>
```

## Usage Examples

### Chat Query

```bash
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Show me sales by region"
  }'
```

### Get Report

```bash
curl http://localhost:8000/api/reports/abc123
```

### Health Check

```bash
curl http://localhost:8000/api/health
```

## WebSocket (Optional)

For streaming responses:
```
ws://localhost:8000/ws/chat
```

Message format:
```json
{
  "type": "message",
  "message": "User query"
}
```

## Performance

- Typical response time: 1-5 seconds
- Max payload: 10MB
- Request timeout: 60 seconds

## Versioning

Current API version: `v1`

Path: `/api/v1/chat`

## CORS

Allowed origins (configurable):
```
http://localhost:3000
http://localhost:8000
```

## Support

For API issues, see `docs/TROUBLESHOOTING.md`.
