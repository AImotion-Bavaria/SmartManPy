
from manpy.simulation.core.ObjectProperty import ObjectProperty
from manpy.simulation.RandomNumberGenerator import RandomNumberGenerator
from manpy.simulation.core.Globals import G
from scipy import interpolate
import copy


class Timeseries(ObjectProperty):
    """
    The TimeSeries ObjectProperty generates TimeSeries for a Machine and stores them in Entities
    :param id: The id of the Feature
    :param name: The name of the Feature
    :param victim: The machine to which the feature belongs
    :param distribution: The statistical distribution of the value of the Datapoints
    :param distribution_state_controller: StateController that can contain different distributions.
    :param reset_distributions: Active with deteriorationType working; Resets distribution_state_controller when the
           victim is interrupted (=repaired)
    :param no_negative: If this value is true, returns 0 for values below 0 of the feature value
    :param contribute: Needs Failures in a list as an input to contribute the TimeSeries value to conditions
    :param start_time: The starting time for the TimeSeries
    :param end_time: The end time for the TimeSeries
    :param start_value: The starting value of the TimeSeries
    :param random_walk: If this is True, the TimeSeries will continuously take the previous Datapoint value into account
    :param step_time: The time between each Datapoint for a TimeSeries
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
                                steptime=step_time
                                )
        G.TimeSeriesList.append(self)
        self.step_time = step_time


    def initialize(self):
        ObjectProperty.initialize(self)


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
            interval = None
            last_interval = None
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

                    # set other features as variables that are used in this timeseries
                    for key in list(self.distribution.keys()):
                        if key not in ["Function", "DataPoints", "Feature"]:
                            locals()[key] = self.distribution.get(key).featureValue

                    # set the interval that is currently being used
                    x = self.intervals[0][0] + (self.stepsize * steps)
                    for idx, i in enumerate(self.intervals):
                        if i[0] <= x <= i[1]:
                            interval = self.intervals[idx]
                            break

                    # check if the interval changed
                    if last_interval != interval:
                        f = None

                    # interpolate or not
                    if type(self.distribution["Function"][interval]) == list:
                        # set f for interpolation
                        if f == None:
                            if interval == (60, 100):
                                pass
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

                    # check random walk
                    if self.random_walk == True:
                        self.featureValue += value
                    else:
                        self.featureValue = value

                    # check no_negative
                    if self.no_negative == True:
                        if self.featureValue < 0:
                            self.featureValue = 0


                    self.featureHistory.append(self.featureValue)
                    self.timeHistory.append(x)

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
                    last_interval = interval

                    # check if it was the last step
                    if steps == self.distribution["DataPoints"]:
                        self.expectedSignals["victimEndsProcessing"] = 0
                        self.expectedSignals["victimIsInterrupted"] = 0
                        remainingTimeTillFeature = None
                        machineIsRunning = False
