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
Created on 08 Sep 2014

@author: George
"""
"""
Class that acts as an abstract. It should have no instances. All ManPy objects inherit from it
Also only abstract ManPy classes inherit directly (CoreObject, Entity, ObjectResource, ObjectInterruption)
"""
import pandas as pd

# ===========================================================================
# the ManPy object
# ===========================================================================
class ManPyObject(object):
    def __init__(self, id, name, **kw):
        if id:
            self.id = id
        # if no id was given create a random one
        else:
            self.id = str(self.__class__.__name__)
            import random

            self.id = self.id + str(random.randint(1, 1000000))
        if name:
            self.name = name
        # if no name was given give id as name
        else:
            self.name = self.id

    # ===========================================================================
    #  method used to request allocation from the Router
    # ===========================================================================
    @staticmethod
    def requestAllocation():
        # TODO: signal the Router, skilled operators must be assigned to operatorPools
        from manpy.simulation.core.Globals import G

        G.RouterList[0].allocation = True
        G.RouterList[0].waitEndProcess = False
        if not G.RouterList[0].invoked and G.RouterList[0].expectedSignals["isCalled"]:
            G.RouterList[0].invoked = True
            succeedTuple = (G.env, G.env.now)
            G.RouterList[0].isCalled.succeed(succeedTuple)
            G.RouterList[0].expectedSignals["isCalled"] = 0

    # ===========================================================================
    #  signalRouter method
    # ===========================================================================
    @staticmethod
    def signalRouter(receiver=None):
        from manpy.simulation.core.Globals import G

        # if an operator is not assigned to the receiver then do not signal the receiver but the Router
        try:
            # in the case of skilled router there is no need to signal
            if "Skilled" in str(G.RouterList[0].__class__):
                return False
            if not receiver.assignedOperator or (
                receiver.isPreemptive and len(receiver.Res.users) > 0
            ):
                if receiver.isLoadRequested():
                    try:
                        if (
                            not G.RouterList[0].invoked
                            and G.RouterList[0].expectedSignals["isCalled"]
                        ):
                            #                             self.printTrace(self.id, signal='router')
                            G.RouterList[0].invoked = True
                            succeedTuple = (G.env, G.env.now)
                            G.RouterList[0].isCalled.succeed(succeedTuple)
                            G.RouterList[0].expectedSignals["isCalled"] = 0
                        return True
                    except:
                        return False
            else:
                return False
        except:
            return False

    # ===========================================================================
    # check if the any of the operators are skilled (having a list of skills regarding the objects)
    # ===========================================================================
    @staticmethod
    def checkForDedicatedOperators():
        from manpy.simulation.core.Globals import G

        # XXX this can also be global
        # flag used to inform if the operators assigned to the station are skilled (skillsList)
        return any(operator.skillsList for operator in G.OperatorsList)

    @staticmethod
    def printTrace(entity="", **kw):
        assert len(kw) == 1, "only one phrase per printTrace supported for the moment"
        from manpy.simulation.core.Globals import G
        from manpy.simulation.core import Globals

        time = G.env.now
        charLimit = 60
        remainingChar = charLimit - len(str(entity)) - len(str(time))
        if G.console == "Yes":
            #print(time, entity, end=" ")
            for key in kw:
                if key not in Globals.getSupportedPrintKwrds():
                    raise ValueError("Unsupported phrase %s for %s" % (key, entity))
                element = Globals.getPhrase()[key]
                phrase = element["phrase"]
                prefix = element.get("prefix", None)
                suffix = element.get("suffix", None)
                arg = kw[key]
                if prefix:
                    print((prefix * remainingChar, phrase, arg))
                elif suffix:
                    remainingChar -= len(phrase) + len(arg)
                    suffix *= remainingChar
                    if key == "enter":
                        suffix = suffix + ">"
                    print((phrase, arg, suffix))
                else:
                    print((phrase, arg))

    # =======================================================================
    # outputs message to the trace.xls
    # outputs message to the trace.xls. Format is (Simulation Time | Entity or Frame Name | message)
    # =======================================================================
    def outputTrace(self, entity_name: str, entity_id: str, message: str):
        from manpy.simulation.core.Globals import G

        if G.trace:
            G.trace_list.append([G.env.now, entity_name, entity_id, self.id, self.name, message])

        if self.type == "Machine":
            if "Left" in message:
                self.processed_entities.append((G.env.now, entity_id))

        if self.type == "Queue":
            entities = [ent.id for ent in self.Res.users]
            self.level_history.append((G.env.now, self.id, entities, len(self.Res.users)))

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

    # ===========================================================================
    # sends a signal
    # ===========================================================================
    def sendSignal(self, sender=None, receiver=None, signal=None, succeedTuple=None):
        assert signal, "there is no signal defined"
        assert receiver, "there is no receiver defined for the signal"
        if not sender:
            sender = self
        if not succeedTuple:
            succeedTuple = (sender, self.env.now)
        # send the signal
        signal.succeed(succeedTuple)
        # reset the expected signals of the receiver to 0
        if hasattr(receiver, "name"):
            if receiver.name == "Feature9":
                pass
        for key, value in list(receiver.expectedSignals.items()):
            receiver.expectedSignals[key] = 0

    # ===========================================================================
    # actions to be performed after the end of the simulation
    # ===========================================================================
    def postProcessing(self):
        pass

    # =======================================================================
    #                       outputs results to JSON File
    # =======================================================================
    def outputResultsJSON(self):
        pass

    # =======================================================================
    #                       ends the simulation
    # ======================================================================
    @staticmethod
    def endSimulation():
        # cancel all the scheduled events
        from manpy.simulation.core.Globals import G
        from copy import copy

        G.env._queue.sort(key=lambda item: item[0])
        scheduledEvents = copy(G.env._queue)
        for index, scheduledEvent in enumerate(scheduledEvents):
            if not index == len(scheduledEvents) - 1:
                G.env._queue.remove(scheduledEvent)
            else:
                edited = [[i for i in event] for event in G.env._queue]
                edited[-1][0] = G.env.now
                G.env._queue = [tuple(i for i in event) for event in edited]
        G.maxSimTime = G.env.now

    # =======================================================================
    #                       checks if there are entities in the system
    # ======================================================================
    @staticmethod
    def checkIfSystemEmpty():
        from manpy.simulation.core.Globals import G

        for object in G.ObjList:
            if len(object.getActiveObjectQueue()):
                return False
        return True
