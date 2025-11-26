# API Architecture

## Overview
The `api/` module provides FastAPI/Flask server and HTTP endpoints.

## Components

### server.py
- FastAPI application setup
- Middleware configuration
- Route registration
- Startup/shutdown logic

### routes/
HTTP endpoint handlers

### middleware/
Request/response processing

## API Endpoints

- `POST /api/chat` - Send chat query
- `GET /api/reports/{id}` - Retrieve generated report
- `GET /api/health` - Health check

## Security
- CORS configuration
- Authentication (if needed)
- Request validation
- Error handling

## Data Flow
```
HTTP Request
      ↓
CORS Middleware
      ↓
Auth Middleware (if enabled)
      ↓
Route Handler
      ↓
Business Logic (src/)
      ↓
Response Middleware
      ↓
HTTP Response
```
