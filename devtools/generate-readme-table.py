import os
import inspect
import sys
import modules

TABLE_HEADERS = """
| **Module name**        | **File name**             | **Description**                                                                                                                                                                                  | **Required parameters**                                                        | **Returned values**                                              | **Dependencies**                                 |
|------------------------|---------------------------|--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|--------------------------------------------------------------------------------|------------------------------------------------------------------|--------------------------------------------------|"""
TABLE_ROW = "| {moduleName} | {fileName} | {desc} |{required} |{returned} |{depends} |"

def main():
    temp = f"{TABLE_HEADERS}"
    modules.loadModules()
    for module in list(map(modules.modules.get, modules.modules.keys())):
        reqs = ""
        rets = ""
        deps = ""
        if len(module.requiredArgs) == 0:
            reqs = " /"
        else:
            for req in module.requiredArgs:
                reqs = f"{reqs} {req[0]}-({req[1].__name__})"
        if len(module.returnedDataTypes) == 0:
            rets = " /"
        else:
            for ret in module.returnedDataTypes:
                rets = f"{rets} {ret[0]}-({ret[1].__name__})"
        if len(module.dependencies) == 0:
            deps = " /"
        else:
            for dep in module.dependencies:
                deps = f"{deps} {dep}"

        # Get the file path more robustly
        try:
            # First try the standard way
            file_path = os.path.abspath(inspect.getfile(module.__class__))
        except (TypeError, OSError):
            # If that fails, try to get it from the module
            try:
                # Try to get it from the module's __module__ attribute
                module_name = module.__class__.__module__
                if module_name in sys.modules:
                    module_obj = sys.modules[module_name]
                    if hasattr(module_obj, '__file__'):
                        file_path = os.path.abspath(module_obj.__file__)
                    else:
                        file_path = "Built-in or dynamically created"
                else:
                    file_path = "Unknown"
            except:
                file_path = "Unknown"
        
        if '/' in file_path:
            file_path = file_path.split('/')[len(file_path.split('/'))-1]

        desc_first_line = module.description.split('\n')[0]
        row = TABLE_ROW.format(
            moduleName=module.name,
            fileName=file_path,
            desc=desc_first_line,
            required=reqs,
            returned=rets,
            depends=deps
        )
        temp = f"{temp}\n{row}"
    print(temp)
    print(f"\n\033[31;1;4m{'Please note that some modules filepath recognition might have failed, so please insert the filepath manually in rows that say `Unknown`'}\033[0m")

if __name__ == "__main__":
    #if len(sys.argv) != 2:
    #    print("Usage: python3 update-readme.py readme.md")
    #    sys.exit(1)

    #readme = sys.argv[1]
    main()
