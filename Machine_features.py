import numpy as np
import pandas as pd
from manpy.simulation.imports import Machine, CoreObject, RandomNumberGenerator
 
class Machine_features(Machine):
    def feature_init(self):                                                                 
        self.feature_times = []                                                                   
        self.feature_values = []
        self.feature_id = []
        for feature in self.features:        
            self.feature_times.append(RandomNumberGenerator(self, feature[0]).generateNumber() * self.tinM + self.env.now)                                        
            self.feature_values.append(RandomNumberGenerator(self, feature[1]).generateNumber())  
        for i in range(len(self.feature_times)):
            self.feature_id.append("F_{}_{}".format(self.id[1:], i))

    def outputFeature(self, entity_name: str, entity_id: str, feature_id: str, i):
        from manpy.simulation.Globals import G

        G.trace_list.append([self.feature_times[i], entity_name, entity_id, feature_id, self.name, self.feature_values[i]])

        entities_list = []
        now = G.env.now

        for obj in G.ObjList:
            if obj.type == "Machine":
                entities = [x.id for x in obj.Res.users]
                entities_list.append((now, obj.id, entities))

        snapshot = pd.DataFrame(entities_list, columns=["sim_time", "station_id", "entities"])
        if not G.simulation_snapshots[-1].equals(snapshot):
            G.simulation_snapshots.append(snapshot)                                               
        
        
    def __init__(
        self,
        id,
        name,
        capacity=1,
        processingTime=None,
        repairman="None",
        operatorPool="None",
        operationType="None",
        setupTime=None,
        loadTime=None,
        preemption={},
        canDeliverOnInterruption=False,
        technology=None,
        priority=0,
        features=[],                                                                        ######################################################
        **kw,
    ):
        self.type = "Machine"  # String that shows the type of object
        CoreObject.__init__(self, id, name)
        from manpy.simulation.Globals import G

        processingTime = self.getOperationTime(time=processingTime)

        setupTime = self.getOperationTime(time=setupTime)

        loadTime = self.getOperationTime(time=loadTime)
        
        #     holds the features
        self.features = features                                                            ######################################################
        self.feature_times = []                                                             ######################################################      
        self.feature_values = []                                                            ######################################################
        self.feature_id = []                                                                ######################################################
        #     holds the capacity of the machine
        self.capacity = capacity
        #     sets the repairman resource of the Machine
        self.repairman = repairman
        #     Sets the attributes of the processing (and failure) time(s)
        self.rng = RandomNumberGenerator(self, processingTime)
        # check whether the operators are provided with a skills set
        # check whether the operators are provided with a skills set
        self.dedicatedOperator = self.checkForDedicatedOperators()
        if operatorPool and not (operatorPool == "None"):
            self.operatorPool = operatorPool
        else:
            if len(G.OperatorPoolsList) > 0:
                for (
                    operatorPool
                ) in (
                    G.OperatorPoolsList
                ):  # find the operatorPool assigned to the machine
                    if (
                        self.id in operatorPool.coreObjectIds
                    ):  # and add it to the machine's operatorPool
                        machineOperatorPoolList = operatorPool  # there must only one operator pool assigned to the machine,
                        # otherwise only one of them will be taken into account
                    else:
                        machineOperatorPoolList = (
                            []
                        )  # if there is no operatorPool assigned to the machine
            else:  # then machineOperatorPoolList/operatorPool is a list
                machineOperatorPoolList = (
                    []
                )  # if there are no operatorsPool created then the
                # then machineOperatorPoolList/operatorPool is a list
            if (
                type(machineOperatorPoolList) is list
            ):  # if the machineOperatorPoolList is a list
                # find the operators assigned to it and add them to the list
                for (
                    operator
                ) in G.OperatorsList:  # check which operator in the G.OperatorsList
                    if (
                        self.id in operator.coreObjectIds
                    ):  # (if any) is assigned to operate
                        machineOperatorPoolList.append(
                            operator
                        )  # the machine with ID equal to id

            self.operatorPool = machineOperatorPoolList

        self.dedicatedOperator = self.checkForDedicatedOperators()
        # create an operatorPool if needed
        self.createOperatorPool(self.operatorPool)
        # holds the Operator currently processing the Machine
        self.currentOperator = None
        # define if load/setup/removal/processing are performed by the operator
        self.operationType = operationType
        # boolean to check whether the machine is being operated
        self.toBeOperated = False
        # define the load times
        self.loadRng = RandomNumberGenerator(self, loadTime)
        # XX variable that informs on the need for setup
        self.setUp = True
        # define the setup times
        self.stpRng = RandomNumberGenerator(self, setupTime)
        # examine if there are multiple operation types performed by the operator
        #     there can be Setup/Processing operationType
        #     or the combination of both (MT-Load-Setup-Processing)
        self.multOperationTypeList = []
        if isinstance(self.operationType, str) and self.operationType.startswith("MT"):
            OTlist = operationType.split("-")
            self.operationType = OTlist.pop(0)
            self.multOperationTypeList = OTlist
        else:
            self.multOperationTypeList.append(self.operationType)
        # technology is used to group machines that perform the same operation when needed
        self.technology = technology

        # flags used for preemption purposes
        self.isPreemptive = False
        self.resetOnPreemption = False
        if len(preemption) > 0:
            self.isPreemptive = bool(int(preemption.get("isPreemptive") or 0))
            self.resetOnPreemption = bool(int(preemption.get("resetOnPreemption", 0)))
        # flag notifying that there is operator assigned to the actievObject
        self.assignedOperator = True
        # flag notifying the the station can deliver entities that ended their processing while interrupted
        self.canDeliverOnInterruption = canDeliverOnInterruption
        self.repairman = "None"
        for (
            repairman
        ) in G.RepairmanList:  # check which repairman in the G.RepairmanList
            if self.id in repairman.coreObjectIds:  # (if any) is assigned to repair
                self.repairman = repairman  # the machine with ID equal to id
        G.MachineList.append(self)  # add machine to global MachineList
        if self.operatorPool != "None":
            G.OperatedMachineList.append(
                self
            )  # add the machine to the operatedMachines List
        # attribute to prioritize against competing parallel machines
        self.priority = priority
        self.processed_entities = []

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
        # timer and values for features
        self.feature_init()                                                              ######################################################
        # variables used to flag any interruptions and the end of the processing
        self.interruption = False
        # local variable that is used to check whether the operation is concluded
        operationNotFinished = True
        # if there is a failure that depends on the working time of the Machine
        # send it the victimStartsProcess signal
        for oi in self.objectInterruptions:
            if oi.type == "Failure":
                if oi.deteriorationType == "working":
                    if oi.expectedSignals["victimStartsProcess"]:
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
            # while len(self.feature_times) > 0:                                           ######################################################
            #     index = self.feature_times.index(min(self.feature_times))                ######################################################
            #     yield self.env.timeout(self.feature_times[index] - self.env.now)         ######################################################
            #     self.outputFeature(self.currentEntity.name, self.currentEntity.id, self.feature_id[index], index)##############################
            #     self.feature_times.pop(index)                                            ######################################################
            #     self.feature_values.pop(index)                                           ######################################################
            #     self.feature_id.pop(index)                                               ######################################################
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
    
    def interruptionActions(self, type="Processing"):
        # if object was processing add the working time
        # only if object is not preempting though
        # in case of preemption endProcessingActions will be called
        if self.isProcessing and not self.shouldPreempt:
            self.totalOperationTime += self.env.now - self.timeLastOperationStarted
            for i in range(len(self.feature_times)):                                         ######################################################
                if self.totalOperationTime <= self.feature_times[i]:                         ######################################################
                    self.feature_times[i] += self.env.now - self.timeLastOperationStarted    ######################################################
            if type == "Processing":
                self.totalWorkingTime = self.totalOperationTime
            elif type == "Setup":
                self.totalSetupTime = self.totalOperationTime
        # if object was blocked add the working time
        if self.isBlocked:
            self.addBlockage()
        # the machine is currently performing nothing
        self.currentlyPerforming = None
        activeObjectQueue = self.Res.users
        if len(activeObjectQueue):
            activeEntity = activeObjectQueue[0]
            self.printTrace(activeEntity.name, interrupted=self.objName)
            self.outputTrace(
                activeObjectQueue[0].name,
                activeObjectQueue[0].id,
                "Interrupted at " + self.objName,
            )
            # recalculate the processing time left tinM
            if self.timeLastOperationStarted >= 0:
                self.tinM = round(
                    self.tinM - (self.env.now - self.timeLastOperationStarted), 4
                )
    
                self.timeToEndCurrentOperation = self.env.now + self.tinM
                self.feature_init                                                     ######################################################
                if np.isclose(
                    self.tinM, 0
                ):  # sometimes the failure may happen exactly at the time that the processing would finish
                    # this may produce disagreement with the simul8 because in both SimPy and Simul8
                    # it seems to be random which happens 1st
                    # this should not appear often to stochastic models though where times are random
                    self.tinM = 0
                    self.interruption = True
        # start counting the down time at breatTime dummy variable
        self.breakTime = self.env.now  # dummy variable that the interruption happened
        # set isProcessing to False
        self.isProcessing = False
        # set isBlocked to False
        self.isBlocked = False
        
    def endOperationActions(self, type):
        activeObjectQueue = self.Res.users
        activeEntity = activeObjectQueue[0]
        for i in range(len(self.feature_times)):                                      ######################################################
            self.outputFeature(activeObjectQueue[0].name, activeObjectQueue[0].id, self.feature_id[i], i)###################################    
        # set isProcessing to False
        self.isProcessing = False
        # the machine is currently performing no operation
        self.currentlyPerforming = None
        # add working time
        self.totalOperationTime += self.env.now - self.timeLastOperationStarted
        if type == "Processing":
            self.totalWorkingTime = self.totalOperationTime
        elif type == "Setup":
            self.totalSetupTime = self.totalOperationTime
            # if there are task_ids defined for each step
            if activeEntity.schedule[-1].get("task_id", None):
                # if the setup is finished then record an exit time for the setup
                activeEntity.schedule[-1]["exitTime"] = self.env.now
        # reseting variables used by operation() process
        self.totalOperationTime = None
        self.timeLastOperationStarted = 0
        # reseting flags
        self.shouldPreempt = False
        # reset the variables used to handle the interruptions timing
        self.breakTime = 0
        # update totalWorking time for operator and also print trace
        if self.currentOperator:
            operator = self.currentOperator
            self.outputTrace(
                operator.name, operator.id, "ended a process in " + self.objName
            )
            operator.totalWorkingTime += (
                self.env.now - operator.timeLastOperationStarted
            )
        # if the station has just concluded a processing turn then
        if type == "Processing":
            # blocking starts
            self.isBlocked = True
            self.timeLastBlockageStarted = self.env.now
            self.printTrace(
                self.getActiveObjectQueue()[0].name, processEnd=self.objName
            )
            # output to trace that the processing in the Machine self.objName ended
            try:
                self.outputTrace(
                    activeObjectQueue[0].name,
                    activeObjectQueue[0].id,
                    "Finished processing on " + str(self.id),
                )
            except IndexError:
                pass
            from manpy.simulation.Globals import G

            if G.RouterList:
                # the just processed entity is added to the list of entities
                # pending for the next processing
                G.pendingEntities.append(activeObjectQueue[0])
            # set the variable that flags an Entity is ready to be disposed
            self.waitToDispose = True
            # update the variables keeping track of Entity related attributes of the machine
            self.timeLastEntityEnded = (
                self.env.now
            )  # this holds the time that the last entity ended processing in Machine
            self.nameLastEntityEnded = (
                self.currentEntity.name
            )  # this holds the name of the last entity that ended processing in Machine
            self.completedJobs += 1  # Machine completed one more Job# it will be used
            self.isProcessingInitialWIP = False
            # if there is a failure that depends on the working time of the Machine
            # send it the victimEndsProcess signal
            for oi in self.objectInterruptions:
                if oi.type == "Failure":
                    if oi.deteriorationType == "working":
                        if oi.expectedSignals["victimEndsProcess"]:
                            self.sendSignal(receiver=oi, signal=oi.victimEndsProcess)
            # in case Machine just performed the last work before the scheduled maintenance signal the corresponding object
            if self.isWorkingOnTheLast:
                # for the scheduled Object interruptions
                # XXX add the SkilledOperatorRouter to this list and perform the signalling only once
                for interruption in G.ObjectInterruptionList:
                    # if the objectInterruption is waiting for a a signal
                    if (
                        interruption.victim == self
                        and interruption.expectedSignals["endedLastProcessing"]
                    ):
                        self.sendSignal(receiver=self, signal=self.endedLastProcessing)
                        interruption.waitingSignal = False
                        self.isWorkingOnTheLast = False
                # set timeLastShiftEnded attribute so that if it is overtime working it is not counted as off-shift time
                if self.interruptedBy == "ShiftScheduler":
                    self.timeLastShiftEnded = self.env.now
