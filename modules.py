from basemodule import BaseModule, ModuleResultType
import importlib.util
import os
import sys
import gc
import inspect
from main import VERSION

p = os.path.abspath(__file__).replace(os.path.basename(__file__),"")

modulesDir:str = p+"modules/"
libsDir:str = p+"lib/"
modules:dict[str, BaseModule] = {} #{name, BaseModule}, name can be the same as BaseModule.name, as long as the program understands it
moduleFileNames:list[str] = []

def loadLib(path:str) -> tuple:
    """
    Loads given script as a library. Returns the importlib module and module name.
    """
    filename:str = os.path.basename(path)
    libName:str = os.path.splitext(filename)[0]
    
    # Check if already loaded to avoid reloading
    if libName in sys.modules:
        return (sys.modules[libName],libName)
    
    spec = importlib.util.spec_from_file_location(libName, path)
    lib = importlib.util.module_from_spec(spec)
    
    # CRITICAL: Add to sys.modules so it can be imported elsewhere
    sys.modules[libName] = lib
    
    spec.loader.exec_module(lib)
    return (lib,libName)

def unloadLib(libName: str) -> None:
    """
    Unloads a previously loaded library by name.
    """
    if libName not in sys.modules:
        raise ModuleNotFoundError(f"'{libName}' is not in sys.modules")

    # Remove the module from sys.modules
    module = sys.modules.pop(libName)

    # Delete references in globals (if any)
    for name, obj in list(globals().items()):
        if obj is module:
            del globals()[name]

    # Force garbage collection
    del module
    gc.collect()

def loadLibs(dir:str = libsDir) -> int:
    """
    Load all scripts in the libsDir folder as libraries. Returns the number of loaded libs.
    """
    loaded:int = 0
    # Add lib directory to Python path so modules can import from it
    if dir not in sys.path:
        sys.path.insert(0, dir)
    
    for filename in os.listdir(dir):
        if filename.endswith(".py") and filename != "__init__.py":
            file_path = os.path.join(dir, filename)
            loadLib(file_path)
            loaded += 1
    return loaded 

def unloadModules():
    for mod in moduleFileNames:
        unloadLib(mod)
    moduleFileNames.clear()

def loadModules(dir:str = modulesDir, checkForDependencies:bool = True) -> None:
    """
    Dynamically imports all Python scripts in the given folder,
    finds classes that inherit from BaseModule,
    instantiates them, and registers them in the global modules dictionary.
    """
    unloadModules() #unload all previously loaded modules, if there are any

    dependencies:list[tuple[str,str]] = [] # Fixed type annotation
    
    # Ensure both directories are in sys.path
    if libsDir not in sys.path:
        sys.path.insert(0, libsDir)
    
    abs_folder = os.path.abspath(dir)
    if abs_folder not in sys.path:
        sys.path.insert(0, abs_folder)

    modules.clear()

    for filename in os.listdir(dir):
        if filename.endswith(".py") and filename != "__init__.py":
            file_path = os.path.join(dir, filename)

            lib = loadLib(file_path)
            module = lib[0]  # This already adds to sys.modules
            moduleFileNames.append(lib[1])

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

    temp = dict(sorted(modules.items()))
    modules.clear()
    modules.update(temp)

def executeModule(name:str, **kwargs) -> ModuleResultType:
    return modules[name].execute(VERSION,**kwargs)

if __name__ == "__main__":
    try:
        loadLibs()
        loadModules()
    except Exception as e:
        print(f"Module load process failed: \n{e.__traceback__}")
    print("Avaiable modules:")
    for module in modules:
        print(f" -{modules[module]}")
    print("\nWhen using this file as a library, load all modules with loadModules() and execute them with executeModule(module name, other arguments).")
