# ===========================================================================
# Copyright 2013 University of Limerick
#
# This file is part of DREAM.
#
# DREAM is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# DREAM is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with DREAM.  If not, see <http://www.gnu.org/licenses/>.
# ===========================================================================


from manpy.simulation.core.Globals import G
from manpy.simulation.ManPyObject import ManPyObject


class CoreObject(ManPyObject):
    """
    Created on 12 Jul 2012

    @author: George
    Class that acts as an abstract. It should have no instances. All the core-objects should inherit from it

    :param id: Internal Id
    :param name: Name of the CoreObject
    """
    class_name = "manpy.CoreObject"

    def __init__(self, id, name, cost=0, **kw):
        ManPyObject.__init__(self, id, name)
        self.objName = name
        #     lists that hold the previous and next objects in the flow
        self.next = []  # list with the next objects in the flow
        self.previous = []  # list with the previous objects in the flow
        self.nextIds = []  # list with the ids of the next objects in the flow
        self.previousIds = []  # list with the ids of the previous objects in the flow
        self.isNext = True
        self.isPrevious = True

        # lists to hold statistics of multiple runs
        self.Failure = []
        self.Working = []
        self.Blockage = []
        self.Waiting = []
        self.OffShift = []
        self.WaitingForOperator = []
        self.WaitingForLoadOperator = []
        self.Loading = []
        self.SettingUp = []
        self.OnBreak = []

        # flag that locks the entry of an object so that it cannot receive entities
        self.isLocked = False

        # list that holds the objectInterruptions that have this element as victim
        self.objectInterruptions = []

        # list that holds the objectProperties that have this elements as victim
        self.objectProperties = []

        # default attributes set so that the CoreObject has them
        self.isPreemptive = False
        self.resetOnPreemption = False
        self.interruptCause = None
        self.gatherWipStat = False
        # flag used to signal that the station waits for removeEntity event
        self.waitEntityRemoval = False
        # attributes/indices used for printing the route,
        # hold the cols corresponding to the object (entities route and operators route)
        self.station_col_inds = []
        self.op_col_indx = None
        # if there is input in a dictionary parse from it

        G.ObjList.append(self)  # add object to ObjList
        # list of expected signals of a station
        # (values can be used as flags to inform on which signals is the station currently yielding)
        self.expectedSignals = {
            "isRequested": 0,
            "canDispose": 0,
            "interruptionStart": 0,
            "interruptionEnd": 0,
            "loadOperatorAvailable": 0,
            "initialWIP": 0,
            "brokerIsSet": 0,
            "preemptQueue": 0,
            "entityRemoved": 0,
            "entityCreated": 0,
            "moveEnd": 0,
            "processOperatorUnavailable": 0,
            "objectPropertyEnd" : 0
        }
        # flag notifying the the station can deliver entities that ended their processing while interrupted
        self.canDeliverOnInterruption = False
        # keep wip stats for every replication
        self.WipStat = []
        # set the cost of going through the object
        self.cost = cost

    def initialize(self):
        self.env = G.env
        self.Up = True  # Boolean that shows if the object is in failure ("Down") or not ("up")
        self.onShift = True
        self.onBreak = False
        self.currentEntity = None
        # ============================== total times ===============================================
        self.totalOperationTime = 0  # dummy variable to hold totalWorkin/SetupTime during an interruption (yield ...(self.operation('setup'))
        self.totalBlockageTime = 0  # holds the total blockage time
        self.totalFailureTime = 0  # holds the total failure time
        self.totalWaitingTime = 0  # holds the total waiting time
        self.totalWorkingTime = 0  # holds the total working time
        self.totalBreakTime = 0  # holds the total break time
        self.totalOffShiftTime = 0  # holds the total off-shift time
        self.completedJobs = 0  # holds the number of completed jobs
        # ============================== Entity related attributes =================================
        self.timeLastEntityEnded = (
            0  # holds the last time that an entity ended processing in the object
        )
        self.nameLastEntityEnded = (
            ""  # holds the name of the last entity that ended processing in the object
        )
        self.timeLastEntityEntered = (
            0  # holds the last time that an entity entered in the object
        )
        self.nameLastEntityEntered = (
            ""  # holds the name of the last entity that entered in the object
        )

        # ============================== shift related times =====================================
        self.timeLastShiftStarted = (
            0  # holds the time that the last shift of the object started
        )
        self.timeLastShiftEnded = (
            0  # holds the time that the last shift of the object ended
        )
        self.offShiftTimeTryingToReleaseCurrentEntity = (
            0  # holds the time that the object was off-shift while trying
        )
        # to release the current entity
        # ============================== failure related times =====================================
        self.timeLastFailure = (
            0  # holds the time that the last failure of the object started
        )
        self.timeLastFailureEnded = (
            0  # holds the time that the last failure of the object ended
        )
        # processing the current entity
        self.downTimeInTryingToReleaseCurrentEntity = (
            0  # holds the time that the object was down while trying
        )
        # to release the current entity . This might be due to failure, off-shift, etc
        self.timeLastEntityLeft = (
            0  # holds the last time that an entity left the object
        )

        self.processingTimeOfCurrentEntity = (
            0  # holds the total processing time that the current entity required
        )
        # ============================== waiting flag ==============================================
        self.waitToDispose = False  # shows if the object waits to dispose an entity

        self.isWorkingOnTheLast = False  # shows if the object is performing the last processing before scheduled interruption

        # ============================== the below are currently used in Jobshop =======================
        self.giver = (
            None  # the CoreObject that the activeObject will take an Entity from
        )
        if len(self.previous) > 0:
            self.giver = self.previous[0]
        self.receiver = (
            None  # the CoreObject that the activeObject will give an Entity to
        )
        if len(self.next) > 0:
            self.receiver = self.next[0]
        # ============================== variable that is used for the loading of objects =============
        self.exitAssignedToReceiver = None  # by default the objects are not blocked
        # when the entities have to be loaded to operated objects
        # then the giverObjects have to be blocked for the time
        # that the object is being loaded
        # ============================== variable that is used signalling of objects ==================
        self.entryAssignedToGiver = None  # by default the objects are not blocked
        # when the entities have to be received by objects
        # then the objects have to be blocked after the first signal they receive
        # in order to avoid signalling the same object
        # while it has not received the entity it has been originally signalled for
        # ============================== lists to hold statistics of multiple runs =====================
        self.totalTimeWaitingForOperator = 0
        self.operatorWaitTimeCurrentEntity = 0
        self.totalTimeInCurrentEntity = 0
        self.operatorWaitTimeCurrentEntity = 0
        self.totalProcessingTimeInCurrentEntity = 0
        #         self.failureTimeInCurrentEntity=0
        self.setupTimeCurrentEntity = 0

        # the time that the object started/ended its wait for the operator
        self.timeWaitForOperatorStarted = 0
        self.timeWaitForOperatorEnded = 0
        # the time that the object started/ended its wait for the operator
        self.timeWaitForLoadOperatorStarted = 0
        self.timeWaitForLoadOperatorEnded = 0
        self.totalTimeWaitingForLoadOperator = 0
        # the time that the operator started/ended loading the object
        self.timeLoadStarted = 0
        self.timeLoadEnded = 0
        self.totalLoadTime = 0
        # the time that the operator started/ended setting-up the object
        self.timeSetupStarted = 0
        self.timeSetupEnded = 0
        self.totalSetupTime = 0
        # Current entity load/setup/loadOperatorwait/operatorWait related times
        self.operatorWaitTimeCurrentEntity = (
            0  # holds the time that the object was waiting for the operator
        )
        self.loadOperatorWaitTimeCurrentEntity = (
            0  # holds the time that the object waits for operator to load the it
        )
        self.loadTimeCurrentEntity = 0  # holds the time to load the current entity
        self.setupTimeCurrentEntity = (
            0  # holds the time to setup the object before processing the current entity
        )

        self.shouldPreempt = (
            False  # flag that shows that the object should preempt or not
        )
        self.isProcessingInitialWIP = (
            False  # flag that is used only when a object has initial wip
        )

        self.lastGiver = None  # variable that holds the last giver of the object, used by object in case of preemption
        # initialize the wipStatList -
        # TODO, think what to do in multiple runs
        # TODO, this should be also updated in Globals.setWIP (in case we have initial wip)
        import numpy as np

        self.wipStatList = np.array([[0, 0]])

        self.isRequested = self.env.event()
        self.canDispose = self.env.event()
        self.interruptionEnd = self.env.event()
        self.interruptionStart = self.env.event()
        self.interruptedBy = None
        self.entityRemoved = self.env.event()
        self.initialWIP = self.env.event()
        # flag used to signal that the station waits for removeEntity event
        self.waitEntityRemoval = False
        # attributes/indices used for printing the route, hold the cols corresponding to the object (entities route and operators route)
        self.station_col_inds = []
        self.op_col_indx = None

        # flag that shows if the object is processing state at any given time
        self.isProcessing = False
        # variable that shows what kind of operation is the station performing at the moment
        """
            it can be Processing or Setup
            XXX: others not yet implemented
        """
        self.currentlyPerforming = None
        # flag that shows if the object is blocked state at any given time
        self.isBlocked = False
        self.timeLastBlockageStarted = None
        # list of expected signals of a station (values can be used as flags to inform on which signals is the station currently yielding)
        self.expectedSignals = {
            "isRequested": 0,
            "canDispose": 0,
            "interruptionStart": 0,
            "interruptionEnd": 0,
            "loadOperatorAvailable": 0,
            "initialWIP": 0,
            "brokerIsSet": 0,
            "preemptQueue": 0,
            "entityRemoved": 0,
            "entityCreated": 0,
            "moveEnd": 0,
            "processOperatorUnavailable": 0,
            "objectPropertyEnd" : 0
        }
        # lists that keep the start/endShiftTimes of the victim
        self.endShiftTimes = []
        self.startShiftTimes = []

    def run(self):
        """
        the main process of the core object, this is dummy, every object must have its own implementation

        :return: None
        """
        raise NotImplementedError("Subclass must define 'run' method")

    def defineRouting(self, predecessorList=[], successorList=[]):
        """
        sets the routing in and out elements for the Object

        :param predecessorList: List containing the predecessor Objects
        :param successorList: List containing the successor Objects

        :return: None
        """
        self.next = successorList
        self.previous = predecessorList

    def defineNext(self, successorList=[]):
        """
        sets the next element for the object and automatically registers itself as previous object of all objects in successorList.
        :param successorList:
        :return: None
        """
        for s in successorList:
            if s.isNext:  # checks if s can be a next object. e.g., exit cannot be a next object
                # __get_routing_target() is used to handle CoreObjects and ProductionLineModules differently
                if s.getRoutingTarget() not in self.next:
                    self.next.extend(s.getRoutingTarget())
                s.appendPrevious(self)

    def definePrevious(self, predecessorList=[]):
        """Sets self.previous"""

        self.previous = predecessorList

    def appendPrevious(self, previous):
        """Append previous to self.previous"""
        # first checks if previous can be a previous object
        # e.g., source cannot be a previous object
        if previous.isPrevious and previous not in self.previous:
            self.previous.append(previous)
        else:
            print(f"Registering {previous.name} as previous in {self.name} failed.")

    def getRoutingTarget(self):
        """Returns the object.
        This method is used for dynamic routing in order to handle CoreObjects and ProductionLineModules differently"""
        return [self]


    def printRouting(self):
        # print(f"{self.name}", end="")
        #
        # print("")
        #
        # for s in self.next:
        #     s.printRouting()
        pass

    def initialSignalReceiver(self):
        """
        checks if there is anything set as WIP at the begging of the simulation and sends an event to initialize the simulation
        """
        if self.haveToDispose():
            self.signalReceiver()

    def initialAllocationRequest(self):
        # TODO if the station is operated, and the operators have skills defined then the SkilledOperatorRouter should be signalled
        # XXX: there may be a case where one object is not assigned an operator, in that case we do not want to invoke the allocation routine
        if self.checkForDedicatedOperators():
            allocationNeeded = False
            from .Globals import G

            for obj in G.MachineList:
                if obj.operatorPool != "None":
                    if obj.operatorPool.operators:
                        allocationNeeded = False
                        break
                    else:
                        allocationNeeded = True
            if allocationNeeded:
                self.requestAllocation()

    def removeEntity(self, entity=None, resetFlags=True, addBlockage=True):
        """
        removes an Entity from the Object the Entity to be removed is passed as argument by getEntity of the receiver

        :param entity:
        :param resetFlags:
        :param addBlockage:
        :return:
        """
        if addBlockage and self.isBlocked:
            # add the blocking time
            self.addBlockage()
        # reset flags
        if resetFlags:
            self.isBlocked = False
            self.isProcessing = False

        # add to cost of entity
        entity.cost += self.cost

        activeObjectQueue = self.Res.users
        activeObjectQueue.remove(entity)  # remove the Entity from the queue
        if self.receiver:
            self.receiver.appendEntity(entity)

        self.downTimeInTryingToReleaseCurrentEntity = 0
        self.offShiftTimeTryingToReleaseCurrentEntity = 0

        self.timeLastEntityLeft = self.env.now
        self.outputTrace(entity.name, entity.id, "Left " + str(self.id))

        # append the time to schedule so that it can be read in the result
        # remember that every entity has it's schedule which is supposed to be updated every time
        # he entity enters a new object
        if entity.schedule:
            entity.schedule[-1]["exitTime"] = self.env.now

        # update wipStatList
        if self.gatherWipStat:
            import numpy

            wip = 0
            for holdEntity in activeObjectQueue:
                wip += holdEntity.numberOfUnits
            self.wipStatList = numpy.concatenate(
                (self.wipStatList, [[self.env.now, wip]])
            )
        if self.expectedSignals["entityRemoved"]:
            self.printTrace(self.id, signal="(removedEntity)")
            self.sendSignal(receiver=self, signal=self.entityRemoved)
        return entity

    def appendEntity(self, entity=None):
        """
        appends entity to the receiver object. to be called by the removeEntity of the giver
        this method is created to be overridden by the Assembly class in its getEntity where Frames are loaded
        """

        activeObjectQueue = self.Res.users
        activeObjectQueue.append(entity)

    def identifyEntityToGet(self):
        """
        called be getEntity it identifies the Entity to be obtained so that getEntity gives it to removeEntity as argument
        """
        giverObjectQueue = self.getGiverObjectQueue()
        return giverObjectQueue[0]

    def addBlockage(self):
        """
        adds the blockage time to totalBlockageTime each time an Entity is removed
        """
        if self.timeLastBlockageStarted:
            self.totalBlockageTime += self.env.now - self.timeLastBlockageStarted

    def getEntity(self):
        """
        gets an entity from the giver
        """

        # get active object and its queue, as well as the active (to be) entity
        # (after the sorting of the entities in the queue of the giver object)
        #         activeObject=self.getActiveObject()
        activeObjectQueue = self.Res.users
        # get giver object, its queue, and sort the entities according to this object priorities
        giverObject = self.giver
        giverObject.sortEntities()  # sort the Entities of the giver
        # according to the scheduling rule if applied
        giverObject.sortEntitiesForReceiver(self)
        giverObjectQueue = giverObject.Res.users

        # if the giverObject is blocked then unBlock it
        if giverObject.exitIsAssignedTo():
            giverObject.unAssignExit()
        # if the activeObject entry is blocked then unBlock it
        if self.entryIsAssignedTo():
            self.unAssignEntry()
        activeEntity = self.identifyEntityToGet()
        activeEntity.currentStation = self

        # update the receiver of the giverObject
        giverObject.receiver = self

        # remove entity from the giver
        activeEntity = giverObject.removeEntity(entity=self.identifyEntityToGet())

        # variable that holds the last giver; used in case of preemption
        self.lastGiver = self.giver
        #         #get the entity from the previous object and put it in front of the activeQ
        #         activeObjectQueue.append(activeEntity)

        # append the time to schedule so that it can be read in the result
        # remember that every entity has it's schedule which is supposed to be updated every time
        # the entity enters a new object
        activeEntity.schedule.append({"station": self, "entranceTime": self.env.now})

        # update variables
        activeEntity.currentStation = self
        self.timeLastEntityEntered = self.env.now
        self.nameLastEntityEntered = (
            activeEntity.name
        )  # this holds the name of the last entity that got into object
        # update the next list of the object
        self.updateNext(activeEntity)
        self.outputTrace(activeEntity.name, activeEntity.id, "Entered " + str(self.id))
        self.printTrace(activeEntity.name, enter=self.id)
        #         # if there are entities with requiredParts then check whether the requirements are fulfilled for them to proceed
        #         #     ass soon as a "buffer" receives an entity it controls if the entity is requested elsewhere,
        #         #     then it checks if there other requested entities by the same requesting entity.
        #         #     Finally, it is controlled whether all the requested parts have concluded
        #         #     their sequences for the requesting entity
        #         from Globals import G
        #         # for all the entities in the EntityList
        #         for entity in G.EntityList:
        #             requiredParts=entity.getRequiredParts()
        #             if requiredParts:
        #                 # if the activeEntity is in the requierdParts of the entity
        #                 if activeEntity in requiredParts:
        #                     # if the entity that requires the activeEntity can proceed then signal the currentStation of the entity
        #                     if entity.checkIfRequiredPartsReady() and entity.currentStation.expectedSignals['canDispose']:
        #                         entity.mayProceed=True
        #                         self.sendSignal(receiver=entity.currentStation, signal=entity.currentStation.canDispose)

        # update wipStatList
        if self.gatherWipStat:
            import numpy

            wip = 0
            for holdEntity in activeObjectQueue:
                wip += holdEntity.numberOfUnits
            self.wipStatList = numpy.concatenate(
                (self.wipStatList, [[self.env.now, wip]])
            )
        return activeEntity

    def updateNext(self, entity=None):
        """
        updates the next list of the object
        """
        pass

    def preemptReceiver(self):
        """
        check whether there is a critical entity to be disposed and if preemption is required
        """
        activeObjectQueue = self.Res.users
        # find a critical order if any
        critical = False
        for entity in activeObjectQueue:
            if entity.isCritical:
                activeEntity = entity
                critical = True
                break
        if critical:
            # pick a receiver
            receiver = None
            if any(
                object
                for object in self.next
                if object.isPreemptive and object.checkIfActive()
            ):
                receiver = next(
                    object
                    for object in self.next
                    if object.isPreemptive and object.checkIfActive()
                )
            # if there is any receiver that can be preempted check if it is operated
            if receiver:
                receiverOperated = False  # local variable to inform if the receiver is operated for Loading
                try:
                    from .MachineJobShop import MachineJobShop
                    from .MachineManagedJob import MachineManagedJob

                    # TODO: implement preemption for simple machines
                    if (
                        receiver.operatorPool
                        and isinstance(receiver, MachineJobShop)
                        or isinstance(receiver, MachineManagedJob)
                    ):
                        # and the operationType list contains Load, the receiver is operated
                        if (receiver.operatorPool != "None") and any(
                            type == "Load" for type in receiver.multOperationTypeList
                        ):
                            receiverOperated = True
                except:
                    pass
                # if the obtained Entity is critical and the receiver is preemptive and not operated
                #     in the case that the receiver is operated the preemption is performed by the operators
                #     if the receiver is not Up then no preemption will be performed
                if not receiverOperated and len(receiver.Res.users) > 0:
                    # if the receiver does not hold an Entity that is also critical
                    if not receiver.Res.users[0].isCritical:
                        receiver.shouldPreempt = True
                        self.printTrace(self.id, preempt=receiver.id)
                        receiver.preempt()
                        receiver.timeLastEntityEnded = (
                            self.env.now
                        )  # required to count blockage correctly in the preemptied station
                        # sort so that the critical entity is placed in front
                        activeObjectQueue.sort(
                            key=lambda x: x == activeEntity, reverse=True
                        )
                # if there is a critical entity and the possible receivers are operated then signal the Router
                elif receiverOperated:
                    self.signalRouter(receiver)
                    activeObjectQueue.sort(
                        key=lambda x: x == activeEntity, reverse=True
                    )
        # update wipStatList
        # update wipStatList
        if self.gatherWipStat:
            import numpy

            wip = 0
            for holdEntity in activeObjectQueue:
                wip += holdEntity.numberOfUnits
            self.wipStatList = numpy.concatenate(
                (self.wipStatList, [[self.env.now, wip]])
            )

    @staticmethod
    def findReceiversFor(activeObject):
        """
        find possible receivers
        """
        receivers = []
        for object in [
            x
            for x in activeObject.next
            if x.canAccept(activeObject)
            and not x.isRequested.triggered
            and x.expectedSignals["isRequested"]
        ]:
            receivers.append(object)
        return receivers

    def signalReceiver(self, transmitter=None):
        """signal the successor that the object can dispose an entity"""

        possibleReceivers = (
            [transmitter] if transmitter else self.findReceiversFor(self)
        )
        if possibleReceivers:
            receiver = self.selectReceiver(possibleReceivers)
            receiversGiver = self

            # perform the checks that canAcceptAndIsRequested used to perform and update activeCallersList or assignExit and operatorPool
            while not receiver.canAcceptAndIsRequested(receiversGiver):
                possibleReceivers.remove(receiver)
                if not possibleReceivers:
                    receiversGiver = None
                    receiver = None
                    # if no receiver can accept then try to preempt a receive if the stations holds a critical order
                    self.preemptReceiver()
                    return False
                receiver = self.selectReceiver(possibleReceivers)
                receiversGiver = self
            # sorting the entities of the object for the receiver
            self.sortEntitiesForReceiver(receiver)
            # signalling the Router if the receiver is operated and not assigned an operator
            if self.signalRouter(receiver):
                return False

            self.receiver = receiver
            self.receiver.giver = self
            self.printTrace(self.id, signalReceiver=self.receiver.id)
            # assign the entry of the receiver
            self.receiver.assignEntryTo()
            # assign the exit of the current object to the receiver
            self.assignExitTo(self.receiver)
            if self.receiver.expectedSignals["isRequested"]:
                self.sendSignal(
                    receiver=self.receiver, signal=self.receiver.isRequested
                )
            return True
        # if no receiver can accept then try to preempt a receive if the stations holds a critical order
        self.preemptReceiver()
        return False

    @staticmethod
    def selectReceiver(possibleReceivers=[]):
        """select a receiver Object"""

        candidates = possibleReceivers
        # dummy variables that help prioritize the objects requesting to give objects to the object (activeObject)
        maxTimeWaiting = 0  # dummy variable counting the time a successor is waiting
        receiver = None
        from .Globals import G

        for object in candidates:
            timeWaiting = (
                G.env.now - object.timeLastEntityLeft
            )  # the time it has been waiting is updated and stored in dummy variable timeWaiting
            if (
                timeWaiting > maxTimeWaiting or maxTimeWaiting == 0
            ):  # if the timeWaiting is the maximum among the ones of the successors
                maxTimeWaiting = timeWaiting
                receiver = (
                    object  # set the receiver as the longest waiting possible receiver
                )
        return receiver

    def sortEntitiesForReceiver(self, receiver=None):
        """sort the entities of the queue for the receiver"""

        pass

    @staticmethod
    def findGiversFor(activeObject):
        """find possible givers"""

        givers = []
        for object in [
            x
            for x in activeObject.previous
            if (not x is activeObject)
            and not x.canDispose.triggered
            and (
                x.expectedSignals["canDispose"]
                or (x.canDeliverOnInterruption and x.timeLastShiftEnded == x.env.now)
            )
        ]:  # extra check.If shift ended right now and the object
            # can unload we relax the canDispose flag
            if object.haveToDispose(activeObject):
                givers.append(object)
        return givers

    def signalGiver(self):
        """signal the giver that the entity is removed from its internalQueue"""

        possibleGivers = self.findGiversFor(self)
        if possibleGivers:
            giver = self.selectGiver(possibleGivers)
            giversReceiver = self
            # perform the checks that canAcceptAndIsRequested used to perform and update activeCallersList or assignExit and operatorPool
            while not self.canAcceptAndIsRequested(giver):
                possibleGivers.remove(giver)
                if not possibleGivers:
                    return False
                giver = self.selectGiver(possibleGivers)
                giversReceiver = self
            self.giver = giver
            self.giver.receiver = self
            if self.giver.expectedSignals["canDispose"] or (
                self.giver.canDeliverOnInterruption
                and self.giver.timeLastShiftEnded == self.env.now
            ):  # extra check.If shift ended right now and the object
                # can unload we relax the canDispose flag
                self.sendSignal(receiver=self.giver, signal=self.giver.canDispose)
                self.printTrace(self.id, signalGiver=self.giver.id)
            return True
        return False

    @staticmethod
    def selectGiver(possibleGivers=[]):
        """select a giver Object"""

        candidates = possibleGivers
        # dummy variables that help prioritize the objects requesting to give objects to the object (activeObject)
        maxTimeWaiting = 0  # dummy variable counting the time a predecessor is blocked
        giver = None
        from .Globals import G

        # loop through the possible givers to see which have to dispose and which is the one blocked for longer
        for object in candidates:
            # calculate how much the giver is waiting
            timeWaiting = G.env.now - object.timeLastEntityEnded
            if timeWaiting >= maxTimeWaiting:
                giver = object  # the object to deliver the Entity to the activeObject is set to the ith member of the previous list
                maxTimeWaiting = timeWaiting
        return giver

    def postProcessing(self, MaxSimtime=None):
        """actions to be taken after the simulation ends"""

        if MaxSimtime == None:
            from .Globals import G

            MaxSimtime = G.maxSimTime

        activeObject = self.getActiveObject()
        activeObjectQueue = self.getActiveObjectQueue()

        # update wipStatList
        if self.gatherWipStat:
            import numpy

            wip = 0
            for holdEntity in activeObjectQueue:
                wip += holdEntity.numberOfUnits
            self.wipStatList = numpy.concatenate(
                (self.wipStatList, [[self.env.now, wip]])
            )

        # calculate the offShift time for current entity
        offShiftTimeInCurrentEntity = 0
        if self.interruptedBy:
            if self.onShift == False:  # and self.interruptedBy=='ShiftScheduler':
                offShiftTimeInCurrentEntity = (
                    self.env.now - activeObject.timeLastShiftEnded
                )

        if self.isBlocked:
            self.addBlockage()

        # if object is currently processing an entity we should count this working time
        if self.isProcessing:
            """XXX currentlyPerforming can be Setup or Processing """
            if self.currentlyPerforming:
                if self.currentlyPerforming == "Setup":
                    activeObject.totalSetupTime += (
                        self.env.now - self.timeLastOperationStarted
                    )
                else:
                    activeObject.totalWorkingTime += (
                        self.env.now - self.timeLastOperationStarted
                    )
            else:
                activeObject.totalWorkingTime += (
                    self.env.now - self.timeLastProcessingStarted
                )
            # activeObject.totalTimeWaitingForOperator+=activeObject.operatorWaitTimeCurrentEntity

        # if object is down we have to add this failure time to its total failure time
        if self.Up == False:
            if self.onShift:
                activeObject.totalFailureTime += (
                    self.env.now - activeObject.timeLastFailure
                )
            # if object is off shift add only the fail time before the shift ended
            if not self.onShift and self.timeLastFailure < self.timeLastShiftEnded:
                self.totalFailureTime += self.timeLastShiftEnded - self.timeLastFailure

        # if the Operator is on break we have to add this break time to its total break time
        if self.onBreak:
            if self.onShift:
                self.totalBreakTime += self.env.now - self.timeLastBreakStarted
            # if object is off shift add only the break time before the shift ended
            if not self.onShift and self.timeLastBreakStarted < self.timeLastShiftEnded:
                self.totalBreakTime += (
                    self.timeLastShiftEnded - self.timeLastBreakStarted
                )

        # if the object is off shift,add this to the off-shift time
        if activeObject.onShift == False:
            # if we ran the simulation for infinite time we have to identify the last event
            now = self.env.now
            if now == float("inf"):
                now = 0
                lastExits = []
                for object in G.ExitList:
                    lastExits.append(object.timeLastEntityEntered)
                if lastExits:
                    now = max(lastExits)
            self.totalOffShiftTime += now - self.timeLastShiftEnded

        # object was idle when it was not in any other state
        activeObject.totalWaitingTime = (
            MaxSimtime
            - activeObject.totalWorkingTime
            - activeObject.totalBlockageTime
            - activeObject.totalFailureTime
            - activeObject.totalLoadTime
            - activeObject.totalSetupTime
            - self.totalOffShiftTime
            - self.totalBreakTime
        )

        if (
            activeObject.totalBlockageTime < 0
            and activeObject.totalBlockageTime > -0.00001
        ):  # to avoid some effects of getting negative cause of rounding precision
            self.totalBlockageTime = 0

        if (
            activeObject.totalWaitingTime < 0
            and activeObject.totalWaitingTime > -0.00001
        ):  # to avoid some effects of getting negative cause of rounding precision
            self.totalWaitingTime = 0

        activeObject.Failure.append(100 * self.totalFailureTime / MaxSimtime)
        activeObject.Blockage.append(100 * self.totalBlockageTime / MaxSimtime)
        activeObject.Waiting.append(100 * self.totalWaitingTime / MaxSimtime)
        activeObject.Working.append(100 * self.totalWorkingTime / MaxSimtime)
        activeObject.WaitingForOperator.append(
            100 * self.totalTimeWaitingForOperator / MaxSimtime
        )
        activeObject.WaitingForLoadOperator.append(
            100 * self.totalTimeWaitingForLoadOperator / MaxSimtime
        )
        activeObject.Loading.append(100 * self.totalLoadTime / MaxSimtime)
        activeObject.SettingUp.append(100 * self.totalSetupTime / MaxSimtime)
        activeObject.OffShift.append(100 * self.totalOffShiftTime / MaxSimtime)
        activeObject.OnBreak.append(100 * self.totalBreakTime / MaxSimtime)
        activeObject.WipStat.append(self.wipStatList.tolist())

    def outputResultsJSON(self):
        """outputs results to JSON File"""

        pass

    def haveToDispose(self, callerObject=None):
        """checks if the Object can dispose an entity to the following object"""

        activeObjectQueue = self.Res.users
        return len(activeObjectQueue) > 0

    def canAcceptAndIsRequested(self, callerObject=None):
        """checks if the Object can accept an entity and there is an entity in some possible giver waiting for it"""

        pass

    # =======================================================================
    def canAccept(self, callerObject=None):
        """checks if the Object can accept an entity"""

        pass

    def isInRouteOf(self, callerObject=None):
        """method used to check whether the station is a successor of the caller"""

        thecaller = callerObject
        # if the caller is not defined then return True. We are only interested in checking whether
        # the station can accept whatever entity from whichever giver
        if not thecaller:
            return True
        # check it the caller object is predecessor to the activeObject
        if thecaller in self.previous:
            return True
        return False

    def sortEntities(self):
        """sorts the Entities in the activeQ of the objects"""

        pass

    def getActiveObject(self):
        """get the active object. This always returns self"""

        return self

    def getActiveObjectQueue(self):
        """get the activeQ of the active object."""

        return self.Res.users

    def getGiverObject(self):
        """get the giver object in a getEntity transaction."""

        return self.giver

    def getGiverObjectQueue(self):
        """get the giver object queue in a getEntity transaction."""

        return self.giver.Res.users

    def getReceiverObject(self):
        """get the receiver object in a removeEntity transaction."""

        return self.receiver

    def getReceiverObjectQueue(self):
        """get the receiver object queue in a removeEntity transaction."""

        return self.receiver.Res.users

    def calculateProcessingTime(self):
        """calculates the processing time"""

        # this is only for processing of the initial wip
        if self.isProcessingInitialWIP:
            activeEntity = self.getActiveObjectQueue()[0]
            if activeEntity.remainingProcessingTime:
                remainingProcessingTime = activeEntity.remainingProcessingTime
                from ..RandomNumberGenerator import RandomNumberGenerator

                initialWIPrng = RandomNumberGenerator(self, remainingProcessingTime)
                return initialWIPrng.generateNumber()
        return (
            self.rng.generateNumber()
        )  # this is if we have a default processing time for all the entities

    def calculateTime(self, type="Processing"):
        """calculates time (running through a dictionary) according to the type of processing given as argument"""

        return {
            "Load": self.loadRng.generateNumber,
            "Setup": self.stpRng.generateNumber,
            "Processing": self.calculateProcessingTime,
        }[type]()

    def exitIsAssignedTo(self):
        """checks if the object is blocked"""

        return self.exitAssignedToReceiver

    def assignExitTo(self, callerObject=None):
        """assign Exit of the object"""

        self.exitAssignedToReceiver = callerObject

    def unAssignExit(self):
        """unblock the object"""

        self.exitAssignedToReceiver = None

    def entryIsAssignedTo(self):
        """checks if the object is blocked"""

        return self.entryAssignedToGiver

    def assignEntryTo(self):
        """assign Exit of the object"""

        self.entryAssignedToGiver = self.giver

    def unAssignEntry(self):
        """unblock the object"""

        self.entryAssignedToGiver = None

    def interruptionActions(self):
        """
        actions to be carried whenever the object is interrupted (failure, break, preemption, etc)
        """

        pass

    def postInterruptionActions(self):
        """
        actions to be carried whenever the object recovers control after an interruption (failure, break, preemption, etc)
        """

        pass

    def preempt(self):
        """method to execute preemption"""

        # ToDO make a generic method
        pass

    def checkIfActive(self):
        """checks if the object is in an active position"""

        return self.Up and self.onShift and (not self.onBreak)

    def activeQueueIsEmpty(self):
        """filter that returns True if the activeObject Queue is empty
        false if object holds entities in its queue"""

        return len(self.Res.users) == 0

    def endOperationActions(self):
        """actions to be carried out when the processing of an Entity ends"""

        pass

    def isInActiveQueue(self, entity=None):
        """check if an entity is in the internal Queue of the object"""

        activeObjectQueue = self.Res.users
        return any(x == entity for x in activeObjectQueue)
