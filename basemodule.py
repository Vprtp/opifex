from abc import ABC, abstractmethod
from typing import Dict, Any, List, Tuple

class ModuleResultType:
    def __init__(self, exception:Exception|None, data:Dict[str, Any]):
        self.exception = exception
        self.data = data
    
    def __str__(self):
        return f"ModuleResultType: exception <{str(self.exception)}> data <{str(self.data)}>"

class BaseModule(ABC):
    def __init__(self):
        self.name:str = ""
        self.description:str = ""
        self.requiredArgs:List[Tuple[str,type]] = [] #list of required parameters as (name, type) pairs
        self.returnedDataTypes:List[Tuple[str,type]] = [] #list of returned key values and respective data types in returned data dict of ModuleResultType
        self.dependencies:List[str] = [] #list of "dependencies" (other modules' name) required for the module to work

    def __str__(self):
        return f"Module <{self.name}>: {self.description.split('\n')[0]}" #prints first line of description, which should always be just the summary. hopefully.
    
    @abstractmethod
    def execute(self, version:str, **kwargs) -> ModuleResultType: #version is the program version, it should be passed automatically by modules.executeModule()
        """Execute the module and return results"""
        pass

