# Notion Auto Equation

A Python utility that automatically converts LaTeX-style mathematical expressions (`$$equation$$` and `$equation$`) in Notion pages into proper Notion equation blocks.

## 🎯 What it does

Transform this:

```text
Some text with $$x = \frac{-b \pm \sqrt{b^2-4ac}}{2a}$$ inline equations and $E=mc^2$ in your Notion pages.
```

Into properly formatted Notion equation blocks that render beautifully with syntax highlighting and LaTeX support.

### Before & After

**Before:** Raw LaTeX syntax mixed with text
![Before](https://github.com/user-attachments/assets/4a4321b3-0dac-470c-9ad6-037e0d3cf0a4)

**After:** Clean, properly formatted Notion equations
![After](https://cdn.discordapp.com/attachments/1177207022152855574/1290625431636148254/2024-10-01_18.44.25.png?ex=66fd2419&is=66fbd299&hm=ab9d884fe4e805c176e1f9a8a405804d1ca6d2153de5f65b517dd03c90532d4f&)

## 🚀 Features

- **Dual Format Support**: Handles both block equations (`$$...$$`) and inline equations (`$...$`)
- **Multi-line Equations**: Supports complex equations spanning multiple lines
- **Batch Processing**: Efficiently processes large pages with rate limiting
- **Block Type Preservation**: Maintains original formatting for paragraphs, headings, quotes, code blocks, and lists
- **Error Handling**: Robust error handling with detailed logging
- **Recursive Processing**: Handles nested blocks and child content

## 📋 Requirements

- Python 3.6+
- Notion API integration token
- Target Notion page ID

### Dependencies

```bash
pip install requests pandas notion-client
```

## ⚙️ Setup

1. **Get your Notion API key:**

   - Go to [Notion Developers](https://www.notion.so/profile/integrations)
   - Create a new integration
   - Copy the API key

2. **Get your page ID:**

   - Open your Notion page in a browser
   - Copy the page ID from the URL (the string after the last `/`)

3. **Configure the script:**

   ```python
   NOTION_API_KEY = "your_notion_api_key_here"  # Replace with your actual API key
   PAGE_ID = "your_page_id_here"  # Replace with your actual page ID
   ```

4. **Grant permissions:**
   - In Notion, share your target page with your integration
   - Give it "Edit" permissions

## 🔧 Usage

1. **Prepare your Notion page:**

   - Add mathematical expressions using `$$...$$` for block equations
   - Use `$...$` for inline equations
   - Example: `The quadratic formula is $$x = \frac{-b \pm \sqrt{b^2-4ac}}{2a}$$`

2. **Run the script:**

   ```bash
   python Main.py
   ```

3. **Follow the prompt:**
   - The script will ask you to manually clear the page content
   - Clear your Notion page and press Enter
   - The script will process and re-upload with proper equation formatting

## 🏗️ How it works

The tool follows a 4-step pipeline:

1. **Fetch** (`get_all_blocks`): Recursively retrieves all blocks from the Notion page
2. **Parse** (`blocks_to_dataframe`): Converts blocks into a pandas DataFrame for processing
3. **Transform** (`format_content_for_notion`): Uses regex to identify and convert LaTeX notation
4. **Upload** (`upload_blocks_in_batches`): Sends processed blocks back to Notion in batches

### Supported Block Types

- Paragraphs
- Headings (H1, H2, H3)
- Quotes
- Code blocks
- Bulleted lists
- Dividers

## ⚠️ Important Notes

- **Manual Step Required**: You must manually clear the target page content before running the script
- **Backup Recommended**: Always backup your Notion page before running the conversion
- **API Rate Limits**: The script uses batching (10 blocks per request) to respect Notion's rate limits
- **One-Way Process**: This converts LaTeX to Notion equations, not the reverse

## 🛠️ Development

### Project Structure

```text
notion-auto-equation/
├── Main.py              # Main script with 4-step pipeline
├── README.md           # This file
├── LICENSE             # GPL v3 license
└── .github/
    └── copilot-instructions.md  # AI coding guidelines
```

### Key Functions

- `get_all_blocks()`: Recursive block fetching with pagination
- `blocks_to_dataframe()`: Block structure parsing
- `format_content_for_notion()`: LaTeX regex processing
- `combine_text_and_equations()`: Block type handling and reconstruction
- `upload_blocks_in_batches()`: Batch upload with error handling

## 📝 License

This project is licensed under the GNU General Public License v3.0 - see the [LICENSE](LICENSE) file for details.

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request. For major changes, please open an issue first to discuss what you would like to change.

## 🐛 Troubleshooting

**Common Issues:**

- **"Failed to fetch blocks"**: Check your API key and page ID
- **"Unauthorized"**: Ensure your integration has access to the target page
- **"Rate limited"**: The script already handles this with batching, but you can increase the delay if needed

For more detailed error information, check the console logs which include timestamps and specific error messages.
