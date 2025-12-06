import os, shutil
import config
import sys
from io import TextIOBase
import modules
from PySide6 import QtCore, QtWidgets, QtGui
from typing import get_origin, get_args
import subprocess

PROJECTNAME = "Opifex"
VERSION = "0.1.0" #current version to show and use in the project, [MAIN RELEASE].[MAIN SUBRELEASE].[MINOR SUBRELEASE]
AUTHORS = "prtp (Vprtp on GitHub)"

def clearTemp(dir:str=config.tempFolder):
    shutil.rmtree(dir)
    os.mkdir(dir)

def loadStylesheet(path: str) -> str:
    with open(path, "r", encoding="utf-8") as f:
        return f.read()

def openFileWithDefaultEditor(file_path):
    if sys.platform == "win32":
        os.startfile(file_path)
    elif sys.platform == "darwin":  # macOS
        subprocess.run(["open", file_path])
    else:  # Linux and other Unix-like systems
        subprocess.run(["xdg-open", file_path])

class QTextEditStream(TextIOBase):
    def __init__(self, text_edit):
        self.text_edit = text_edit
        
    def write(self, text):
        self.text_edit.moveCursor(QtGui.QTextCursor.MoveOperation.End)
        self.text_edit.insertPlainText(text)
        self.text_edit.moveCursor(QtGui.QTextCursor.MoveOperation.End)
        
    def flush(self):
        pass

class ModuleWorker(QtCore.QThread):
    result = QtCore.Signal(object)      # emitted when the module finishes
    error = QtCore.Signal(Exception)     # emitted if exception occurs
    output = QtCore.Signal(str)  # every line of print

    def __init__(self, selectedModule, params):
        super().__init__()
        self.selectedModule = selectedModule
        self.params = params

    def run(self):
        # Patch stdout only inside worker
        sys.stdout = self

        try:
            res = modules.executeModule(self.selectedModule, **self.params)
            self.result.emit(res)
        except Exception as e:
            self.error.emit(e)

    # This replaces stdout.write()
    def write(self, text):
        if text.strip():
            self.output.emit(text)

    def flush(self):
        pass  # required for file-like wrappers

