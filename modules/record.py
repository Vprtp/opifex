import os
import time
import subprocess
import platform
from pathlib import Path
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from basemodule import BaseModule, ModuleResultType
import random
import base64

from screenshot import format_html_template

import config

tempFiles: list[str] = []
tempFolder: str = config.tempFolder

def clearTemp(files: list[str] = tempFiles) -> None:
    """Clean up temporary files created during execution."""
    for file in files:
        try:
            os.remove(file)
            print(f"Cleaned up temporary file: {file}")
        except:
            print(f"WARNING: unable to delete temporary file {file}")

def make_size_even(window_size:tuple[int,int]):
    w, h = window_size
    if w % 2 != 0:
        w += 1
    if h % 2 != 0:
        h += 1
    return (w, h)
            
def find_ffmpeg():
    """
    Find ffmpeg executable path.
    
    Returns:
        str: Path to ffmpeg executable or None if not found
    """
    possible_paths = ['ffmpeg', 'ffmpeg.exe']
    
    if platform.system() == "Windows":
        program_files = os.environ.get("ProgramFiles", "C:\\Program Files")
        possible_paths.extend([
            os.path.join(program_files, "ffmpeg", "bin", "ffmpeg.exe"),
            os.path.join(program_files + " (x86)", "ffmpeg", "bin", "ffmpeg.exe"),
        ])
    
    for path in possible_paths:
        try:
            subprocess.run([path, '-version'], capture_output=True, check=True)
            return path
        except:
            continue
    
    return None

def record_video_ffmpeg_pipe(
    driver,
    output_video_path,
    duration,
    fps,
    window_size
):
    width, height = window_size
    total_frames = int(duration * fps)

    ffmpeg_path = find_ffmpeg()
    if not ffmpeg_path:
        raise Exception("ffmpeg not found")

    ffmpeg = subprocess.Popen(
        [
            ffmpeg_path,
            "-y",
            "-f", "image2pipe",
            "-vcodec", "png",
            "-r", str(fps),
            "-i", "-",
            "-c:v", "libx264",
            "-preset", "veryfast",
            "-crf", "18",
            "-pix_fmt", "yuv420p",
            "-movflags", "+faststart",
            output_video_path
       ],
        stdin=subprocess.PIPE,
        stderr=subprocess.PIPE
    )

    for i in range(total_frames):
        screenshot = driver.execute_cdp_cmd(
            "Page.captureScreenshot",
            {"format": "png", "fromSurface": True}
        )
        img = base64.b64decode(screenshot["data"])
	
        # If ffmpeg already died, grab its stderr and raise a meaningful error
        if ffmpeg.poll() is not None:
            stderr = ffmpeg.stderr.read().decode(errors="replace")
            raise RuntimeError(f"ffmpeg exited before frame {i}. returncode={ffmpeg.returncode}\nffmpeg stderr:\n{stderr}")

        try:
            ffmpeg.stdin.write(img)
        except BrokenPipeError:
            # ffmpeg closed the pipe while we tried to write — read stderr and raise a helpful exception
            stderr = ffmpeg.stderr.read().decode(errors="replace")
            raise RuntimeError(f"BrokenPipeError while writing frame {i} — ffmpeg likely exited. "
                                f"returncode={ffmpeg.returncode}\nffmpeg stderr:\n{stderr}")

    ffmpeg.stdin.close()
    ffmpeg.wait()

