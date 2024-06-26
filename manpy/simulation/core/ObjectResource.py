# ===========================================================================
# Copyright 2013 University of Limerick
#
# This file is part of DREAM.
#
# DREAM is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# DREAM is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with DREAM.  If not, see <http://www.gnu.org/licenses/>.
# ===========================================================================
"""
Created on 18 Aug 2013

@author: George
"""

# from SimPy.Simulation import Resource
import simpy
from manpy.simulation.ManPyObject import ManPyObject

class ObjectResource(ManPyObject):
    """
    The resource that repairs the machines
    Class that acts as an abstract. It should have no instances. All the Resources should inherit from it.
    """
    def __init__(self, id="", name="", **kw):
        ManPyObject.__init__(self, id, name)
        self.initialized = False
        # list that holds the objectInterruptions that have this element as victim
        self.objectInterruptions = []
        # alias used for printing the trace
        self.alias = None
        # list with the coreObjects IDs that the resource services
        self.coreObjectIds = []
        from manpy.simulation.core.Globals import G

        G.ObjectResourceList.append(self)

    def initialize(self):
        from manpy.simulation.core.Globals import G

        # flag that shows if the resource is on shift
        self.onShift = True
        # flag that shows if the resource is on break
        self.onBreak = False
        self.env = G.env
        self.timeLastOperationStarted = (
            0  # holds the time that the last repair was started
        )
        self.Res = simpy.Resource(self.env, capacity=self.capacity)
        # variable that checks whether the resource is already initialized
        self.initialized = True
        # list with the coreObjects IDs that the resource services
        self.coreObjectIds = []
        # list with the coreObjects that the resource services
        self.coreObjects = []
        # flag that locks the resource so that it cannot get new jobs
        self.isLocked = False
        # lists that keep the start/endShiftTimes of the victim
        self.endShiftTimes = []
        self.startShiftTimes = []

    def checkIfResourceIsAvailable(self, callerObject=None):
        """checks if the worker is available"""

        # return true if the operator is idle and on shift
        return (
            len(self.Res.users) < self.capacity
            and self.onShift
            and (not self.isLocked)
            and (not self.onBreak)
        )

    def getResource(self):
        """returns the resource"""

        return self.Res

    def getResourceQueue(self):
        """returns the active queue of the resource"""

        return self.Res.users

    def isInitialized(self):
        """check if the resource is already initialized"""

        return self.initialized

    def printRoute(self):
        """print the route (the different stations the resource was occupied by)"""
        pass