class TypeInputFactory:
    @staticmethod
    def create_input_widget(value_type, parent=None):
        """Create input widget based on type alone, supporting generics"""
        
        # Handle generic types like list[str], dict[str, int], etc.
        origin = get_origin(value_type)
        if origin is not None:
            args = get_args(value_type)
            if origin == list:
                return TypeInputFactory._create_list_input(parent, item_type=args[0] if args else str)
            elif origin == tuple:
                return TypeInputFactory._create_tuple_input(parent, item_type=args[0] if args else str)
            elif origin == dict:
                key_type = args[0] if len(args) > 0 else str
                value_type = args[1] if len(args) > 1 else str
                return TypeInputFactory._create_dict_input(parent, key_type=key_type, value_type=value_type)
        
        # Handle basic types (original code)
        if value_type == bool:
            return TypeInputFactory._create_bool_input(parent)
        elif value_type == int:
            return TypeInputFactory._create_int_input(parent)
        elif value_type == float:
            return TypeInputFactory._create_float_input(parent)
        elif value_type == str:
            return TypeInputFactory._create_string_input(parent)
        elif value_type == list:
            return TypeInputFactory._create_list_input(parent, item_type=str)  # Default to string
        elif value_type == dict:
            return TypeInputFactory._create_dict_input(parent, key_type=str, value_type=str)  # Default to string
        elif value_type == tuple:
            return TypeInputFactory._create_tuple_input(parent, item_type=str)  # Default to string
        else:
            return TypeInputFactory._create_fallback_input(parent)
    
    @staticmethod
    def get_input_value(widget):
        """Get value from input widget based on its type"""
        if isinstance(widget, QtWidgets.QCheckBox):
            return widget.isChecked()
        elif isinstance(widget, QtWidgets.QSpinBox):
            return widget.value()
        elif isinstance(widget, QtWidgets.QDoubleSpinBox):
            return widget.value()
        elif isinstance(widget, QtWidgets.QLineEdit):
            return widget.text()
        elif isinstance(widget, QtWidgets.QWidget) and hasattr(widget, '_type_input_type'):
            # Handle container types
            if widget._type_input_type == 'list':
                return TypeInputFactory._get_list_value(widget)
            elif widget._type_input_type == 'dict':
                return TypeInputFactory._get_dict_value(widget)
            elif widget._type_input_type == 'tuple':
                return tuple(TypeInputFactory._get_list_value(widget))
        else:
            # Fallback
            try:
                return eval(widget.text())
            except:
                return widget.text()
    
    # Basic type creators (with default values)
    @staticmethod
    def _create_bool_input(parent):
        widget = QtWidgets.QCheckBox(parent)
        widget.setChecked(False)  # Default false
        return widget
    
    @staticmethod
    def _create_int_input(parent):
        widget = QtWidgets.QSpinBox(parent)
        widget.setValue(0)  # Default 0
        widget.setRange(-1000000, 1000000)
        return widget
    
    @staticmethod
    def _create_float_input(parent):
        widget = QtWidgets.QDoubleSpinBox(parent)
        widget.setValue(0.0)  # Default 0.0
        widget.setRange(-1e9, 1e9)
        widget.setDecimals(6)
        return widget
    
    @staticmethod
    def _create_string_input(parent):
        widget = QtWidgets.QLineEdit(parent)
        widget.setText("")  # Default empty string
        return widget
    
    # Container type creators
    @staticmethod
    def _create_list_input(parent, item_type=str):
        container = QtWidgets.QWidget(parent)
        container._type_input_type = 'list'
        container._item_type = item_type  # Store the item type
        layout = QtWidgets.QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Store child widgets
        container._input_widgets = []
        
        # Add button with type info
        type_name = item_type.__name__ if hasattr(item_type, '__name__') else str(item_type)
        add_btn = QtWidgets.QPushButton(f"+ Add {type_name} Item")
        layout.addWidget(add_btn)
        
        # Create scroll area for items
        scroll = QtWidgets.QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll.setMaximumHeight(200)
        
        scroll_widget = QtWidgets.QWidget()
        scroll_layout = QtWidgets.QVBoxLayout(scroll_widget)
        scroll_layout.setContentsMargins(0, 0, 0, 0)
        container._items_layout = scroll_layout
        
        scroll.setWidget(scroll_widget)
        layout.addWidget(scroll)
        
        # Start with one empty item of the correct type
        TypeInputFactory._add_list_item(container, "", item_type)
        
        # Connect add button
        add_btn.clicked.connect(lambda: TypeInputFactory._add_list_item(container, "", item_type))
        
        return container
    
    @staticmethod
    def _add_list_item(container, value, item_type=None):
        if item_type is None:
            item_type = getattr(container, '_item_type', str)
        
        # Create widget of the specific item type
        item_widget = TypeInputFactory.create_input_widget(item_type)
        
        # Set initial value if provided
        if value:
            TypeInputFactory._set_widget_value(item_widget, value)
        
        remove_btn = QtWidgets.QPushButton("−")
        remove_btn.setFixedWidth(30)
        
        item_container = QtWidgets.QWidget()
        item_layout = QtWidgets.QHBoxLayout(item_container)
        item_layout.setContentsMargins(0, 0, 0, 0)
        item_layout.addWidget(item_widget, 1)
        item_layout.addWidget(remove_btn)
        
        container._items_layout.addWidget(item_container)
        container._input_widgets.append(item_widget)
        
        remove_btn.clicked.connect(lambda: TypeInputFactory._remove_list_item(container, item_container))
    
    @staticmethod
    def _remove_list_item(container, item_widget):
        container._input_widgets = [w for w in container._input_widgets 
                                  if w.parent() != item_widget]
        item_widget.deleteLater()
    
    @staticmethod
    def _create_dict_input(parent, key_type=str, value_type=str):
        container = QtWidgets.QWidget(parent)
        container._type_input_type = 'dict'
        container._key_type = key_type
        container._value_type = value_type
        layout = QtWidgets.QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        
        container._key_widgets = []
        container._value_widgets = []
        
        # Add button with type info
        key_type_name = key_type.__name__ if hasattr(key_type, '__name__') else str(key_type)
        value_type_name = value_type.__name__ if hasattr(value_type, '__name__') else str(value_type)
        add_btn = QtWidgets.QPushButton(f"+ Add {key_type_name}→{value_type_name} Entry")
        layout.addWidget(add_btn)
        
        scroll = QtWidgets.QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setMaximumHeight(200)
        
        scroll_widget = QtWidgets.QWidget()
        scroll_layout = QtWidgets.QVBoxLayout(scroll_widget)
        scroll_layout.setContentsMargins(0, 0, 0, 0)
        container._entries_layout = scroll_layout
        
        scroll.setWidget(scroll_widget)
        layout.addWidget(scroll)
        
        # Start with one empty entry
        TypeInputFactory._add_dict_entry(container, "", "", key_type, value_type)
        
        add_btn.clicked.connect(lambda: TypeInputFactory._add_dict_entry(container, "", "", key_type, value_type))
        
        return container
    
    @staticmethod
    def _add_dict_entry(container, key, value, key_type=None, value_type=None):
        if key_type is None:
            key_type = getattr(container, '_key_type', str)
        if value_type is None:
            value_type = getattr(container, '_value_type', str)
        
        key_widget = TypeInputFactory.create_input_widget(key_type)
        value_widget = TypeInputFactory.create_input_widget(value_type)
        
        # Set initial values if provided
        if key:
            TypeInputFactory._set_widget_value(key_widget, key)
        if value:
            TypeInputFactory._set_widget_value(value_widget, value)
        
        remove_btn = QtWidgets.QPushButton("−")
        remove_btn.setFixedWidth(30)
        
        entry_container = QtWidgets.QWidget()
        entry_layout = QtWidgets.QHBoxLayout(entry_container)
        entry_layout.setContentsMargins(0, 0, 0, 0)
        entry_layout.addWidget(QtWidgets.QLabel("Key:"))
        entry_layout.addWidget(key_widget, 1)
        entry_layout.addWidget(QtWidgets.QLabel("Value:"))
        entry_layout.addWidget(value_widget, 1)
        entry_layout.addWidget(remove_btn)
        
        container._entries_layout.addWidget(entry_container)
        container._key_widgets.append(key_widget)
        container._value_widgets.append(value_widget)
        
        remove_btn.clicked.connect(lambda: TypeInputFactory._remove_dict_entry(container, entry_container))
    
    @staticmethod
    def _remove_dict_entry(container, entry_widget):
        # Find and remove the corresponding widgets
        for i in range(container._entries_layout.count()):
            item = container._entries_layout.itemAt(i)
            if item and item.widget() == entry_widget:
                if i < len(container._key_widgets):
                    container._key_widgets.pop(i)
                    container._value_widgets.pop(i)
                break
        entry_widget.deleteLater()
    
    @staticmethod
    def _create_tuple_input(parent, item_type=str):
        # Reuse list input but mark as tuple
        widget = TypeInputFactory._create_list_input(parent, item_type)
        widget._type_input_type = 'tuple'
        return widget
    
    @staticmethod
    def _create_fallback_input(parent):
        widget = QtWidgets.QLineEdit(parent)
        widget.setText("")  # Default empty
        return widget
    
    # Value getters for container types
    @staticmethod
    def _get_list_value(container):
        values = []
        for widget in container._input_widgets:
            values.append(TypeInputFactory.get_input_value(widget))
        return values
    
    @staticmethod
    def _get_dict_value(container):
        result = {}
        for key_widget, value_widget in zip(container._key_widgets, container._value_widgets):
            key = TypeInputFactory.get_input_value(key_widget)
            value = TypeInputFactory.get_input_value(value_widget)
            # Ensure key is hashable
            if not isinstance(key, (str, int, float, bool)):
                key = str(key)
            result[key] = value
        return result

    @staticmethod
    def _set_widget_value(widget, value):
        """Set a value on a widget, handling different widget types"""
        if isinstance(widget, QtWidgets.QCheckBox):
            widget.setChecked(bool(value))
        elif isinstance(widget, QtWidgets.QSpinBox):
            try:
                widget.setValue(int(value))
            except (ValueError, TypeError):
                pass
        elif isinstance(widget, QtWidgets.QDoubleSpinBox):
            try:
                widget.setValue(float(value))
            except (ValueError, TypeError):
                pass
        elif isinstance(widget, QtWidgets.QLineEdit):
            widget.setText(str(value))
        elif hasattr(widget, '_type_input_type'):
            # For container widgets, we'd need more complex logic
            # For now, just set text if it's a line edit fallback
            if hasattr(widget, 'setText'):
                widget.setText(str(value))

