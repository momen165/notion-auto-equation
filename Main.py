##step 1 get data
import requests
import pandas as pd
from notion_client import Client

NOTION_API_KEY = "your api key"
PAGE_ID = "your page id"
HEADERS = {
    "Authorization": f"Bearer {NOTION_API_KEY}",
    "Notion-Version": "2022-06-28",
    "Content-Type": "application/json"
}

# 用於遞歸獲取所有區塊及其子區塊
def get_all_blocks(block_id):
    url = f"https://api.notion.com/v1/blocks/{block_id}/children?page_size=100"
    blocks = []
    has_more = True
    start_cursor = None

    while has_more:
        if start_cursor:
            response = requests.get(url, headers=HEADERS, params={"start_cursor": start_cursor})
        else:
            response = requests.get(url, headers=HEADERS)

        data = response.json()
        results = data.get('results', [])
        for block in results:
            blocks.append(block)
            # 如果區塊有子區塊，遞歸獲取
            if block.get('has_children', False):
                child_blocks = get_all_blocks(block['id'])
                blocks.extend(child_blocks)

        has_more = data.get('has_more', False)
        start_cursor = data.get('next_cursor')

    return blocks

def get_notion_page_content(page_id):
    blocks = get_all_blocks(page_id)
    return blocks

page_content = get_notion_page_content(PAGE_ID)

## Step 2: 將區塊轉換為 DataFrame
def blocks_to_dataframe(blocks):
    data = []
    for block in blocks:
        block_type = block['type']
        content = ''
        
        # 處理有 rich_text 的區塊類型
        if 'rich_text' in block.get(block_type, {}):
            for item in block[block_type]['rich_text']:
                if item['type'] == 'text':
                    content += item['text']['content']
                elif item['type'] == 'equation':
                    content += f"$$ {item['equation']['expression']} $$"
        # 處理其他類型的區塊，例如 code 區塊
        elif block_type == 'code':
            content += block['code']['text'][0]['text']['content']
        # 處理引言（quote）區塊
        elif block_type == 'quote':
            for item in block['quote']['rich_text']:
                if item['type'] == 'text':
                    content += item['text']['content']
                elif item['type'] == 'equation':
                    content += f"$$ {item['equation']['expression']} $$"
        # 其他可能的區塊類型可以在這裡添加

        data.append({'id': block['id'], 'type': block_type, 'content': content})
    
    return pd.DataFrame(data)

df = blocks_to_dataframe(page_content)

## Step 3: 處理內容，提取公式並格式化
def format_content_for_notion(block):
    # 如果 block 是字串，處理其中的公式
    if isinstance(block, str):
        parts = block.split("$$")
        formatted_parts = []

        for i, part in enumerate(parts):
            part = part.strip()
            if i % 2 == 1:  # 奇數索引部分是公式
                formatted_parts.append({
                    "type": "equation",
                    "equation": {"expression": part}
                })
            else:
                if part:
                    formatted_parts.append({
                        "type": "text",
                        "text": {"content": f" {part} "}
                    })
        return formatted_parts
    else:
        # 如果 block 是字典，直接返回
        return block

def combine_text_and_equations(df):
    combined_blocks = []

    for _, row in df.iterrows():
        content = row['content']
        notion_block_content = format_content_for_notion(content)

        # 處理 divider 類型（不需要附帶任何內容）
        if row['type'] == "divider":
            combined_blocks.append({
                'type': 'divider',
                'divider': {}
            })
        
        # 處理 heading_3 類型，使用 heading_3 來替換 paragraph
        elif row['type'] == "heading_3" or row['type'] == "heading_2" or row['type'] == "heading_1":
            combined_blocks.append({
                'type': row['type'],
                row['type']: {
                    'rich_text': notion_block_content
                }
            })
        
        # 處理 quote 類型
        elif row['type'] == "quote":
            combined_blocks.append({
                'type': 'quote',
                'quote': {
                    'rich_text': notion_block_content
                }
            })
        
        # 處理一般段落類型，保證不為空且有正確結構
        elif row['type'] == "paragraph":
            if notion_block_content:  # 檢查 rich_text 不為空
                combined_blocks.append({
                    'type': 'paragraph',
                    'paragraph': {
                        'rich_text': notion_block_content
                    }
                })
        # 處理其他類型的區塊（例如 code）
        elif row['type'] == "code":
            combined_blocks.append({
                'type': 'code',
                'code': {
                    'text': notion_block_content,
                    'language': 'python'  # 根據實際情況設置語言
                }
            })
        # 其他區塊類型可以在這裡添加
        elif row['type'] == "bulleted_list_item":
            combined_blocks.append({
                'type': 'bulleted_list_item',
                'bulleted_list_item': {
                    'rich_text': notion_block_content
                }
            })

    return combined_blocks

combined_data = combine_text_and_equations(df)

##step 4 upload to notion
def upload_to_notion(page_id, combined_blocks):
    url = f"https://api.notion.com/v1/blocks/{page_id}/children"
    children_blocks = combined_blocks
    payload = {
        "children": children_blocks
    }
    response = requests.patch(url, json=payload, headers=HEADERS)
    return response.json()

upload_to_notion(PAGE_ID, combined_data)
