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
Created on 6 June 2013

@author: George
"""
"""
the exit of the capacity station. Only change from buffer that it can be blocked.
"""

from manpy.simulation.core.Exit import Exit


# ===========================================================================
#                            the CapacityStationExit object
# ===========================================================================
class CapacityStationExit(Exit):

    # ===========================================================================
    # the __init__ method of the CapacityStationExit
    # ===========================================================================
    def __init__(self, id, name=None, cost=0, nextCapacityStationBufferId=None, **kw):
        Exit.__init__(self, id, name, cost=cost)
        self.isLocked = True
        self.nextCapacityStationBufferId = (
            nextCapacityStationBufferId  # the id of the next station. If it is None it
        )
        # means it is the end of the system.
        self.nextCapacityStationBuffer = None  # the next buffer. If it is None it
        from manpy.simulation.core.Globals import G

        if hasattr(G, "CapacityStationExitList"):
            G.CapacityStationExitList.append(self)
        else:
            G.CapacityStationExitList = []
            G.CapacityStationExitList.append(self)

    def initialize(self):
        Exit.initialize(self)
        self.isLocked = True
        # list that contains the entities that are just obtained so that they can be
        # moved to the next buffer
        self.currentlyObtainedEntities = []
        # find the next buffer
        if self.nextCapacityStationBufferId:
            from manpy.simulation.core.Globals import G

            # find the project that the capacity entity is part of
            for capacityStationBuffer in G.CapacityStationBufferList:
                if capacityStationBuffer.id == self.nextCapacityStationBufferId:
                    self.nextCapacityStationBuffer = capacityStationBuffer
                    break

    def canAccept(self, callerObject=None):
        if self.isLocked:
            return False
        return Exit.canAccept(self)

    # =======================================================================
    # outputs results to JSON File
    # =======================================================================
    def outputResultsJSON(self):
        # output results only for the last exit
        if not self.nextCapacityStationBuffer:
            Exit.outputResultsJSON(self)

    # extend so that it updates alreadyWorkedDict of the project
    def getEntity(self):
        activeEntity = Exit.getEntity(self)
        alreadyWorkedDict = activeEntity.capacityProject.alreadyWorkedDict
        stationId = self.giver.id
        alreadyWorkedDict[stationId] += activeEntity.requiredCapacity
