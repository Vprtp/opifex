import os
from pathlib import Path
import subprocess
import time
import re
import config
from basemodule import BaseModule, ModuleResultType

p = os.path.abspath(__file__).replace(os.path.basename(__file__),"")

piperLocation: str = config.piperLocation
model: str = config.piperModel
destinationPath: str = config.audioOutputPath

allowedChars_EN:list[str] = [
    ' ', '.', ',', ';', ':', "'", '"', '(', ')', '!', '?', '%', '&', '$', '€',#punctuation
    'a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l', 'm', 'n', 'o', 'p', 'q', 'r', 's', 't', 'u', 'v', 'w', 'x', 'y', 'z', #lowercase alphabet
    'A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M', 'N', 'O', 'P', 'Q', 'R', 'S', 'T', 'U', 'V', 'W', 'X', 'Y', 'Z', #uppercase alphabet
    '0', '1', '2', '3', '4', '5', '6', '7', '8', '9' #digits
]
htmlCodes:dict[str,str] = {
    #special characters
    "&deg;" : "°", "&#176;" : "°",
    "&laquo;" : "«", "&#171;" : "«",
    "&raquo;" : "»", "&#187;" : "»",
    "&ndash;" : "–", "&#8211;" : "–",
    "&mdash;" : "—", "&#8212;" : "—",
    "&iexcl;" : "¡", "&#161;" : "¡",
    "&iquest;" : "¿", "&#191;" : "¿",
    "&quot;" : '"', "&#34;" : '"',
    "&ldquo;" : "“", "&#8220;" : "“",
    "&rdquo;" : "”", "&#8221;" : "”",
    "&lsquo;" : "‘", "&#8216;" : "‘",
    "&rsquo;" : "’", "&#8217;" : "’",
    "&nbsp;" : " ", "&#160;" : " ",
    #symbols
    "&amp;" : "&", "&#38;" : "&",
    "&cent;" : "¢", "&#162;" : "¢",
    "&copy;" : "©", "&#169;" : "©",
    "&divide;" : "÷", "&#247;" : "÷",
    "&gt;" : ">", "&#62;" : ">",
    "&lt;" : "<", "&#60;" : "<",
    "&micro;" : "µ", "&#181;" : "µ",
    "&middot;" : "·", "&#183;" : "·",
    "&para;" : "¶", "&#182;" : "¶",
    "&plusmn;" : "±", "&#177;" : "±",
    "&euro;" : "€", "&#8364;" : "€",
    "&pound;" : "£", "&#163;" : "£",
    "&reg;" : "®", "&#174;" : "®",
    "&sect;" : "§", "&#167;" : "§",
    "&trade;" : "™", "&#153;" : "™",
    "&yen;" : "¥", "&#165;" : "¥",
    #diacriticals
    "&aacute;" : "á", "&#225;" : "á",
    "&Aacute;" : "Á", "&#193;" : "Á",
    "&agrave;" : "à", "&#224;" : "à",
    "&Agrave;" : "À", "&#192;" : "À",
    "&acirc;" : "â", "&#226;" : "â",
    "&Acirc;" : "Â", "&#194;" : "Â",
    "&aring;" : "å", "&#229;" : "å",
    "&Aring;" : "Å", "&#197;" : "Å",
    "&atilde;" : "ã", "&#227;" : "ã",
    "&Atilde;" : "Ã", "&#195;" : "Ã",
    "&auml;" : "ä", "&#228;" : "ä",
    "&Auml;" : "Ä", "&#196;" : "Ä",
    "&aelig;" : "æ", "&#230;" : "æ",
    "&AElig;" : "Æ", "&#198;" : "Æ",
    "&ccedil;" : "ç", "&#231;" : "ç",
    "&Ccedil;" : "Ç", "&#199;" : "Ç",
    "&eacute;" : "é", "&#233;" : "é",
    "&Eacute;" : "É", "&#201;" : "É",
    "&egrave;" : "è", "&#232;" : "è",
    "&Egrave;" : "È", "&#200;" : "È",
    "&ecirc;" : "ê", "&#234;" : "ê",
    "&Ecirc;" : "Ê", "&#202;" : "Ê",
    "&euml;" : "ë", "&#235;" : "ë",
    "&Euml;" : "Ë", "&#203;" : "Ë",
    "&iacute;" : "í", "&#237;" : "í",
    "&Iacute;" : "Í", "&#205;" : "Í",
    "&igrave;" : "ì", "&#236;" : "ì",
    "&Igrave;" : "Ì", "&#204;" : "Ì",
    "&icirc;" : "î", "&#238;" : "î",
    "&Icirc;" : "Î", "&#206;" : "Î",
    "&iuml;" : "ï", "&#239;" : "ï",
    "&Iuml;" : "Ï", "&#207;" : "Ï",
    "&ntilde;" : "ñ", "&#241;" : "ñ",
    "&Ntilde;" : "Ñ", "&#209;" : "Ñ",
    "&oacute;" : "ó", "&#243;" : "ó",
    "&Oacute;" : "Ó", "&#211;" : "Ó",
    "&ograve;" : "ò", "&#242;" : "ò",
    "&Ograve;" : "Ò", "&#210;" : "Ò",
    "&ocirc;" : "ô", "&#244;" : "ô",
    "&Ocirc;" : "Ô", "&#212;" : "Ô",
    "&oslash;" : "ø", "&#248;" : "ø",
    "&Oslash;" : "Ø", "&#216;" : "Ø",
    "&otilde;" : "õ", "&#245;" : "õ",
    "&Otilde;" : "Õ", "&#213;" : "Õ",
    "&ouml;" : "ö", "&#246;" : "ö",
    "&Ouml;" : "Ö", "&#214;" : "Ö",
    "&uacute;" : "ú", "&#250;" : "ú",
    "&Uacute;" : "Ú", "&#218;" : "Ú",
    "&ugrave;" : "ù", "&#249;" : "ù",
    "&Ugrave;" : "Ù", "&#217;" : "Ù",
    "&ucirc;" : "û", "&#251;" : "û",
    "&Ucirc;" : "Û", "&#219;" : "Û",
    "&uuml;" : "ü", "&#252;" : "ü",
    "&Uuml;" : "Ü", "&#220;" : "Ü",
    "&szlig;" : "ß", "&#223;" : "ß",
    "&yuml;" : "ÿ", "&#255;" : "ÿ",
    "&#180;" : "´",
    "&#96;" : "`",
}
htmlCodesPattern:re.Pattern = re.compile("|".join(map(re.escape, htmlCodes.keys())))

def cleanText(original:str, allowed:list[str]=allowedChars_EN, htmlCodes:dict[str,str]=htmlCodes, pattern:re.Pattern = htmlCodesPattern) -> str:
    filtered:str = pattern.sub(lambda match: htmlCodes[match.group(0)], original)
    filtered = ''.join([char for char in filtered if char in allowed])
    return filtered

def generate(text: str, clean:bool = True, textVoice: str = model, destination: str = destinationPath, piper: str = piperLocation, cleanIterations:int = 2, speed:float = 0.9, noiseScale:float = 0.667, lengthScale:float = 1.2) -> str:
    timestamp: int = int(time.time())
    
    # Create the output directory
    output_dir = destination.format(time=timestamp, fileName="").rsplit('/', 1)[0]
    os.makedirs(output_dir, exist_ok=True)
    
    textDestination: str = destination.format(time=timestamp, fileName=f"speech{int(time.time()*1000)%1000}")
    
    print(f"piper: '{piper}' clean: '{clean}' textVoice: '{textVoice}' destination: '{destination}' cleanIterations: {cleanIterations} speed: {speed} noiseScale: {noiseScale} lengthScale: {lengthScale}")

    if clean:
        text = cleanText(text)
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
