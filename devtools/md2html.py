import sys
import os
import requests

TITLE = "Opifex - Manual"

STYLE = """
body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; line-height: 1.6; max-width: 800px; margin: 0 auto; padding: 20px; }
h1, h2, h3, h4, h5, h6 { margin-top: 24px; margin-bottom: 16px; font-weight: 600; line-height: 1.25; }
h1 { font-size: 2em; border-bottom: 1px solid #eee; padding-bottom: 0.3em; }
h2 { font-size: 1.5em; border-bottom: 1px solid #eee; padding-bottom: 0.3em; }
code { background: #f6f8fa; padding: 2px 4px; border-radius: 3px; font-size: 110%;}
pre { background: #f6f8fa; padding: 16px; border-radius: 6px; overflow: auto; }
pre code { background: none; padding: 0; }
blockquote { margin: 0; padding-left: 16px; border-left: 4px solid #ddd; color: #666; }
table { border-collapse: collapse; width: 100%; }
th, td { border: 1px solid #ddd; padding: 8px 12px; text-align: left; }
th { background: #f6f8fa; font-weight: 600; }
"""

def markdown_to_github_html(markdown_text, css_content):
    """
    Convert markdown to GitHub-styled HTML using GitHub's API
    
    Args:
        markdown_text (str): Raw markdown content
        css_content (str): CSS styles for styling the content
    
    Returns:
        str: Complete HTML document with GitHub-styled markdown
    """
    # Convert markdown to HTML using GitHub API
    url = "https://api.github.com/markdown/raw"
    headers = {
        "Content-Type": "text/plain",
        "Accept": "application/vnd.github.v3+json",
        "User-Agent": "Markdown-Converter/1.0"
    }
    
    try:
        response = requests.post(url, data=markdown_text.encode('utf-8'), headers=headers)
        response.raise_for_status()
        html_content = response.text
    except requests.exceptions.RequestException as e:
        raise Exception(f"GitHub API request failed: {e}")
    
    # Build complete HTML document
    full_html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{TITLE}</title>
    <style>
        body {{
            box-sizing: border-box;
            min-width: 200px;
            max-width: 980px;
            margin: 0 auto;
            padding: 45px;
        }}
        {css_content}
    </style>
</head>
<body class="markdown-body">
    {html_content}
</body>
</html>"""
    
    return full_html

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python3 md2html.py input.md")
        sys.exit(1)

    input_file = sys.argv[1]
    output_file = os.path.splitext(input_file)[0] + '.html'
    markdown = ""

    with open(input_file, 'r') as f:
        markdown = f.read()
    
    with open(output_file, 'w') as f:
        f.write(markdown_to_github_html(markdown,STYLE))