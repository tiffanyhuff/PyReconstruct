from PySide6.QtWidgets import (
    QWidget, 
    QDialog, 
    QDialogButtonBox, 
    QHBoxLayout, 
    QLabel, 
    QLineEdit, 
    QVBoxLayout, 
    QComboBox, 
    QPushButton, 
    QInputDialog, 
    QCheckBox,
    QRadioButton
)
from PySide6.QtCore import Qt

from modules.gui.color_button import ColorButton

from modules.pyrecon.obj_group_dict import ObjGroupDict
from modules.pyrecon.trace import Trace


class TraceDialog(QDialog):

    def __init__(self, parent : QWidget, traces : list[Trace]=[], name=None, include_radius=False, pos=None):
        """Create an attribute dialog.
        
            Params:
                parent (QWidget): the parent widget
                traces (list): a list of traces
                pos (tuple): the point to create the dialog
        """
        super().__init__(parent)

        # move to desired position
        if pos:
            self.move(*pos)

        self.include_radius = include_radius

        # get the display values if traces have been provided
        if traces:
            trace = traces[0]
            name = trace.name
            color = trace.color
            tags = trace.tags
            fill_style, fill_condition = trace.fill_mode

            # keep track of the traces passed
            self.traces = traces

            # only include radius for editing single palette traces
            if self.include_radius:
                assert(len(traces) == 1)
            
            for trace in traces[1:]:
                if trace.name != name:
                    name = "*"
                if trace.color != color:
                    color = None
                if trace.tags != tags:
                    tags = set()
                if trace.fill_mode[0] != fill_style:
                    fill_style = None
                if trace.fill_mode[1] != fill_condition:
                    fill_condition = None
        else:
            if not name:
                name = "*"
            color = None
            tags = set()
            fill_style = None
            fill_condition = None

        self.setWindowTitle("Set Attributes")

        self.name_row = QHBoxLayout()
        self.name_text = QLabel(self)
        self.name_text.setText("Name:")
        self.name_input = QLineEdit(self)
        self.name_input.setText(name)
        self.name_row.addWidget(self.name_text)
        self.name_row.addWidget(self.name_input)

        self.color_row = QHBoxLayout()
        self.color_text = QLabel(self)
        self.color_text.setText("Color:")
        self.color_input = ColorButton(color, parent)
        self.color_row.addWidget(self.color_text)
        self.color_row.addWidget(self.color_input)
        self.color_row.addStretch()

        self.tags_row = QHBoxLayout()
        self.tags_text = QLabel(self)
        self.tags_text.setText("Tags:")
        self.tags_input = QLineEdit(self)
        self.tags_input.setText(", ".join(tags))
        self.tags_row.addWidget(self.tags_text)
        self.tags_row.addWidget(self.tags_input)

        self.condition_row = QHBoxLayout()
        self.condition_input = QCheckBox("Fill when selected")
        if fill_condition == "selected":
            self.condition_input.setChecked(True)
        else:
            self.condition_input.setChecked(False)
        self.condition_row.addWidget(self.condition_input)

        self.style_row = QHBoxLayout()
        self.style_text = QLabel(self)
        self.style_text.setText("Fill:")
        self.style_none = QRadioButton("None")
        self.style_none.toggled.connect(self.checkDisplayCondition)
        self.style_transparent = QRadioButton("Transparent")
        self.style_transparent.toggled.connect(self.checkDisplayCondition)
        self.style_solid = QRadioButton("Solid")
        self.style_solid.toggled.connect(self.checkDisplayCondition)
        if fill_style == "none":
            self.style_none.setChecked(True)
        elif fill_style == "transparent":
            self.style_transparent.setChecked(True)
        elif fill_style == "solid":
            self.style_solid.setChecked(True)
        else:
            self.checkDisplayCondition()
        self.style_row.addWidget(self.style_text)
        self.style_row.addWidget(self.style_none)
        self.style_row.addWidget(self.style_transparent)
        self.style_row.addWidget(self.style_solid)

        if self.include_radius:
            self.stamp_size_row = QHBoxLayout()
            self.stamp_size_text = QLabel(self)
            self.stamp_size_text.setText("Stamp radius (microns):")
            self.stamp_size_input = QLineEdit(self)
            self.stamp_size_input.setText(str(round(trace.getRadius(), 6)))
            self.stamp_size_row.addWidget(self.stamp_size_text)
            self.stamp_size_row.addWidget(self.stamp_size_input)

        QBtn = QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        self.buttonbox = QDialogButtonBox(QBtn)
        self.buttonbox.accepted.connect(self.accept)
        self.buttonbox.rejected.connect(self.reject)

        self.vlayout = QVBoxLayout()
        self.vlayout.setSpacing(10)
        self.vlayout.addLayout(self.name_row)
        self.vlayout.addLayout(self.color_row)
        self.vlayout.addLayout(self.tags_row)
        self.vlayout.addLayout(self.style_row)
        self.vlayout.addLayout(self.condition_row)
        if self.include_radius:
            self.vlayout.addLayout(self.stamp_size_row)
        self.vlayout.addWidget(self.buttonbox)

        self.setLayout(self.vlayout)
    
    def checkDisplayCondition(self):
        """Determine whether the "fill when selected" checkbox should be displayed."""
        if self.style_transparent.isChecked() or self.style_solid.isChecked():
            self.condition_input.show()
        else:
            self.condition_input.hide()
    
    def exec(self):
        """Run the dialog."""
        confirmed = super().exec()
        if confirmed:
            retlist = []

            # name
            name = self.name_input.text()
            if name == "*" or name == "":
                name = None
            retlist.append(name)

            color = self.color_input.getColor()
            retlist.append(color)

            # color
            tags = self.tags_input.text().split(", ")
            if tags == [""]:
                tags = None
            else:
                tags = set(tags)
            retlist.append(tags)
            
            # fill mode
            if self.style_none.isChecked():
                style = "none"
                condition = "none"
            else:
                if self.style_transparent.isChecked():
                    style = "transparent"
                elif self.style_solid.isChecked():
                    style = "solid"
                else:
                    style = None
                    condition = None
                if self.condition_input.isChecked():
                    condition = "selected"
                else:
                    condition = "unselected"
            retlist.append((style, condition))

            # radius
            if self.include_radius:
                stamp_size = self.stamp_size_input.text()
                try:
                    stamp_size = float(stamp_size)
                except ValueError:
                    stamp_size = None
                retlist.append(stamp_size)
            
            return tuple(retlist), True
        
        # user pressed cancel
        else:
            return None, False