class aboutPage(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()

        # window settings
        self.sizes:tuple[int,int] = (400, 400) #(width, size), in pixels
        self.setWindowTitle(f"About {PROJECTNAME}")
        self.icon = QtGui.QPixmap(config.icon)
        self.setWindowIcon(self.icon)
        self.setFixedSize(self.sizes[0], self.sizes[1])

        #image
        self.image = QtWidgets.QLabel(self)
        pixmap = QtGui.QPixmap(config.icon).scaled(256,256)
        self.image.setPixmap(pixmap)
        
        #text
        self.title = QtWidgets.QLabel(PROJECTNAME)
        self.title.setStyleSheet("font-weight: bold")
        self.title.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.lbl = QtWidgets.QLabel(f"An extensive tool for automatic content creation\nVersion {VERSION}\nBy {AUTHORS}")
        self.lbl.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)

        self.layout = QtWidgets.QVBoxLayout()
        self.layout.addWidget(self.image)
        self.layout.addSpacing(20)
        self.layout.addWidget(self.title)
        self.layout.addSpacing(10)
        self.layout.addWidget(self.lbl)
        self.setLayout(self.layout)
        self.layout.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)


class singleUI(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        
        self.sizes:tuple[int,int] = config.windowSize #(width, size), in pixels

        #create splitters
        self.hSplitter = QtWidgets.QSplitter(QtCore.Qt.Orientation.Horizontal)
        self.vSplitter = QtWidgets.QSplitter(QtCore.Qt.Orientation.Vertical)

        # widgets that will be added
        self.modulesLbl = QtWidgets.QLabel("Modules")
        self.modulesLbl.setStyleSheet("font-weight: bold")
        self.moduleList = QtWidgets.QListWidget()
        self.updateModulesBtn = QtWidgets.QPushButton("Reload")
        self.consoleLbl = QtWidgets.QLabel("Console")
        self.consoleLbl.setStyleSheet("font-weight: bold")
        self.consoleTxt = QtWidgets.QPlainTextEdit()
        self.consoleTxt.setReadOnly(True)

        # connect actions
        self.moduleList.itemActivated.connect(self.updateSelectedModule)
        self.updateModulesBtn.clicked.connect(self.updateModuleList)

        # add widgets to left panel
        self.left = QtWidgets.QWidget()
        self.leftLayout = QtWidgets.QVBoxLayout(self.left)
        self.leftLayout.addWidget(self.modulesLbl)
        self.leftLayout.addWidget(self.moduleList)
        self.leftLayout.addWidget(self.updateModulesBtn)

        # add widgets to right panel
        self.right = QtWidgets.QWidget()
        self.rightLayout = QtWidgets.QVBoxLayout(self.right)

        #add widgets to bottom panel
        self.bottom = QtWidgets.QWidget()
        self.bottomLayout = QtWidgets.QVBoxLayout(self.bottom)
        self.bottomLayout.addWidget(self.consoleLbl)
        self.bottomLayout.addWidget(self.consoleTxt)

        # finalize splitter
        self.hSplitter.addWidget(self.left)
        self.hSplitter.addWidget(self.right)
        self.hSplitter.setSizes([self.sizes[0]*0.2, self.sizes[0]*0.8])
        self.vSplitter.addWidget(self.hSplitter)
        self.vSplitter.addWidget(self.bottom)
        self.vSplitter.setSizes([self.sizes[1]*0.7, self.sizes[1]*0.3])
        self.layout = QtWidgets.QVBoxLayout()
        self.layout.addWidget(self.vSplitter)
        self.setLayout(self.layout)

        # run init functions
        self.setupConsoleRedirect()
        self.selectedModule: str = ""
        self.moduleParams:list[QtWidgets.QWidget] = []
        self.updateModuleList()

    @QtCore.Slot()
    def updateModuleList(self):
        self.moduleList.clear()
        modules.loadModules()
        for module in modules.modules:
            self.moduleList.addItem(QtWidgets.QListWidgetItem(module))
        self.renderModule("")
        self.selectedModule = ""
        print(f"Loaded {len(modules.modules)} modules.")
    
    @QtCore.Slot()
    def updateSelectedModule(self, item):
        self.selectedModule = item.text()
        self.renderModule(self.selectedModule)
    
    @QtCore.Slot()
    def executeModule(self):
        print(f"Executing {self.selectedModule}...")

        # prepare params
        params = {}
        args = modules.modules[self.selectedModule].requiredArgs
        for i in range(len(args)):
            params[args[i][0]] = TypeInputFactory.get_input_value(self.moduleParams[i])

        # UI busy lock
        self.hSplitter.setEnabled(False)
        QtWidgets.QApplication.setOverrideCursor(QtCore.Qt.CursorShape.WaitCursor)

        # Create worker thread
        self.worker = ModuleWorker(self.selectedModule, params)
        self.worker.result.connect(self.taskFinished)
        self.worker.error.connect(self.taskErrored)
        self.worker.output.connect(self.consoleTxt.appendPlainText)

        # Start background thread
        self.worker.start()

    def taskFinished(self, result):
        print("\nReturned:\n", result)

        # Restore UI
        self.hSplitter.setEnabled(True)
        QtWidgets.QApplication.restoreOverrideCursor()
        # Clean up worker
        self.worker = None

    def taskErrored(self, exception):
        print("ERROR:", exception)

        # Restore UI
        self.hSplitter.setEnabled(True)
        QtWidgets.QApplication.restoreOverrideCursor()

        # Clean up worker
        self.worker = None

    def renderModule(self, moduleName: str):
        """
        Render given module to the right layout. If moduleName == "", it will render an empty window.
        """
    
        self.moduleParams = []

        # Create new right widget
        right = QtWidgets.QWidget()
        rightLayout = QtWidgets.QVBoxLayout(right)  # Pass 'right' as parent

        if moduleName != "":
            module:modules.BaseModule = modules.modules[moduleName]

            # Create scroll area
            scrollArea = QtWidgets.QScrollArea()
            scrollArea.setWidgetResizable(True)
            scrollArea.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarPolicy.ScrollBarAsNeeded)
            scrollArea.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarPolicy.ScrollBarAsNeeded)

            # Add widgets to the new layout
            descLbl = QtWidgets.QLabel(module.description)
            descLbl.setWordWrap(True)
            nameLbl = QtWidgets.QLabel(module.name)
            nameLbl.setStyleSheet("font-weight: bold")
            rightLayout.addWidget(nameLbl)
            rightLayout.addWidget(descLbl)
            
            i:int = 0
            for v in module.requiredArgs: #TO FIX
                self.moduleParams.append(TypeInputFactory.create_input_widget(v[1]))
                rightLayout.addWidget(QtWidgets.QLabel(f"{v[0]} - {v[1].__name__}"))
                rightLayout.addWidget(self.moduleParams[i])
                i += 1
            
            rightLayout.addStretch()
            execBtn = QtWidgets.QPushButton("Execute")
            execBtn.clicked.connect(self.executeModule)
            rightLayout.addWidget(execBtn)
            
            scrollArea.setWidget(right)
        else:
            rightLayout.addWidget(QtWidgets.QLabel("Click any module to view its settings."))
            scrollArea = right
        
        # Replace the widget in the splitter
        old_right = self.hSplitter.widget(1)
        if old_right:
            old_right.deleteLater()  # Clean up the old widget
        
        
        self.hSplitter.replaceWidget(1, scrollArea)
        self.right = scrollArea  # Update reference to the current right widget

    def setupConsoleRedirect(self):
        # Redirect stdout and stderr
        sys.stdout = QTextEditStream(self.consoleTxt)
        sys.stderr = QTextEditStream(self.consoleTxt)
        print(f"{PROJECTNAME.upper()} - Internal console stream initialized.")


