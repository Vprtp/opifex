import os
from pathlib import Path
import subprocess
import time
from lib.textprocessing import cleanText
import config
from basemodule import BaseModule, ModuleResultType

p = os.path.abspath(__file__).replace(os.path.basename(__file__),"")

piperLocation: str = config.piperLocation
model: str = config.piperModel
destinationPath: str = config.audioOutputPath

def generate(text: str, clean:bool = True, textVoice: str = model, destination: str = destinationPath, piper: str = piperLocation, cleanIterations:int = 2, speed:float = 0.9, noiseScale:float = 0.667, lengthScale:float = 1.2) -> str:
    timestamp: int = int(time.time())
    
    # Create the output directory
    output_dir = destination.format(time=timestamp, fileName="").rsplit('/', 1)[0]
    os.makedirs(output_dir, exist_ok=True)
    
    textDestination: str = destination.format(time=timestamp, fileName=f"speech{int(time.time()*1000)%1000}")
    
    print(f"piper: '{piper}' clean: '{clean}' textVoice: '{textVoice}' destination: '{destination}' cleanIterations: {cleanIterations} speed: {speed} noiseScale: {noiseScale} lengthScale: {lengthScale}")

    if clean:
        text = cleanText(text, forceAllowed=True)
        for _ in range(cleanIterations): #generate and delete the file multiple times and then take the last one in consideration
            if os.path.exists(textDestination):
                os.remove(textDestination)
            
            subprocess.run(
                [
                    piper,
                    "--model", textVoice,
                    "--output_file", textDestination,
                    "--speed", str(speed),
                    "--noise_scale", str(noiseScale),
                    "--length_scale", str(lengthScale),
                ],
                input=text.encode(),
                check=True, 
            )
    else:
        subprocess.run(
            [
                piper,
                "--model", textVoice,
                "--output_file", textDestination,
                "--speed", str(speed),
                "--noise_scale", str(noiseScale),
                "--length_scale", str(lengthScale),
            ],
            input=text.encode(),
            check=True, 
        )
    
    return textDestination

class TTS(BaseModule):
    def __init__(self):
        self.name = "TTS"
        self.description = "Module for generating speech from a given text.\n\nParameters:\n-text: Text to run through the model, which will become speech"
        self.requiredArgs = [("text",str)]
        self.returnedDataTypes = [("destination",Path)]
        self.dependencies = []
    
    def execute(self, version:str, **kwargs):
        try:
            path = generate(kwargs["text"])
            return ModuleResultType(None,{"destination":Path(path)})
        except Exception as e:
            return ModuleResultType(e,{})
