from basemodule import BaseModule, ModuleResultType
import importlib.util
import os
import sys
import inspect
from main import VERSION

p = os.path.abspath(__file__).replace(os.path.basename(__file__),"")

modulesDir:str = p+"modules/"
modules:dict[str, BaseModule] = {} #{name, BaseModule}, name can be the same as BaseModule.name, as long as the program understands it

def loadModules(dir:str = modulesDir, checkForDependencies:bool = True) -> None:
    """
    Dynamically imports all Python scripts in the given folder,
    finds classes that inherit from BaseModule,
    instantiates them, and registers them in the global modules dictionary.
    """
    dependencies:tuple[str,str] = [] #list of all dependencies and scripts requiring them: [(dependencyName1, pluginThatRequiresIt1),(dependencyName2, pluginThatRequiresIt2)]
    abs_folder = os.path.abspath(dir)
    if abs_folder not in sys.path:
        sys.path.insert(0, abs_folder)

    modules.clear()

    for filename in os.listdir(dir):
        if filename.endswith(".py") and filename != "__init__.py":
            module_name = filename[:-3]
            file_path = os.path.join(dir, filename)

            spec = importlib.util.spec_from_file_location(module_name, file_path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)

            # Iterate over all classes in the module
            for _, obj in inspect.getmembers(module, inspect.isclass):
                # Check if it's a subclass of BaseModule (but not BaseModule itself)
                if issubclass(obj, BaseModule) and obj is not BaseModule:
                    instance = obj()
                    modules[instance.name] = instance
                    #add possible dependencies to list
                    if checkForDependencies:
                        if len(instance.dependencies) > 0:
                            for d in instance.dependencies:
                                dependencies.append((d,instance.name))
    
    #check for dependencies
    if checkForDependencies:
        for d in dependencies:
            if d[0] not in modules:
                raise ModuleNotFoundError(f"Module '{d[0]}', required by '{d[1]}', was not found in the modules folder.")          

def executeModule(name:str, **kwargs) -> ModuleResultType:
    return modules[name].execute(VERSION,**kwargs)

if __name__ == "__main__":
    try:
        loadModules()
    except Exception as e:
        print(f"Module load process failed: \n{e.__traceback__}")
    print("Avaiable modules:")
    for module in modules:
        print(f" -{modules[module]}")
    print("\nWhen using this file as a library, load all modules with loadModules() and execute them with executeModule(module name, other arguments).")