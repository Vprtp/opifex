import os
import time
import subprocess
from pathlib import Path
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from basemodule import BaseModule, ModuleResultType
import random

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
        except Exception as e:
            print(f"WARNING: unable to delete temporary file {file}: {str(e)}")

def make_size_even(window_size:tuple[int,int]):
    w, h = window_size
    if w % 2 != 0:
        w += 1
    if h % 2 != 0:
        h += 1
    return (w, h)
            
def find_ffmpeg() -> str: #this is necessary because the conda build of ffmpeg doesn't include x11grab
    # First look for system ffmpeg that supports x11grab
    system_paths = ['/usr/bin/ffmpeg', '/usr/local/bin/ffmpeg']
    for path in system_paths:
        if os.path.exists(path):
            try:
                # Quick check for x11grab support
                result = subprocess.run([path, '-demuxers'], capture_output=True, text=True)
                if 'x11grab' in result.stdout:
                    return path
            except:
                continue
    # Fallback to any ffmpeg in PATH (but may fail)
    return 'ffmpeg'

def start_virtual_display(width, height):
    display_num = ":99"
    # Capture stderr so we can see why Xvfb might crash
    xvfb = subprocess.Popen(
        ["Xvfb", display_num, "-screen", "0", f"{width}x{height}x24", "-ac"],
        stderr=subprocess.PIPE,
        stdout=subprocess.DEVNULL
    )
    time.sleep(0.5)
    
    # Check if Xvfb died immediately
    if xvfb.poll() is not None:
        _, stderr = xvfb.communicate()
        raise RuntimeError(f"Xvfb failed to start: {stderr.decode()}")
    
    return xvfb, display_num

def wait_for_display(display, timeout=5):
    """Wait until the X display accepts connections."""
    start = time.time()
    while time.time() - start < timeout:
        try:
            subprocess.run(
                ["xdpyinfo", "-display", display],
                check=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            return True
        except subprocess.CalledProcessError:
            time.sleep(0.2)
    return False

def record_video(
    html_path,
    output_video_path,
    duration=5.0,
    window_size=(800, 600),
    fps=30
):
    width, height = make_size_even(window_size)

    # Start virtual display
    xvfb, display = start_virtual_display(width, height)
    os.environ["DISPLAY"] = display
    #wayland fixes
    saved_env = {}
    if "WAYLAND_DISPLAY" in os.environ:
        saved_env["WAYLAND_DISPLAY"] = os.environ.pop("WAYLAND_DISPLAY")
    if "XDG_SESSION_TYPE" in os.environ:
        saved_env["XDG_SESSION_TYPE"] = os.environ.pop("XDG_SESSION_TYPE")

    if not wait_for_display(display):
        raise RuntimeError(f"Display {display} not ready after timeout")

    # Start Chrome (NOT headless!)
    chrome_options = Options()
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument(f"--window-size={width},{height}")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument(f"--app=file://{os.path.abspath(html_path)}")
    chrome_options.add_argument("--disable-infobars")
    chrome_options.add_argument("--disable-session-crashed-bubble")
    chrome_options.add_argument("--no-first-run")
    chrome_options.add_argument("--disable-default-apps")
    chrome_options.add_argument("--disable-notifications")
    chrome_options.add_argument("--hide-scrollbars")
    chrome_options.add_argument("--window-position=0,0")
    chrome_options.add_argument("--ozone-platform=x11")

    driver = webdriver.Chrome(options=chrome_options)

    try:
        time.sleep(1)

        if xvfb.poll() is not None:
            _, stderr = xvfb.communicate()
            raise RuntimeError(f"Xvfb died before FFmpeg started: {stderr.decode()}")

        # Start ffmpeg capture from Xvfb
        ffmpeg_cmd = [
            find_ffmpeg(),
            "-v", "info",
            "-y",
            "-video_size", f"{width}x{height}",
            "-framerate", str(fps),
            "-f", "x11grab",
            "-draw_mouse", "0",
            "-i", f"{display}.0",
            "-t", str(duration),
            "-c:v", "libx264",
            "-preset", "veryfast",
            "-crf", "18",
            "-pix_fmt", "yuv420p",
            output_video_path
        ]

        result = subprocess.run(ffmpeg_cmd, env=os.environ.copy(), capture_output=True, text=True)
        if result.returncode != 0:
            print("FFmpeg stdout:", result.stdout)
            print("FFmpeg stderr:", result.stderr)
            raise subprocess.CalledProcessError(result.returncode, ffmpeg_cmd)
    finally:
        driver.quit()
        xvfb.terminate()
        xvfb.wait()

    return output_video_path

def process_html_to_video(html_template_path, data=None, window_size=(1080, 1080), 
                          duration=5.0, fps=30):
    """
    Process HTML template to video recording.
    
    Args:
        html_template_path (str): Path to HTML template file
        data (dict): Dictionary of values to substitute in template (default: {})
        window_size (tuple): (width, height) of browser window
        duration (float): Duration of recording in seconds
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
        tempFiles.append(str(html_output_path))  # Track for cleanup
        
        # Record video
        record_video(
            html_output_path,
            video_output_path,
            duration=duration,
            window_size=window_size,
            fps=fps,
        )
        
        # Clean up intermediate files
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
        self.description = "Module that records a video of an HTML template with given parameter values.\nParameters:\n- template: Path to the HTML template\n- data: Dictionary with parameters that should be filled in the template {'Parameter name':Value}\n- size: Tuple (width, height), in pixel, that indicate the web window size\n- duration: Duration of the recording in seconds\n- fps: Frames per second"
        self.requiredArgs = [
            ("template", Path),
            ("data", dict), 
            ("size", tuple[int, int]),
            ("duration", float),
            ("fps", int)
        ]
        self.returnedDataTypes = [("destination", Path)]
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
            output_path = process_html_to_video(
                str(kwargs["template"].absolute()), 
                kwargs["data"], 
                kwargs["size"], 
                kwargs["duration"], 
                kwargs["fps"]
            )
            
            return ModuleResultType(None, {"destination":Path(output_path)}) 
        except Exception as e:
            # Clean up any remaining temp files on error
            clearTemp()
            return ModuleResultType(e, {}) 
