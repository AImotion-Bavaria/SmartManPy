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


# from SimPy.Simulation import Process, Resource, reactivate, now
from manpy.simulation.ManPyObject import ManPyObject

# ===============================================================================
# The ObjectInterruption process
# ===============================================================================
class ObjectInterruption(ManPyObject):
    """
    Class that acts as an abstract. It should have no instances. All object interruptions (eg failures, breaks) should inherit from it
    """

    def __init__(self, id="", name="", victim=None, remove=False, cost=0, **kw):
        ManPyObject.__init__(self, id, name)
        self.victim = victim
        # variable used to hand in control to the objectInterruption
        self.call = False
        from .Globals import G
        # variable used to remove current entity from victim at failure
        self.remove = remove

        # G.ObjectInterruptionList.append(self)
        # append the interruption to the list that victim (if any) holds
        if self.victim:
            if isinstance(self.victim.objectInterruptions, list):
                self.victim.objectInterruptions.append(self)
        # list of expected signals of an interruption (values can be used as flags to inform on which signals is the interruption currently yielding)
        self.expectedSignals = {
            "victimOffShift": 0,
            "victimOnShift": 0,
            "victimStartsProcessing": 0,
            "victimEndsProcessing": 0,
            "isCalled": 0,
            "endedLastProcessing": 0,
            "victimIsEmptyBeforeMaintenance": 0,
            "resourceAvailable": 0,
            "victimFailed": 0,
            "contribution": 0,
            "victimIsInterrupted": 0,
            "victimResumesProcessing": 0
        }
        self.cost = 0

    def initialize(self):
        from manpy.simulation.core.Globals import G

        self.env = G.env
        self.call = False
        # events that are send by one interruption to all the other interruptions that might wait for them
        self.victimOffShift = self.env.event()
        self.victimOnShift = self.env.event()
        self.victimFailed = self.env.event()
        # flags that show if the interruption waits for the event
        self.isWaitingForVictimOffShift = False
        self.isWaitingForVictimOnShift = False
        # list of expected signals of an interruption (values can be used as flags to inform on which signals is the interruption currently yielding)
        self.expectedSignals = {
            "victimOffShift": 0,
            "victimOnShift": 0,
            "victimStartsProcessing": 0,
            "victimEndsProcessing": 0,
            "isCalled": 0,
            "endedLastProcessing": 0,
            "victimIsEmptyBeforeMaintenance": 0,
            "resourceAvailable": 0,
            "victimFailed": 0,
            "contribution": 0,
            "victimIsInterrupted": 0,
            "victimResumesProcessing": 0
        }

    def run(self):
        """ the main process of the core object. this is a dummy, every object must have its own implementation"""

        raise NotImplementedError("Subclass must define 'run' method")

    def invoke(self):
        """hand in the control to the objectIterruption.run to be called by the machine"""

        # TODO: consider removing this method,
        # signalling can be done via Machine request/releaseOperator
        if self.expectedSignals["isCalled"]:
            succeedTuple = (self.victim, self.env.now)
            self.sendSignal(
                receiver=self, signal=self.isCalled, succeedTuple=succeedTuple
            )

    def getVictimQueue(self):
        """returns the internal queue of the victim"""

        return self.victim.getActiveObjectQueue()

    def victimQueueIsEmpty(self):
        """check if the victim's internal queue is empty"""

        return len(self.getVictimQueue()) == 0

    def interruptVictim(self):
        """interrupts the victim"""

        # add cost to entity
        self.victim.activeEntity.cost += self.cost

        # print(f"Starting failure at {self.env.now}")
        # inform the victim by whom will it be interrupted
        # TODO: reconsider what happens when failure and ShiftScheduler (e.g.) signal simultaneously
        if self.victim.expectedSignals["interruptionStart"]:
            # print(f"Sending interruptionStart to {self.victim.name}")
            self.victim.interruptedBy = self.type
            self.sendSignal(receiver=self.victim, signal=self.victim.interruptionStart)
            # ToDo following is needed for synching, check why
            self.victim.expectedSignals["interruptionEnd"] = 1
        else:
            self.victim.isBlocked = False
            self.victim.isProcessing = False
        # if the machines are operated by dedicated operators
        if self.victim.dedicatedOperator:
            # request allocation
            self.victim.requestAllocation()
        # remove entity if needed
        if self.remove:
            self.victim.activeEntity.result = "Fail"
            self.victim.discards.append(self.victim.activeEntity)
            self.victim.removeEntity(self.victim.activeEntity)

    def reactivateVictim(self):
        """reactivate the victim"""

        # print(f"Ending failure at {self.env.now}")
        if self.victim.expectedSignals["interruptionEnd"]:
            self.sendSignal(receiver=self.victim, signal=self.victim.interruptionEnd)
            # reset the interruptionStart event of the victim
            self.victim.interruptionStart = self.env.event()
            # TODO: reconsider what happens when failure and ShiftScheduler (e.g.) signal simultaneously
            self.victim.interruptedBy = None
        # if the machines are operated by dedicated operators
        if self.victim.dedicatedOperator:
            # request allocation
            self.victim.requestAllocation()

    def printTrace(self, entityName, message):
        """print message in the console. Format is (Simulation Time | Entity or Frame Name | message)"""

        from manpy.simulation.core.Globals import G

        if G.console == "Yes":  # output only if the user has selected to
            print((self.env.now, entityName, message))
