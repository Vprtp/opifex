# Opifex

Manual for version `0.1.0`.

[<div style="text-align: center"><img src="source/img/logo.png" width="200"/></div>](source/img/logo.png)

_Opifex_ is a modular tool designed for automated content creation (videos, images, texts, audios, and more, depending on which modules are installed and used).

## Installation

After downloading the repository, Opifex can be properly set up by running `bash install.sh` in the main directory.

The script will download various assets that are used by the program (or by the default modules) that are too heavy to be hosted on GitHub and it will set up a _Conda_ environment for the program (based on `environment.yml`), as well as install Conda (precisely _Miniconda3_) if no Conda version was found on the system.  
Opifex requires this environment to function properly, as some Conda-exclusive programs (such as _Montreal Forced Aligner_) are being used.

Opifex can then be started by running `bash main.sh` in the main directory.

(On both cases, please **avoid** running the scripts in other methods, for example `./main.sh`, since this way of execution might cause problems.)

So, as of now, **Opifex runs exclusively on Linux**.

## Modules

### What are modules?

**Modules** are independent pieces of code, each with a specific function, that can be executed through Opifex.  
Modules are Python scripts that can be found in the `modules` direcory and that contain the `basemodule.BaseModule` class.  
They are imported upon startup and can be executed, with proper parameters, using `modules.executeModule()`, returning a class of type `basemodule.ModuleResultType`.

Based on this, in reality, the main program (for now) still just works as a layer for the user to call and interact with modules, which actually do the content creation operations.

**Be careful** when you download modules made by other people!  
By executing a module, you will be running code on your machine like any other program, so be certain that the downloaded script doesn't contain any malicious code.

### Default modules

Many modules are already part of Opifex by default, but everyone is free to write their own modules or download other community-made modules, by just placing them inside the `modules` directory. Here is a list of the preinstalled modules:

| **Module name**        | **File name**             | **Description**                                                                                                                                                                                  | **Required parameters**                                                        | **Returned values**                                              | **Dependencies**                                 |
|------------------------|---------------------------|--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|--------------------------------------------------------------------------------|------------------------------------------------------------------|--------------------------------------------------|
| _RedditVideoGenerator_ | reddit-video-generator.py | Module that generates a video, or multiple videos, based the content contained in a given Reddit post. Returns paths to the generated videos (list of size 1 when only one video is generated)   | url-(str) commentsOrDesc-(bool) accountName-(str)                              | paths-(list[str])                                                | Reddit TTS Aligner VideoGenerator URLunshortener |
| _URLunshortener_       | unshortenURL.py           | Module that returns the final URL from redirections by a given one (thus 'unshortening' shortened URLs)                                                                                          | url-(str) rmpars-(bool)                                                        | url-(str)                                                        | /                                                |
| _Reddit_               | reddit.py                 | Module for fetching reddit posts.                                                                                                                                                                | url-(str) upvotesMin-(float) wordsMin-(int) checkMax-(int)                     | title-(str) description-(str) upvotes-(int) comments-(list[str]) | Screenshot                                       |
| _TTS_                  | tts.py                    | Module for generating speech from a given title and text.                                                                                                                                        | title-(str) text-(str)                                                         | titleDestination-(str) textDestination-(str)                     | /                                                |
| _Aligner_              | alignSRT.py               | Module for generating subtitles from a given audio and its transcript.                                                                                                                           | audio-(str) transcript-(str) output-(str)                                      | textgridOutput-(str) srtOutput-(str)                             | /                                                |
| _VideoGenerator_       | video.py                  | Module for generating a video based on given title, subtitles, audio for both title and text, and a destination path.                                                                            | title-(str) subtitles-(str) titleAudio-(str) textAudio-(str) destination-(str) | /                                                                | /                                                |
| _Screenshot_           | screenshot.py             | Module that screenshots an HTML template with given parameter values to fill it and cleans it to be a transparent PNG. Returns the path to the generated image.                                  | template-(str) data-(dict) size-(tuple[int,int])                               | destination-(str)                                                | /                                                |

### Creating modules

Creating modules is simple: all you have to do is write a Python script that does what you want it to do and attach a personalized `basemodule.Basemodule` class at the end of it, so that it can be recognized by Opifex.  
Be careful to put all your code in functions: anything outside them will be run when loading the module, because they are being imported as Python libraries.

```
class BaseModule:
    def __init__(self):
        self.name = ABC
        self.description = ABC
        self.requiredArgs:List[Tuple[str,type]] = ABC #list of required parameters as (name, type) pairs
        self.returnedDataTypes:List[Tuple[str,type]] = ABC #list of returned key values and respective data types in returned data dict of ModuleResultType
        self.dependencies:List[str] = ABC #list of "dependencies" (other plugins' name) required for the plugin to work

    def __str__(self):
        return f"Module <{self.name}>: {self.description.split("\n")[0]}" #prints first line of description, which should always be just the summary. hopefully.
    
    @abstractmethod
    def execute(self, **kwargs) -> ModuleResultType:
        """Execute the module and return results"""
        pass
```
`YourModule.execute()` must return a variable of type `basemodule.ModuleResultType`, which will contain information about possible execution errors and data returned by the module:
```
class ModuleResultType:
    def __init__(self, exception:Exception|None, data:Dict[str, Any]):
        self.exception = exception
        self.data = data
    
    def __str__(self):
        return f"ModuleResultType: exception <{str(self.exception)}> data <{str(self.data)}>"
```

## GUI mode

Opifex can run in an intuitive **GUI mode**:

[<div style="text-align: center"><img src="source/img/opifex-gui.png" width="600"/></div>](source/img/opifex-gui.png)

The interface is devided in specialized sections:
* On the left, there's a list of all loaded **modules**. Each module can be inspected by _double clicking_. Modules can be reloaded by pressing the `Reload` button.
* On the right, details of the **selected module** are displayed. You can _execute_ the selected module by pressing the `Execute` button, after having provided all of the selected module's parameters.
* On the bottom, a **console** shows all output from modules and Opifex itself (after startup, all `stdout` and `stderr` calls get redirected here).
* On the top, a **toolbar** allows you to have quick access to the _configurations file_, to this page and to a quick _info page_.

Output from **executed modules** will be printed to console (at least for now).

## Credits and info

All code for Opifex has been written by **prtp** ([Vprtp](https://github.com/Vprtp) on GitHub).  
Opifex is distributed under the [GNU GPL v3](https://www.gnu.org/licenses/gpl-3.0-standalone.html) license.  
To function properly, Opifex uses the following libraries/software (which are included with the installation of this program):
* _PyQt6_ for its graphic functionalities
* _PiperTTS_ for text-to-speech
* _Montreal Forced Aligner_ to align the generated TTS with its transcript and create a subtitles file
* _FFmpeg_ to edit and compose videos
* _Selenium_ to capture web pages


Opifex (which, btw, means "artisan, manifacturer" in Latin) is just a hobby project, so don't expect it to be top-quality software However, I still plan to add a lot of other things to it in future: first of all, a slighly more user-friendly GUI, then a CLI mode, tons of other modules, and all of this just for the "single" mode (which runs entirely on the main machine). So, most importantly, I plan to add a "master" mode that offloads processing to multiple machines running in "worker" mode, effectively turning Opifex into a sort of "content farm" software.

Thanks for your attention.