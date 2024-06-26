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
"""
Created on 8 Nov 2012

@author: George
"""
from manpy.simulation.core.Entity import Entity



# from SimPy.Simulation import now, Process, Resource, infinity, hold, SimEvent, activate, waitevent
import simpy
from manpy.simulation.RandomNumberGenerator import RandomNumberGenerator
from manpy.simulation.core.CoreObject import CoreObject
from manpy.simulation.core.Globals import G
from manpy.simulation.core import Globals


class EntityGenerator(object):
    """
    models the source object that generates the entities
    """

    def __init__(self, victim=None):
        self.env = G.env
        self.type = "EntityGenerator"
        self.victim = victim

    def run(self):
        while 1:
            # if the Source is empty create the Entity
            if len(self.victim.getActiveObjectQueue()) == 0:

                # create the Entity object and assign its name
                entity = self.victim.createEntity()

                # assign the current simulation time as the Entity's creation time
                entity.creationTime = self.env.now

                # assign the current simulation time as the Entity's start time
                entity.startTime = self.env.now

                # update the current station of the Entity
                entity.currentStation = self.victim

                G.EntityList.append(entity)

                #self.victim.outputTrace(
                #    entity_name=entity.name, entity_id=entity.id, message="generated"
                #)

                self.victim.getActiveObjectQueue().append(entity)
                self.victim.numberOfArrivals += 1
                G.numberOfEntities += 1
                self.victim.appendEntity(entity)

                if self.victim.expectedSignals["entityCreated"]:
                    succeedTupple = (entity, self.env.now)
                    self.victim.entityCreated.succeed(succeedTupple)
                    self.victim.expectedSignals["entityCreated"] = 0

            # else put it on the time list for scheduled Entities
            else:
                # this is used just ot output the trace correctly
                entityCounter = G.numberOfEntities + len(self.victim.scheduledEntities)
                self.victim.scheduledEntities.append(self.env.now)
                """
                self.victim.outputTrace(
                    f"{self.victim.item.type}{entityCounter}",
                    f"{self.victim.item.type}{entityCounter}",
                    "generated",
                )"""

            # wait until the next arrival
            yield self.env.timeout(
                self.victim.calculateInterArrivalTime()
            )


