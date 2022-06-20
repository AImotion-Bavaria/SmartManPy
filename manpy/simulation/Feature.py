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
    :param threshold: If this threshold is exceeded or subceeded, a Failure will commence
    :param repairman: The resource that may be needed to fix the failure
    :param no_negative: If this value is true, returns 0 for values below 0 of the feature value
    :param kw: The keyword arguments are mainly used for classification and calculation
    """
    def __init__(self, id="", name="", victim=None, deteriorationType="constant", distribution={}, contribution=None, repairman=None, no_negative=False, start_time=0, start_value=0, **kw):
        ObjectInterruption.__init__(self, id, name, victim=victim)
        self.rngTime = RandomNumberGenerator(self, distribution.get("Time", {"Fixed": {"mean": 100}}))
        self.rngFeature = RandomNumberGenerator(self, distribution.get("Feature", {"Fixed": {"mean": 10}}))
        self.rngTTR = RandomNumberGenerator(self, distribution.get("TTR", {"Fixed": {"mean": 10}}))
        self.repairman = repairman
        self.id = id
        self.name = name
        self.type = "Failure"
        self.deteriorationType = deteriorationType
        self.contribution = contribution
        self.no_negative = no_negative
        self.start_time = start_time
        self.featureValue = start_value

    def initialize(self):
        ObjectInterruption.initialize(self)
        self.victimStartsProcess = self.env.event()
        self.victimEndsProcess = self.env.event()

    def run(self):
        """Every Object has to have a run method. Simpy is mainly useed in this function

        :timeTillFeature: The time until the next Feature should occur
        :featureNotTriggered: Wether or not the Feature has already been generated

        :return: None
        """
        while 1:
            timeTillFeature = self.rngTime.generateNumber()
            remainingTimeTillFeature = timeTillFeature
            featureNotTriggered = True

            # if time to failure counts not matter the state of the victim
            if self.deteriorationType == "constant":
                yield self.env.timeout(remainingTimeTillFeature)

            # if time to failure counts only in working time
            elif self.deteriorationType == "working":
                # wait for victim to start process
                yield self.victimStartsProcess

                self.victimStartsProcess = self.env.event()
                while featureNotTriggered:
                    timeRestartedCounting = self.env.now
                    self.expectedSignals["victimEndsProcess"] = 1

                    # wait either for the feature or end of process
                    receivedEvent = yield self.env.any_of([self.env.timeout(remainingTimeTillFeature), self.victimEndsProcess])
                    if self.victimEndsProcess in receivedEvent:
                        self.expectedSignals["victimEndsProcess"] = 0
                        self.victimEndsProcess = self.env.event()
                        remainingTimeTillFeature = remainingTimeTillFeature - (self.env.now - timeRestartedCounting)

                        # wait for victim to start again processing
                        yield self.victimStartsProcess
                        self.victimStartsProcess = self.env.event()
                    else:
                        featureNotTriggered = False

            # generate the Feature
            self.featureValue = self.rngFeature.generateNumber(start_time=self.start_time)
            if self.no_negative == True:
                if self.featureValue < 0:
                    self.featureValue = 0
            self.outputTrace(self.victim.name, self.victim.id, str(self.featureValue))  # add Feature to DataFrame

            # check contribution
            if self.contribution != None:
                for contribution in self.contribution:
                    self.sendSignal(receiver=contribution, signal=contribution.contribute)



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
