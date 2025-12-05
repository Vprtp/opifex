import subprocess
from pathlib import Path
import shutil
import re
from typing import List
import config
from basemodule import BaseModule, ModuleResultType

def generateSubtitles(audioPath: str, transcript: str, outputDir: str, convertToSRT:bool = True) -> tuple[str,str]:
    """
    Align a single audio file with its transcript using MFA. Warning: will return a SRT path no matter if the conversion is actually done.
    
    Args:
        audioPath: Path to audio file (must be .wav)
        transcript: Text transcript (will create temporary .lab file)
        outputDir: Where to save the TextGrid output
    """
    # Create directories
    input_dir = Path(config.tempFolder)
    outputDir = Path(outputDir)
    
    input_dir.mkdir(exist_ok=True)
    outputDir.mkdir(exist_ok=True)
    
    # Prepare file structure
    stem = Path(audioPath).stem
    lab_path = input_dir / f"{stem}.lab"
    
    # Write transcript to .lab file
    with open(lab_path, 'w') as f:
        f.write(transcript)
    
    # Copy audio to input dir (MFA requires specific structure)
    audio_dest = input_dir / f"{stem}.wav"
    shutil.copy(audioPath, audio_dest)  # Always overwrite
    
    # Build MFA command
    mfa_cmd = [
        "mfa", "align",
        str(input_dir),        # Input directory
        config.alignerDict,  # Dictionary (will auto-download)
        config.alignerModel,      # Acoustic model
        str(outputDir),      # Output directory
        "--clean",            # Remove temporary files
        "--single_speaker"    # Single speaker mode
    ]
    
    textgridOutput:str = ""
    srtOutput:str = ""

    # Run MFA
    try:
        print("Running alignment...")
        result = subprocess.run(
            mfa_cmd,
            check=True,
            capture_output=True,
            text=True
        )
        print("Alignment succeeded!")
        textgridOutput = outputDir / (stem + '.TextGrid')
        print(f"Output saved to: {textgridOutput}")

        srtOutput = outputDir / (stem + '.srt')

        if convertToSRT:
            textgridToSrt(textgridOutput,srtOutput)
            print(f"Converted {textgridOutput} into {srtOutput} successfully.")
    except subprocess.CalledProcessError as e:
        print("Alignment failed!")
        print("Error:", e.stderr)
        raise
    
    return (textgridOutput,srtOutput)

#converter:
def textgridToSrt(textgrid_path: str, srt_path: str, tier_name: str = None) -> None:
    """
    Convert a Praat TextGrid file to SRT subtitle format.
    
    Args:
        textgrid_path: Path to the input TextGrid file
        srt_path: Path to save the output SRT file
        tier_name: Name of the tier to convert (if None, uses first tier)
    """
    with open(textgrid_path, 'r', encoding='utf-8') as f:
        textgrid = f.read()
    
    # Parse tiers from TextGrid
    tiers = parse_textgrid(textgrid)
    
    # Select the appropriate tier
    if tier_name:
        tier = next((t for t in tiers if t['name'] == tier_name), None)
        if tier is None:
            raise ValueError(f"Tier '{tier_name}' not found in TextGrid")
    else:
        tier = tiers[0]
    
    # Convert intervals to SRT format
    srt_entries = []
    for i, interval in enumerate(tier['intervals'], 1):
        start_time = format_time(interval['start'])
        end_time = format_time(interval['end'])
        text = interval['text'].strip()
        
        if text:  # Skip empty intervals
            srt_entries.append(
                f"{i}\n"
                f"{start_time} --> {end_time}\n"
                f"{text}\n"
            )
    
    # Write SRT file
    with open(srt_path, 'w', encoding='utf-8') as f:
        f.write("\n".join(srt_entries))

# Example usage:
# textgrid_to_srt('input.TextGrid', 'output.srt', 'words')

def parse_textgrid(textgrid: str) -> List[dict]:
    """Parse TextGrid content into a list of tiers with intervals."""
    tiers = []
    
    # Find all tier sections
    tier_sections = re.findall(
        r'item \[\d+\]:\s*\n\s*class = ".*?"\s*\n\s*name = "(.*?)"\s*\n(.*?)(?=(item|$))',
        textgrid,
        re.DOTALL
    )
    
    for name, content, _ in tier_sections:
        # Check if it's an interval tier
        if 'intervals [' in content:
            intervals = parse_intervals(content)
            tiers.append({'name': name, 'intervals': intervals})
    
    return tiers

def parse_intervals(tier_content: str) -> List[dict]:
    """Parse intervals from a tier's content."""
    intervals = []
    
    # Find all intervals
    interval_matches = re.finditer(
        r'intervals \[\d+\]:\s*\n'
        r'\s*xmin = (\d+\.?\d*)\s*\n'
        r'\s*xmax = (\d+\.?\d*)\s*\n'
        r'\s*text = "(.*?)"\s*\n',
        tier_content
    )
    
    for match in interval_matches:
        intervals.append({
            'start': float(match.group(1)),
            'end': float(match.group(2)),
            'text': match.group(3).replace('"', '')
        })
    
    return intervals

def format_time(seconds: float) -> str:
    """Convert seconds to SRT time format (HH:MM:SS,mmm)."""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    seconds_remainder = seconds % 60
    milliseconds = int((seconds_remainder - int(seconds_remainder)) * 1000)
    
    return f"{hours:02d}:{minutes:02d}:{int(seconds_remainder):02d},{milliseconds:03d}"

class Aligner(BaseModule):
    def __init__(self):
        self.name = "Aligner"
        self.description = "Module for generating subtitles from a given audio and its transcript.\n\nParameters:\n-audio: Path to the audio file\n-transcript: Text transcription of speech inside audio file\n-output: Output directory for generated SRT file"
        self.requiredArgs = [("audio",str),("transcript",str),("output",str)]
        self.returnedDataTypes = [("textgridOutput",str),("srtOutput",str)]
        self.dependencies = []
    
    def execute(self, version:str, **kwargs):
        try:
            paths = generateSubtitles(kwargs["audio"],kwargs["transcript"],kwargs["output"])
            return ModuleResultType(None,{"textgridOutput":paths[0],"srtOutput":paths[1]})
        except Exception as e:
            return ModuleResultType(e,{})