# ============================================================================
#                 The Source object is a Process
# ============================================================================
class Source(CoreObject):
    """Spawns new entities for the simulations.

    :param id: Internal ID
    :param name: Name of the Source
    :param interArrivalTime: Time until the next Entity is spawned
    :param entity: Type of Entity that's generated. One of "manpy.{Part, Batch, Frame, Job, CapacityEntity, CapacityProject}".
    :param capacity: Capacity of the generated Entities, Only relevant for entity="manpy.Frame"
    """

    def __init__(self, id, name, cost=0, interArrivalTime=None, entity="manpy.Part", capacity=1, **kw):

        if not interArrivalTime:
            interArrivalTime = {"Fixed": {"mean": 1}}

        if (
            "Normal" in list(interArrivalTime.keys())
            and interArrivalTime["Normal"].get("max", None) is None
        ):

            interArrivalTime["Normal"]["max"] = (
                interArrivalTime["Normal"]["mean"]
                + 5 * interArrivalTime["Normal"]["stdev"]
            )

        CoreObject.__init__(self, id, name, cost)
        # properties used for statistics

        self.totalinterArrivalTime = 0

        # the number of entities that were created
        self.numberOfArrivals = 0

        # String that shows the type of object
        self.type = "Source"
        self.isNext = False
        self.isPrevious = True

        self.rng = RandomNumberGenerator(self, interArrivalTime)
        self.capacity = capacity

        if isinstance(entity, str):
            self.item = Globals.getClassFromName(entity)
        elif isinstance(entity, Entity) or issubclass(entity, Entity):
            self.item = entity

        # list of creations that are scheduled. pattern is [timeOfCreation, EntityCounter]
        self.scheduledEntities = []

        from manpy.simulation.core.Globals import G

        G.SourceList.append(self)

    # ===========================================================================
    # The initialize method of the Source class
    # ===========================================================================
    def initialize(self):
        # using the Process __init__ and not the CoreObject __init__
        CoreObject.initialize(self)

        # initialize the internal Queue (type Resource) of the Source
        self.Res = simpy.Resource(self.env, capacity=float("inf"))
        self.Res.users = []

        # the EntityGenerator of the Source
        self.entityGenerator = EntityGenerator(victim=self)

        self.numberOfArrivals = 0
        self.env.process(self.entityGenerator.run())
        self.entityCreated = self.env.event()

        # event used by router
        self.loadOperatorAvailable = self.env.event()
        # list of creations that are scheduled
        self.scheduledEntities = []

        self.expectedSignals["entityCreated"] = 1
        self.expectedSignals["loadOperatorAvailable"] = 1
        self.expectedSignals["canDispose"] = 1

    def run(self):
        # get active object and its queue
        activeObject = self.getActiveObject()
        activeObjectQueue = self.getActiveObjectQueue()

        while 1:
            # wait for any event (entity creation or request for disposal of entity)
            self.expectedSignals["canDispose"] = 1
            self.expectedSignals["entityCreated"] = 1
            self.expectedSignals["loadOperatorAvailable"] = 1

            receivedEvent = yield self.env.any_of(
                [self.entityCreated, self.canDispose, self.loadOperatorAvailable]
            )
            self.printTrace(self.id, received="")

            # if an entity is created try to signal the receiver and continue
            if self.entityCreated in receivedEvent:
                transmitter, eventTime = self.entityCreated.value
                self.entityCreated = self.env.event()

            # otherwise, if the receiver requests availability then try to signal him if there is anything to dispose of
            if self.canDispose in receivedEvent:
                transmitter, eventTime = self.canDispose.value
                self.canDispose = self.env.event()

            if self.loadOperatorAvailable in receivedEvent:
                transmitter, eventTime = self.loadOperatorAvailable.value
                self.loadOperatorAvailable = self.env.event()

            if self.haveToDispose():
                if self.signalReceiver():
                    continue

    def appendEntity(self, entity):
        """add newly created entity to pendingEntities"""

        from manpy.simulation.core.Globals import G

        assert entity, "cannot append None entity"

        activeEntity = entity
        if G.RouterList:
            G.pendingEntities.append(activeEntity)

    def defineRouting(self, successorList=[]):
        """sets the routing out element for the Source"""

        self.next = successorList

    def definePrevious(self, **kw):
        """Safeguarding to avoid setting predecessors to sources"""

    def appendPrevious(self, previous):
        """Safeguarding to avoid setting predecessors to sources"""

    def createEntity(self):
        """creates an Entity"""

        from manpy.simulation.core.Globals import G

        self.printTrace(self.id, create="")
        if self.item.type == "Frame":
            return self.item(
                id=self.item.type + str(G.numberOfEntities),
                name=self.item.type + str(self.numberOfArrivals),
                capacity=self.capacity
            )  # return the newly created Entity
        else:
            return self.item(
                id=self.item.type + str(G.numberOfEntities),
                name=self.item.type + str(self.numberOfArrivals),
            )  # return the newly created Entity

    def calculateInterArrivalTime(self):
        """calculates the processing time"""

        # this is if we have a default interarrival time for all the entities
        return self.rng.generateNumber()

    def removeEntity(self, entity=None):
        """removes an entity from the Source"""

        if len(self.getActiveObjectQueue()) == 1 and len(self.scheduledEntities):

            # create the Entity object and assign its name
            newEntity = self.createEntity()

            # assign the current simulation time as the Entity's creation time
            newEntity.creationTime = self.scheduledEntities.pop(0)

            # assign the current simulation time as the Entity's start time
            newEntity.startTime = newEntity.creationTime

            # update the current station of the Entity
            newEntity.currentStation = self

            G.EntityList.append(newEntity)

            # append the entity to the resource
            self.getActiveObjectQueue().append(newEntity)
            self.numberOfArrivals += 1  # we have one new arrival
            G.numberOfEntities += 1
            self.appendEntity(newEntity)

        # run the default method
        activeEntity = CoreObject.removeEntity(self, entity)
        if len(self.getActiveObjectQueue()) == 1:
            if self.expectedSignals["entityCreated"]:
                self.sendSignal(receiver=self, signal=self.entityCreated)

        return activeEntity
