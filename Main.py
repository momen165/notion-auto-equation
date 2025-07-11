##step 1 get data
import requests
import pandas as pd
from notion_client import Client
import logging
import re

NOTION_API_KEY = "your_notion_api_key_here"  # Replace with your Notion API key
PAGE_ID = "your_page_id_here"  # Replace with your Notion page ID
HEADERS = {
    "Authorization": f"Bearer {NOTION_API_KEY}",
    "Notion-Version": "2022-06-28",
    "Content-Type": "application/json"
}

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# Used to recursively get all blocks and their child blocks
def get_all_blocks(block_id):
    url = f"https://api.notion.com/v1/blocks/{block_id}/children?page_size=100"
    blocks = []
    has_more = True
    start_cursor = None

    while has_more:
        try:
            if start_cursor:
                response = requests.get(url, headers=HEADERS, params={"start_cursor": start_cursor})
            else:
                response = requests.get(url, headers=HEADERS)
            response.raise_for_status()
            data = response.json()
        except requests.exceptions.RequestException as e:
            logging.error(f"Failed to fetch blocks: {e}")
            break
        except Exception as e:
            logging.error(f"Unexpected error while fetching blocks: {e}")
            break

        results = data.get('results', [])
        for block in results:
            blocks.append(block)
            # If the block has children, recursively get them
            if block.get('has_children', False):
                child_blocks = get_all_blocks(block['id'])
                blocks.extend(child_blocks)

        has_more = data.get('has_more', False)
        start_cursor = data.get('next_cursor')

    logging.info(f"Fetched {len(blocks)} blocks from Notion.")
    return blocks

def get_notion_page_content(page_id):
    logging.info(f"Getting content for Notion page: {page_id}")
    blocks = get_all_blocks(page_id)
    if not blocks:
        logging.warning("No blocks found for the given page.")
    return blocks

try:
    page_content = get_notion_page_content(PAGE_ID)
except Exception as e:
    logging.error(f"Error getting Notion page content: {e}")
    page_content = []

## Step 2: Convert blocks to DataFrame
def blocks_to_dataframe(blocks):
    data = []
    for block in blocks:
        block_type = block['type']
        content = ''
        
        # Handle block types with rich_text
        if 'rich_text' in block.get(block_type, {}):
            for item in block[block_type]['rich_text']:
                if item['type'] == 'text':
                    content += item['text']['content']
                elif item['type'] == 'equation':
                    content += f"$$ {item['equation']['expression']} $$"
        # Handle other types of blocks, such as code blocks
        elif block_type == 'code':
            content += block['code']['text'][0]['text']['content']
        # Handle quote blocks
        elif block_type == 'quote':
            for item in block['quote']['rich_text']:
                if item['type'] == 'text':
                    content += item['text']['content']
                elif item['type'] == 'equation':
                    content += f"$$ {item['equation']['expression']} $$"
        # Handle equation blocks (block type 'equation')
        elif block_type == 'equation':
            # Equation blocks have a single expression
            content += f"$$ {block['equation']['expression']} $$"
        # Other possible block types can be added here

        data.append({'id': block['id'], 'type': block_type, 'content': content})
    
    logging.info(f"Converted {len(data)} blocks to DataFrame.")
    return pd.DataFrame(data)

try:
    df = blocks_to_dataframe(page_content)
except Exception as e:
    logging.error(f"Error converting blocks to DataFrame: {e}")
    df = pd.DataFrame([])

