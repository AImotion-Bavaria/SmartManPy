import pandas as pd
from .ObjectInterruption import ObjectInterruption
from .RandomNumberGenerator import RandomNumberGenerator


class Feature(ObjectInterruption):
    """
    The Feature ObjectInterruption generates Features for a Machine
    :param id: The id of the Feature
    :param name: The name of the Feature
    :param victim: The machine to which the feature belongs
    :param deteriorationType: The way the time until the next Feature is counted, working counts only during the operation of the victim, constant is constant
    :param distribution: The statistical distribution of the time and value of the Feature
    :param repairman: The resource that may be needed to fix the failure
    :param no_negative: If this value is true, returns 0 for values below 0 of the feature value
    :param contribute: Needs Failures in a list as an input to contribute the Feature value to conditions
    :param entity: If this value is true, saves the Feature value inside the current Entity
    :param start_time: The starting time for the feature
    :param start_value: The starting value, mainly used when setting up a condition
    :param kw: The keyword arguments are mainly used for classification and calculation
    """
    def __init__(
        self,
        id="",
        name="",
        victim=None,
        deteriorationType="constant",
        distribution={},
        repairman=None,
        no_negative=False,
        contribute=None,
        entity=False,
        start_time=0,
        start_value=0,
        random_walk=False,
        **kw
    ):
        ObjectInterruption.__init__(self, id, name, victim=victim)
        self.id = id
        self.name = name
        self.deteriorationType = deteriorationType
        self.rngTime = RandomNumberGenerator(self, distribution.get("Time", {"Fixed": {"mean": 100}}))
        self.rngFeature = RandomNumberGenerator(self, distribution.get("Feature", {"Fixed": {"mean": 10}}))
        self.repairman = repairman
        self.no_negative = no_negative
        self.contribute = contribute
        self.entity = entity
        self.start_time = start_time
        self.featureValue = start_value
        self.type = "Failure"

    def initialize(self):
        if self.entity == True:
            self.deteriorationType="working"
        ObjectInterruption.initialize(self)
        self.victimStartsProcessing = self.env.event()
        self.victimEndsProcessing = self.env.event()

    def run(self):
        """Every Object has to have a run method. Simpy is mainly used in this function

        :remainingTimeTillFeature: The time until the next Feature should occur
        :featureNotTriggered: Boolean for if the Feature has already been generated

        :return: None
        """
        remainingTimeTillFeature = None
        while 1:
            while remainingTimeTillFeature == None:
                timeTillFeature = self.rngTime.generateNumber(start_time=self.start_time)
                remainingTimeTillFeature = timeTillFeature
                if remainingTimeTillFeature == None:
                    yield self.env.timeout(1)
            featureNotTriggered = True

            # if time to failure counts not matter the state of the victim
            if self.deteriorationType == "constant":
                yield self.env.timeout(remainingTimeTillFeature)

            # if time to failure counts only in working time
            elif self.deteriorationType == "working":
                # wait for victim to start process
                self.expectedSignals["victimStartsProcessing"] = 1
                yield self.victimStartsProcessing
                self.victimStartsProcessing = self.env.event()

                # check if feature belongs to entity
                if self.entity == True:
                    remainingTimeTillFeature = timeTillFeature * self.victim.tinM

                while featureNotTriggered:
                    timeRestartedCounting = self.env.now
                    self.expectedSignals["victimEndsProcessing"] = 1

                    # wait either for the feature or end of process
                    receivedEvent = yield self.env.any_of([self.env.timeout(remainingTimeTillFeature), self.victimEndsProcessing])
                    if self.victimEndsProcessing in receivedEvent:
                        self.victimEndsProcessing = self.env.event()
                        remainingTimeTillFeature = remainingTimeTillFeature - (self.env.now - timeRestartedCounting)

                        # wait for victim to start processing again
                        self.expectedSignals["victimStartsProcessing"] = 1
                        yield self.victimStartsProcessing
                        self.victimStartsProcessing = self.env.event()
                    else:
                        self.expectedSignals["victimEndsProcessing"] = 0
                        remainingTimeTillFeature = None
                        featureNotTriggered = False


            # generate the Feature
            self.featureValue = self.rngFeature.generateNumber(start_time=self.start_time)
            if self.no_negative == True:
                if self.featureValue < 0:
                    self.featureValue = 0
            # check contribution
            if self.contribute != None:
                for c in self.contribute:
                    if c.expectedSignals["contribution"]:
                        self.sendSignal(receiver=c, signal=c.contribution)
            # check Entity
            if self.entity == True:
                self.victim.Res.users[0].set_feature(self.featureValue)
                self.expectedSignals["victimEndsProcessing"] = 1
                yield self.victimEndsProcessing
                self.victimEndsProcessing = self.env.event()
            # add Feature to DataFrame
            self.outputTrace(self.victim.name, self.victim.id, str(self.featureValue))

    def get_feature_value(self):
        return self.featureValue


    def outputTrace(self, entity_name: str, entity_id: str, message: str):
        """Overwrites the ouputTrace function to better suite Features

        :param entity_name: The Name of the target Machine
        :param entity_id: The ID of the target Machine
        :param message: The value of the Feature

        :return: None
        """
        from manpy.simulation.Globals import G

        G.trace_list.append([G.env.now, entity_name, entity_id, self.id, self.name, message])

        entities_list = []
        now = G.env.now

        for obj in G.ObjList:
            if obj.type == "Machine":
                entities = [x.id for x in obj.Res.users]
                entities_list.append((now, obj.id, entities))

        snapshot = pd.DataFrame(entities_list, columns=["sim_time", "station_id", "entities"])
        if not G.simulation_snapshots[-1].equals(snapshot):
            G.simulation_snapshots.append(snapshot)
