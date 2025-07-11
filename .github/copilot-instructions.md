# Copilot Instructions for notion-auto-equation

## Project Overview

This is a Python utility that converts LaTeX-style mathematical expressions (`$$equation$$` and `$equation$`) in Notion pages into proper Notion equation blocks. The tool follows a 4-step pipeline: fetch → parse → transform → upload.

## Architecture & Data Flow

The application uses a **linear pipeline pattern** with explicit error handling at each stage:

1. **Step 1 (Fetch)**: `get_all_blocks()` recursively retrieves all blocks from a Notion page using pagination
2. **Step 2 (Parse)**: `blocks_to_dataframe()` converts Notion block structures into a pandas DataFrame for processing
3. **Step 3 (Transform)**: `format_content_for_notion()` uses regex to convert LaTeX math notation to Notion's equation format
4. **Step 4 (Upload)**: `upload_blocks_in_batches()` sends processed blocks back to Notion in manageable chunks

## Core Dependencies & Configuration

- **Notion API**: Uses direct REST API calls (not the official notion-client) for maximum control
- **Authentication**: Requires `NOTION_API_KEY` and `PAGE_ID` constants at the top of `Main.py`
- **API Version**: Hard-coded to `"2022-06-28"` in headers - critical for compatibility
- **Required packages**: `requests`, `pandas`, `notion_client` (imported but unused), `logging`, `re`

## Critical Patterns & Conventions

### Equation Processing Logic

The core transformation uses **two-pass regex parsing**:

```python
# Pass 1: Block equations $$...$$
pattern = re.compile(r'\$\$(.+?)\$\$', re.DOTALL)
# Pass 2: Inline equations $...$
inline_pattern = re.compile(r'\$(.+?)\$')
```

### Block Type Handling

The code maps Notion block types to specific processing logic in `combine_text_and_equations()`:

- `paragraph`, `heading_1/2/3`, `quote`: Use `rich_text` arrays
- `code`: Uses `text` property with language specification
- `bulleted_list_item`: Uses `rich_text` arrays
- `divider`: Empty object `{}`

### Error Handling Pattern

All API calls follow this pattern:

```python
try:
    response = requests.get(url, headers=HEADERS)
    response.raise_for_status()
    # process response
except requests.exceptions.RequestException as e:
    logging.error(f"Failed to fetch: {e}")
    break  # or return None
```

### Batching Strategy

- Default batch size: 10 blocks per request
- Used to avoid Notion API rate limits
- Function: `upload_blocks_in_batches(page_id, blocks, batch_size=10)`

## Development Workflow

### Setup Requirements

1. Replace placeholder values in `Main.py`:
   - `NOTION_API_KEY = "your_notion_api_key_here"`
   - `PAGE_ID = "your_page_id_here"`
2. No requirements.txt exists - install: `requests pandas notion-client`

### Testing & Debugging

- All operations log to console with timestamps
- Manual step required: User must clear Notion page content before upload
- Entry point: `python Main.py` (runs `main()` function)

### Key Gotchas

- **Manual Page Clearing**: The workflow requires manual intervention - user must clear the target Notion page before running
- **Unused Import**: `notion_client` is imported but not used - the code uses direct REST API calls instead
- **Regex Complexity**: The equation parsing handles both block (`$$`) and inline (`$`) math with multi-line support
- **API Version Lock**: Notion API version is hard-coded - changing it may break block structure compatibility

## Modification Guidelines

- When adding new block types, extend `blocks_to_dataframe()` and `combine_text_and_equations()`
- For equation format changes, modify the regex patterns in `format_content_for_notion()`
- Batch size can be adjusted in `upload_blocks_in_batches()` if rate limiting occurs
- Always preserve the try/except pattern for API calls with proper logging
