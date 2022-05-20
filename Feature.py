import pandas as pd
from manpy.simulation.imports import RandomNumberGenerator, ObjectInterruption, Machine


class Feature(ObjectInterruption):
    """
    The Feature ObjectInterruption generates Features for a Machine without actually interrupting it
    :param id: The id of the Feature
    :param name: The name of the Feature
    :param victim: The machine to which the feature belongs
    :param deteriorationType: The way the time until the next Feature is counted
    :param distribution: The statisticcal distribution of the time and value of the Feature
    :param kw: The keyword arguments are mainly used for classification and calculation
    """
    def __init__(self, id="", name="", victim=None, deteriorationType="constant", distribution={}, **kw):
        ObjectInterruption.__init__(self, id, name, victim=victim)
        self.rngTime = RandomNumberGenerator(self, distribution.get("Time", {"Fixed": {"mean": 100}}))
        self.rngFeature = RandomNumberGenerator(self, distribution.get("Feature", {"Fixed": {"mean": 10}}))
        self.id = id
        self.name = name
        self.type = "Failure"

        # shows how the time to failure is measured
        # 'constant' means it counts not matter the state of the victim
        # 'working' counts only working time
        self.deteriorationType = deteriorationType

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
            self.featureValue = self.rngFeature.generateNumber()

            # add Feature to DataFrame
            self.outputTrace(self.victim.name, self.victim.id, str(self.featureValue))

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


