import pandas as pd
import numpy as np
from .ObjectInterruption import ObjectInterruption
from .RandomNumberGenerator import RandomNumberGenerator
from manpy.simulation.Globals import G


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
    :param start_value: The starting value of the Feature
    :param random_walk: If this is True, the Feature will continuously take the previous feature_value into account
    :param dependent: A dictionary containing a Function and the corresponding variables, to determine dependencies between features
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
        dependent=None,
        timeseries=None,
        **kw
    ):
        ObjectInterruption.__init__(self, id, name, victim=victim)
        self.id = id
        self.name = name
        self.deteriorationType = deteriorationType
        self.distribution = distribution
        if distribution.keys().__contains__("Feature") == False:
            self.distribution["Feature"] = {"Fixed": {"mean": 10}}
        self.rngTime = RandomNumberGenerator(self, self.distribution.get("Time", {"Fixed": {"mean": 100}}))
        self.rngFeature = RandomNumberGenerator(self, self.distribution.get("Feature"))
        self.repairman = repairman
        self.no_negative = no_negative
        self.contribute = contribute
        self.entity = entity
        self.start_time = start_time
        self.featureHistory = [start_value]
        self.featureValue = self.featureHistory[-1]
        self.random_walk = random_walk
        self.dependent = dependent
        self.type = "Feature"
        self.timeseries = timeseries

        G.FeatureList.append(self)

    def initialize(self):
        if self.timeseries != None:
            self.step_time = (self.timeseries["I_time"][1] - self.timeseries["I_time"][0]) / self.timeseries["DataPoints"]
            self.step_value = (self.timeseries["I_value"][1] - self.timeseries["I_value"][0]) / self.timeseries["DataPoints"]
        if self.entity == True:
            self.deteriorationType="working"
        if self.victim == None:
            self.deteriorationType="constant"
            self.entity=False
        ObjectInterruption.initialize(self)
        self.victimStartsProcessing = self.env.event()
        self.victimEndsProcessing = self.env.event()
        self.victimIsInterrupted = self.env.event()
        self.victimResumesProcessing = self.env.event()

    def generate_feature(self, n, value=None):
        print("generate")
        if value:
            self.featureValue = value
        else:
            # check timeseries
            if self.timeseries != None:
                if self.dependent == None:
                    x = self.timeseries["I_value"][0] + (self.stepsize * n)
                    self.distribution["Feature"][list(self.distribution["Feature"].keys())[0]]["mean"] = eval(
                        self.timeseries["Function"])
                    self.rngFeature = RandomNumberGenerator(self, self.distribution.get("Feature"))
                if n + 1 == self.timeseries["DataPoints"]:
                    self.generate_feature(n, 0)
                    n = 0
                else:
                    n += 1

            # check dependent
            if self.dependent:
                for key in list(self.dependent.keys()):
                    if key != "Function":
                        self.dependent["Function"] = self.dependent["Function"].replace(key, str(self.dependent.get(
                            key).featureValue))
                self.distribution["Feature"][list(self.distribution["Feature"].keys())[0]]["mean"] = eval(
                    self.dependent["Function"])
                self.rngFeature = RandomNumberGenerator(self, self.distribution.get("Feature"))

            value = self.rngFeature.generateNumber(start_time=self.start_time)

            if self.random_walk == True:
                self.featureValue += value
            else:
                self.featureValue = value

            # check no_negative
            if self.no_negative == True:
                if self.featureValue < 0:
                    self.featureValue = 0

        self.featureHistory.append(self.featureValue)

        # check contribution
        if self.contribute != None:
            for c in self.contribute:
                if c.expectedSignals["contribution"]:
                    self.sendSignal(receiver=c, signal=c.contribution)

        # send data to QuestDB
        if G.db:
            G.sender.row(
                self.name,
                columns={"time": self.env.now, "value": self.featureValue}
            )
            G.sender.flush()

        # check Entity
        if self.entity == True:
            # add Feature value and time to Entity
            self.victim.Res.users[0].set_feature(self.featureValue, self.env.now, (self.id, self.victim.id))
            self.outputTrace(self.victim.Res.users[0].name, self.victim.Res.users[0].id, str(self.featureValue))
            if self.timeseries == None:
                self.expectedSignals["victimEndsProcessing"] = 1
                yield self.victimEndsProcessing
                self.victimEndsProcessing = self.env.event()

        else:
            # add Feature to DataFrame
            if self.victim == None:
                self.outputTrace("--", "--", self.featureValue)
            else:
                self.outputTrace(self.victim.name, self.victim.id, str(self.featureValue))

        return n

    def run(self):
        """Every Object has to have a run method. Simpy is mainly used in this function

        :remainingTimeTillFeature: The time until the next Feature should occur
        :featureNotTriggered: Boolean for if the Feature has already been generated

        :return: None
        """
        remainingTimeTillFeature = None
        n = 0
        while 1:
            while remainingTimeTillFeature == None:
                timeTillFeature = self.rngTime.generateNumber(start_time=self.start_time)
                remainingTimeTillFeature = timeTillFeature
                if remainingTimeTillFeature == None:
                    yield self.env.timeout(1)
            featureNotTriggered = True

            # time to feature always counts
            if self.deteriorationType == "constant":
                # check if feature is a timeseries
                if self.timeseries != None:
                    if self.env.now < self.timeseries["I_time"][0]:
                        remainingTimeTillFeature = self.timeseries["I_time"][0] - self.env.now
                    elif self.env.now > self.timeseries["I_time"][1]:
                        remainingTimeTillFeature = float("inf")
                    else:
                        remainingTimeTillFeature = self.stepsize
                yield self.env.timeout(remainingTimeTillFeature)

            # time to feature counts only in working time
            elif self.deteriorationType == "working":
                # wait for victim to start process
                self.expectedSignals["victimStartsProcessing"] = 1
                if self.timeseries != None:
                    if n == 0:
                        yield self.victimStartsProcessing
                        self.victimStartsProcessing = self.env.event()
                else:
                    yield self.victimStartsProcessing
                    self.victimStartsProcessing = self.env.event()

                # check if feature belongs to entity
                if self.entity:
                    remainingTimeTillFeature = timeTillFeature * self.victim.tinM

                # check if feature is a timeseries
                if self.timeseries != None:
                    if self.entity:
                        if n == 0:
                            entity_time = self.victim.tinM
                            start = self.env.now
                        if self.victim.timeLastFailureEnded > start:
                            if (entity_time * self.timeseries["I_time"][0]) - (self.env.now - start - (self.victim.timeLastFailureEnded - self.victim.tinM)) > 0:
                                remainingTimeTillFeature = (entity_time * self.timeseries["I_time"][0]) - (self.env.now - start - (self.victim.timeLastFailureEnded - self.victim.tinM))
                            elif (entity_time * self.timeseries["I_time"][1]) - (self.env.now - start - (self.victim.timeLastFailureEnded - self.victim.tinM)) < 0:
                                remainingTimeTillFeature = (1 - self.timeseries["I_time"][1] + self.timeseries["I_time"][0]) * entity_time
                            else:
                                if n == 0:
                                    remainingTimeTillFeature = 0
                                else:
                                    remainingTimeTillFeature = self.stepsize
                        else:
                            if self.env.now < start + entity_time * self.timeseries["I_time"][0]:
                                remainingTimeTillFeature = entity_time * self.timeseries["I_time"][0]
                            # elif self.env.now > start + entity_time * self.timeseries["I_time"][1]:
                            #     remainingTimeTillFeature = (1 - self.timeseries["I_time"][1] + self.timeseries["I_time"][0]) * entity_time
                            else:
                                if n == 0:
                                    remainingTimeTillFeature = 0.1*10**-10
                                    self.generate_feature(n, 0)
                                else:
                                    remainingTimeTillFeature = self.stepsize
                    else:
                        if self.env.now < self.timeseries["I_time"][0]:
                            remainingTimeTillFeature = self.timeseries["I_time"][0] - self.env.now
                        elif self.env.now > self.timeseries["I_time"][1]:
                            remainingTimeTillFeature = float("inf")
                        else:
                            remainingTimeTillFeature = self.stepsize

                while featureNotTriggered:
                    timeRestartedCounting = self.env.now
                    self.expectedSignals["victimEndsProcessing"] = 1
                    self.expectedSignals["victimIsInterrupted"] = 1

                    # wait either for the feature or end of process
                    receivedEvent = yield self.env.any_of([self.env.timeout(remainingTimeTillFeature), self.victimEndsProcessing, self.victimIsInterrupted])
                    if self.victimEndsProcessing in receivedEvent:
                        self.victimEndsProcessing = self.env.event()
                        remainingTimeTillFeature = remainingTimeTillFeature - (self.env.now - timeRestartedCounting)

                        # wait for victim to start processing again
                        self.expectedSignals["victimStartsProcessing"] = 1
                        yield self.victimStartsProcessing
                        self.victimStartsProcessing = self.env.event()
                    elif self.victimIsInterrupted in receivedEvent:
                        self.victimIsInterrupted = self.env.event()
                        remainingTimeTillFeature = remainingTimeTillFeature - (self.env.now - timeRestartedCounting)

                        # wait for victim to start processing again
                        self.expectedSignals["victimResumesProcessing"] = 1
                        yield self.victimResumesProcessing
                        self.victimResumesProcessing = self.env.event()
                    else:
                        self.expectedSignals["victimEndsProcessing"] = 0
                        self.expectedSignals["victimIsInterrupted"] = 0
                        remainingTimeTillFeature = None
                        featureNotTriggered = False

            n = self.generate_feature(n)

    def get_feature_value(self):
        return self.featureValue


    def outputTrace(self, entity_name: str, entity_id: str, message: str):
        """Overwrites the ouputTrace function to better suite Features

        :param entity_name: The Name of the target Machine
        :param entity_id: The ID of the target Machine
        :param message: The value of the Feature

        :return: None
        """
        from .Globals import G

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
