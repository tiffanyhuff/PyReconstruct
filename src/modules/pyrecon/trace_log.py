import os
from datetime import datetime

class TraceLog():

    def __init__(self, *args):
        if type(args[0]) is str:
            self.message = args[0]
            self.username = os.getlogin()
            t = datetime.now()
            self.dt = f"{t.year}{t.month:02d}{t.day:02d}_{t.hour:02d}{t.minute:02d}{t.second:02d}"
        elif type(args[0]) is list or type(args[0]) is tuple:
            self.dt = args[0][0]
            self.username = args[0][1]
            self.message = args[0][2]
    
    def __str__(self):
        return f"{self.dt} {self.username} {self.message}"
    
    def __iter__(self):
        return [self.dt, self.username, self.message].__iter__()
    
    def __gt__(self, other):
        return self.dt > other.dt
    
    def __lt__(self, other):
        return self.dt < other.dt
    
    def copy(self):
        return TraceLog(list(self).copy())
