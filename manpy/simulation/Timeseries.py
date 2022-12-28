
from .ObjectProperty import ObjectProperty
from .RandomNumberGenerator import RandomNumberGenerator
from manpy.simulation.Globals import G
import copy


class Timeseries(ObjectProperty):
    """
    The Feature ObjectInterruption generates Features for a Machine
    :param id: The id of the Feature
    :param name: The name of the Feature
    :param victim: The machine to which the feature belongs
    :param deteriorationType: The way the time until the next Feature is counted, working counts only during the operation of the victim, constant is constant
    :param distribution: The statistical distribution of the time and value of the Feature
    :param distribution_state_controller: StateController that can contain different distributions.
    :param reset_distributions: Active with deteriorationType working; Resets distribution_state_controller when the
           victim is interrupted (=repaired)
    :param repairman: The resource that may be needed to fix the failure
    :param no_negative: If this value is true, returns 0 for values below 0 of the feature value
    :param contribute: Needs Failures in a list as an input to contribute the Feature value to conditions
    :param entity: If this value is true, saves the Feature value inside the current Entity
    :param start_time: The starting time for the feature
    :param end_time: The end time for the feature
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
        distribution={},
        distribution_state_controller=None,
        reset_distributions=True,
        no_negative=False,
        contribute=None,
        start_time=0,
        end_time=0,
        start_value=0,
        random_walk=False,
        dependent=None,
        **kw
    ):
        ObjectProperty.__init__(self, id,
                                name,
                                victim=victim,
                                distribution=distribution,
                                distribution_state_controller=distribution_state_controller,
                                reset_distributions=reset_distributions,
                                no_negative=no_negative,
                                contribute=contribute,
                                start_time=start_time,
                                end_time=end_time,
                                start_value=start_value,
                                random_walk=random_walk,
                                dependent=dependent
                                )


    def initialize(self):
        ObjectProperty.initialize(self)

        if self.dependent:
            for key in list(self.dependent.keys()):
                if key != "Function":
                    self.distribution["DataPoints"] = self.dependent.get(key).distribution["DataPoints"]
        else:
            self.stepsize = (self.distribution["Interval"][1] - self.distribution["Interval"][0]) / self.distribution["DataPoints"]
        self.victimIsInterrupted = self.env.event()
        self.victimStartsProcessing = self.env.event()
        self.victimEndsProcessing = self.env.event()

    def run(self):
        """Every Object has to have a run method. Simpy is mainly used in this function
        :return: None
        """

        while 1:
            machineIsRunning = True

            # wait for victim to start process
            self.expectedSignals["victimStartsProcessing"] = 1
            yield self.victimStartsProcessing
            self.victimStartsProcessing = self.env.event()

            steptime = self.victim.tinM / self.distribution["DataPoints"]
            remainingTimeTillFeature = steptime
            steps = 0

            while machineIsRunning:
                timeRestartedCounting = self.env.now
                self.expectedSignals["victimEndsProcessing"] = 1
                self.expectedSignals["victimIsInterrupted"] = 1

                receivedEvent = yield self.env.any_of([
                    self.env.timeout(remainingTimeTillFeature),
                    self.victimIsInterrupted,
                    self.victimEndsProcessing
                ])

                if self.victimIsInterrupted in receivedEvent:
                    self.victimIsInterrupted = self.env.event()
                    remainingTimeTillFeature = remainingTimeTillFeature - (self.env.now - timeRestartedCounting)

                    # state_controller
                    if self.distribution_state_controller and self.reset_distributions:
                        self.distribution_state_controller.reset()

                    # wait for victim to start processing again
                    self.expectedSignals["victimResumesProcessing"] = 1
                    yield self.victimResumesProcessing
                    self.victimResumesProcessing = self.env.event()

                elif self.victimEndsProcessing in receivedEvent:
                    self.victimEndsProcessing = self.env.event()
                    remainingTimeTillFeature = remainingTimeTillFeature - (self.env.now - timeRestartedCounting)

                    if self.distribution_state_controller:
                        self.distribution = self.distribution_state_controller.get_and_update()
                        # TODO is this necessary? does it make sense to change the time?
                        self.rngTime = RandomNumberGenerator(self,
                                                             self.distribution.get("Time", {"Fixed": {"mean": 1}}))
                        self.rngFeature = RandomNumberGenerator(self, self.distribution.get("Feature"))
                else:
                    # generate the Feature
                    if self.dependent:
                        for key in list(self.dependent.keys()):
                            if key != "Function":
                                locals()[key] = self.dependent.get(key).featureValue
                                locals()[key + '_history'] = self.dependent.get(key).featureHistory
                        self.distribution["Feature"][list(self.distribution["Feature"].keys())[0]]["mean"] = eval(self.dependent["Function"])
                        self.rngFeature = RandomNumberGenerator(self, self.distribution.get("Feature"))
                        value = self.rngFeature.generateNumber(start_time=self.start_time)

                    else:
                        x = self.distribution["Interval"][0] + (self.stepsize * steps)
                        self.distribution["Feature"][list(self.distribution["Feature"].keys())[0]]["mean"] = eval(
                            self.distribution["Function"])
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

                    # send data to QuestDB
                    # TODO: make it work with floats
                    self.featureValue = int(self.featureValue)
                    # try:
                    if G.db:
                        G.sender.row(
                            self.name,
                            columns={"time": self.env.now, "value": self.featureValue}
                        )
                        G.sender.flush()
                    # except:
                    #     print("Quest-DB error: TimeSeries")

                    # check contribution
                    if self.contribute != None:
                        for c in self.contribute:
                            if c.expectedSignals["contribution"]:
                                self.sendSignal(receiver=c, signal=c.contribution)

                    # add Feature value and time to Entity
                    self.victim.Res.users[0].set_feature(self.featureValue, self.env.now,
                                                         (self.id, self.victim.id))
                    self.outputTrace(self.victim.Res.users[0].name, self.victim.Res.users[0].id,
                                     str(self.featureValue))





                        # if self.random_walk == True:
                        #     self.featureValue += value
                        # else:
                        #     self.featureValue = value
                        #
                        # # check no_negative
                        # if self.no_negative == True:
                        #     if self.featureValue < 0:
                        #         self.featureValue = 0
                        #
                        # self.featureHistory.append(self.featureValue)
                        #
                        # # send data to QuestDB
                        # try:
                        #     if G.db:
                        #         G.sender.row(
                        #             self.name,
                        #             columns={"time": self.env.now, "value": self.featureValue}
                        #         )
                        #         G.sender.flush()
                        # except:
                        #     print("Quest-DB error: non-dependent TS")
                        #
                        # # check contribution
                        # if self.contribute != None:
                        #     for c in self.contribute:
                        #         if c.expectedSignals["contribution"]:
                        #             self.sendSignal(receiver=c, signal=c.contribution)
                        #
                        # # add Feature value and time to Entity
                        # self.victim.Res.users[0].set_feature(self.featureValue, self.env.now,
                        #                                      (self.id, self.victim.id))
                        # self.outputTrace(self.victim.Res.users[0].name, self.victim.Res.users[0].id,
                        #                  str(self.featureValue))



                    remainingTimeTillFeature = steptime
                    steps += 1

                    # check if it was the last step
                    if steps == self.distribution["DataPoints"]:
                        self.expectedSignals["victimEndsProcessing"] = 0
                        self.expectedSignals["victimIsInterrupted"] = 0
                        remainingTimeTillFeature = None
                        machineIsRunning = False
