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
Created on 9 Nov 2012

@author: George
"""

"""
models the failures that servers can have
"""

# from SimPy.Simulation import now, Process, hold, request, release
from manpy.simulation.RandomNumberGenerator import RandomNumberGenerator
from manpy.simulation.core.ObjectInterruption import ObjectInterruption
from manpy.simulation.core.utils import check_config_dict


class Failure(ObjectInterruption):
    """
    Models failures of machines.

    :param id: Internal ID of the failure.
    :param name: Name of the failure.
    :param victim: Victim (i.e. the machine that should fail) for the Failure
    :param distribution: dictionary containing the individual distributions, e.g. TTF and TTR
    :param index: Internal index, only used if name is empty.
    :param repairman: Repairman with constrained resources that's assigned to this failure. Optional.
    :param offshift: flag used to identify if the time between failures should be counted while the victim is off-shift
    :param deteriorationType: shows how the time to failure is measured;
            'constant' means it counts not matter the state of the victim;
            'onShift' counts only if the victim is onShift;
            'working' counts only working time
    :param waitOnTie: flag to show if the failure will wait on tie with other events before interrupting the victim
    :param conditional: function that evaluates a condition. If return value true, the failure will be triggered.
                        Is used instead of passing a TTF in distribution.
    :param entity: With the parameter entity=True, the Time-to-Failure (TTF) is calculated based on the processing time of the entity within the machine
    :param remove: Should the entities on which the failure occured be removed from the production line (=destroyed)?
    :param kw:
    """
    def __init__(
        self,
        id="",
        name="",
        victim=None,
        distribution={},
        index=0,
        repairman=None,
        offshift=False,
        deteriorationType="constant",
        waitOnTie=False,
        conditional=None,
        entity=False,
        remove=False,
        cost=0,
        **kw
    ):

        ObjectInterruption.__init__(self, id, name, victim=victim, remove=remove)

        check_config_dict(distribution, ["TTF", "TTR"], name)

        self.rngTTF = RandomNumberGenerator(
            self, distribution.get("TTF", {"Fixed": {"mean": 0.1}})
        )
        self.rngTTR = RandomNumberGenerator(
            self, distribution.get("TTR", {"Fixed": {"mean": 0.1}})
        )


        if self.name == "":
            self.name = "F" + str(index)
        self.repairman = repairman  # the resource that may be needed to fix the failure
        # if now resource is needed this will be "None"
        self.type = "Failure"

        # shows how the time to failure is measured
        # 'constant' means it counts not matter the state of the victim
        # 'onShift' counts only if the victim is onShift
        # 'working' counts only working time
        self.deteriorationType = deteriorationType
        # flag used to identify if the time between failures should be counted while the victim is off-shift
        self.offshift = offshift
        # flag to show if the failure will wait on tie with other events before interrupting the victim
        self.waitOnTie = waitOnTie
        # set a default function for conditional if none is defined
        if conditional == None:
            def condition(self):
                return None

            self.conditional = condition
        else:
            self.conditional = conditional

        self.entity = entity
        self.cost = cost

    def initialize(self):
        ObjectInterruption.initialize(self)
        if self.conditional(self) != None:
            self.entity = True
        if self.entity == True:
            self.deteriorationType="working"
        self.victimStartsProcessing = self.env.event()
        self.victimEndsProcessing = self.env.event()
        self.contribution = self.env.event()

    def run(self):
        """The run method for the failure which has to served by a repairman"""

        if self.conditional(self) != None:
            from .Globals import G
            while 1:
                failureNotTriggered = True
                self.expectedSignals["contribution"] = 1
                yield self.contribution
                self.contribution = self.env.event()

                # wait for victim to start process
                if self.conditional(self) == True:
                    # if the time that the victim is off-shift should not be counted
                    timeToFailure = self.rngTTF.generateNumber()
                    remainingTimeToFailure = timeToFailure
                    failureNotTriggered = True

                    # if time to failure counts not matter the state of the victim
                    if self.deteriorationType == "constant":
                        yield self.env.timeout(remainingTimeToFailure)
                    # if time to failure counts only in onShift time
                    elif self.deteriorationType == "onShift":
                        while failureNotTriggered:
                            timeRestartedCounting = self.env.now
                            self.isWaitingForVictimOffShift = True

                            self.expectedSignals["victimOffShift"] = 1

                            receivedEvent = (
                                yield self.env.timeout(remainingTimeToFailure)
                                      | self.victimOffShift
                            )
                            # the failure should receive a signal if there is a shift-off triggered
                            if self.victimOffShift in receivedEvent:
                                assert (
                                    self.victim.onShift == False
                                ), "shiftFailure cannot recalculate TTF if the victim is onShift"
                                self.victimOffShift = self.env.event()
                                remainingTimeToFailure = remainingTimeToFailure - (
                                    self.env.now - timeRestartedCounting
                                )
                                # wait for the shift to start again
                                self.isWaitingForVictimOnShift = True

                                self.expectedSignals["victimOnShift"] = 1

                                yield self.victimOnShift

                                self.isWaitingForVictimOnShift = False
                                self.victimOnShift = self.env.event()
                                assert (
                                    self.victim.onShift == True
                                ), "the victim of shiftFailure must be onShift to continue counting the TTF"
                            else:
                                self.isWaitingForVictimOffShift = False
                                failureNotTriggered = False

                    # if time to failure counts only in working time
                    elif self.deteriorationType == "working":

                        # wait for victim to start process
                        self.expectedSignals["victimStartsProcessing"] = 1

                        yield self.victimStartsProcessing

                        self.victimStartsProcessing = self.env.event()

                        # check if failure should occur on entity
                        if self.entity == True:
                            remainingTimeToFailure = timeToFailure * self.victim.tinM

                        while failureNotTriggered:
                            timeRestartedCounting = self.env.now

                            self.expectedSignals["victimEndsProcessing"] = 1

                            # wait either for the failure or end of process
                            receivedEvent = (
                                yield self.env.timeout(remainingTimeToFailure)
                                      | self.victimEndsProcessing
                            )

                            # This happens because the victim stopped processing before remainingTimeToFailure passed;
                            # That means the countdown is paused until the victim starts processing
                            if self.victimEndsProcessing in receivedEvent:
                                self.victimEndsProcessing = self.env.event()
                                remainingTimeToFailure = remainingTimeToFailure - (
                                    self.env.now - timeRestartedCounting
                                )

                                self.expectedSignals["victimStartsProcessing"] = 1

                                yield self.victimStartsProcessing

                                # wait for victim to start again processing
                                self.victimStartsProcessing = self.env.event()

                            # Countdown to failure is over
                            else:
                                self.expectedSignals["victimEndsProcessing"] = 0
                                failureNotTriggered = False

                    downtime = self.rngTTR.generateNumber()
                    if downtime != 0:

                        # if the mode is to wait on tie before interruption add a dummy hold for 0
                        # this is done so that if processing finishes exactly at the time of interruption
                        # the processing will finish first (if this mode is selected)
                        if self.waitOnTie:
                            if hasattr(self.victim, "timeToEndCurrentOperation"):
                                if float(self.victim.timeToEndCurrentOperation) == float(
                                    self.env.now
                                ):
                                    yield self.env.timeout(0)

                        self.interruptVictim()


                        # check in the ObjectInterruptions of the victim. If there is a one that is waiting for victimFailed send it
                        for oi in self.victim.objectInterruptions:
                            if oi.expectedSignals["victimFailed"]:
                                self.sendSignal(receiver=oi, signal=oi.victimFailed)

                        for op in self.victim.objectProperties:
                            if op.expectedSignals["victimFailed"]:
                                self.sendSignal(receiver=op, signal=op.victimFailed)

                        self.victim.Up = False
                        self.victim.timeLastFailure = self.env.now

                        self.outputTrace(self.victim.name, self.victim.id, "is down")
                        # send Data to QuestDB
                        from .Globals import G
                        if G.db:
                            G.db.insert(
                                self.name,
                                {"time": float(self.env.now),
                                         "message": self.victim.id + " is down"}
                            )
                            G.db.commit()

                        # update the failure time
                        failTime = self.env.now
                        if (
                            self.repairman and self.repairman != "None"
                        ):  # if the failure needs a resource to be fixed,
                            # the machine waits until the
                            # resource is available

                            with self.repairman.getResource().request() as request:
                                yield request
                                # update the time that the repair started
                                timeOperationStarted = self.env.now
                                self.repairman.timeLastOperationStarted = self.env.now

                                yield self.env.timeout(
                                    self.rngTTR.generateNumber()
                                )  # wait until the repairing process is over
                                self.victim.totalFailureTime += self.env.now - failTime
                                self.reactivateVictim()  # since repairing is over, the Machine is reactivated
                                self.victim.Up = True
                                self.outputTrace(self.victim.name, self.victim.id, "is up")
                                # send Data to QuestDB
                                if G.db:
                                    G.db.insert(
                                        self.name,
                                        {"time": float(self.env.now),
                                                 "message": self.victim.id + " is up"}
                                    )
                                    G.db.commit()

                                self.repairman.totalWorkingTime += (
                                    self.env.now - timeOperationStarted
                                )
                            continue

                        yield self.env.timeout(downtime)  # wait until the repairing process is over

                        # add the failure
                        # if victim is off shift add only the fail time before the shift ended
                        if not self.victim.onShift and failTime < self.victim.timeLastShiftEnded:
                            self.victim.totalFailureTime += (
                                self.victim.timeLastShiftEnded - failTime
                            )
                        # if the victim was off shift since the start of the failure add nothing
                        elif not self.victim.onShift and failTime >= self.victim.timeLastShiftEnded:
                            pass
                        # if victim was off shift in the start of the fail time, add on
                        elif self.victim.onShift and failTime < self.victim.timeLastShiftStarted:
                            self.victim.totalFailureTime += (
                                self.env.now - self.victim.timeLastShiftStarted
                            )
                            # this can happen only if deteriorationType is constant
                            assert (
                                self.deteriorationType == "constant"
                            ), "object got failure while off-shift and deterioration type not constant"
                        else:
                            self.victim.totalFailureTime += self.env.now - failTime
                        self.reactivateVictim()  # since repairing is over, the Machine is reactivated
                        self.victim.Up = True
                        self.outputTrace(self.victim.name, self.victim.id, "is up")


        else:
            while 1:
                # if the time that the victim is off-shift should not be counted
                timeToFailure = self.rngTTF.generateNumber()
                remainingTimeToFailure = timeToFailure
                failureNotTriggered = True

                # if time to failure counts not matter the state of the victim
                if self.deteriorationType == "constant":
                    yield self.env.timeout(remainingTimeToFailure)
                # if time to failure counts only in onShift time
                elif self.deteriorationType == "onShift":
                    while failureNotTriggered:
                        timeRestartedCounting = self.env.now
                        self.isWaitingForVictimOffShift = True

                        self.expectedSignals["victimOffShift"] = 1

                        receivedEvent = (
                            yield self.env.timeout(remainingTimeToFailure)
                            | self.victimOffShift
                        )
                        # the failure should receive a signal if there is a shift-off triggered
                        if self.victimOffShift in receivedEvent:
                            assert (
                                self.victim.onShift == False
                            ), "shiftFailure cannot recalculate TTF if the victim is onShift"
                            self.victimOffShift = self.env.event()
                            remainingTimeToFailure = remainingTimeToFailure - (
                                self.env.now - timeRestartedCounting
                            )
                            # wait for the shift to start again
                            self.isWaitingForVictimOnShift = True

                            self.expectedSignals["victimOnShift"] = 1

                            yield self.victimOnShift

                            self.isWaitingForVictimOnShift = False
                            self.victimOnShift = self.env.event()
                            assert (
                                self.victim.onShift == True
                            ), "the victim of shiftFailure must be onShift to continue counting the TTF"
                        else:
                            self.isWaitingForVictimOffShift = False
                            failureNotTriggered = False

                # if time to failure counts only in working time
                elif self.deteriorationType == "working":


                    # wait for victim to start process
                    self.expectedSignals["victimStartsProcessing"] = 1

                    yield self.victimStartsProcessing

                    self.victimStartsProcessing = self.env.event()

                    # check if failure should occur on entity
                    if self.entity == True:
                        remainingTimeToFailure = timeToFailure * self.victim.tinM

                    while failureNotTriggered:
                        timeRestartedCounting = self.env.now

                        self.expectedSignals["victimEndsProcessing"] = 1

                        # wait either for the failure or end of process
                        receivedEvent = (
                            yield self.env.timeout(remainingTimeToFailure)
                            | self.victimEndsProcessing
                        )

                        # This happens because the victim stopped processing before remainingTimeToFailure passed;
                        # That means the countdown is paused until the victim starts processing
                        if self.victimEndsProcessing in receivedEvent:
                            self.victimEndsProcessing = self.env.event()
                            remainingTimeToFailure = remainingTimeToFailure - (
                                self.env.now - timeRestartedCounting
                            )

                            self.expectedSignals["victimStartsProcessing"] = 1

                            yield self.victimStartsProcessing

                            # wait for victim to start again processing
                            self.victimStartsProcessing = self.env.event()

                        # Countdown to failure is over
                        else:
                            self.expectedSignals["victimEndsProcessing"] = 0
                            failureNotTriggered = False

                downtime = self.rngTTR.generateNumber()
                if downtime != 0:

                    # if the mode is to wait on tie before interruption add a dummy hold for 0
                    # this is done so that if processing finishes exactly at the time of interruption
                    # the processing will finish first (if this mode is selected)
                    if self.waitOnTie:
                        if hasattr(self.victim, "timeToEndCurrentOperation"):
                            if float(self.victim.timeToEndCurrentOperation) == float(
                                self.env.now
                            ):
                                yield self.env.timeout(0)

                    self.interruptVictim()

                    # check in the ObjectInterruptions of the victim. If there is a one that is waiting for victimFailed send it
                    for oi in self.victim.objectInterruptions:
                        if oi.expectedSignals["victimFailed"]:
                            self.sendSignal(receiver=oi, signal=oi.victimFailed)

                    for op in self.victim.objectProperties:
                        if op.expectedSignals["victimFailed"]:
                            self.sendSignal(receiver=op, signal=op.victimFailed)

                    self.victim.Up = False
                    self.victim.timeLastFailure = self.env.now

                    self.outputTrace(self.victim.name, self.victim.id, "is down")
                    # send Data to QuestDB
                    from .Globals import G
                    if G.db:
                        G.db.insert(
                            self.name,
                            {"time": float(self.env.now),
                                     "message": self.victim.id + " is down"}
                        )
                        G.db.commit()

                    # update the failure time
                    failTime = self.env.now
                    if (
                        self.repairman and self.repairman != "None"
                    ):  # if the failure needs a resource to be fixed,
                        # the machine waits until the
                        # resource is available

                        with self.repairman.getResource().request() as request:
                            yield request
                            # update the time that the repair started
                            timeOperationStarted = self.env.now
                            self.repairman.timeLastOperationStarted = self.env.now

                            yield self.env.timeout(
                                self.rngTTR.generateNumber()
                            )  # wait until the repairing process is over
                            self.victim.totalFailureTime += self.env.now - failTime
                            self.reactivateVictim()  # since repairing is over, the Machine is reactivated
                            self.victim.Up = True
                            self.outputTrace(self.victim.name, self.victim.id, "is up")
                            # send Data to QuestDB
                            if G.db:
                                G.db.insert(
                                    self.name,
                                    {"time": float(self.env.now),
                                             "message": self.victim.id + " is up"}
                                )
                                G.db.commit()

                            self.repairman.totalWorkingTime += (
                                self.env.now - timeOperationStarted
                            )
                        continue

                    yield self.env.timeout(downtime)  # wait until the repairing process is over

                    # add the failure
                    # if victim is off shift add only the fail time before the shift ended
                    if not self.victim.onShift and failTime < self.victim.timeLastShiftEnded:
                        self.victim.totalFailureTime += (
                            self.victim.timeLastShiftEnded - failTime
                        )
                    # if the victim was off shift since the start of the failure add nothing
                    elif not self.victim.onShift and failTime >= self.victim.timeLastShiftEnded:
                        pass
                    # if victim was off shift in the start of the fail time, add on
                    elif self.victim.onShift and failTime < self.victim.timeLastShiftStarted:
                        self.victim.totalFailureTime += (
                            self.env.now - self.victim.timeLastShiftStarted
                        )
                        # this can happen only if deteriorationType is constant
                        assert (
                            self.deteriorationType == "constant"
                        ), "object got failure while off-shift and deterioration type not constant"
                    else:
                        self.victim.totalFailureTime += self.env.now - failTime
                    self.reactivateVictim()  # since repairing is over, the Machine is reactivated
                    self.victim.Up = True
                    self.outputTrace(self.victim.name, self.victim.id,  "is up")