## Step 3: Process content, extract formulas and format
def format_content_for_notion(block):
    # Improved: Use regex to find all $$equation$$ and convert to equation blocks
    if isinstance(block, str):
        # Find all $$...$$ and split text accordingly
        # Support multi-line equations by using DOTALL
        pattern = re.compile(r'\$\$(.+?)\$\$', re.DOTALL)
        parts = []
        last_end = 0
        for m in pattern.finditer(block):
            # Add text before equation
            if m.start() > last_end:
                text_part = block[last_end:m.start()]
                if text_part:
                    parts.append({
                        "type": "text",
                        "text": {"content": text_part}
                    })
            # Add equation
            eq = m.group(1).strip()
            if eq:
                parts.append({
                    "type": "equation",
                    "equation": {"expression": eq}
                })
            last_end = m.end()
        # Add any remaining text
        if last_end < len(block):
            text_part = block[last_end:]
            if text_part:
                parts.append({
                    "type": "text",
                    "text": {"content": text_part}
                })
        # After extracting $$...$$ equations, handle inline $...$ equations within text parts
        final_parts = []
        inline_pattern = re.compile(r'\$(.+?)\$')
        for part in parts:
            if part.get('type') == 'text':
                text = part['text']['content']
                last = 0
                for m in inline_pattern.finditer(text):
                    if m.start() > last:
                        txt = text[last:m.start()]
                        if txt:
                            final_parts.append({'type': 'text', 'text': {'content': txt}})
                    expr = m.group(1).strip()
                    if expr:
                        final_parts.append({'type': 'equation', 'equation': {'expression': expr}})
                    last = m.end()
                # remaining text
                if last < len(text):
                    rem = text[last:]
                    if rem:
                        final_parts.append({'type': 'text', 'text': {'content': rem}})
            else:
                # equation blocks pass through
                final_parts.append(part)
        return final_parts
    else:
        # If the block is a dictionary, return directly
        return block

def combine_text_and_equations(df):
    combined_blocks = []

    for _, row in df.iterrows():
        content = row['content']
        notion_block_content = format_content_for_notion(content)

        # Handle divider type (no content needed)
        if row['type'] == "divider":
            combined_blocks.append({
                'type': 'divider',
                'divider': {}
            })
        
        # Handle heading types (heading_1, heading_2, heading_3)
        elif row['type'] == "heading_3" or row['type'] == "heading_2" or row['type'] == "heading_1":
            combined_blocks.append({
                'type': row['type'],
                row['type']: {
                    'rich_text': notion_block_content
                }
            })
        
        # Handle quote type
        elif row['type'] == "quote":
            combined_blocks.append({
                'type': 'quote',
                'quote': {
                    'rich_text': notion_block_content
                }
            })
        
        # Handle general paragraph type, ensure it's not empty and has correct structure
        elif row['type'] == "paragraph":
            if notion_block_content:  # Check that rich_text is not empty
                combined_blocks.append({
                    'type': 'paragraph',
                    'paragraph': {
                        'rich_text': notion_block_content
                    }
                })
        # Handle other block types (e.g., code)
        elif row['type'] == "code":
            combined_blocks.append({
                'type': 'code',
                'code': {
                    'text': notion_block_content,
                    'language': 'python'  # Set language according to actual situation
                }
            })
        # Other block types can be added here
        elif row['type'] == "bulleted_list_item":
            combined_blocks.append({
                'type': 'bulleted_list_item',
                'bulleted_list_item': {
                    'rich_text': notion_block_content
                }
            })

    return combined_blocks

try:
    combined_data = combine_text_and_equations(df)
    logging.info(f"Combined data contains {len(combined_data)} blocks.")
except Exception as e:
    logging.error(f"Error combining text and equations: {e}")
    combined_data = []

##step 4 upload to notion
def upload_to_notion(page_id, combined_blocks):
    url = f"https://api.notion.com/v1/blocks/{page_id}/children"
    children_blocks = combined_blocks
    payload = {
        "children": children_blocks
    }
    try:
        response = requests.patch(url, json=payload, headers=HEADERS)
        response.raise_for_status()
        logging.info(f"Successfully uploaded {len(children_blocks)} blocks to Notion page {page_id}.")
        return response.json()
    except requests.exceptions.RequestException as e:
        logging.error(f"Failed to upload blocks to Notion: {e}")
        return None
    except Exception as e:
        logging.error(f"Unexpected error during upload: {e}")
        return None
    
# Batch upload in chunks to avoid rate limits
def upload_blocks_in_batches(page_id, combined_blocks, batch_size=10):
    total = len(combined_blocks)
    for i in range(0, total, batch_size):
        batch = combined_blocks[i:i+batch_size]
        logging.info(f"Uploading blocks {i+1} to {i+len(batch)} of {total}")
        upload_to_notion(page_id, batch)





def main():
    # Prompt user to manually clear page content in Notion
    input("Please manually clear all content on the Notion page, then press Enter to continue... ")
    # Proceed to upload processed blocks in batches
    if combined_data:
        upload_blocks_in_batches(PAGE_ID, combined_data, batch_size=10)
    else:
        logging.warning("No data to upload to Notion.")

if __name__ == "__main__":
    main()
