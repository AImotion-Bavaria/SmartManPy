
from .ObjectProperty import ObjectProperty
from .RandomNumberGenerator import RandomNumberGenerator
from manpy.simulation.Globals import G


class Feature(ObjectProperty):
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
        start_value=None,
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
        if start_value != None:
            self.featureValue = start_value
            self.featureHistory = [start_value]
        else:
            self.featureValue = 0
            self.featureHistory = []


    def initialize(self):

        ObjectProperty.initialize(self)
        self.victimIsInterrupted = self.env.event()
        self.victimResumesProcessing = self.env.event()
        self.victimEndsProcessing = self.env.event()

    def generate_feature(self):
        if self.dependent:
            if self.name == "Pmax":
                pass
            for key in list(self.dependent.keys()):
                if key != "Function":
                    locals()[key] = self.dependent.get(key).featureValue
                    locals()[key + '_history'] = self.dependent.get(key).featureHistory

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

    def run(self):
        """Every Object has to have a run method. Simpy is mainly used in this function
        :return: None
        """

        while 1:
            self.generate_feature()
            self.expectedSignals["victimEndsProcessing"] = 1
            self.expectedSignals["victimIsInterrupted"] = 1

            receivedEvent = yield self.env.any_of([
               self.victimIsInterrupted,
               self.victimEndsProcessing
            ])

            if self.victimIsInterrupted in receivedEvent:
                self.victimIsInterrupted = self.env.event()
                # print(f"{self.name}: victimIsInterrupted")
                # wait for victim to start processing again
                self.expectedSignals["victimResumesProcessing"] = 1

                if self.distribution_state_controller and self.reset_distributions:
                    self.distribution_state_controller.reset()

                yield self.victimResumesProcessing

                # print(f"{self.name} Resuming")
                self.victimResumesProcessing = self.env.event()
            elif self.victimEndsProcessing in receivedEvent:
                self.label = None
                self.victimEndsProcessing = self.env.event()

                # print(f"{self.name} received victimEndsProcessing")

                if self.distribution_state_controller:
                    self.distribution, self.label = self.distribution_state_controller.get_and_update()
                    self.rngFeature = RandomNumberGenerator(self, self.distribution.get("Feature"))
                    self.generate_feature()

                # add featureValue to History
                self.featureHistory.append(self.featureValue)

                # send data to DataBase
                from manpy.simulation.Globals import G
                try:
                    if G.db:
                        self.featureValue = int(self.featureValue)
                        G.db.insert(self.name, {"time": self.env.now, "value": self.featureValue})
                        G.db.commit()
                except:
                    print("Quest-DB error: Feature")

                # check contribution
                if self.contribute != None:
                    for c in self.contribute:
                        if c.expectedSignals["contribution"]:
                            self.sendSignal(receiver=c, signal=c.contribution)


                # add Feature value and time to Entity
                try:
                    self.victim.activeEntity.set_feature(self.featureValue, self.label, self.env.now, (self.id, self.victim.id))
                    self.outputTrace(self.victim.activeEntity.name, self.victim.activeEntity.id, str(self.featureValue))
                except IndexError:
                    print(self.victim.activeEntity)


                # add Feature to Trace
                if self.victim == None:
                    self.outputTrace("--", "--", self.featureValue)
                else:
                    self.outputTrace(self.victim.name, self.victim.id, str(self.featureValue))

                if self.victim:
                    if self.victim.expectedSignals["objectPropertyEnd"]:
                        self.sendSignal(receiver=self.victim, signal=self.victim.objectPropertyEnd)

            else:
                self.expectedSignals["victimEndsProcessing"] = 0
                self.expectedSignals["victimIsInterrupted"] = 0
