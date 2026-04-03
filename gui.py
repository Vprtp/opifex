from PySide6 import QtCore, QtWidgets, QtGui
import pathlib
from typing import Any
from typing import get_origin, get_args
import subprocess
import sys

def openFileWithDefaultEditor(file_path):
    if sys.platform == "win32":
        os.startfile(file_path)
    elif sys.platform == "darwin":  # macOS
        subprocess.run(["open", file_path])
    else:  # Linux and other Unix-like systems
        subprocess.run(["xdg-open", file_path])

class TypeOutputFactory:
    @staticmethod
    def create_output_widget(value, parent:Any=None) -> QtWidgets.QWidget:
        if isinstance(value, int) or isinstance(value, float):
            return TypeOutputFactory._create_num_output(value, parent)
        elif isinstance(value, str):
            return TypeOutputFactory._create_string_output(value, parent)
        elif isinstance(value, bool):
            return TypeOutputFactory._create_bool_output(value, parent)
        elif isinstance(value, list):
            return TypeOutputFactory._create_list_output(value, parent)
        elif isinstance(value, dict):
            return TypeOutputFactory._create_dict_output(value, parent)
        elif isinstance(value, tuple):
            return TypeOutputFactory._create_tuple_output(value, parent)
        elif isinstance(value, pathlib.Path):
            return TypeOutputFactory._create_path_output(value, parent)
        else:
            return TypeOutputFactory._create_string_output(str(value), parent)

    @staticmethod
    def _create_string_output(value:str, parent) -> QtWidgets.QWidget:
        widget = QtWidgets.QLabel(parent)
        widget.setText(value)
        widget.setWordWrap(True) #make label multi-line
        widget.setTextInteractionFlags(QtCore.Qt.TextInteractionFlag.TextSelectableByMouse | QtCore.Qt.TextInteractionFlag.TextSelectableByKeyboard) #make label selectable and copiable
        return widget

    @staticmethod
    def _create_num_output(value:int|float, parent) -> QtWidgets.QWidget:
        return TypeOutputFactory._create_string_output(str(value), parent)

    @staticmethod
    def _create_bool_output(value:bool, parent) -> QtWidgets.QWidget:
        if value:
            return TypeOutputFactory._create_string_output("True", parent)
        else:
            return TypeOutputFactory._create_string_output("False", parent)

    @staticmethod
    def _create_list_output(value:list[Any], parent) -> QtWidgets.QWidget:
        container = QtWidgets.QWidget(parent)
        layout = QtWidgets.QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Create scroll area for items
        scroll = QtWidgets.QScrollArea()
        scroll.setProperty("class", "value_container")
       
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll.setMinimumHeight(100)
        
        scroll_widget = QtWidgets.QWidget()
        scroll_layout = QtWidgets.QVBoxLayout(scroll_widget)
        scroll_layout.setContentsMargins(0, 0, 0, 0)
        
        scroll.setWidget(scroll_widget)
        layout.addWidget(scroll)
        
        for val in value:
            scroll_layout.addWidget(TypeOutputFactory.create_output_widget(val, scroll_widget))
            # Create a horizontal separator line
            separator = QtWidgets.QFrame()
            separator.setFrameShape(QtWidgets.QFrame.HLine)
            separator.setFrameShadow(QtWidgets.QFrame.Sunken)
            scroll_layout.addWidget(separator)
        
        return container

    @staticmethod
    def _create_dict_output(value:dict[Any,Any], parent) -> QtWidgets.QWidget:
        container = QtWidgets.QWidget(parent)
        layout = QtWidgets.QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Create scroll area for items
        scroll = QtWidgets.QScrollArea()
        scroll.setProperty("class", "value_container")
       
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll.setMinimumHeight(100)
        
        scroll_widget = QtWidgets.QWidget()
        scroll_layout = QtWidgets.QVBoxLayout(scroll_widget)
        scroll_layout.setContentsMargins(0, 0, 0, 0)
        
        scroll.setWidget(scroll_widget)
        layout.addWidget(scroll)

        for key in value.keys():
            hWidget = QtWidgets.QWidget(scroll_widget)
            hLayout = QtWidgets.QHBoxLayout(hWidget)
            hLayout.addWidget(TypeOutputFactory.create_output_widget(key, hWidget))
            hLayout.addWidget(TypeOutputFactory.create_output_widget(value[key], hWidget))
            scroll_layout.addWidget(hWidget)
            # Create a horizontal separator line
            separator = QtWidgets.QFrame()
            separator.setFrameShape(QtWidgets.QFrame.HLine)
            separator.setFrameShadow(QtWidgets.QFrame.Sunken)
            scroll_layout.addWidget(separator)

        return container

    @staticmethod
    def _create_tuple_output(value:tuple[Any], parent) -> QtWidgets.QWidget:
        return TypeOutputFactory._create_list_output(value, parent)

    @staticmethod
    def _create_path_output(value:pathlib.Path, parent) -> QtWidgets.QWidget:
        container = QtWidgets.QWidget(parent)
        layout = QtWidgets.QHBoxLayout(container)
        lbl = TypeOutputFactory._create_string_output(str(value.absolute()),container)
        layout.addWidget(lbl)
        btn = QtWidgets.QPushButton("Open")
        btn.clicked.connect(lambda: openFileWithDefaultEditor(str(value.absolute())))
        layout.addWidget(btn)
        return container


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
                return TypeInputFactory._create_tuple_input(parent, item_types=args)
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
            return TypeInputFactory._create_tuple_input(parent, item_types=[str])  # Default to string
        elif value_type == pathlib.Path:
            return TypeInputFactory._create_path_input(parent)
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
                values = [TypeInputFactory.get_input_value(w) for w in widget._field_widgets]
                return tuple(values)
            elif widget._type_input_type == "path":
                return pathlib.Path(widget._line_edit.text())
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
        widget.setRange(-2147483647, 2147483647)
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
        scroll.setProperty("class", "value_container")
 
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll.setMinimumHeight(100)
        scroll.setMaximumHeight(500)
 
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
        
        # Add the item container to the list's layout
        container._items_layout.addWidget(item_container)

        # Create a horizontal separator line
        separator = QtWidgets.QFrame()
        separator.setFrameShape(QtWidgets.QFrame.HLine)
        separator.setFrameShadow(QtWidgets.QFrame.Sunken)
        container._items_layout.addWidget(separator)

        # Store the input widget for value retrieval
        container._input_widgets.append(item_widget)

        # Connect remove button, passing both the item container and its separator
        remove_btn.clicked.connect(
            lambda: TypeInputFactory._remove_list_item(container, item_container, separator)
        )

    @staticmethod
    def _remove_list_item(container, item_container, separator):
        # Remove the associated input widget from the stored list
        # The input widget is a child of item_container
        for i, w in enumerate(container._input_widgets):
            if w.parent() == item_container:
                del container._input_widgets[i]
                break

        # Delete the widgets
        item_container.deleteLater()
        separator.deleteLater()
       

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
        add_btn = QtWidgets.QPushButton(f"+ Add {key_type_name}-{value_type_name} Entry")
        layout.addWidget(add_btn)
        
        scroll = QtWidgets.QScrollArea()
        scroll.setProperty("class", "value_container")
        scroll.setWidgetResizable(True)
        scroll.setMinimumHeight(100)
        scroll.setMaximumHeight(500)
        
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
    def _create_tuple_input(parent, item_types):
        """
        item_types: a tuple of types, one for each element in the tuple
        """
        container = QtWidgets.QWidget(parent)
        container._type_input_type = "tuple"
        container._item_types = item_types #store the sequence of types
        container._field_widgets = []
        layout = QtWidgets.QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        for i, typ in enumerate(item_types):
            sub_layout = QtWidgets.QHBoxLayout()
            #create a label
            label = QtWidgets.QLabel(f"{i}:")
            sub_layout.addWidget(label)
            #create input widget for this field type
            field_widget = TypeInputFactory.create_input_widget(typ)
            sub_layout.addWidget(field_widget, 1)
            layout.addLayout(sub_layout)
            container._field_widgets.append(field_widget)

        return container
    
    @staticmethod
    def _create_path_input(parent):
        widget = QtWidgets.QWidget(parent)
        widget._type_input_type = "path" #identify this widget
        layout = QtWidgets.QHBoxLayout(widget)

        #line edit
        line_edit = QtWidgets.QLineEdit()
        line_edit.setText("") #default is empty
        layout.addWidget(line_edit, 1)
        
        #file browse button
        file_btn = QtWidgets.QPushButton("Select file")
        layout.addWidget(file_btn)

        #dir browse button
        dir_btn = QtWidgets.QPushButton("Select dir")
        layout.addWidget(dir_btn)

        widget._line_edit = line_edit #store for value retrieval

        def browse_file():
            file_path, _ = QtWidgets.QFileDialog.getOpenFileName(widget, "Select File")
            if file_path:
                line_edit.setText(file_path)
        
        def browse_dir():
            dir_path = QtWidgets.QFileDialog.getExistingDirectory(widget, "Select Directory")
            if dir_path:
                line_edit.setText(dir_path)

        file_btn.clicked.connect(browse_file)
        dir_btn.clicked.connect(browse_dir)

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
            if widget._type_input_type == "tuple" and isinstance(value, (tuple,list)) and len(widget._field_widgets):
                for sub_widget, sub_value in zip(widget._field_widgets, value):
                    TypeInputFactory._set_widget_value(sub_widget, sub_value)
            # For container widgets, we'd need more complex logic
            # For now, just set text if it's a line edit fallback
            if hasattr(widget, 'setText'):
                widget.setText(str(value))

