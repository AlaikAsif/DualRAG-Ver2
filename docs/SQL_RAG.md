# SQL RAG Setup Guide

## Overview

SQL RAG enables querying databases through natural language using text-to-SQL conversion.

## Components

1. **Schema Retriever** - Get relevant database schema
2. **SQL Generator** - LLM converts NL to SQL
3. **Query Executor** - Execute query safely
4. **Result Parser** - Format results for LLM

## Safety Considerations

⚠️ **This module executes SQL queries. Always enable safety constraints.**

- Read-only user for database
- Query timeout limits
- Result row limits
- Forbidden keywords list
- Audit logging

## Setup Steps

### 1. Database Configuration

Edit `data/config/sql_rag.json`:
```json
{
  "database_type": "postgresql",
  "host": "localhost",
  "port": 5432,
  "database": "chatbot_db",
  "user": "chatbot_readonly",
  "max_rows": 1000,
  "query_timeout": 30,
  "forbidden_keywords": ["DROP", "DELETE", "UPDATE", "INSERT"]
}
```

### 2. Create Read-Only User
```sql
CREATE ROLE chatbot_readonly WITH LOGIN PASSWORD 'password';
GRANT CONNECT ON DATABASE chatbot_db TO chatbot_readonly;
GRANT USAGE ON SCHEMA public TO chatbot_readonly;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO chatbot_readonly;
```

### 3. Initialize Sample Database
```bash
python scripts/init_sql_db.py
```

Loads schema from `data/database/schema.sql`.

### 4. Seed Sample Data
```bash
python scripts/seed_data.py
```

Loads data from `data/database/sample_data.sql`.

## Configuration

Key safety settings:

```python
{
  "max_rows": 1000,           # Max results returned
  "query_timeout": 30,         # Seconds
  "forbidden_keywords": [...], # Blacklist dangerous SQL
  "allowed_tables": [...],     # Whitelist approach
  "log_all_queries": true      # Audit trail
}
```

## Query Flow

```
User: "Show me sales by product"
    ↓
chains/sql_rag_chain.py (query reformulation)
    ↓
rag/sql/schema_retriever.py (get relevant tables/columns)
    ↓
rag/sql/query_generator.py (LLM generates SQL with schema context)
    ↓
rag/sql/executor.py (validate & execute)
    ↓
rag/sql/result_parser.py (format results)
    ↓
chains/response_synthesizer.py (LLM synthesis)
    ↓
Final answer with data summary
```

## Safety Validation

Before execution, queries are checked for:
```python
- Contains only SELECT statements
- Within timeout limit
- Returns <= max_rows
- No forbidden keywords
- Table/column access allowed
- Audit logged
```

## Testing

```bash
pytest tests/unit/test_chains/test_sql_rag.py
pytest tests/integration/test_e2e_flow.py -k sql
```

## Best Practices

1. **Always use read-only user** for chatbot DB access
2. **Whitelist tables** instead of blacklisting
3. **Set reasonable timeouts** (30s is good)
4. **Limit result rows** to prevent data dumps
5. **Audit all queries** for compliance
6. **Monitor execution time** per query type

## Query Examples

```
"Show me total sales by region"
→ SELECT region, SUM(amount) FROM sales GROUP BY region

"What are the top 5 products by revenue?"
→ SELECT product, SUM(amount) AS revenue FROM sales GROUP BY product ORDER BY revenue DESC LIMIT 5

"How many customers are in each country?"
→ SELECT country, COUNT(*) FROM customers GROUP BY country
```

## Troubleshooting

**Syntax errors in generated SQL**:
- Improve schema context
- Add more examples
- Check LLM's schema understanding

**Wrong results**:
- Verify table structure
- Check LLM prompt
- Test query manually

**Timeout errors**:
- Reduce timeout threshold
- Optimize slow queries
- Check database performance

**Access denied errors**:
- Check user permissions
- Verify connection credentials
- Check IP allowlist
