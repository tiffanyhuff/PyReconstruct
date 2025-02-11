import os
import json

from .contour import Contour
from .trace import Trace
from .transform import Transform

from modules.calc import (
    getDistanceFromTrace,
    distance
)
from modules.constants import assets_dir


class Section():

    def __init__(self, n : int, series):
        """Load the section file.
        
            Params:
                n (int): the section number
                series (Series): the series that contains the section
        """
        self.n = n
        self.series = series
        self.filepath = os.path.join(
            self.series.getwdir(),
            self.series.sections[n]
        )

        self.selected_traces = []
        self.selected_ztraces = []

        self.temp_hide = []

        self.added_traces = []
        self.removed_traces = []
        self.modified_traces = []

        with open(self.filepath, "r") as f:
            section_data = json.load(f)
        
        Section.updateJSON(section_data)  # update any missing attributes
        
        self.src = section_data["src"]
        self.brightness = section_data["brightness"]
        self.contrast = section_data["contrast"]
        self.mag = section_data["mag"]
        self.align_locked = section_data["align_locked"]

        self.tforms = {}
        for a in section_data["tforms"]:
            self.tforms[a] = Transform(section_data["tforms"][a])
        
        self.thickness = section_data["thickness"]
        self.contours = section_data["contours"]
        for name in self.contours:
            trace_list = []
            for trace_data in self.contours[name]:
                trace = Trace.fromList(trace_data, name)
                # screen for defective traces
                if len(trace.points) > 1:
                    trace_list.append(trace)
            self.contours[name] = Contour(
                name,
                trace_list
            )
        
        # ADDED SINCE JAN 25TH

        self.calgrid = section_data["calgrid"]
    
    # STATIC METHOD
    def updateJSON(section_data):
        """Add missing attributes to section JSON."""
        empty_section = Section.getEmptyDict()
        for key in empty_section:
            if key not in section_data:
                section_data[key] = empty_section[key]
        
        # modify brightness/contrast
        if abs(section_data["brightness"]) > 100:
            section_data["brightness"] = 0
        section_data["contrast"] = int(section_data["contrast"])

        # scan contours
        flagged_contours = []
        for cname in section_data["contours"]:
            flagged_traces = []
            for i, trace in enumerate(section_data["contours"][cname]):
                # convert trace to list format if needed
                if type(trace) is dict:
                    trace = [
                        trace["x"],
                        trace["y"],
                        trace["color"],
                        trace["closed"],
                        trace["negative"],
                        trace["hidden"],
                        trace["mode"],
                        trace["tags"],
                        trace["history"]
                    ]
                    section_data["contours"][cname][i] = trace
                # check for empty/defective traces
                if len(trace[0]) < 2:
                    flagged_traces.append(i)
            # remove the flagged defective traces
            for i in sorted(flagged_traces, reverse=True):
                section_data["contours"][cname].pop(i)
            # check if the contour is empty
            if not section_data["contours"][cname]:
                flagged_contours.append(cname)
        # remove flagged contours
        for cname in flagged_contours:
            del(section_data["contours"][cname])

    def getDict(self) -> dict:
        """Convert section object into a dictionary.
        
            Returns:
                (dict) all of the compiled section data
        """
        d = {}
        d["src"] = self.src
        d["brightness"] = self.brightness
        d["contrast"] = self.contrast
        d["mag"] = self.mag
        d["align_locked"] = self.align_locked

        # save tforms
        d["tforms"] = {}
        for a in self.tforms:
            d["tforms"][a] = self.tforms[a].getList()

        d["thickness"] = self.thickness

        # save contours
        d["contours"] = {}
        for contour_name in self.contours:
            if not self.contours[contour_name].isEmpty():
                d["contours"][contour_name] = [
                    trace.getList(include_name=False) for trace in self.contours[contour_name]
                ]
        
        # ADDED SINCE JAN 25TH

        d["calgrid"] = self.calgrid

        return d
    
    # STATIC METHOD
    def getEmptyDict():
        section_data = {}
        section_data["src"] = ""  # image location
        section_data["brightness"] = 0
        section_data["contrast"] = 0
        section_data["mag"] = 0.00254  # microns per pixel
        section_data["align_locked"] = True
        section_data["thickness"] = 0.05  # section thickness
        section_data["tforms"] = {}  
        section_data["tforms"]["default"]= [1, 0, 0, 0, 1, 0] # identity matrix default
        section_data["contours"] = {}

        # ADDED SINCE JAN 25TH

        section_data["calgrid"] = False

        return section_data
    
    # STATIC METHOD
    def new(series_name : str, snum : int, image_location : str, mag : float, thickness : float, wdir : str):
        """Create a new blank section file.
        
            Params:
                series_name (str): the name for the series
                snum (int): the sectino number
                image_location (str): the file path for the image
                mag (float): microns per pixel for the section
                thickness (float): the section thickness in microns
                wdir (str): the working directory for the sections
            Returns:
                (Section): the newly created section object
        """
        section_data = Section.getEmptyDict()
        section_data["src"] = os.path.basename(image_location)  # image location
        section_data["mag"] = mag  # microns per pixel
        section_data["thickness"] = thickness  # section thickness

        section_fp = os.path.join(wdir, series_name + "." + str(snum))
        with open(section_fp, "w") as section_file:
            section_file.write(json.dumps(section_data, indent=2))
   
    def save(self):
        """Save file into json."""
        try:
            if os.path.samefile(self.filepath, os.path.join(assets_dir, "welcome_series", "welcome.0")):
                return  # ignore welcome series
        except FileNotFoundError:
            pass
    
        d = self.getDict()
        with open(self.filepath, "w") as f:
            f.write(json.dumps(d, indent=1))
    
    def tracesAsList(self) -> list[Trace]:
        """Return the trace dictionary as a list. Does NOT copy traces.
        
            Returns:
                (list): a list of traces
        """
        trace_list = []
        for contour_name in self.contours:
            for trace in self.contours[contour_name]:
                trace_list.append(trace)
        return trace_list
    
    def setAlignLocked(self, align_locked : bool):
        """Set the alignment locked status of the section.
        
            Params:
                align_locked (bool): the new locked status
        """
        self.align_locked = align_locked
    
    def clearTracking(self):
        """Clear the added_traces and removed_traces lists."""
        self.added_traces = []
        self.removed_traces = []
        self.modified_traces = []
    
    def setMag(self, new_mag : float):
        """Set the magnification for the section.
        
            Params:
                new_mag (float): the new magnification for the section
        """
        # modify the translation component of the transformation
        for tform in self.tforms.values():
            tform.magScale(self.mag, new_mag)
        
        # modify the traces
        for trace in self.tracesAsList():
            trace.magScale(self.mag, new_mag)
        
        self.mag = new_mag
    
    def addTrace(self, trace : Trace, log_message=None):
        """Add a trace to the trace dictionary.
        
            Params:
                trace (Trace): the trace to add
                log_message (str): the history log message to put on the trace
        """
        # add to the trace history
        if log_message:
            trace.addLog(log_message)
        else:
            if trace.isNew():
                trace.addLog("created")
            else:
                trace.addLog("modified")

        if trace.name in self.contours:
            self.contours[trace.name].append(trace)
        else:
            self.contours[trace.name] = Contour(trace.name, [trace])
        
        self.added_traces.append(trace)
    
    def removeTrace(self, trace : Trace):
        """Remove a trace from the trace dictionary.
        
            Params:
                trace (Trace): the trace to remove from the traces dictionary
        """
        if trace.name in self.contours:
            self.contours[trace.name].remove(trace)
            self.removed_traces.append(trace.copy())

    def editTraceAttributes(self, traces : list[Trace], name : str, color : tuple, tags : set, mode : tuple, add_tags=False):
        """Change the name and/or color of a trace or set of traces.
        
            Params:
                traces (list): the list of traces to modify
                name (str): the new name
                color (tuple): the new color
                tags (set): the new set of tags
                mode (tuple): the new fill mode for the traces
                add_tags (bool): True if tags should be added (rather than replaced)
        """
        for trace in traces:
            # check if trace was highlighted
            if trace in self.selected_traces:
                self.selected_traces.remove(trace)
                selected = True
            else:
                selected = False
            
            # remove the trace and modify
            self.removeTrace(trace)
            new_trace = trace.copy()
            if name is not None:
                new_trace.name = name
            if color is not None:
                new_trace.color = color
            if tags is not None:
                if add_tags:
                    for tag in tags:
                        new_trace.tags.add(tag)
                else:
                    new_trace.tags = tags
            fill_mode = list(new_trace.fill_mode)
            if mode is not None:
                style, condition = mode
                if style is not None:
                    fill_mode[0] = style
                if condition is not None:
                    fill_mode[1] = condition
                new_trace.fill_mode = tuple(fill_mode)
            
            # add trace back to scene and highlight if needed
            self.addTrace(new_trace, "attributes modified")
            if selected:
                self.selected_traces.append(new_trace)
    
    def editTraceRadius(self, traces : list[Trace], new_rad : float):
        """Change the radius of a trace or set of traces.
        
            Params:
                traces (list): the list of traces to change
                new_rad (float): the new radius for the trace(s)
        """
        for trace in traces:
            self.removeTrace(trace)
            trace.resize(new_rad)
            self.addTrace(trace, "radius modified")
    
    def findClosestTrace(self, field_x : float, field_y : float, radius=0.5, traces_in_view : list[Trace] = None) -> Trace:
        """Find closest trace to field coordinates in a given radius.
        
            Params:
                field_x (float): x coordinate of search center
                field_y (float): y coordinate of search center
                radius (float): 1/2 of the side length of search square
            Returns:
                (Trace) the trace closest to the center
                None if no trace points are found within the radius
        """
        min_distance = -1
        closest_trace = None
        min_interior_distance = -1
        closest_trace_interior = None
        tform = self.tforms[self.series.alignment]

        # only check the traces within the view if provided
        if traces_in_view:
            traces = traces_in_view
        else:
            traces = self.tracesAsList()
        
        # iterate through all traces to get closest
        for trace in traces:
            # skip hidden traces
            if trace.hidden:
                continue
            points = []
            for point in trace.points:
                x, y = tform.map(*point)
                points.append((x,y))
            
            # find the distance of the point from each trace
            dist = getDistanceFromTrace(
                field_x,
                field_y,
                points,
                factor=1/self.mag,
                absolute=False
            )
            if closest_trace is None or abs(dist) < min_distance:
                min_distance = abs(dist)
                closest_trace = trace
            
            # check if the point is inside any filled trace
            if (
                trace.fill_mode[0] != "none" and
                dist > 0 and 
                (closest_trace_interior is None or dist < min_interior_distance)
            ):
                min_interior_distance = dist
                closest_trace_interior = trace
        
        # check for ztrace points close by
        for ztrace in self.series.ztraces.values():
            for i, pt in enumerate(ztrace.points):
                if pt[2] == self.n:
                    x, y = tform.map(*pt[:2])
                    dist = distance(field_x, field_y, x, y)
                    if closest_trace is None or dist < min_distance:
                        min_distance = dist
                        closest_trace = (ztrace, i)
        
        return closest_trace if min_distance <= radius else closest_trace_interior
    
    def deselectAllTraces(self):
        """Deselect all traces."""
        self.selected_traces = []
        self.selected_ztraces = []
    
    def selectAllTraces(self):
        """Select all traces."""
        self.selected_traces = self.tracesAsList()
    
    def hideTraces(self, traces : list = None, hide=True):
        """Hide traces.
        
            Params:
                traces (list): the traces to hide
                hide (bool): True if traces should be hidden
        """
        modified = False

        if not traces:
            traces = self.selected_traces

        for trace in traces:
            modified = True
            trace.setHidden(hide)
            self.modified_traces.append(trace)
        
        self.selected_traces = []

        return modified
    
    def unhideAllTraces(self):
        """Unhide all traces on the section."""
        modified = False
        for trace in self.tracesAsList():
            hidden = trace.hidden
            if hidden:
                modified = True
                trace.setHidden(False)
                self.modified_traces.append(trace)
        
        return modified
    
    def makeNegative(self, negative=True):
        """Make a set of traces negative."""
        traces = self.selected_traces
        for trace in traces:
            self.removeTrace(trace)
            trace.negative = negative
            self.addTrace(trace, "made negative")
    
    def deleteTraces(self, traces : list = None, ztraces_i : list = None):
        """Delete selected traces.
        
            Params:
                traces (list): a list of traces to delete (default is selected traces)
                ztraces (list): a list of ztrace, index pair points to delete
        """
        modified = False

        if traces is None:
            traces = self.selected_traces.copy()
        if ztraces_i is None:
            ztraces_i = self.selected_ztraces.copy()

        for trace in traces:
            modified = True
            self.removeTrace(trace)
            if trace in self.selected_traces:
                self.selected_traces.remove(trace)
        # for ztrace_i in ztraces_i:
        #     ztrace, i = ztrace_i
        #     del(ztrace.points[i])
        #     if ztrace_i in self.selected_ztraces:
        #         self.selected_ztraces.remove(ztrace_i)

        return modified
    
    def translateTraces(self, dx : float, dy : float):
        """Translate the selected traces.
        
            Params:
                dx (float): x-translate
                dy (float): y-translate
        """
        tform = self.tforms[self.series.alignment]
        for trace in self.selected_traces:
            self.removeTrace(trace)
            for i, p in enumerate(trace.points):
                # apply forward transform
                x, y = tform.map(*p)
                # apply translate
                x += dx
                y += dy
                # apply reverse transform
                x, y = tform.map(x, y, inverted=True)
                # replace point
                trace.points[i] = (x, y)
            self.addTrace(trace, log_message="translated")
        for ztrace, i in self.selected_ztraces:
            x, y, snum = ztrace.points[i]
            # apply forward tform
            x, y = tform.map(x, y)
            # apply translate
            x += dx
            y += dy
            # apply reverse transform
            x, y = tform.map(x, y, inverted=True)
            # replace point
            ztrace.points[i] = (x, y, snum)
            # keep track of modified ztrace
            self.series.modified_ztraces.append(ztrace.name)
    
    def importTraces(self, other):
        """Import the traces from another section.
        
            Params:
                other (Section): the section with traces to import
        """
        for cname, contour in other.contours.items():
            if cname in self.contours:
                self.contours[cname].importTraces(contour)
            else:
                self.contours[cname] = contour.copy()
        
        self.save()