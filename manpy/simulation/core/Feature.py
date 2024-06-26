from manpy.simulation.core.Globals import G
from manpy.simulation.core.ObjectProperty import ObjectProperty
from manpy.simulation.RandomNumberGenerator import RandomNumberGenerator
from manpy.simulation.core.utils import check_config_dict


class Feature(ObjectProperty):
    """
    The Feature ObjectProperty generates Features for a Machine and stores them in Entities

    :param id: The id of the Feature
    :param name: The name of the Feature
    :param victim: The machine to which the feature belongs
    :param distribution: The statistical distribution of the value of the Feature
    :param distribution_state_controller: StateController that can contain different distributions.
    :param reset_distributions: Active with deteriorationType working; Resets distribution_state_controller when the
           victim is interrupted (=repaired)
    :param no_negative: If this value is true, returns 0 for values below 0 of the feature value
    :param contribute: Needs Failures in a list as an input to contribute the Feature value to conditions
    :param start_time: The starting time for the feature. If >0, the feature generation is started if start_time is reached
    :param end_time: The end time for the feature. If >0 and > start_time, the feature generation is ended if end_time is reached
    :param start_value: The starting value of the Feature
    :param random_walk: If this is True, the Feature will continuously take the previous feature_value into account
    :param dependent: A dictionary containing a Function and the corresponding variables, to determine dependencies between features
    :param kw: The keyword arguments
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
        G.FeatureList.append(self)

        # Internal label; can be used for quality control -> indicates a defect or similar
        self.label = None

        if start_value != None:
            self.featureValue = start_value
            self.featureHistory = [start_value]
        else:
            self.featureValue = 0
            self.featureHistory = []

    def initialize(self):

        ObjectProperty.initialize(self)

        check_config_dict(self.distribution, ["Feature"], self.name)

        if self.dependent:
            check_config_dict(self.dependent, ["Function"], self.name)

        self.victimIsInterrupted = self.env.event()
        self.victimResumesProcessing = self.env.event()
        self.victimEndsProcessing = self.env.event()

    def generate_feature(self):
        """Generates the actual feature value"""

        if self.dependent:
            for key in list(self.dependent.keys()):
                if key != "Function":
                    locals()[key] = self.dependent.get(key).featureValue
                    locals()[key + '_history'] = self.dependent.get(key).featureHistory

            self.distribution["Feature"][list(self.distribution["Feature"].keys())[0]]["mean"] = eval(
                self.dependent["Function"])
            self.rngFeature = RandomNumberGenerator(self, self.distribution.get("Feature"))

        value = self.rngFeature.generateNumber(start_time=self.start_time, end_time=self.end_time)

        if value is None:
            self.featureValue = None
            return

        if self.random_walk == True:
            if self.featureValue is None:
                self.featureValue = self.start_value
            else:
                self.featureValue += value
        else:
            self.featureValue = value

        # check no_negative
        if self.no_negative == True:
            if self.featureValue < 0:
                self.featureValue = 0

    def run(self):
        """Every Object has to have a run method. Simpy is mainly used in this function
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

                if self.featureValue is None:
                    continue
                # add featureValue to History
                self.featureHistory.append(self.featureValue)

                # send data to QuestDB
                from manpy.simulation.core.Globals import G
                try:
                    if G.db:
                        G.db.insert(self.name, {"time": float(self.env.now), "value": float(self.featureValue)})
                        G.db.commit()
                except:
                    print(f"QuestDB error while trying to insert feature {self.name}")

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
