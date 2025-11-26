# Report Generation Guide

## Overview

Report generation creates structured HTML/PDF reports from query results.

## Components

1. **Generator** - Orchestrates report creation
2. **Templates** - HTML/CSS templates
3. **Customization Parser** - Parse user requirements
4. **Renderer** - Render final report

## Report Types

### Default Report
Standard HTML report with:
- Title
- Data summary
- Tables/charts
- Styling

### Custom Report
User specifies:
- Layout
- Sections
- Styling
- Export format

## Customization Options

Users can request:
```
"Create a report with:
- Title: Q4 Sales Report
- Include: Revenue table, Product breakdown pie chart
- Style: Professional Blue theme
- Export as: PDF"
```

## Setup

### 1. Install Dependencies
```bash
pip install jinja2 weasyprint
```

### 2. Configure Report Templates

Edit `data/config/reports.json`:
```json
{
  "templates": {
    "default": {
      "layout": "single_column",
      "colors": ["#1f77b4", "#ff7f0e"],
      "fonts": "Arial, sans-serif"
    }
  }
}
```

## Template Structure

Reports use Jinja2 templates in `src/report/templates/`:

```html
<!-- templates/default.py -->
<html>
  <head>
    <title>{{ report.title }}</title>
    <style>{{ report.css }}</style>
  </head>
  <body>
    <h1>{{ report.title }}</h1>
    {% for section in report.sections %}
      <section class="{{ section.type }}">
        {{ section.content }}
      </section>
    {% endfor %}
  </body>
</html>
```

## Generation Flow

```
Query Results
    ↓
chains/report_chain.py (decide report type)
    ↓
src/report/customization_parser.py (parse requirements)
    ↓
src/report/generator.py (aggregate data)
    ↓
src/report/templates/default.py (select template)
    ↓
src/report/renderer.py (render HTML)
    ↓
Optional: Convert to PDF
    ↓
Save & return to user
```

## Request Format

API request:
```json
{
  "query": "Create Q4 sales report",
  "customization": {
    "title": "Q4 Sales Report",
    "sections": ["summary", "by_region", "by_product"],
    "theme": "professional_blue",
    "export_format": "html"
  }
}
```

## Customization Options

```python
{
  "title": "string",
  "subtitle": "string",
  "sections": ["summary", "data_table", "charts", "conclusion"],
  "theme": "default" | "professional_blue" | "minimal",
  "include_charts": true,
  "include_tables": true,
  "chart_types": ["pie", "bar", "line"],
  "export_format": "html" | "pdf",
  "page_size": "A4" | "Letter"
}
```

## Built-in Components

Available in `src/report/templates/components.py`:

- **SummarySection** - Key metrics
- **TableSection** - Data tables
- **ChartSection** - Visualizations
- **ConclusionSection** - Summary text
- **Header/Footer** - Document metadata

## Testing

```bash
pytest tests/unit/test_chains/test_report.py
```

Test custom reports:
```python
report = generate_report(
    data=query_results,
    customization={"title": "Test Report"}
)
```

## Best Practices

1. **Pre-design templates** for common use cases
2. **Limit customization options** to prevent complexity
3. **Include data source** in reports
4. **Add timestamps** to reports
5. **Test PDF rendering** with complex layouts
6. **Version templates** for reproducibility

## Performance

- Cache rendered templates
- Pre-compile Jinja2 templates
- Use async rendering for large reports
- Batch PDF generation

## Troubleshooting

**Rendering issues**:
- Check template syntax
- Validate HTML structure
- Test CSS in browser

**PDF conversion fails**:
- Ensure WeasyPrint installed
- Check for missing fonts
- Reduce page complexity

**Slow generation**:
- Profile template rendering
- Optimize data aggregation
- Use async rendering
