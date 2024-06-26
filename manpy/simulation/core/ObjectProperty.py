# ===========================================================================
# TODO new copyright notice
# ===========================================================================

"""
Created on 18 Aug 2013

@author: LodesL
"""


# from SimPy.Simulation import Process, Resource, reactivate, now
from manpy.simulation.ManPyObject import ManPyObject
from manpy.simulation.RandomNumberGenerator import RandomNumberGenerator
from manpy.simulation.core.utils import info
import pandas as pd


class ObjectProperty(ManPyObject):
    """
    Abstract class for all kinds of object properties that are generated in somehow regular interval. Example: Features
    """

    def __init__(
        self,
        id="",
        name="",
        victim=None,
        distribution={},
        distribution_state_controller=None,
        reset_distributions=True,
        no_negative=False,
        contribute=None,
        start_time=0,
        end_time=0,
        start_value=None,
        random_walk=False,
        dependent=None,
        **kw
    ):
        ManPyObject.__init__(self, id, name)
        self.victim = victim
        # variable used to hand in control to the objectInterruption
        self.call = False
        from manpy.simulation.core.Globals import G

        # G.ObjectInterruptionList.append(self)
        # append the interruption to the list that victim (if any) holds
        if self.victim:
            if isinstance(self.victim.objectProperties, list):
                self.victim.objectProperties.append(self)
        # list of expected signals of an interruption (values can be used as flags to inform on which signals is the interruption currently yielding)
        self.expectedSignals = {
            "victimStartsProcessing": 0,
            "victimEndsProcessing": 0,
            "isCalled": 0,
            "victimFailed": 0,
            "contribution": 0,
            "victimIsInterrupted": 0,
            "victimResumesProcessing": 0
        }

        self.id = id
        self.name = name

        self.distribution_state_controller = distribution_state_controller
        self.reset_distributions = reset_distributions

        if self.distribution_state_controller:
            self.distribution, _ = self.distribution_state_controller.get_initial_state()
        else:
            self.distribution = distribution

        # check_config_dict(self.distribution, ["Feature", "Time"], name)

        if not self.distribution.keys().__contains__("Feature"):
            info(f"Defaulting to {{'Fixed': {{'mean': 10}}}} for {self.name}")
            self.distribution["Feature"] = {"Fixed": {"mean": 10}}

        self.rngTime = RandomNumberGenerator(self, self.distribution.get("Time", {"Fixed": {"mean": 1}}))
        self.rngFeature = RandomNumberGenerator(self, self.distribution.get("Feature"))

        self.no_negative = no_negative
        self.contribute = contribute
        self.start_time = start_time
        self.featureValue = None

        self.start_value = start_value

        if start_value:
            self.featureHistory = [start_value]
            self.featureValue = self.featureHistory[-1]
        else:
            self.featureHistory = []
        self.end_time = end_time
        self.random_walk = random_walk
        self.dependent = dependent
        self.type = "Feature"

    def initialize(self):
        from manpy.simulation.core.Globals import G

        self.env = G.env
        self.call = False
        # events that are send by one interruption to all the other interruptions that might wait for the
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

    def printTrace(self, entityName, message):
        """print message in the console. Format is (Simulation Time | Entity or Frame Name | message)"""

        from manpy.simulation.core.Globals import G

        if G.console == "Yes":  # output only if the user has selected to
            print((self.env.now, entityName, message))

    def get_feature_value(self):
        """Returns the current value of the feature."""
        return self.featureValue

    def outputTrace(self, entity_name: str, entity_id: str, message: str):
        """
        Overwrites the ouputTrace function to better suite Features

        :param entity_name: The Name of the target Machine
        :param entity_id: The ID of the target Machine
        :param message: The value of the Feature

        :return: None
        """
        from manpy.simulation.core.Globals import G

        if G.trace:
            G.trace_list.append([G.env.now, entity_name, entity_id, self.id, self.name, message])

        if G.snapshots:
            entities_list = []
            now = G.env.now

            for obj in G.ObjList:
                if obj.type == "Machine":
                    entities = [x.id for x in obj.Res.users]
                    entities_list.append((now, obj.id, entities))

            snapshot = pd.DataFrame(entities_list, columns=["sim_time", "station_id", "entities"])
            if not G.simulation_snapshots[-1].equals(snapshot):
                G.simulation_snapshots.append(snapshot)

