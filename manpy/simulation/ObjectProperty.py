# ===========================================================================
# TODO new copyright notice
# ===========================================================================

"""
Created on 18 Aug 2013

@author: LodesL
"""
"""
Abstract class for all kinds of object properties that are generated in somehow regular interval. Example: Features
"""

# from SimPy.Simulation import Process, Resource, reactivate, now
import simpy
from .ManPyObject import ManPyObject

# ===============================================================================
# The ObjectProperty process
# ===============================================================================
class ObjectProperty(ManPyObject):
    def __init__(self, id="", name="", victim=None, **kw):
        ManPyObject.__init__(self, id, name)
        self.victim = victim
        # variable used to hand in control to the objectInterruption
        self.call = False
        from .Globals import G

        # G.ObjectInterruptionList.append(self)
        # append the interruption to the list that victim (if any) holds
        if self.victim:
            if isinstance(self.victim.objectProperties, list):
                self.victim.objectProperties.append(self)
        # list of expected signals of an interruption (values can be used as flags to inform on which signals is the interruption currently yielding)
        self.expectedSignals = {
            # "victimOffShift": 0,
            # "victimOnShift": 0,
            "victimStartsProcessing": 0,
            "victimEndsProcessing": 0,
            "isCalled": 0,
            # "endedLastProcessing": 0,
            # "victimIsEmptyBeforeMaintenance": 0,
            # "resourceAvailable": 0,
            "victimFailed": 0,
            "contribution": 0,
            "victimIsInterrupted": 0,
            "victimResumesProcessing": 0
        }

    def initialize(self):
        from .Globals import G

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
            # "victimOffShift": 0,
            # "victimOnShift": 0,
            "victimStartsProcessing": 0,
            "victimEndsProcessing": 0,
            "isCalled": 0,
            # "endedLastProcessing": 0,
            # "victimIsEmptyBeforeMaintenance": 0,
            # " resourceAvailable": 0,
            "victimFailed": 0,
            "contribution": 0,
            "victimIsInterrupted": 0,
            "victimResumesProcessing": 0
        }

    # ===========================================================================
    # the main process of the core object
    # this is dummy, every object must have its own implementation
    # ===========================================================================
    def run(self):
        raise NotImplementedError("Subclass must define 'run' method")

    # =======================================================================
    #           hand in the control to the objectIterruption.run
    #                   to be called by the machine
    # TODO: consider removing this method,
    #     signalling can be done via Machine request/releaseOperator
    # =======================================================================
    def invoke(self):
        if self.expectedSignals["isCalled"]:
            succeedTuple = (self.victim, self.env.now)
            self.sendSignal(
                receiver=self, signal=self.isCalled, succeedTuple=succeedTuple
            )

    # ===========================================================================
    # returns the internal queue of the victim
    # ===========================================================================
    def getVictimQueue(self):
        return self.victim.getActiveObjectQueue()

    # ===========================================================================
    # check if the victim's internal queue is empty
    # ===========================================================================
    def victimQueueIsEmpty(self):
        return len(self.getVictimQueue()) == 0

    # ===========================================================================
    # prints message to the console
    # ===========================================================================
    # print message in the console. Format is (Simulation Time | Entity or Frame Name | message)
    def printTrace(self, entityName, message):
        from .Globals import G

        if G.console == "Yes":  # output only if the user has selected to
            print((self.env.now, entityName, message))
