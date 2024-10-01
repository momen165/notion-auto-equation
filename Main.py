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

def get_notion_page_content(page_id):
    url = f"https://api.notion.com/v1/blocks/{page_id}/children"
    response = requests.get(url, headers=HEADERS)
    return response.json()

page_content = get_notion_page_content(PAGE_ID)

##step 2 block to data frame
def blocks_to_dataframe(blocks):
    data = []
    for block in blocks['results']:
        block_type = block['type']
        content = ''
        
        # 處理有 rich_text 的區塊
        if 'rich_text' in block.get(block_type, {}):
            for item in block[block_type]['rich_text']:
                if item['type'] == 'text':
                    content += item['text']['content']
                elif item['type'] == 'equation':
                    content += f"$$ {item['equation']['expression']} $$"
        
        data.append({'id': block['id'], 'type': block_type, 'content': content})
    
    return pd.DataFrame(data)

df = blocks_to_dataframe(page_content)

##step 3 get the eqation
def format_content_for_notion(block):
    # 檢查 block 是否是一個字典類型
    if isinstance(block, dict):
        # 只處理 paragraph 和 heading_3 兩種類型
        if block["type"] == "paragraph" or block["type"] == "heading_3":
            parts = block[block["type"]]["rich_text"][0]["text"]["content"].split("$$")
            formatted_parts = []

            for i, part in enumerate(parts):
                part = part.strip()
                if i % 2 == 1:  # 偶數部分是公式
                    formatted_parts.append({
                        "type": "equation",
                        "equation": {"expression": part}
                    })
                else:
                    if part:  # 將文字前後加上空白
                        formatted_parts.append({
                            "type": "text",
                            "text": {"content": f" {part} "}  # 在文字前後加空白
                        })

            # 返回與原始 block 同類型的格式
            return {
                "type": block["type"],
                block["type"]: {"rich_text": formatted_parts}
            }

        # 如果是 divider 等非文本類型，保持原狀
        return block
    
    elif isinstance(block, str):  # 如果 block 是字串，則處理文字中的公式
        parts = block.split("$$")
        formatted_parts = []

        for i, part in enumerate(parts):
            part = part.strip()
            if i % 2 == 1:  # 偶數部分是公式
                formatted_parts.append({
                    "type": "equation",
                    "equation": {"expression": part}
                })
            else:
                if part:  # 將文字前後加上空白
                    formatted_parts.append({
                        "type": "text",
                        "text": {"content": f" {part} "}  # 在文字前後加空白
                    })

        # 返回格式化後的內容
        return formatted_parts
    
    else:
        raise TypeError(f"Unsupported block type: {type(block)}")


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
        elif row['type'] == "heading_3":
            combined_blocks.append({
                'type': 'heading_3',
                'heading_3': {
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
