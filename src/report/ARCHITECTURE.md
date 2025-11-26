# Report Architecture

## Overview
The `report/` module handles HTML/PDF report generation from query results.

## Components

### generator.py
- Report generation orchestrator
- Data aggregation
- Template selection

### templates/
HTML and component templates for report rendering.

### customization_parser.py
- Parse user custom requirements
- Layout customization
- Styling options

### renderer.py
- Render final HTML
- Apply styling
- Generate PDF (optional)

## Report Flow
```
Query Results
      ↓
Customization Parsing (user requirements)
      ↓
Template Selection
      ↓
Data Aggregation
      ↓
HTML/CSS Rendering
      ↓
Final Report Output
```
