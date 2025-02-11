from PySide6.QtCore import Qt

from modules.datatypes import (
    Series,
    ZtraceTableItem
)
from modules.gui.table import ZtraceTableWidget

class ZtraceTableManager():

    def __init__(self, series : Series, mainwindow):
        """Create the ztrace table manager.
        
            Params:
                series (Series): the series object
                mainwindow (MainWindow): the main window widget"""
        self.tables = []
        self.series = series
        self.mainwindow = mainwindow
        self.loadSeries()
    
    def loadSeries(self):
        """Load the section thicknesses and transforms from the series."""        
        # load the ztrace data
        self.series.gatherSectionData()
        self.data = {}
        for name, ztrace in self.series.ztraces.items():
            self.data[name] = ZtraceTableItem(
                ztrace,
                self.series
            )
    
    def refresh(self):
        """Refresh the series data."""
        self.loadSeries()
        for table in self.tables:
            self.updateTable(table)
    
    def newTable(self):
        """Create a new ztrace list."""
        new_table = ZtraceTableWidget(
            self.series,
            self.data,
            self.mainwindow,
            self
        )
        self.tables.append(new_table)
        self.mainwindow.addDockWidget(Qt.LeftDockWidgetArea, new_table)
    
    def updateTable(self, table : ZtraceTableWidget):
        """Update a table's data.
        
            Params:
                table: the table to update
        """
        table.createTable(self.data)
    
    def updateZtraces(self, ztrace_names : list):
        """Update the data for a set of ztraces.
        
            Params:
                ztrace_names (str): the names of the ztraces to update
        """
        # load the ztrace data
        for name in ztrace_names:
            self.data[name] = ZtraceTableItem(
                self.series.ztraces[name],
                self.series
            )
        for table in self.tables:
            self.updateTable(table)

    # MENU-REALTED FUNCTIONS

    def editAttributes(self, name : str, new_name : str, new_color : tuple):
        """Edit the name of a ztrace.
        
            Params:
                name (str): the name of the ztrace to change
                new_name (str): the new name for the trace
                new_color (tuple): the new color for the trace
        """
        # modify the ztrace data
        ztrace = self.series.ztraces[name]
        if new_name:
            ztrace.name = new_name
            if new_name != name:
                del(self.series.ztraces[name])
                self.series.ztraces[new_name] = ztrace
        if new_color:
            ztrace.color = new_color
        
        # modify the tables
        if new_name and new_name != name:
            self.data[new_name] = self.data[name]
            self.data[new_name].name = new_name
            del(self.data[name])
            for table in self.tables:
                table.createTable(self.data)
        
        # update the view
        self.mainwindow.field.reload()
        self.mainwindow.seriesModified(True)
    
    def smooth(self, names : list, smooth : int, newztrace : bool):
        """Smooth a set of ztraces.
        
            Params:
                names (list): the names of the ztraces to smooth
                smooth (int): the smoothing factor
                newztrace (bool): False if ztrace should be overwritten
        """
        # smooth the ztraces
        for name in names:
            # create a new ztrace if requested
            if newztrace:
                ztrace = self.series.ztraces[name].copy()
                new_name = f"{ztrace.name}_smooth{smooth}"
                ztrace.name = new_name
                self.series.ztraces[new_name] = ztrace
            else:
                ztrace = self.series.ztraces[name]
            ztrace.smooth(self.series, smooth)
            # update the table data
            self.data[ztrace.name] = ZtraceTableItem(
                ztrace,
                self.series
            )
        
        for table in self.tables:
            table.createTable(self.data)
        
        # update the view
        self.mainwindow.field.reload()
        self.mainwindow.seriesModified(True)
        
    def addTo3D(self, names : list):
        """Add a set of ztraces to the 3D scene."""
        # access the object viewer object
        obj_table_manager = self.mainwindow.field.obj_table_manager
        if not obj_table_manager:
            return
        object_viewer = obj_table_manager.object_viewer
        if not object_viewer:
            return
        
        object_viewer.addZtraces(names)
    
    def remove3D(self, names : list):
        """Remove ztraces from the 3D scene.
        
            Params:
                names (list): the names of ztraces to remove
        """
        # access the object viewer object
        obj_table_manager = self.mainwindow.field.obj_table_manager
        if not obj_table_manager:
            return
        object_viewer = obj_table_manager.object_viewer
        if not object_viewer:
            return
        
        object_viewer.remove(names, ztrace=True)

    def delete(self, names : list):
        """Delete a set of ztraces.
        
            Params:
                names (list): the list of ztraces to delete
        """
        for name in names:
            del(self.series.ztraces[name])
            del(self.data[name])
        
        for table in self.tables:
            table.createTable(self.data)

        # update the view
        self.mainwindow.field.reload()
        self.mainwindow.seriesModified(True)
    
    def close(self):
        """Close all the tables."""
        for table in self.tables:
            table.close()
        

        
        
            