class MainWindow(QtWidgets.QMainWindow):
        def __init__(self):
            super().__init__()
            
            self.setCentralWidget(singleUI())
            # window settings
            self.sizes:tuple[int,int] = config.windowSize #(width, size), in pixels
            self.setWindowTitle(f"{PROJECTNAME} - Single")
            self.icon = QtGui.QPixmap(config.icon)
            self.setWindowIcon(self.icon)
            self.resize(self.sizes[0], self.sizes[1])

            # Now you can add real toolbars
            self.create_toolbar()
        
        def create_toolbar(self):
            toolbar = QtWidgets.QToolBar("Main Toolbar")
            self.addToolBar(toolbar)
            
            config = QtGui.QAction("Config",self)
            config.triggered.connect(self.openConfigPage)  # Connect to your method
            toolbar.addAction(config)  # Add to toolbar

            config = QtGui.QAction("Help",self)
            config.triggered.connect(self.openManual)  # Connect to your method
            toolbar.addAction(config)  # Add to toolbar

            config = QtGui.QAction("About",self)
            config.triggered.connect(self.openAboutPage)  # Connect to your method
            toolbar.addAction(config)  # Add to toolbar
        
        @QtCore.Slot()
        def openAboutPage(self):
            self.about = aboutPage()
            # Center the about window on the main window
            self.about.setGeometry(
                QtWidgets.QStyle.alignedRect(
                    QtCore.Qt.LayoutDirection.LeftToRight,
                    QtCore.Qt.AlignmentFlag.AlignCenter,
                    self.about.size(),
                    self.geometry()  # Main window's geometry
                )
            )
            self.about.show()

        @QtCore.Slot()
        def openConfigPage(self):
            openFileWithDefaultEditor(f"{config.p}config.py")

        @QtCore.Slot()
        def openManual(self):
            openFileWithDefaultEditor(config.manual)