class ObjectGroupDialog(QDialog):

    def __init__(self, parent : QWidget, objgroupdict : ObjGroupDict, new_group=True):
        """Create an object group dialog.
        
            Params:
                parent (QWidget): the parent widget
                objgroupdict (ObjGroupDict): object containing information on object groups
                new_group (bool): whether or not to include new group button
        """
        super().__init__(parent)

        self.setWindowTitle("Object Group")

        self.group_row = QHBoxLayout()
        self.group_text = QLabel(self)
        self.group_text.setText("Group:")
        self.group_input = QComboBox(self)
        self.group_input.addItem("")
        self.group_input.addItems(sorted(objgroupdict.getGroupList()))
        self.group_input.resize(self.group_input.sizeHint())
        self.group_row.addWidget(self.group_text)
        self.group_row.addWidget(self.group_input)
        if new_group:
            self.newgroup_bttn = QPushButton(self, "new_group", text="New Group...")
            self.newgroup_bttn.clicked.connect(self.newGroup)
            self.group_row.addWidget(self.newgroup_bttn)

        QBtn = QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        self.buttonbox = QDialogButtonBox(QBtn)
        self.buttonbox.accepted.connect(self.accept)
        self.buttonbox.rejected.connect(self.reject)

        self.vlayout = QVBoxLayout()
        self.vlayout.setSpacing(10)
        self.vlayout.addLayout(self.group_row)
        self.vlayout.addSpacing(10)
        self.vlayout.addWidget(self.buttonbox)

        self.setLayout(self.vlayout)
    
    def newGroup(self):
        """Add a new group to the list."""
        new_group_name, confirmed = QInputDialog.getText(self, "New Object Group", "New group name:")
        if not confirmed:
            return
        self.group_input.addItem(new_group_name)
        self.group_input.setCurrentText(new_group_name)
        self.group_input.resize(self.group_input.sizeHint())
        
    def exec(self):
        """Run the dialog."""
        confirmed = super().exec()
        text = self.group_input.currentText()
        if confirmed and text:
            return self.group_input.currentText(), True
        else:
            return "", False


