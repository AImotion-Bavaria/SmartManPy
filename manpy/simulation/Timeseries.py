
from .ObjectProperty import ObjectProperty
from .RandomNumberGenerator import RandomNumberGenerator
from manpy.simulation.Globals import G
from scipy import interpolate
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
        step_time=None,
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
                                dependent=dependent,
                                steptime=step_time
                                )
        G.TimeSeriesList.append(self)
        self.step_time = step_time


    def initialize(self):
        ObjectProperty.initialize(self)

        if self.dependent:
            for key in list(self.dependent.keys()):
                if key != "Function":
                    self.distribution["DataPoints"] = self.dependent.get(key).distribution["DataPoints"]
            self.step_time = self.dependent.get(key).step_time
        else:
            # put all intervals into a sorted list
            self.intervals = []
            for i in self.distribution["Function"].keys():
                self.intervals.append(i)
            self.intervals.sort()

            # check if intervals overlap
            for i in range(len(self.intervals) - 1):
                if self.intervals[i][1] > self.intervals[i+1][0]:
                    raise Exception("Intervals {} and {} from {} overlap".format(self.intervals[i], self.intervals[i+1], self.name))

            self.stepsize = (self.intervals[-1][1] - self.intervals[0][0]) / (self.distribution["DataPoints"] - 1)

        self.victimIsInterrupted = self.env.event()
        self.victimStartsProcessing = self.env.event()
        self.victimEndsProcessing = self.env.event()

    def run(self):
        """Every Object has to have a run method. Simpy is mainly used in this function
        :return: None
        """

        while 1:
            machineIsRunning = True

            # wait for victim to start process if it is not already processing
            if self.victim.operationNotFinished == True or self.env.now == 0:
                self.expectedSignals["victimStartsProcessing"] = 1
                yield self.victimStartsProcessing
                self.victimStartsProcessing = self.env.event()

            self.featureHistory = []
            self.timeHistory = []
            if self.step_time == None:
                step_time = self.victim.tinM / self.distribution["DataPoints"]
            else:
                step_time = self.step_time
            remainingTimeTillFeature = 0
            steps = 0
            interval = 0
            f = None

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
                        self.rngFeature = RandomNumberGenerator(self, self.distribution.get("Feature"))
                else:
                    # generate the Feature
                    self.label = None
                    if self.dependent:
                        for key in list(self.dependent.keys()):
                            if key != "Function":
                                locals()[key] = self.dependent.get(key).featureValue
                                locals()[key + '_history'] = self.dependent.get(key).featureHistory
                        self.distribution["Feature"][list(self.distribution["Feature"].keys())[0]]["mean"] = eval(self.dependent["Function"])
                        self.rngFeature = RandomNumberGenerator(self, self.distribution.get("Feature"))
                        value = self.rngFeature.generateNumber(start_time=self.start_time)

                    else:
                        for key in list(self.distribution.keys()):
                            if key not in ["Function", "DataPoints", "Feature"]:
                                locals()[key] = self.distribution.get(key).featureValue

                        x = self.intervals[0][0] + (self.stepsize * steps)
                        for idx, i in enumerate(self.intervals):
                            if i[0] <= x <= i[1]:
                                interval = self.intervals[idx]
                                break

                        if type(self.distribution["Function"][interval]) == list:
                            # set f for interpolation
                            if f == None:
                                data = copy.deepcopy(self.distribution["Function"][interval])
                                for i, axes in enumerate(data):
                                    for j, coord in enumerate(axes):
                                        if type(coord) == str:
                                            data[i][j] = eval(coord)
                                xs = data[0]
                                ys = data[1]
                                f = interpolate.UnivariateSpline(xs, ys)
                            # calculate mean for interpolation
                            try :
                                if min(xs) <= x <= max(xs):
                                    self.distribution["Feature"][list(self.distribution["Feature"].keys())[0]]["mean"] = f(x)
                                else:
                                    self.distribution["Feature"][list(self.distribution["Feature"].keys())[0]]["mean"] = 0
                            except:
                                print("Interpolation needs at least 4 values")
                        else:
                            self.distribution["Feature"][list(self.distribution["Feature"].keys())[0]]["mean"] = eval(self.distribution["Function"][interval])
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
                    self.timeHistory.append(self.env.now)

                    # add TimeSeries value and time to Entity
                    ent = self.victim.Res.users[0]
                    self.victim.Res.users[0].set_timeseries(self.featureHistory, self.label, self.timeHistory,
                                                         (self.id, self.victim.id))
                    self.outputTrace(self.victim.Res.users[0].name, self.victim.Res.users[0].id, str(self.featureValue))

                    # send data to QuestDB
                    # try:
                    if G.db:
                        G.db.insert(self.name, {"time": self.env.now, "value": self.featureValue})
                        G.db.commit()
                    # except:
                    #     print("Quest-DB error: TimeSeries")

                    # check contribution
                    if self.contribute != None:
                        for c in self.contribute:
                            if c.expectedSignals["contribution"]:
                                self.sendSignal(receiver=c, signal=c.contribution)


                    remainingTimeTillFeature = step_time
                    steps += 1

                    # check if it was the last step
                    if steps == self.distribution["DataPoints"]:
                        self.expectedSignals["victimEndsProcessing"] = 0
                        self.expectedSignals["victimIsInterrupted"] = 0
                        remainingTimeTillFeature = None
                        machineIsRunning = False