class Machine(Machine):
    #Just accessed a single line to fix a bug
    def operation(self, type="Processing"):
        # assert that the type is not None and is one of the already implemented ones
        assert type != None, "there must be an operation type defined"
        assert type in set(
            ["Processing", "Setup"]
        ), "the operation type provided is not yet defined"
        # identify the method to get the operation time and initialise the totalOperationTime
        if type == "Setup":
            self.totalOperationTime = self.totalSetupTime
        elif type == "Processing":
            self.totalOperationTime = self.totalWorkingTime
            # if there are task_ids defined for each step
            if self.currentEntity.schedule[-1].get("task_id", None):
                # if exit Time is defined for the previous step of the schedule then add a new step for processing (the previous step is setup and is concluded)
                if self.currentEntity.schedule[-1].get("exitTime", None):
                    # define a new schedule step for processing
                    self.currentEntity.schedule.append(
                        {
                            "station": self,
                            "entranceTime": self.env.now,
                            "task_id": self.currentEntity.currentStep["task_id"],
                        }
                    )
        # variables dedicated to hold the processing times, the time when the Entity entered,
        # and the processing time left
        # get the operation time, tinMStarts holds the processing time of the machine
        self.totalOperationTimeInCurrentEntity = self.calculateTime(type)
        # timer to hold the operation time left
        self.tinM = self.totalOperationTimeInCurrentEntity
        self.timeToEndCurrentOperation = self.env.now + self.tinM
        # variables used to flag any interruptions and the end of the processing
        self.interruption = False
        # local variable that is used to check whether the operation is concluded
        operationNotFinished = True
        # if there is a failure that depends on the working time of the Machine
        # send it the victimStartsProcess signal
        for oi in self.objectInterruptions:
            if oi.type == "Failure":
                if oi.deteriorationType == "working": #deleted one if line which was causing errors
                    self.sendSignal(receiver=oi, signal=oi.victimStartsProcess)
        # this loop is repeated until the processing time is expired with no failure
        # check when the processingEndedFlag switched to false
        while operationNotFinished:
            self.expectedSignals["interruptionStart"] = 1
            self.expectedSignals["preemptQueue"] = 1
            self.expectedSignals["processOperatorUnavailable"] = 1
            # dummy variable to keep track of the time that the operation starts after every interruption

            # update timeLastOperationStarted both for Machine and Operator (if any)
            self.timeLastOperationStarted = self.env.now
            if self.currentOperator:
                self.currentOperator.timeLastOperationStarted = self.env.now
            #             # if the type is setup then the time to record is timeLastProcessingStarted
            #             if type=='Setup':
            #                 self.timeLastSetupStarted=self.timeLastOperationStarted
            #             # else if the type is processing then the time to record is timeLastProcessingStarted
            #             elif type=='Processing':
            #                 self.timeLastProcessingStarted=self.timeLastOperationStarted
            # processing starts, update the flags
            self.isProcessing = True
            self.currentlyPerforming = type
            # wait for the processing time left tinM, if no interruption occurs then change the processingEndedFlag and exit loop,
            #     else (if interrupted()) set interruption flag to true (only if tinM==0),
            #     and recalculate the processing time left tinM, passivate while waiting for repair.
            # if a preemption has occurred then react accordingly (proceed with getting the critical entity)
            receivedEvent = yield self.env.any_of(
                [
                    self.interruptionStart,
                    self.env.timeout(self.tinM),
                    self.preemptQueue,
                    self.processOperatorUnavailable,
                ]
            )
            # if a failure occurs while processing the machine is interrupted.
            if self.interruptionStart in receivedEvent:
                transmitter, eventTime = self.interruptionStart.value
                assert (
                    eventTime == self.env.now
                ), "the interruption has not been processed on the time of activation"
                self.interruptionStart = self.env.event()
                self.interruptionActions(type)  # execute interruption actions
                # ===========================================================
                # # release the operator if there is interruption
                # ===========================================================
                if self.shouldYield(
                    operationTypes={str(type): 1}, methods={"isOperated": 1}
                ):
                    yield self.env.process(self.release())
                # loop until we reach at a state that there is no interruption
                while 1:
                    self.expectedSignals["interruptionEnd"] = 1
                    yield self.interruptionEnd  # interruptionEnd to be triggered by ObjectInterruption
                    transmitter, eventTime = self.interruptionEnd.value
                    assert (
                        eventTime == self.env.now
                    ), "the interruptionEnd was received later than anticipated"
                    self.interruptionEnd = self.env.event()

                    # check if the machine is active and break
                    if self.checkIfActive():
                        if self.shouldYield(
                            operationTypes={str(type): 1}, methods={"isInterrupted": 0}
                        ):
                            self.timeWaitForOperatorStarted = self.env.now
                            yield self.env.process(self.request())
                            self.timeWaitForOperatorEnded = self.env.now
                            self.operatorWaitTimeCurrentEntity += (
                                self.timeWaitForOperatorEnded
                                - self.timeWaitForOperatorStarted
                            )
                        break
                    self.postInterruptionActions()  # execute interruption actions
                    # ===========================================================
                    # # request a resource after the repair
                    # ===========================================================
                    if self.shouldYield(
                        operationTypes={str(type): 1}, methods={"isInterrupted": 0}
                    ):
                        self.timeWaitForOperatorStarted = self.env.now
                        yield self.env.process(self.request())
                        self.timeWaitForOperatorEnded = self.env.now
                        self.operatorWaitTimeCurrentEntity += (
                            self.timeWaitForOperatorEnded
                            - self.timeWaitForOperatorStarted
                        )

            # if the processing operator left
            elif self.processOperatorUnavailable in receivedEvent:
                transmitter, eventTime = self.processOperatorUnavailable.value
                assert (
                    self.env.now == eventTime
                ), "the operator leaving has not been processed at the time it should"
                self.processOperatorUnavailable = self.env.event()
                # carry interruption actions
                self.interruptionActions(type)
                # ===========================================================
                # # release the operator
                # ===========================================================
                self.currentOperator.totalWorkingTime += (
                    self.env.now - self.currentOperator.timeLastOperationStarted
                )
                yield self.env.process(self.release())
                from manpy.simulation.Globals import G

                # append the entity that was stopped to the pending ones
                if G.RouterList:
                    G.pendingEntities.append(self.currentEntity)
                # ===========================================================
                # # request a resource after the interruption
                # ===========================================================
                self.timeWaitForOperatorStarted = self.env.now
                yield self.env.process(self.request())
                self.timeWaitForOperatorEnded = self.env.now
                self.operatorWaitTimeCurrentEntity += (
                    self.timeWaitForOperatorEnded - self.timeWaitForOperatorStarted
                )
                # carry post interruption actions
                self.postInterruptionActions()

            # if the station is reactivated by the preempt method
            elif self.shouldPreempt:
                if self.preemptQueue in receivedEvent:
                    transmitter, eventTime = self.preemptQueue.value
                    assert (
                        eventTime == self.env.now
                    ), "the preemption must be performed on the time of request"
                    self.preemptQueue = self.env.event()
                    self.interruptionActions(type)  # execute interruption actions
                # ===========================================================
                # # release the operator if there is interruption
                # ===========================================================
                if self.shouldYield(
                    operationTypes={str(self.currentlyPerforming): 1},
                    methods={"isOperated": 1},
                ):
                    yield self.env.process(self.release())
                self.postInterruptionActions()  # execute interruption actions
                break
            # if no interruption occurred the processing in M1 is ended
            else:
                if self.processOperatorUnavailable.triggered:
                    self.processOperatorUnavailable = self.env.event()
                operationNotFinished = False