class TableColumnsDialog(QDialog):

    def __init__(self, parent, columns : dict):
        """Create an object table column dialog.
        
            Params:
                parent (QWidget): the parent widget for the dialog
                columns (dict): the existing columns and their status
        """
        super().__init__(parent)

        self.setWindowTitle("Table Columns")

        self.title_text = QLabel(self)
        self.title_text.setText("Table columns:")

        self.cbs = []
        for c in columns:
            c_cb = QCheckBox(self)
            c_cb.setText(c)
            c_cb.setChecked(columns[c])
            self.cbs.append(c_cb)

        QBtn = QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        self.buttonbox = QDialogButtonBox(QBtn)
        self.buttonbox.accepted.connect(self.accept)
        self.buttonbox.rejected.connect(self.reject)

        self.vlayout = QVBoxLayout(self)
        self.vlayout.setSpacing(10)
        self.vlayout.addWidget(self.title_text)
        for c_row in self.cbs:
            self.vlayout.addWidget(c_row)
        self.vlayout.addWidget(self.buttonbox)

        self.setLayout(self.vlayout)
    
    def exec(self):
        """Run the dialog."""
        confirmed = super().exec()
        if confirmed:
            columns = {}
            for cb in self.cbs:
                columns[cb.text()] = cb.isChecked()
            return columns, True
        else:
            return {}, False


class AlignmentDialog(QDialog):

    def __init__(self, parent : QWidget, alignment_names : list):
        """Create an object group dialog.
        
            Params:
                parent (QWidget): the parent widget
                alignment_names (list): the list of alignments
        """
        super().__init__(parent)

        self.setWindowTitle("Change Alignment")

        self.align_row = QHBoxLayout()
        self.align_text = QLabel(self)
        self.align_text.setText("Alignment:")
        self.align_input = QComboBox(self)
        self.align_input.addItem("")
        self.align_input.addItems(sorted(alignment_names))
        self.align_input.resize(self.align_input.sizeHint())
        self.newalign_bttn = QPushButton(self, "new_alignment", text="New Alignment...")
        self.newalign_bttn.clicked.connect(self.newAlignment)
        self.align_row.addWidget(self.align_text)
        self.align_row.addWidget(self.align_input)
        self.align_row.addWidget(self.newalign_bttn)

        QBtn = QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        self.buttonbox = QDialogButtonBox(QBtn)
        self.buttonbox.accepted.connect(self.accept)
        self.buttonbox.rejected.connect(self.reject)

        self.vlayout = QVBoxLayout()
        self.vlayout.setSpacing(10)
        self.vlayout.addLayout(self.align_row)
        self.vlayout.addSpacing(10)
        self.vlayout.addWidget(self.buttonbox)

        self.setLayout(self.vlayout)
    
    def newAlignment(self):
        """Add a new alignment to the list."""
        new_group_name, confirmed = QInputDialog.getText(self, "New Alignment", "New alignment name:")
        if not confirmed:
            return
        self.align_input.addItem(new_group_name)
        self.align_input.setCurrentText(new_group_name)
        self.align_input.resize(self.align_input.sizeHint())
        
    def exec(self):
        """Run the dialog."""
        confirmed = super().exec()
        text = self.align_input.currentText()
        if confirmed and text:
            return self.align_input.currentText(), True
        else:
            return "", False