def main(mode:str, gui:bool):
    clearTemp()
    match mode:
        case "single":
            if gui:
                app = QtWidgets.QApplication([])
                
                app.setStyleSheet(loadStylesheet(config.style))                
                
                widget = MainWindow()
                widget.show()

                sys.exit(app.exec())
            else:
                #THIS IS ALL PLACEHOLDER CODE FOR TESTING PURPOSES!
                print(f"""
    Welcome to {PROJECTNAME} - an extensive tool for automatic content creation!
    A video will be generated from the reddit link you provide.
    Use 'exit' to exit this program.

                        """)
                e = True
                print("Loading modules...")
                modules.loadModules()
                print(f"Done! Loaded {len(modules.modules)} modules.")
                while e:
                    inp = input(">>> ")
                    if inp.startswith("exit"):
                        e = False
                    else: 
                        modules.executeModule("RedditVideoGenerator",url=inp,commentsOrDesc=False,accountName=config.accountName)
        case "master":
            print("This mode hasn't been implemented yet.")
        case "worker":
            print("This mode hasn't been implemented yet.")

if __name__ == "__main__":
    if len(sys.argv) != 3 or sys.argv[1] not in ["master","worker","single"] or sys.argv[2] not in ["gui","nogui"]:
        print(f"""{PROJECTNAME.upper()} --- Program for automatic content creation

Usage:
python3 main.py [MODE] [GUI]
    MODE='single': run the program entirely on this machine
    MODE='master': use this machine as a master node to run the program on other machines
    MODE='worker': use this machine as a worker node in a network controlled by a master node
    GUI='gui': starts the program with a GUI (only for 'single' and 'master')
    GUI='nogui': starts the program in CLI mode
            """)
    else:
        g = sys.argv[2] == "gui" #g = True if GUI mode was required, False if it wasn't
        main(sys.argv[1],g)