def record_video(html_path, output_video_path, duration=5, window_size=(800, 600), 
                 fps=30, transparent_bg=True, headless=True):
    """
    Record video of HTML page for a specified duration.
    
    Args:
        html_path (str): Path to HTML file to record
        output_video_path (str): Path to save video (MP4 format)
        duration (int): Duration of recording in seconds
        window_size (tuple): (width, height) of browser window
        fps (int): Frames per second for video
        transparent_bg (bool): Whether to make green background transparent
        headless (bool): Whether to run browser in headless mode
    
    Returns:
        str: Path to the recorded video file
    """
    # Ensure tempFolder exists
    os.makedirs(tempFolder, exist_ok=True)
    
    window_size = make_size_even(window_size)

    # Set up Chrome options
    chrome_options = Options()
    chrome_options.add_argument("--hide-scrollbars")
    chrome_options.add_argument("--force-device-scale-factor=1")
    chrome_options.add_argument("--disable-infobars")
    chrome_options.add_argument("--disable-notifications")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument(f"--window-size={window_size[0]},{window_size[1]}")
    
    if transparent_bg:
        chrome_options.add_argument("--disable-gpu")
    
    if headless:
        chrome_options.add_argument("--headless")
    
    # Initialize WebDriver
    driver = webdriver.Chrome(options=chrome_options)
    
    try:
        # Open the HTML file
        driver.get(f"file://{os.path.abspath(html_path)}")
        time.sleep(1)  # Give time for page to load, TODO: if you want to overengineer in the future, make it wait for the exact time

        #force window size
        driver.execute_cdp_cmd(
            "Emulation.setDeviceMetricsOverride",
            {
                "width": window_size[0],
                "height": window_size[1],
                "deviceScaleFactor": 1,
                "mobile": False
            }
        )

        record_video_ffmpeg_pipe(
            driver,
            output_video_path,
            duration,
            fps,
            window_size
        )
       
    finally:
        driver.quit()
    
    return output_video_path

def process_html_to_video(html_template_path, data=None, window_size=(1080, 1080), 
                          duration=5, fps=30):
    """
    Process HTML template to video recording.
    
    Args:
        html_template_path (str): Path to HTML template file
        data (dict): Dictionary of values to substitute in template (default: {})
        window_size (tuple): (width, height) of browser window
        duration (int): Duration of recording in seconds
        fps (int): Frames per second
    
    Returns:
        str: Path to the generated video file in temp folder
    """
    # Set default data if none provided
    if data is None:
        data = {}

    original_path = Path(html_template_path)
    html_output_path = original_path.parent / "temp_formatted.html"
  
    video_output_filename = f"recording_{random.randint(10000,99999)}.mp4"
    video_output_path = os.path.join(tempFolder, video_output_filename)
    
    try:
        # Format the HTML template
        format_html_template(html_template_path, html_output_path, data)
        tempFiles.append(html_output_path)  # Track for cleanup
        
        # Record video
        record_video(
            html_output_path,
            video_output_path,
            duration=duration,
            window_size=window_size,
            fps=fps,
            transparent_bg=True,
            headless=True
        )
        
        # Clean up intermediate files (frames, HTML, ffmpeg input list)
        clearTemp()
        
        return video_output_path
    
    except Exception as e:
        # Clean up on error
        clearTemp()
        raise e

class RecordPage(BaseModule):
    """
    Module that records a video of an HTML template with given parameter values.
    """
    def __init__(self):
        self.name = "RecordPage"
        self.description = "Module that records a video of an HTML template with given parameter values. Note that the template's animations in the video might look off, depending on the host machine's performance.\nParameters:\n- template: Path to the HTML template\n- data: Dictionary with parameters that should be filled in the template {'Parameter name':Value}\n- size: Tuple (width, height), in pixel, that indicate the web window size\n- duration: Duration of the recording in seconds\n- fps: Frames per second"
        self.requiredArgs = [
            ("template", str),
            ("data", dict), 
            ("size", tuple[int, int]),
            ("duration", float),
            ("fps", int)
        ]
        self.returnedDataTypes = [("destination", str)]
        self.dependencies = ["ScreenshotPage"]


    def execute(self, version: str, **kwargs):
        """
        Execute the video recording.
        
        Args:
            version: Module version
            **kwargs: Keyword arguments including template, data, size, duration, fps
        
        Returns:
            ModuleResultType with destination path or error
        """
        try:
            duration = kwargs.get("duration")
            fps = kwargs.get("fps")
            
            output_path = process_html_to_video(
                kwargs["template"], 
                kwargs["data"], 
                kwargs["size"], 
                duration, 
                fps
            )
            
            return ModuleResultType(None, {"destination":output_path}) 
        except Exception as e:
            # Clean up any remaining temp files on error
            clearTemp()
            return ModuleResultType(e, {}) 