class Object3DDialog(QDialog):

    def __init__(self, parent, type3D=None, opacity=None):
        """Create a dialog for 3D object settings."""
        super().__init__(parent)

        self.setWindowTitle("3D Object Settings")

        self.type_row = QHBoxLayout()
        self.type_text = QLabel(self)
        self.type_text.setText("3D Type:")
        self.type_input = QComboBox(self)
        type_list = ["surface", "spheres"]
        if not type3D:
            self.type_input.addItem("")
        self.type_input.addItems(type_list)
        if type3D:
            self.type_input.setCurrentText(type3D)
        self.type_input.resize(self.type_input.sizeHint())
        self.type_row.addWidget(self.type_text)
        self.type_row.addWidget(self.type_input)

        self.opacity_row = QHBoxLayout()
        self.opacity_text = QLabel(self)
        self.opacity_text.setText("Opacity (0-1):")
        self.opacity_input = QLineEdit(self)
        if opacity:
            self.opacity_input.setText(str(round(opacity, 6)))
        self.opacity_row.addWidget(self.opacity_text)
        self.opacity_row.addWidget(self.opacity_input)

        QBtn = QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        self.buttonbox = QDialogButtonBox(QBtn)
        self.buttonbox.accepted.connect(self.accept)
        self.buttonbox.rejected.connect(self.reject)

        self.vlayout = QVBoxLayout()
        self.vlayout.setSpacing(10)
        self.vlayout.addLayout(self.type_row)
        self.vlayout.addLayout(self.opacity_row)
        self.vlayout.addWidget(self.buttonbox)

        self.setLayout(self.vlayout)
    
    def exec(self):
        "Run the dialog."
        confirmed = super().exec()
        if confirmed:
            type3D = self.type_input.currentText()
            opacity = self.opacity_input.text()
            try:
                opacity = float(opacity)
            except ValueError:
                opacity = None
            return (type3D, opacity), confirmed
        else:
            return None, None


class BCDialog(QDialog):

    def __init__(self, parent):
        """Create a dialog for brightness/contrast."""
        super().__init__(parent)

        self.setWindowTitle("Set Brightness/Contrast")

        self.b_row = QHBoxLayout()
        self.b_text = QLabel(self)
        self.b_text.setText("Brightness (-100 - 100):")
        self.b_input = QLineEdit(self)
        self.b_row.addWidget(self.b_text)
        self.b_row.addWidget(self.b_input)

        self.c_row = QHBoxLayout()
        self.c_text = QLabel(self)
        self.c_text.setText("Contrast (-100 - 100):")
        self.c_input = QLineEdit(self)
        self.c_row.addWidget(self.c_text)
        self.c_row.addWidget(self.c_input)

        QBtn = QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        self.buttonbox = QDialogButtonBox(QBtn)
        self.buttonbox.accepted.connect(self.accept)
        self.buttonbox.rejected.connect(self.reject)

        self.vlayout = QVBoxLayout()
        self.vlayout.setSpacing(10)
        self.vlayout.addLayout(self.b_row)
        self.vlayout.addLayout(self.c_row)
        self.vlayout.addWidget(self.buttonbox)

        self.setLayout(self.vlayout)
    
    def exec(self):
        "Run the dialog."
        confirmed = super().exec()
        if confirmed:
            b = self.b_input.text()
            c = self.c_input.text()
            try:
                b = int(b)
                if abs(b) > 100:
                    b = None
            except ValueError:
                b = None
            try:
                c = int(c)
                if abs(c) > 100:
                    c = None
            except ValueError:
                c = None
            return (b, c), confirmed
        else:
            return (None, None), False


        