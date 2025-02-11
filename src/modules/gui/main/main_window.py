import os
import time

from PySide6.QtWidgets import (
    QMainWindow, 
    QFileDialog,
    QInputDialog, 
    QApplication,
    QMessageBox, 
    QMenu
)
from PySide6.QtGui import (
    QKeySequence,
    QShortcut,
    QPixmap
)
from PySide6.QtCore import Qt

from .field_widget import FieldWidget

from modules.gui.palette import MousePalette
from modules.gui.dialog import AlignmentDialog
from modules.gui.popup import HistoryWidget
from modules.gui.utils import (
    progbar,
    populateMenuBar,
    populateMenu,
    notify,
    saveNotify,
    unsavedNotify,
    getSaveLocation,
    setMainWindow
)
from modules.backend.func import (
    xmlToJSON,
    jsonToXML,
    importTransforms
)
from modules.datatypes import Series, Transform
from modules.constants import assets_dir, img_dir


class MainWindow(QMainWindow):

    def __init__(self, argv):
        """Constructs the skeleton for an empty main window."""
        super().__init__() # initialize QMainWindow
        self.setWindowTitle("PyReconstruct")

        # set the window icon
        pix = QPixmap(os.path.join(img_dir, "PyReconstruct.ico"))
        self.setWindowIcon(pix)

        # set the main window to be slightly less than the size of the monitor
        screen = QApplication.primaryScreen()
        screen_rect = screen.size()
        x = 50
        y = 80
        w = screen_rect.width() - 100
        h = screen_rect.height() - 160
        self.setGeometry(x, y, w, h)

        # misc defaults
        self.series = None
        self.field = None  # placeholder for field
        self.menubar = None
        self.mouse_palette = None  # placeholder for mouse palette
        self.setMouseTracking(True) # set constant mouse tracking for various mouse modes
        self.is_zooming = False
        self.explorer_dir = ""

        # create status bar at bottom of window
        self.statusbar = self.statusBar()

        # open the series requested from command line
        if len(argv) > 1:
            self.openSeries(jser_fp=argv[1])
        else:
            open_series = Series(
                os.path.join(assets_dir, "welcome_series", "welcome.ser"),
                {0: "welcome.0"}
            )
            self.openSeries(open_series)
        
        self.field.generateView()

        # create menu and shortcuts
        self.createMenuBar()
        self.createContextMenus()
        self.createShortcuts()

        # set the main window as the parent of the progress bar
        setMainWindow(self)

        self.show()

    def createMenuBar(self):
        """Create the menu for the main window."""
        menu = [
            
            {
                "attr_name": "filemenu",
                "text": "File",
                "opts":
                [   
                    ("new_act", "New", "Ctrl+N", self.newSeries),
                    ("open_act", "Open", "Ctrl+O", self.openSeries),
                    None,  # None acts as menu divider
                    ("save_act", "Save", "Ctrl+S", self.saveToJser),
                    ("saveas_act", "Save as...", "", self.saveAsToJser),
                    ("backup_act", "Auto-backup series", "checkbox", self.autoBackup),
                    None,
                    ("fromxml_act", "New from XML series...", "", self.newFromXML),
                    ("exportxml_act", "Export as XML series...", "", self.exportToXML),
                    None,
                    ("import_transforms_act", "Import transformations", "", self.importTransforms),
                    None,
                    ("username_act", "Change username...", "", self.changeUsername),
                    None,
                    ("quit_act", "Quit", "Ctrl+Q", self.close),
                ]
            },

            {
                "attr_name": "editmenu",
                "text": "Edit",
                "opts":
                [
                    ("undo_act", "Undo", "Ctrl+Z", self.field.undoState),
                    ("redo_act", "Redo", "Ctrl+Y", self.field.redoState),
                    None,
                    ("cut_act", "Cut", "Ctrl+X", self.field.cut),
                    ("copy_act", "Copy", "Ctrl+C", self.field.copy),
                    ("paste_act", "Paste", "Ctrl+V", self.field.paste),
                    ("pasteattributes_act", "Paste attributes", "Ctrl+B", self.field.pasteAttributes),
                    None,
                    ("incbr_act", "Increase brightness", "=", lambda : self.editImage(option="brightness", direction="up")),
                    ("decbr_act", "Decrease brightness", "-", lambda : self.editImage(option="brightness", direction="down")),
                    ("inccon_act", "Increase contrast", "]", lambda : self.editImage(option="contrast", direction="up")),
                    ("deccon_act", "Decrease contrast", "[", lambda : self.editImage(option="contrast", direction="down"))
                ]
            },

            {
                "attr_name": "seriesmenu",
                "text": "Series",
                "opts":
                [
                    ("change_src_act", "Find images", "", self.changeSrcDir),
                    None,
                    ("objectlist_act", "Object list", "Ctrl+Shift+O", self.openObjectList),
                    ("ztracelist_act", "Z-trace list", "Ctrl+Shift+Z", self.openZtraceList),
                    ("history_act", "View series history", "", self.viewSeriesHistory),
                    None,
                    ("changealignment_act", "Change alignment", "Ctrl+Shift+A", self.changeAlignment),
                    {
                        "attr_name": "propogatemenu",
                        "text": "Propogate transform",
                        "opts":
                        [
                            ("startpt_act", "Begin propogation", "", lambda : self.field.setPropogationMode(True)),
                            ("endpt_act", "Finish propogation", "", lambda : self.field.setPropogationMode(False)),
                            None,
                            ("proptostart_act", "Propogate to start", "", lambda : self.field.propogateTo(False)),
                            ("proptoend_act", "Propogate to end", "", lambda : self.field.propogateTo(True))
                        ]
                    },
                    None,
                    {
                        "attr_name": "importmenu",
                        "text": "Import",
                        "opts":
                        [
                            ("importtraces_act", "Import traces", "", self.importTraces),
                            ("importzrtraces_act", "Import ztraces", "", self.importZtraces)
                        ]
                    },
                    None,
                    ("calibrate_act", "Calibrate pixel size...", "", self.calibrateMag)           
                ]
            },
            
            {
                "attr_name": "sectionmenu",
                "text": "Section",
                "opts":
                [
                    ("nextsection_act", "Next section", "PgUp", self.incrementSection),
                    ("prevsection_act", "Previous section", "PgDown", lambda : self.incrementSection(down=True)),
                    None,
                    ("sectionlist_act", "Section list", "Ctrl+Shift+S", self.openSectionList),
                    ("goto_act", "Go to section", "Ctrl+G", self.changeSection),
                    ("changetform_act", "Change transformation", "Ctrl+T", self.changeTform),
                    None,
                    ("tracelist_act", "Trace list", "Ctrl+Shift+T", self.openTraceList),
                    ("findcontour_act", "Find contour...", "Ctrl+F", self.field.findContourDialog),
                    None,
                    ("linearalign_act", "Align linear", "", self.field.linearAlign)
                ]
            },

            {
                "attr_name": "viewmenu",
                "text": "View",
                "opts":
                [
                    ("fillopacity_act", "Edit fill opacity...", "", self.setFillOpacity),
                    None,
                    ("homeview_act", "Set view to image", "Home", self.field.home),
                    ("viewmag_act", "View magnification...", "", self.field.setViewMagnification),
                    None,
                    ("paletteside_act", "Palette to other side", "Shift+L", self.mouse_palette.toggleHandedness),
                    ("cornerbuttons_act",  "Toggle corner buttons", "Shift+T", self.mouse_palette.toggleCornerButtons)
                ]
            }
        ]

        if self.menubar:
            self.menubar.close()

        # Populate menu bar with menus and options
        self.menubar = self.menuBar()
        self.menubar.setNativeMenuBar(False)
        populateMenuBar(self, self.menubar, menu)
    
    def createContextMenus(self):
        """Create the right-click menus used in the field."""
        field_menu_list = [
            ("edittrace_act", "Edit attributes...", "Ctrl+E", self.field.traceDialog),
            {
                "attr_name": "modifymenu",
                "text": "Modify",
                "opts":
                [
                    ("mergetraces_act", "Merge traces", "Ctrl+M", self.field.mergeSelectedTraces),
                    None,
                    ("makenegative_act", "Make negative", "", self.field.makeNegative),
                    ("makepositive_act", "Make positive", "", lambda : self.field.makeNegative(False))
                ]
            },
            None,
            {
                "attr_name": "viewmenu",
                "text": "View",
                "opts":
                [
                    ("hidetraces_act", "Hide traces", "Ctrl+H", self.field.hideTraces),
                    ("unhideall_act", "Unhide all traces", "Ctrl+U", self.field.unhideAllTraces),
                    None,
                    ("hideall_act", "Toggle hide all", "H", self.field.toggleHideAllTraces),
                    ("showall_act", "Toggle show all", "A", self.field.toggleShowAllTraces),
                    None,
                    ("blend_act", "Toggle section blend", " ", self.field.toggleBlend),
                ]
            },
            None,
            self.cut_act,
            self.copy_act,
            self.paste_act,
            self.pasteattributes_act,
            None,
            ("selectall_act", "Select all traces", "Ctrl+A", self.field.selectAllTraces),
            ("deselect_act", "Deselect traces", "Ctrl+D", self.field.deselectAllTraces),
            None,
            ("deletetraces_act", "Delete traces", "Del", self.field.backspace)
        ]
        self.field_menu = QMenu(self)
        populateMenu(self, self.field_menu, field_menu_list)

        # organize actions
        self.trace_actions = [
            self.edittrace_act,
            self.modifymenu,
            self.mergetraces_act,
            self.makepositive_act,
            self.makenegative_act,
            self.hidetraces_act,
            self.cut_act,
            self.copy_act,
            self.pasteattributes_act,
            self.deletetraces_act
        ]
        self.ztrace_actions = [
            self.edittrace_act
        ]

    def createShortcuts(self):
        """Create shortcuts that are NOT included in any menus."""
        # domain translate motions
        shortcuts = [
            ("Backspace", self.field.backspace),

            ("/", self.flickerSections),

            ("Ctrl+Left", lambda : self.translate("left", "small")),
            ("Left", lambda : self.translate("left", "med")),
            ("Shift+Left", lambda : self.translate("left", "big")),
            ("Ctrl+Right", lambda : self.translate("right", "small")),
            ("Right", lambda : self.translate("right", "med")),
            ("Shift+Right", lambda : self.translate("right", "big")),
            ("Ctrl+Up", lambda : self.translate("up", "small")),
            ("Up", lambda : self.translate("up", "med")),
            ("Shift+Up", lambda : self.translate("up", "big")),
            ("Ctrl+Down", lambda : self.translate("down", "small")),
            ("Down", lambda : self.translate("down", "med")),
            ("Shift+Down", lambda : self.translate("down", "big"))
        ]

        for kbd, act in shortcuts:
            QShortcut(QKeySequence(kbd), self).activated.connect(act)
    
    def createPaletteShortcuts(self):
        """Create shortcuts associate with the mouse palette."""
        # trace palette shortcuts (1-20)
        trace_shortcuts = []
        for i in range(1, 21):
            sc_str = ""
            if (i-1) // 10 > 0:
                sc_str += "Shift+"
            sc_str += str(i % 10)
            s_switch = (
                sc_str,
                lambda pos=i-1 : self.mouse_palette.activatePaletteButton(pos)
            )
            s_modify = (
                "Ctrl+" + sc_str,
                lambda pos=i-1 : self.mouse_palette.modifyPaletteButton(pos)
            )
            trace_shortcuts.append(s_switch)
            trace_shortcuts.append(s_modify)
        
        # mouse mode shortcuts (F1-F8)
        mode_shortcuts = [
            ("p", lambda : self.mouse_palette.activateModeButton("Pointer")),
            ("z", lambda : self.mouse_palette.activateModeButton("Pan/Zoom")),
            ("k", lambda : self.mouse_palette.activateModeButton("Knife")),
            ("c", lambda : self.mouse_palette.activateModeButton("Closed Trace")),
            ("o", lambda : self.mouse_palette.activateModeButton("Open Trace")),
            ("s", lambda : self.mouse_palette.activateModeButton("Stamp"))
        ]
  
        for kbd, act in (mode_shortcuts + trace_shortcuts):
            QShortcut(QKeySequence(kbd), self).activated.connect(act)
    
    def changeSrcDir(self, new_src_dir : str = None, notify=False):
        """Open a series of dialogs to change the image source directory.
        
            Params:
                new_src_dir (str): the new image directory
                notify (bool): True if user is to be notified with a pop-up
        """
        if notify:
            reply = QMessageBox.question(
                self,
                "Images Not Found",
                "Images not found.\nWould you like to locate them?",
                QMessageBox.Yes,
                QMessageBox.No
            )
            if reply == QMessageBox.No:
                return
        if new_src_dir is None:
            new_src_dir = QFileDialog.getExistingDirectory(
                self,
                "Select folder containing images",
                dir=self.explorer_dir
            )
        if not new_src_dir:
            return
        self.series.src_dir = new_src_dir
        if self.field:
            self.field.reloadImage()
    
    def changeUsername(self, new_name : str = None):
        """Edit the login name used to track history.
        
            Params:
                new_name (str): the new username
        """
        if new_name is None:
            new_name, confirmed = QInputDialog.getText(
                self,
                "Change Login",
                "Enter your desired username:",
                text=os.getlogin()
            )
            if not confirmed or not new_name:
                return
        
        def getlogin():
            return new_name
        
        os.getlogin = getlogin
    
    def setFillOpacity(self, opacity : float = None):
        """Set the opacity of the trace highlight.
        
            Params:
                opacity (float): the new fill opacity
        """
        if opacity is None:
            opacity, confirmed = QInputDialog.getText(
                self,
                "Fill Opacity",
                "Enter fill opacity (0-1):",
                text=str(round(self.series.options["fill_opacity"], 3))
            )
            if not confirmed:
                return
        
        try:
            opacity = float(opacity)
        except ValueError:
            return
        
        if not (0 <= opacity <= 1):
            return
        
        self.series.options["fill_opacity"] = opacity
        self.field.generateView(generate_image=False)

    def openSeries(self, series_obj=None, jser_fp=None):
        """Open an existing series and create the field.
        
            Params:
                series_obj (Series): the series object (optional)
        """
        if not series_obj:  # if series is not provided            
            # get the new series
            new_series = None
            if not jser_fp:
                jser_fp, extension = QFileDialog.getOpenFileName(
                    self,
                    "Select Series",
                    dir=self.explorer_dir,
                    filter="*.jser"
                )
                if jser_fp == "": return  # exit function if user does not provide series
            
            # user has opened an existing series
            if self.series:
                response = self.saveToJser(notify=True)
                if response == "cancel":
                    return

            # check for a hidden series folder
            sdir = os.path.dirname(jser_fp)
            sname = os.path.basename(jser_fp)
            sname = sname[:sname.rfind(".")]
            hidden_series_dir = os.path.join(sdir, f".{sname}")

            if os.path.isdir(hidden_series_dir):
                # find the series and timer files
                new_series_fp = ""
                sections = {}
                for f in os.listdir(hidden_series_dir):
                    # check if the series is currently being modified
                    if "." not in f:
                        current_time = round(time.time())
                        time_diff = current_time - int(f)
                        if time_diff <= 7:  # the series is currently being operated on
                            QMessageBox.information(
                                self,
                                "Series In Use",
                                "This series is already open in another window.",
                                QMessageBox.Ok
                            )
                            if not self.series:
                                exit()
                            else:
                                return
                    else:
                        ext = f[f.rfind(".")+1:]
                        if ext.isnumeric():
                            sections[int(ext)] = f
                        elif ext == "ser":
                            new_series_fp = os.path.join(hidden_series_dir, f)                    

                # if a series file has been found
                if new_series_fp:
                    # ask the user if they want to open the unsaved series
                    open_unsaved = unsavedNotify()
                    if open_unsaved:
                        new_series = Series(new_series_fp, sections)
                        new_series.modified = True
                        new_series.jser_fp = jser_fp
                    else:
                        # remove the folder if not needed
                        for f in os.listdir(hidden_series_dir):
                            os.remove(os.path.join(hidden_series_dir, f))
                        os.rmdir(hidden_series_dir)
                else:
                    # remove the folder if no series file detected
                    for f in os.listdir(hidden_series_dir):
                        os.remove(os.path.join(hidden_series_dir, f))
                    os.rmdir(hidden_series_dir)

            
            # open the JSER file if no unsaved series was opened
            if not new_series:
                new_series = Series.openJser(jser_fp)
                # user pressed cancel
                if new_series is None:
                    if self.series is None:
                        exit()
                    else:
                        return
            
            # clear the current series
            if self.series and not self.series.isWelcomeSeries():
                self.series.close()

            self.series = new_series

        # series has already been provided by other function
        else:
            self.series = series_obj
        
        # ensure that images are found
        # check saved directory first
        section = self.series.loadSection(self.series.current_section)
        src_path = os.path.join(
            self.series.src_dir,
            os.path.basename(section.src)
        )
        images_found = os.path.isfile(src_path) or os.path.isdir(src_path)
        # check series location second (welcome series case)
        if not images_found:
            src_path = os.path.join(
                os.path.join(self.series.getwdir(), ".."),
                os.path.basename(section.src)
            )
            images_found = os.path.isfile(src_path) or os.path.isdir(src_path)
        # check jser directory last
        if not images_found:
            src_path = os.path.join(
                os.path.dirname(self.series.jser_fp),
                os.path.basename(section.src)
            )
            images_found = os.path.isfile(src_path) or os.path.isdir(src_path)
        
        if not images_found:
            self.changeSrcDir(notify=True)
        else:
            self.series.src_dir = os.path.dirname(src_path)
        
        # set the title of the main window
        self.seriesModified(self.series.modified)

        # set the explorer filepath to the series
        if not self.series.isWelcomeSeries():
            self.explorer_dir = os.path.dirname(self.series.getwdir())

        # create field
        if self.field is not None:  # close previous field widget
            self.field.createField(self.series)
        else:
            self.field = FieldWidget(self.series, self)
            self.setCentralWidget(self.field)

        # create mouse palette
        if self.mouse_palette: # close previous mouse dock
            self.mouse_palette.reset(self.series.palette_traces, self.series.current_trace)
        else:
            self.mouse_palette = MousePalette(self.series.palette_traces, self.series.current_trace, self)
            self.createPaletteShortcuts()
        self.changeTracingTrace(self.series.current_trace) # set the current trace
    
    def newSeries(
        self,
        image_locations : list = None,
        series_name : str = None,
        mag : float = None,
        thickness : float = None
    ):
        """Create a new series from a set of images.
        
            Params:
                image_locations (list): the filpaths for the section images.
        """
        # get images from user
        if not image_locations:
            image_locations, extensions = QFileDialog.getOpenFileNames(
                self,
                "Select Images",
                dir=self.explorer_dir,
                filter="*.jpg *.jpeg *.png *.tif *.tiff"
            )
            if len(image_locations) == 0:
                return
        # get the name of the series from user
        if series_name is None:
            series_name, confirmed = QInputDialog.getText(
                self, "New Series", "Enter series name:")
            if not confirmed:
                return
        # get calibration (microns per pix) from user
        if mag is None:
            mag, confirmed = QInputDialog.getDouble(
                self, "New Series", "Enter image calibration (μm/px):",
                0.00254, minValue=0.000001, decimals=6)
            if not confirmed:
                return
        # get section thickness (microns) from user
        if thickness is None:
            thickness, confirmed = QInputDialog.getDouble(
                self, "New Series", "Enter section thickness (μm):",
                0.05, minValue=0.000001, decimals=6)
            if not confirmed:
                return
        
        # save and clear the existing backend series
        self.saveToJser(notify=True, close=True)
        
        # create new series
        series = Series.new(sorted(image_locations), series_name, mag, thickness)
        series.modified = True
    
        # open series after creating
        self.openSeries(series)
    
    def newFromXML(self, series_fp : str = None):
        """Create a new series from a set of XML files.
        
            Params:
                series_fp (str): the filepath for the XML series
        """

        # get xml series filepath from the user
        if not series_fp:
            series_fp, ext = QFileDialog.getOpenFileName(
                self,
                "Select XML Series",
                dir=self.explorer_dir,
                filter="*.ser"
            )
        if series_fp == "": return  # exit function if user does not provide series

        # save and clear the existing backend series
        self.saveToJser(notify=True, close=True)
        
        # convert the series
        series = xmlToJSON(os.path.dirname(series_fp))
        if not series:
            return

        # flag to save
        series.modified = True

        # open the series
        self.openSeries(series)
    
    def exportToXML(self, export_fp : str = None):
        """Export the current series to XML.
        
            Params:
                export_fp (str): the filepath for the XML .ser file
        """
        # save the current data
        self.saveAllData()

        # get the new xml series filepath from the user
        if not export_fp:
            export_fp, ext = QFileDialog.getSaveFileName(
                self,
                "Export Series",
                f"{self.series.name}.ser",
                filter="XML Series (*.ser)"
            )
            if not export_fp:
                return False
        
        # convert the series
        jsonToXML(self.series, os.path.dirname(export_fp))
    
    def seriesModified(self, modified=True):
        """Change the title of the window reflect modifications."""
        # check for welcome series
        if self.series.isWelcomeSeries():
            self.setWindowTitle("PyReconstruct")
            return
        
        if modified:
            self.setWindowTitle(self.series.name + "*")
        else:
            self.setWindowTitle(self.series.name)
        self.series.modified = modified
    
    def importTransforms(self, tforms_fp : str = None):
        """Import transforms from a text file.
        
            Params:
                tforms_file (str): the filepath for the transforms file
        """
        self.saveAllData()
        # get file from user
        if tforms_fp is None:
            tforms_fp, ext = QFileDialog.getOpenFileName(
                self,
                "Select file containing transforms",
                dir=self.explorer_dir
            )
        if not tforms_fp:
            return
        # import the transforms
        importTransforms(self.series, tforms_fp)
        # reload the section
        self.field.reload()
    
    def importTraces(self, jser_fp : str = None):
        """Import traces from another jser series.
        
            Params:
                jser_fp (str): the filepath with the series to import data from
        """
        if jser_fp is None:
            jser_fp, extension = QFileDialog.getOpenFileName(
                self,
                "Select Series",
                dir=self.explorer_dir,
                filter="*.jser"
            )
        if jser_fp == "": return  # exit function if user does not provide series

        self.saveAllData()

        # open the other series
        o_series = Series.openJser(jser_fp)

        # import the traces and close the other series
        self.series.importTraces(o_series)
        o_series.close()

        # reload the field to update the traces
        self.field.reload()

        # refresh the object list if needed
        if self.field.obj_table_manager:
            self.field.obj_table_manager.refresh()
    
    def importZtraces(self, jser_fp : str = None):
        """Import ztraces from another jser series.
        
            Params:
                jser_fp (str): the filepath with the series to import data from
        """
        if jser_fp is None:
            jser_fp, extension = QFileDialog.getOpenFileName(
                self,
                "Select Series",
                dir=self.explorer_dir,
                filter="*.jser"
            )
        if jser_fp == "": return  # exit function if user does not provide series

        self.saveAllData()

        # open the other series
        o_series = Series.openJser(jser_fp)

        # import the ztraces and close the other series
        self.series.importZtraces(o_series)
        o_series.close()

        # reload the field to update the ztraces
        self.field.reload()

        # refresh the ztrace list if needed
        if self.field.ztrace_table_manager:
            self.field.ztrace_table_manager.refresh()
    
    def editImage(self, option : str, direction : str):
        """Edit the brightness or contrast of the image.
        
            Params:
                option (str): brightness or contrast
                direction (str): up or down
        """
        if option == "brightness" and direction == "up":
            self.field.changeBrightness(1)
        elif option == "brightness" and direction == "down":
            self.field.changeBrightness(-1)
        elif option == "contrast" and direction == "up":
            self.field.changeContrast(2)
        elif option == "contrast" and direction == "down":
            self.field.changeContrast(-2)
    
    def changeMouseMode(self, new_mode):
        """Change the mouse mode of the field (pointer, panzoom, tracing...).

        Called when user clicks on mouse mode palette.

            Params:
                new_mode: the new mouse mode to set
        """
        self.field.setMouseMode(new_mode)

    def changeTracingTrace(self, trace):
        """Change the trace utilized by the user.

        Called when user clicks on trace palette.

            Params:
                trace: the new tracing trace to set
        """
        self.series.current_trace = trace
        self.field.setTracingTrace(trace)
    
    def changeSection(self, section_num : int = None, save=True):
        """Change the section of the field.
        
            Params:
                section_num (int): the section number to change to
                save (bool): saves data to files if True
        """
        if section_num is None:
            section_num, confirmed = QInputDialog.getText(
                self, "Go To Section", "Enter the desired section number:", text=str(self.series.current_section))
            if not confirmed:
                return
            try:
                section_num = int(section_num)
            except ValueError:
                return
        
        # end the field pending events
        self.field.endPendingEvents()
        # save data
        if save:
            self.saveAllData()
        # change the field section
        self.field.changeSection(section_num)
        # update status bar
        self.field.updateStatusBar()
    
    def flickerSections(self):
        """Switch between the current and b sections."""
        if self.field.b_section:
            self.changeSection(self.field.b_section.n, save=False)
    
    def incrementSection(self, down=False):
        """Increment the section number by one.
        
            Params:
                down (bool): the direction to move
        """
        section_numbers = sorted(list(self.series.sections.keys()))  # get list of all section numbers
        section_number_i = section_numbers.index(self.series.current_section)  # get index of current section number in list
        if down:
            if section_number_i > 0:
                self.changeSection(section_numbers[section_number_i - 1])  
        else:   
            if section_number_i < len(section_numbers) - 1:
                self.changeSection(section_numbers[section_number_i + 1])       
    
    def wheelEvent(self, event):
        """Called when mouse scroll is used."""
        # do nothing if middle button is clicked
        if self.field.mclick:
            return
        
        modifiers = QApplication.keyboardModifiers()

        # if zooming
        if modifiers == Qt.ControlModifier:
            field_cursor = self.field.cursor()
            p = self.field.mapFromGlobal(field_cursor.pos())
            x, y = p.x(), p.y()
            if not self.is_zooming:
                # check if user just started zooming in
                self.field.panzoomPress(x, y)
                self.zoom_factor = 1
                self.is_zooming = True

            if event.angleDelta().y() > 0:  # if scroll up
                self.zoom_factor *= 1.1
            elif event.angleDelta().y() < 0:  # if scroll down
                self.zoom_factor *= 0.9
            self.field.panzoomMove(zoom_factor=self.zoom_factor)
        
        # if changing sections
        elif modifiers == Qt.NoModifier:
            # check for the position of the mouse
            mouse_pos = event.point(0).pos()
            field_geom = self.field.geometry()
            if not field_geom.contains(mouse_pos.x(), mouse_pos.y()):
                return
            # change the section
            if event.angleDelta().y() > 0:  # if scroll up
                self.incrementSection()
            elif event.angleDelta().y() < 0:  # if scroll down
                self.incrementSection(down=True)
    
    def keyReleaseEvent(self, event):
        """Overwritten: checks for Ctrl+Zoom."""
        if self.is_zooming and event.key() == 16777249:
            self.field.panzoomRelease(zoom_factor=self.zoom_factor)
            self.is_zooming = False
        
        super().keyReleaseEvent(event)
    
    def saveAllData(self):
        """Write current series and section data into backend JSON files."""
        # save the trace palette
        self.series.palette_traces = []
        for button in self.mouse_palette.palette_buttons:  # get trace palette
            self.series.palette_traces.append(button.trace)
            if button.isChecked():
                self.series.current_trace = button.trace
        self.field.section.save()
        self.series.save()
    
    def saveToJser(self, notify=False, close=False):
        """Save all data to JSER file.
        
        Params:
            save_data (bool): True if series and section files in backend should be save
            close (bool): Deletes backend series if True
        """
        # save the series data
        self.saveAllData()

        # if welcome series -> close without saving
        if self.series.isWelcomeSeries():
            return
        
        # notify the user and check if series was modified
        if notify and self.series.modified:
            save = saveNotify()
            if save == "no":
                if close:
                    self.series.close()
                return
            elif save == "cancel":
                return "cancel"
        
        # check if the user is closing and the series was not modified
        if close and not self.series.modified:
            self.series.close()
            return

        # run save as if there is no jser filepath
        if not self.series.jser_fp:
            self.saveAsToJser(close=close)
        else:        
            self.series.saveJser(close=close)
        
        # set the series to unmodified
        self.seriesModified(False)
    
    def saveAsToJser(self, close=False):
        """Prompt the user to find a save location."""
        # save the series data
        self.saveAllData()

        # check for wlecome series
        if self.series.isWelcomeSeries():
            return

        # get location from user
        new_jser_fp, confirmed = getSaveLocation(self.series)
        if not confirmed:
            return
        
        # move the working hidden folder to the new jser directory
        self.series.move(
            new_jser_fp,
            self.field.section,
            self.field.b_section
        )
        
        # save the file
        self.series.saveJser(close=close)

        # set the series to unmodified
        self.seriesModified(False)
    
    def autoBackup(self):
        """Set up the auto-backup functionality for the series."""
        # user checked the option
        if self.backup_act.isChecked():
            # prompt the user to find a folder to store backups
            new_dir = QFileDialog.getExistingDirectory(
                self,
                "Select folder to contain backup files",
                dir=self.explorer_dir
            )
            if not new_dir:
                self.backup_act.setChecked(False)
                return
            self.series.options["backup_dir"] = new_dir
        # user unchecked the option
        else:
            self.series.options["backup_dir"] = ""
        
        self.seriesModified()
    
    def viewSeriesHistory(self):
        """View the history for the entire series."""
        # load all log objects from the all traces
        log_history = []
        update, canceled = progbar("Object History", "Loading history...")
        progress = 0
        final_value = len(self.series.sections)
        for snum in self.series.sections:
            section = self.series.loadSection(snum)
            for trace in section.tracesAsList():
                for log in trace.history:
                    log_history.append((log, trace.name, snum))
            if canceled():
                return
            progress += 1
            update(progress/final_value * 100)
        
        log_history.sort()

        output_str = "Series History\n"
        for log, name, snum in log_history:
            output_str += f"Section {snum} "
            output_str += name + " "
            output_str += str(log) + "\n"
        
        self.history_widget = HistoryWidget(self, output_str)
    
    def openObjectList(self):
        """Open the object list widget."""
        self.saveAllData()
        self.field.openObjectList()
    
    def openZtraceList(self):
        """Open the ztrace list widget."""
        self.saveAllData()
        self.field.openZtraceList()
    
    def openTraceList(self):
        """Open the trace list widget."""
        self.field.openTraceList()
    
    def openSectionList(self):
        """Open the section list widget."""
        self.saveAllData()
        self.field.openSectionList()
    
    def setToObject(self, obj_name : str, section_num : str):
        """Focus the field on an object from a specified section.
        
            Params:
                obj_name (str): the name of the object
                section_num (str): the section the object is located
        """
        self.changeSection(section_num)
        self.field.findContour(obj_name)
    
    def changeTform(self, new_tform_list : list = None):
        """Open a dialog to change the transform of a section."""
        # check for section locked status
        if self.field.section.align_locked:
            return
        
        if new_tform_list is None:
            current_tform = " ".join(
                [str(round(n, 5)) for n in self.field.section.tforms[self.series.alignment].getList()]
            )
            new_tform_list, confirmed = QInputDialog.getText(
                self, "New Transform", "Enter the desired section transform:", text=current_tform)
            if not confirmed:
                return
            try:
                new_tform_list = [float(n) for n in new_tform_list.split()]
                if len(new_tform_list) != 6:
                    return
            except ValueError:
                return
        self.field.changeTform(Transform(new_tform_list))
    
    def translate(self, direction : str, amount : str):
        """Translate the current transform.
        
            Params:
                direction (str): left, right, up, or down
                amount (str): small, med, or big
        """
        if amount == "small":
            num = self.series.options["small_dist"]
        elif amount == "med":
            num = self.series.options["med_dist"]
        elif amount == "big":
            num = self.series.options["big_dist"]
        if direction == "left":
            x, y = -num, 0
        elif direction == "right":
            x, y = num, 0
        elif direction == "up":
            x, y = 0, num
        elif direction == "down":
            x, y = 0, -num
        self.field.translate(x, y)
    
    def newAlignment(self, new_alignment_name : str):
        """Add a new alignment (based on existing alignment).
        
            Params:
                new_alignment_name (str): the name of the new alignment
        """
        if new_alignment_name in self.field.section.tforms:
            QMessageBox.information(
                self,
                " ",
                "This alignment already exists.",
                QMessageBox.Ok
            )
            return
        self.series.newAlignment(
            new_alignment_name,
            self.series.alignment
        )
    
    def changeAlignment(self, alignment_name : str = None):
        """Switch alignments.
        
            Params:
                alignment_name (str): the name of the new alignment"""
        alignments = list(self.field.section.tforms.keys())

        if alignment_name is None:
            alignment_name, confirmed = AlignmentDialog(
                self,
                alignments
            ).exec()
            if not confirmed:
                return
        
        if alignment_name not in alignments:
            self.newAlignment(alignment_name)

        self.field.changeAlignment(alignment_name)
    
    def calibrateMag(self, trace_lengths : dict = None):
        """Calibrate the pixel size for the series.
        
            Params:
                trace_lengths (dict): the lengths of traces to calibrate
        """
        self.saveAllData()
        
        if trace_lengths is None:
            # gather trace names
            names = []
            for trace in self.field.section_layer.selected_traces:
                if trace.name not in names:
                    names.append(trace.name)
            
            if len(names) == 0:
                notify("Please select traces for calibration.")
            
            # prompt user for length of each trace name
            trace_lengths = {}
            for name in names:
                d, confirmed = QInputDialog.getText(
                    self,
                    "Trace Length",
                    f'Length of "{name}" in microns:'
                )
                if not confirmed:
                    return
                try:
                    d = float(d)
                except ValueError:
                    return
                trace_lengths[name] = d
        
        self.field.calibrateMag(trace_lengths)
            
    def closeEvent(self, event):
        """Save all data to files when the user exits."""
        if self.series.options["autosave"]:
            self.saveToJser(close=True)
        else:
            response = self.saveToJser(notify=True, close=True)
            if response == "cancel":
                event.ignore()
                return
        event.accept()
