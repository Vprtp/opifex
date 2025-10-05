import os
from pathlib import Path
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from PIL import Image

def format_html_template(template_path, output_path, data):
    """
    Format HTML template with provided data.
    
    Args:
        template_path (str): Path to HTML template file
        output_path (str): Path to save formatted HTML
        data (dict): Dictionary of values to substitute in template
    
    Returns:
        str: Path to the formatted HTML file
    """
    with open(template_path, 'r') as f:
        template = f.read()
    
    formatted_html = template.format(**data)
    
    with open(output_path, 'w') as f:
        f.write(formatted_html)
    
    return output_path

def take_screenshot(html_path, output_png_path, window_size=(800, 600), transparent_bg=True):
    """
    Take screenshot of HTML file and save as PNG with transparent background.
    
    Args:
        html_path (str): Path to HTML file to screenshot
        output_png_path (str): Path to save PNG screenshot
        window_size (tuple): (width, height) of browser window
        transparent_bg (bool): Whether to make background transparent
    
    Returns:
        str: Path to the screenshot PNG file
    """
    # Set up Chrome options
    chrome_options = Options()
    chrome_options.add_argument("--hide-scrollbars")  # Hide scrollbars
    chrome_options.add_argument("--force-device-scale-factor=1")  # Prevent scaling issues
    chrome_options.add_argument("--headless")
    chrome_options.add_argument(f"--window-size={window_size[0]},{window_size[1]}")
    
    if transparent_bg:
        chrome_options.add_argument("--disable-gpu")
    
    # Initialize WebDriver
    driver = webdriver.Chrome(options=chrome_options)
    
    try:
        # Open the HTML file
        driver.get(f"file://{os.path.abspath(html_path)}")
        
        # Take screenshot
        driver.save_screenshot(output_png_path)
        
        # If transparent background requested, process the image
        if transparent_bg:
            make_background_transparent(output_png_path, output_png_path)
            
    finally:
        driver.quit()
    
    return output_png_path

def make_background_transparent(input_path, output_path):
    """
    Make green background transparent in an image.
    
    Args:
        input_path (str): Path to input image
        output_path (str): Path to save output image
    
    Returns:
        str: Path to the processed image file
    """
    img = Image.open(input_path)
    img = img.convert("RGBA")
    
    datas = img.getdata()
    new_data = []
    
    # Make green (and near-green) pixels transparent
    for item in datas:
        # Change all green (also shades of green) pixels to transparent
        if item[0] < 20 and item[1] > 230 and item[2] < 20:
            new_data.append((255, 255, 255, 0))
        else:
            new_data.append(item)
    
    img.putdata(new_data)
    img.save(output_path, "PNG")
    return output_path

def process_html_to_image(html_template_path, data=None, window_size=(1080, 1080)):
    """
    Process HTML template to transparent PNG image.
    
    Args:
        html_template_path (str): Path to HTML template file
        data (dict): Dictionary of values to substitute in template (default: {})
        window_size (tuple): (width, height) of browser window (default: (800, 800))
    
    Returns:
        str: Path to the generated PNG file in temp folder
    
    Raises:
        ValueError: If temp directory cannot be created
    """
    # Create temp directory if it doesn't exist
    temp_dir = Path("temp")
    try:
        temp_dir.mkdir(exist_ok=True)
    except Exception as e:
        raise ValueError(f"Could not create temp directory: {e}")
    
    # Set default data if none provided
    if data is None:
        data = {}
    
    # Generate unique filenames
    original_path = Path(html_template_path)
    html_output_path = original_path.parent / "temp_formatted.html"
    png_output_path = temp_dir / "screenshot.png"
    
    try:
        # Format the HTML template
        format_html_template(html_template_path, str(html_output_path), data)
        
        # Take screenshot
        take_screenshot(
            str(html_output_path),
            str(png_output_path),
            window_size=window_size,
            transparent_bg=True
        )
        
        return str(png_output_path)
    
    finally:
        # Clean up temporary HTML file
        if html_output_path.exists() and html_output_path != original_path:
            html_output_path.unlink()
