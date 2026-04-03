import os
import shutil
import basemodule
import config
import sys
from io import TextIOBase
import modules
from PySide6 import QtCore, QtWidgets, QtGui
from gui import TypeInputFactory, TypeOutputFactory, openFileWithDefaultEditor

PROJECTNAME = "Opifex"
VERSION = "0.1.9" #current version to show and use in the project, [MAIN].[MINOR].[PATCH]
AUTHORS = "prtp (Vprtp on GitHub)"

def clearTemp(dir:str=config.tempFolder):
    shutil.rmtree(dir)
    os.mkdir(dir)

def loadStylesheet(path: str) -> str:
    with open(path, "r", encoding="utf-8") as f:
        return f.read()

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


class aboutPage(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()

        # window settings
        self.sizes:tuple[int,int] = (400, 425) #(width, height), in pixels
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
        self.returnSplitter = QtWidgets.QSplitter(QtCore.Qt.Orientation.Horizontal)

        # widgets that will be added
        self.modulesLbl = QtWidgets.QLabel("Modules")
        self.modulesLbl.setStyleSheet("font-weight: bold")
        self.moduleList = QtWidgets.QListWidget()
        self.updateModulesBtn = QtWidgets.QPushButton("Reload")
        self.consoleLbl = QtWidgets.QLabel("Console")
        self.consoleLbl.setStyleSheet("font-weight: bold")
        self.consoleTxt = QtWidgets.QPlainTextEdit()
        self.consoleTxt.setReadOnly(True)
        self.clearConsoleBtn = QtWidgets.QPushButton("Clear")
        self.clearConsoleBtn.setMaximumWidth(100)

        # connect actions
        self.moduleList.itemActivated.connect(self.updateSelectedModule)
        self.updateModulesBtn.clicked.connect(self.updateModuleList)
        self.clearConsoleBtn.clicked.connect(self.clearConsole)

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
        consoleTitle = QtWidgets.QWidget()
        consoleTitleLayout = QtWidgets.QHBoxLayout(consoleTitle)
        consoleTitleLayout.setAlignment(QtCore.Qt.AlignmentFlag.AlignVCenter)
        consoleTitleLayout.addWidget(self.consoleLbl)
        consoleTitleLayout.addWidget(self.clearConsoleBtn)
        self.bottomLayout.addWidget(consoleTitle)
        self.bottomLayout.addWidget(self.consoleTxt)

        #add widgets to return panel
        self.returns = QtWidgets.QWidget()
        self.returnsLayout = QtWidgets.QVBoxLayout(self.returns)

        # finalize splitter
        self.hSplitter.addWidget(self.left)
        self.hSplitter.addWidget(self.right)
        self.hSplitter.setSizes([int(self.sizes[0]*0.175), int(self.sizes[0]*0.625)])
        self.vSplitter.addWidget(self.hSplitter)
        self.vSplitter.addWidget(self.bottom)
        self.vSplitter.setSizes([int(self.sizes[1]*0.7), int(self.sizes[1]*0.3)])
        self.returnSplitter.addWidget(self.vSplitter)
        self.returnSplitter.addWidget(self.returns)
        self.returnSplitter.setSizes([int(self.sizes[0]*0.8), int(self.sizes[0]*0.2)])
        self.layout = QtWidgets.QVBoxLayout()
        self.layout.addWidget(self.returnSplitter)
        self.setLayout(self.layout)

        # run init functions
        self.setupConsoleRedirect() #REMEMBER TO DISABLE THIS WHEN DEBUGGING AND A CRASH HAPPENS ON STARTUP, OR WHEN TRYING TO READ OUTPUT FROM EXTERNAL PROCESSES
        self.selectedModule: str = ""
        self.moduleParams:list[QtWidgets.QWidget] = []
        self.updateModuleList()

    @QtCore.Slot()
    def updateModuleList(self):
        self.moduleList.clear()
        num:int = modules.loadLibs()
        modules.loadModules()
        for module in modules.modules:
            self.moduleList.addItem(QtWidgets.QListWidgetItem(module))
        self.renderModule("")
        self.renderResult(None)
        self.selectedModule = ""
        print(f"Loaded {len(modules.modules)} modules and {num} libraries.")
    
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
    
    @QtCore.Slot()
    def clearConsole(self):
        self.consoleTxt.setPlainText("")

    def taskFinished(self, result):
        print("\nReturned:\n", result)
        self.renderResult(result)
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

    def renderResult(self, result:basemodule.ModuleResultType|None) -> None:
        """
        Render given module result to the return layout. If result == None, it will render an empty window.
        """
        #create new result widget
        resultWidget = QtWidgets.QWidget(self.returnSplitter)
        resultLayout = QtWidgets.QVBoxLayout(resultWidget)
        if result == None: #put placeholder text if no module was executed
            placeholderLbl = QtWidgets.QLabel("After executing a module, the result will be shown here.")
            placeholderLbl.setWordWrap(True)
            resultLayout.addWidget(placeholderLbl)
            scrollArea = result
        else:
            # Create scroll area
            scrollArea = QtWidgets.QScrollArea()
            scrollArea.setWidgetResizable(True)
            scrollArea.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarPolicy.ScrollBarAsNeeded)
            scrollArea.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarPolicy.ScrollBarAsNeeded)

            if result.exception != None: #add exception info in case of an exception
                exceptionTitleLbl = QtWidgets.QLabel("Exception")
                exceptionTitleLbl.setAlignment(QtCore.Qt.AlignCenter)
                exceptionTitleLbl.setStyleSheet("font-weight: bold")
                exceptionLbl = TypeOutputFactory.create_output_widget(result.exception)
                resultLayout.addWidget(exceptionTitleLbl)
                resultLayout.addWidget(exceptionLbl)
            dataLbl = QtWidgets.QLabel("Module Result Data")

            dataLbl.setAlignment(QtCore.Qt.AlignCenter)
            dataLbl.setStyleSheet("font-weight: bold")
            resultLayout.addWidget(dataLbl)
            for key in result.data.keys():
                valueNameLbl = QtWidgets.QLabel(f"{key} - {type(result.data[key]).__name__}")
                valueNameLbl.setStyleSheet("font-weight: bold")
                valueWidget = TypeOutputFactory.create_output_widget(result.data[key])
                resultLayout.addWidget(valueNameLbl)
                resultLayout.addWidget(valueWidget)

            resultLayout.addStretch()
            scrollArea.setWidget(resultWidget)
        # Replace the widget in the splitter
        old_result = self.returnSplitter.widget(1)
        if old_result:
            old_result.deleteLater()  # Clean up the old widget
        
        self.returnSplitter.replaceWidget(1, scrollArea)
        self.returns = scrollArea

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
            for v in module.requiredArgs:
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

            # toolbars
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
                print("Loading libraries...")
                num:int = modules.loadLibs()
                print(f"Done! Loaded {num} libraries.")
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
