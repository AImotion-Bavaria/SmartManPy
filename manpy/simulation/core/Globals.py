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
"""
carries some global variables
"""

import warnings
import pandas as pd
import simpy
import xlwt
from manpy.simulation.core.Database import ManPyDatabase
from manpy.simulation.core.utils import info


class G:
    """Defines global properties for the whole simulation"""

    ObjList = []  # a list that holds all the CoreObjects
    EntityList = []  # a list that holds all the Entities
    ObjectResourceList = []
    ObjectInterruptionList = []
    ObjectPropertyList = []
    RouterList = []
    simulation_snapshots = [pd.DataFrame()]

    numberOfReplications = 1  # the number of replications default=1git
    confidenceLevel = 0.9  # the confidence level default=90%
    Base = 1  # the Base time unit. Default =1 minute
    maxSimTime = 0  # the total simulation time

    # flag for printing in console
    console = ""

    # data for the trace output in excel
    trace = ""  # this is written from input. If it is "Yes" then you write to trace, else we do not
    snapshots = False
    traceIndex = 0  # index that shows in what row we are
    sheetIndex = 1  # index that shows in what sheet we are
    traceFile = xlwt.Workbook()  # create excel file
    traceSheet = traceFile.add_sheet(
        "sheet " + str(sheetIndex), cell_overwrite_ok=True
    )  # create excel sheet
    trace_list = []
    # variables for excel output
    outputIndex = 0  # index that shows in what row we are
    sheetIndex = 1  # index that shows in what sheet we are
    outputFile = xlwt.Workbook()  # create excel file
    outputSheet = outputFile.add_sheet(
        "sheet " + str(sheetIndex), cell_overwrite_ok=True
    )  # create excel sheet

    # variables for json output
    outputJSON = {}
    outputJSONFile = None

    numberOfEntities = 0

    #                define the lists of each object type
    SourceList = []
    MachineList = []
    ExitList = []
    QueueList = []
    RepairmanList = []
    AssemblyList = []
    DismantleList = []
    ConveyerList = []
    MachineJobShopList = []
    QueueJobShopList = []
    ExitJobShopList = []
    BatchDecompositionList = []
    BatchSourceList = []
    BatchReassemblyList = []
    LineClearanceList = []
    EventGeneratorList = []
    OperatorsList = []
    OperatorManagedJobsList = []
    OperatorPoolsList = []
    BrokersList = []
    OperatedMachineList = []
    BatchScrapMachineList = []
    OrderDecompositionList = []
    ConditionalBufferList = []
    MouldAssemblyBufferList = []
    MouldAssemblyList = []
    MachineManagedJobList = []
    QueueManagedJobList = []
    ModelResourceList = []
    FeatureList = []
    TimeSeriesList = []

    JobList = []
    WipList = []
    EntityList = []
    PartList = []
    OrderComponentList = []
    OrderList = []
    MouldList = []
    BatchList = []
    SubBatchList = []
    # entities that just finished processing in a station
    # and have to enter the next machine
    pendingEntities = []
    env = simpy.Environment()

    totalPulpTime = 0  # temporary to track how much time PuLP needs to run

    @staticmethod
    def get_simulation_results_dataframe() -> pd.DataFrame:
        """
        Collects the logs from the traces in the simulation into a pandas dataframe.
        This dataframe contains the columns:
        - Simulation time
        - Entity (aka Resource) name
        - Entity ID
        - Station (aka Machine) ID
        - Station name
        - Trace message

        :returns Dataframe containing the described columns

        """
        df = pd.DataFrame(
            G.trace_list,
            columns=[
                "simulation_time",
                "entity_name",
                "entity_id",
                "station_id",
                "station_name",
                "message",
            ],
        )

        return df

    @staticmethod
    def get_simulation_entities_history() -> pd.DataFrame:
        """
        Iterates through all entities that passed through the simulation and collects
        their history, i.e. all the objects they passed through and when they entered/left
        them.

        :returns History containing all

        """
        dfs = []

        for entity in G.EntityList:
            history = entity.schedule
            en = [entity.id] * len(history)
            dfs.append(pd.DataFrame(history, index=en))

        entity_hist = pd.concat(dfs, sort=False)
        entity_hist["station_id"] = entity_hist.station.apply(lambda x: x.id)

        return entity_hist


def moveExcess(consumption=1, safetyStock=70, giverId=None, receiverId=None):
    """method to move entities exceeding a certain safety stock"""
    giver = findObjectById(giverId)
    receiver = findObjectById(receiverId)
    safetyStock = int(safetyStock)
    consumption = int(consumption)
    if giver and receiver:
        if len(giver.getActiveObjectQueue()) > safetyStock:
            giver.receiver = receiver
            receiver.giver = giver
            for i in range(consumption):
                receiver.getEntity()
            giver.next = []
            receiver.previous = []
    else:
        print("Giver and/or Receiver not defined")


def getClassFromName(dotted_name):
    """Import a class from a dotted name used in json."""

    from zope.dottedname.resolve import resolve
    import logging

    logger = logging.getLogger("manpy.platform")
    parts = dotted_name.split(".")
    # this is added for backwards compatibility
    if dotted_name.startswith("manpy"):
        if 'core' in dotted_name:
            class_name = dotted_name.split(".")[-1]
            new_dotted_name = "manpy.simulation.core.%s.%s" % (class_name, class_name)
            dotted_name = new_dotted_name
        else:
            class_name = dotted_name.split(".")[-1]
            new_dotted_name = "manpy.simulation.%s.%s" % (class_name, class_name)
            # logger.info(("Old style name %s used, using %s instead" % (dotted_name, new_dotted_name)))
            dotted_name = new_dotted_name
    return resolve(dotted_name)


def getMethodFromName(dotted_name):
    """returns a method by its name. name should be given as manpy.ClassName.MethodName"""

    name = dotted_name.split(".")
    methodName = name[-1]
    # if the method is in this script
    if "Globals" in name:
        methodName = name[name.index("Globals") + 1]
        possibles = globals().copy()
        possibles.update(locals())
        method = possibles.get(methodName)
    # if the method is in a class
    else:
        clsName = ""
        # clsName=name[0]+'.'+name[1]
        for i in range(len(name) - 1):
            clsName += name[i]
            clsName += "."
        clsName = clsName[:-1]
        cls = getClassFromName(clsName)
        method = getattr(cls, methodName)
    if not method:
        raise Exception("Method %s not implemented" % methodName)
    return method


def findObjectById(id):
    """method finding objects by ID"""

    for obj in (
        G.ObjList
        + G.ObjectResourceList
        + G.EntityList
        + G.ObjectInterruptionList
        + G.ObjectPropertyList
        + G.OrderList
    ):
        if obj.id == id:
            return obj
    return None


class SetWipTypeError(Exception):
    """Error in the setting up of the WIP"""

    def __init__(self, setWipError):
        Exception.__init__(self, setWipError)


def setWIP(entityList):
    """
    method to set-up the entities in the current stations as Work In Progress
    in this case the current station must be defined!
    otherwise there is no current station but a list of possible stations although the entity cannot be in more than one stations
    """

    # for all the entities in the entityList
    for entity in entityList:
        # if the entity is of type Part
        if entity.type in ["Part", "Batch", "SubBatch", "CapacityEntity", "Vehicle"]:
            # these entities have to have a currentStation.
            # TODO apply a more generic approach so that all need to have
            if entity.currentStation:
                object = entity.currentStation  # identify the object
                object.getActiveObjectQueue().append(
                    entity
                )  # append the entity to its Queue
                entity.schedule.append(
                    {"station": object, "entranceTime": G.env.now}
                )  # append the time to schedule so that it can be read in the result

        # if the entity is of type Job/OrderComponent/Order/Mould
        # XXX Orders do no more run in the system, instead we have OrderDesigns
        elif entity.type in ["Job", "OrderComponent", "Order", "OrderDesign", "Mould"]:

            # find the list of starting station of the entity
            # XXX if the entity is in wip then the current station is already defined and the remainingRoute has to be redefined
            currentObjectIds = entity.remainingRoute[0].get("stationIdsList", [])
            # if the list of starting stations has length greater than one then there is a starting WIP definition error
            try:
                if len(currentObjectIds) == 1:
                    objectId = currentObjectIds[0]
                else:
                    raise SetWipTypeError(
                        "The starting station of the the entity is not defined uniquely"
                    )
            except SetWipTypeError as setWipError:
                print(("WIP definition error: {0}".format(setWipError)))
            # get the starting station of the entity and load it with it
            object = findObjectById(objectId)
            object.getActiveObjectQueue().append(
                entity
            )  # append the entity to its Queue
            # if the entity is to be appended to a mouldAssemblyBuffer then it is readyForAsselbly
            if object.__class__.__name__ == "MouldAssemblyBuffer":
                entity.readyForAssembly = 1

            # read the IDs of the possible successors of the object
            nextObjectIds = entity.remainingRoute[1].get("stationIdsList", [])
            # for each objectId in the nextObjects find the corresponding object and populate the object's next list
            nextObjects = []
            for nextObjectId in nextObjectIds:
                nextObject = findObjectById(nextObjectId)
                nextObjects.append(nextObject)
            # update the next list of the object
            for nextObject in nextObjects:
                # append only if not already in the list
                if nextObject not in object.next:
                    object.next.append(nextObject)
            entity.currentStep = entity.remainingRoute.pop(
                0
            )  # remove data from the remaining route.
            entity.schedule.append(
                {"station": object, "entranceTime": G.env.now}
            )  # append the time to schedule so that it can be read in the result
            # if there is currentStep task_id  then append it to the schedule
            if entity.currentStep:
                if entity.currentStep.get("task_id", None):
                    entity.schedule[-1]["task_id"] = entity.currentStep["task_id"]
        # if the currentStation of the entity is of type Machine then the entity
        #     must be processed first and then added to the pendingEntities list
        #     Its hot flag is not raised
        # the following to be performed only if there is a current station. Orders, Projects e.t.c do not have
        # TODO, maybe we should loop in wiplist here
        if (not (entity.currentStation in G.MachineList)) and entity.currentStation:
            # add the entity to the pendingEntities list
            G.pendingEntities.append(entity)

        # if the station is buffer then sent the canDispose signal
        from .Queue import Queue

        if entity.currentStation:
            if issubclass(entity.currentStation.__class__, Queue):
                # send the signal only if it is not already triggered
                if not entity.currentStation.canDispose.triggered:
                    if entity.currentStation.expectedSignals["canDispose"]:
                        succeedTuple = (G.env, G.env.now)
                        entity.currentStation.canDispose.succeed(succeedTuple)
                        entity.currentStation.expectedSignals["canDispose"] = 0
        # if we are in the start of the simulation the object is of server type then we should send initialWIP signal
        # TODO, maybe use 'class_family attribute here'
        if G.env.now == 0 and entity.currentStation:
            if entity.currentStation.class_name:
                stationClass = entity.currentStation.__class__.__name__
                if stationClass in [
                    "ProductionPoint",
                    "ConveyorMachine",
                    "ConveyorPoint",
                    "ConditionalPoint",
                    "Machine",
                    "BatchScrapMachine",
                    "MachineJobShop",
                    "BatchDecomposition",
                    "BatchReassembly",
                    "M3",
                    "MouldAssembly",
                    "BatchReassemblyBlocking",
                    "BatchDecompositionBlocking",
                    "BatchScrapMachineAfterDecompose",
                    "BatchDecompositionStartTime",
                ]:
                    entity.currentStation.currentEntity = entity
                    # trigger initialWIP event only if it has not been triggered. Otherwise
                    # if we set more than one entities (e.g. in reassembly) it will crash
                    if not (entity.currentStation.initialWIP.triggered):
                        if entity.currentStation.expectedSignals["initialWIP"]:
                            succeedTuple = (G.env, G.env.now)
                            entity.currentStation.initialWIP.succeed(succeedTuple)
                            entity.currentStation.expectedSignals["initialWIP"] = 0


def countIntervalThroughput(**kw):
    from .Exit import Exit

    currentExited = 0
    for obj in G.ObjList:
        if isinstance(obj, Exit):
            totalExited = obj.totalNumberOfUnitsExited
            previouslyExited = sum(obj.intervalThroughPutList)
            currentExited += totalExited - previouslyExited
            obj.intervalThroughPutList.append(currentExited)


# #===========================================================================
# # printTrace
# #===========================================================================
# def printTrace(entity='',station='', **kw):
#     assert len(kw)==1, 'only one phrase per printTrace supported for the moment'
#     from Globals import G
#     time=G.env.now
#     charLimit=60
#     remainingChar=charLimit-len(entity)-len(str(time))
#     if(G.console=='Yes'):
#         print time,entity,
#         for key in kw:
#             if key not in getSupportedPrintKwrds():
#                 raise ValueError("Unsupported phrase %s for %s" % (key, station.id))
#             element=getPhrase()[key]
#             phrase=element['phrase']
#             prefix=element.get('prefix',None)
#             suffix=element.get('suffix',None)
#             arg=kw[key]
#             if prefix:
#                 print prefix*remainingChar,phrase,arg
#             elif suffix:
#                 remainingChar-=len(phrase)+len(arg)
#                 suffix*=remainingChar
#                 if key=='enter':
#                     suffix=suffix+'>'
#                 print phrase,arg,suffix
#             else:
#                 print phrase,arg

def getSupportedPrintKwrds():
    """get the supported print Keywords"""
    return (
        "create",
        "signal",
        "signalReceiver",
        "signalGiver",
        "attemptSignal",
        "attemptSignalGiver",
        "attemptSignalReceiver",
        "preempt",
        "preempted",
        "startWork",
        "finishWork",
        "processEnd",
        "interrupted",
        "enter",
        "destroy",
        "waitEvent",
        "received",
        "isRequested",
        "canDispose",
        "interruptionEnd",
        "loadOperatorAvailable",
        "resourceAvailable",
        "entityRemoved",
        "conveyerEnd",
        "conveyerFull",
        "moveEnd",
    )


def getPhrase():
    """get the phrase to print from the keyword"""
    printKwrds = {
        "create": {"phrase": "created an entity"},
        "destroy": {"phrase": "destroyed at", "suffix": " * "},
        "signal": {"phrase": "signalling"},
        "signalGiver": {"phrase": "signalling giver", "prefix": "_"},
        "signalReceiver": {"phrase": "signalling receiver", "prefix": "_"},
        "attemptSignal": {"phrase": "will try to signal"},
        "attemptSignalGiver": {"phrase": "will try to signal a giver"},
        "attemptSignalReceiver": {"phrase": "will try to signal a receiver"},
        "preempt": {"phrase": "preempts", "suffix": " ."},
        "preempted": {"phrase": "is being preempted", "suffix": ". "},
        "startWork": {"phrase": "started working in"},
        "finishWork": {"phrase": "finished working in"},
        "processEnd": {"phrase": "ended processing in"},
        "interrupted": {"phrase": "interrupted at", "suffix": " ."},
        "enter": {"phrase": "got into", "suffix": "="},
        "waitEvent": {"phrase": "will wait for event"},
        "received": {"phrase": "received event"},
        "isRequested": {"phrase": "received an isRequested event from"},
        "canDispose": {"phrase": "received an canDispose event"},
        "interruptionEnd": {"phrase": "received an interruptionEnd event at"},
        "loadOperatorAvailable": {
            "phrase": "received a loadOperatorAvailable event at"
        },
        "resourceAvailable": {"phrase": "received a resourceAvailable event"},
        "entityRemoved": {"phrase": "received an entityRemoved event from"},
        "moveEnd": {"phrase": "received a moveEnd event"},
        "conveyerEnd": {"phrase": "has reached conveyer End", "suffix": ".!"},
        "conveyerFull": {"phrase": "is now Full, No of units:", "suffix": "(*)"},
    }
    return printKwrds


def runSimulation(
    objectList=[],
    maxSimTime=100,
    numberOfReplications=1,
    trace=False,
    snapshots=False,
    seed=1,
    env=None,
    data="No",
    db: ManPyDatabase = None,
):
    """
    Starts the simulation

    :param objectList: Objects for the simulation
    :param maxSimTime: Timespan that's simulated
    :param numberOfReplications: TODO
    :param trace: TODO
    :param snapshots: TODO
    :param seed: TODO
    :param env: TODO
    :param data: TODO
    :param db: Database object. Optional. If passed, the results are saved to the database
    """

    G.numberOfReplications = numberOfReplications
    G.trace = trace
    G.snapshots = snapshots
    G.maxSimTime = float(maxSimTime)
    G.seed = seed
    G.data = data

    G.ObjList = []
    G.ObjectInterruptionList = []
    G.ObjectResourceList = []
    G.trace_list = []
    G.ftr_st = []   # list of (feature, corresponding station)
    G.feature_indices = {}
    G.ts_st = []   # list of (timeseries, corresponding station)
    G.timeseries_indices = {}
    G.db = db
    G.objectList = objectList

    from manpy.simulation.core.CoreObject import CoreObject
    from .ObjectInterruption import ObjectInterruption
    from .ObjectProperty import ObjectProperty
    from .ObjectResource import ObjectResource
    from manpy.simulation.core.Entity import Entity


    for object in objectList:
        if issubclass(object.__class__, CoreObject):
            G.ObjList.append(object)
        elif issubclass(object.__class__, ObjectInterruption):
            G.ObjectInterruptionList.append(object)
        elif issubclass(object.__class__, ObjectProperty):
            G.ObjectPropertyList.append(object)
        elif issubclass(object.__class__, ObjectResource):
            G.ObjectResourceList.append(object)

    # set ftr_st
    for f in G.FeatureList:
        if f.victim == None:
            G.ftr_st.append((f.id, None))
        else:
            G.ftr_st.append((f.id, f.victim.id))
        G.feature_indices[f.id] = len(G.ftr_st) - 1
    # set ts_st
    for ts in G.TimeSeriesList:
        if ts.victim == None:
            G.ts_st.append((ts.id, None))
        else:
            G.ts_st.append((ts.id, ts.victim.id))
        G.timeseries_indices[ts.id] = len(G.ts_st) - 1

    # connect to QuestDB
    if G.db:
        G.db.establish_connection()

        # run the replications
        for i in range(G.numberOfReplications):
            G.env = env or simpy.Environment()
            # this is where all the simulation object 'live'

            G.EntityList = []
            for object in objectList:
                if issubclass(object.__class__, Entity):
                    G.EntityList.append(object)

            # initialize all the objects
            for object in (
                G.ObjList + G.ObjectInterruptionList + G.ObjectResourceList + G.EntityList + G.ObjectPropertyList
            ):
                object.initialize()

            # activate all the objects
            for object in G.ObjectInterruptionList:
                G.env.process(object.run())

            for object in G.ObjectPropertyList:
                G.env.process(object.run())

            # activate all the objects
            for object in G.ObjList:
                G.env.process(object.run())

            # set the WIP
            setWIP(G.EntityList)

            info("Config finished. Starting simulation...")
            G.env.run(until=G.maxSimTime)  # run the simulation

            # identify from the exits what is the time that the last entity has ended.
            endList = []
            from manpy.simulation.core.Exit import Exit

            for object in G.ObjList:
                if issubclass(object.__class__, Exit):
                    endList.append(object.timeLastEntityLeft)

            # identify the time of the last event
            if G.env.now == float("inf"):
                G.maxSimTime = float(max(endList))
            # do not let G.maxSimTime=0 so that there will be no crash
            if G.maxSimTime == 0:
                print("simulation ran for 0 time, something may have gone wrong")
                import sys

                sys.exit()

            # carry on the post processing operations for every object in the topology
            for object in G.ObjList + G.ObjectResourceList:
                object.postProcessing()
        G.db.commit()
        G.db.close_connection()
    else:
        # run the replications
        for i in range(G.numberOfReplications):
            G.env = env or simpy.Environment()
            # this is where all the simulation object 'live'

            G.EntityList = []
            for object in objectList:
                if issubclass(object.__class__, Entity):
                    G.EntityList.append(object)

            # initialize all the objects
            for object in (
                G.ObjList + G.ObjectInterruptionList + G.ObjectResourceList + G.EntityList + G.ObjectPropertyList
            ):
                object.initialize()

            # activate all the objects
            for object in G.ObjectInterruptionList:
                G.env.process(object.run())

            for object in G.ObjectPropertyList:
                G.env.process(object.run())

            # activate all the objects
            for object in G.ObjList:
                G.env.process(object.run())

            # set the WIP
            setWIP(G.EntityList)

            info("Config finished. Starting simulation...")
            G.env.run(until=G.maxSimTime)  # run the simulation

            # identify from the exits what is the time that the last entity has ended.
            endList = []
            from manpy.simulation.core.Exit import Exit

            for object in G.ObjList:
                if issubclass(object.__class__, Exit):
                    endList.append(object.timeLastEntityLeft)

            # identify the time of the last event
            if G.env.now == float("inf"):
                G.maxSimTime = float(max(endList))
            # do not let G.maxSimTime=0 so that there will be no crash
            if G.maxSimTime == 0:
                print("simulation ran for 0 time, something may have gone wrong")
                import sys

                sys.exit()

            # carry on the post processing operations for every object in the topology
            for object in G.ObjList + G.ObjectResourceList:
                object.postProcessing()

def ExcelPrinter(df, filename):
    """
    Prints a dataframe to excel

    :param df: The dataframe to export
    :param filename: Filename for export
    """
    number_sheets = df.shape[0] // 65535 + 1

    if number_sheets > 1:
        for i in range(number_sheets):
            file = "{}({}).xls".format(filename, i)
            df[65535 * (i): 65535 * (i + 1)].to_excel(file)
    else:
        df.to_excel("{}.xls".format(filename))


def getFeatureData(objectList=[], time=False, price=False) -> pd.DataFrame:
    """
    getFeatureData returns feature data of specific machines as dataframes

    :param objectList: a list of machines that will be included in the dataframe
    :param time: boolean, should timestamps be included or not
    :return: dataframe
    """

    columns = ["ID"]    # name of columns
    df_list = []        # list for the DataFrame
    feature_list = []   # list of included features

    # set columns
    for ftr in G.ftr_st:
        for o in objectList:
            if ftr[1] == o.id:
                if time:
                    columns.append("{}_{}_v".format(ftr[1], ftr[0]))
                    columns.append("{}_{}_t".format(ftr[1], ftr[0]))
                else:
                    columns.append("{}_{}".format(ftr[1], ftr[0]))
                feature_list.append(G.ftr_st.index(ftr))

    columns.append("Result")
    if price:
        columns.append("Price")

    # set df_list
    unique = []
    for o in objectList:
        entities = o.entities + o.discards
        for entity in entities:
            if entity not in unique:
                # check which features
                features = []
                times = []
                for f in feature_list:
                    features.append(entity.features[f])
                    times.append(entity.feature_times[f])
                features.append(entity.result)

                if time:
                    if price:
                        l = [None] * (len(columns) - 2)
                    else:
                        l = [None] * (len(columns) - 1)
                    for i in range(len(l)):
                        if i % 2 == 0:
                            l[i] = features[i // 2]
                        else:
                            l[i] = times[i // 2]
                    l = [int(entity.id[4:])] + l
                else:
                    l = [int(entity.id[4:])] + features

                if price:
                    l.append(entity.cost)

                if len(l) == len(columns):
                    df_list.append(l)
                unique.append(entity)

    # return result
    result = pd.DataFrame(df_list, columns=columns).sort_values("ID")

    if "Success" in result["Result"].unique() or "Fail" in result["Result"].unique():
        return result
    else:
        return result.drop("Result", axis=1)


def getTimeSeriesData(ts) -> pd.DataFrame:
    """
    getTimeSeriesData returns timeseries data

    :param ts: the timeseries you want the data of
    :return: dataframe with entity-ID|time|value as columns
    """

    columns = ["ID", "Time", "Value"]
    id = []
    time = []
    value = []
    entities = ts.victim.entities + ts.victim.discards
    for entity in entities:
        id += [int(entity.id[4:])] * (len(entity.timeseries[G.TimeSeriesList.index(ts)]))
        time += entity.timeseries_times[G.TimeSeriesList.index(ts)]
        value += entity.timeseries[G.TimeSeriesList.index(ts)]

    return pd.DataFrame(list(zip(id, time, value)), columns=columns)


def get_feature_values_by_id(entity, feature_ids):
    """
    Returns a list of the entity's feature values of the specified ids

    :param entity: The entity of which the feature values should be retrieved.
    :param feature_ids: List containing the IDs of the features (as string) that should be retrieved.
    """

    try:
        indices = [G.feature_indices[i] for i in feature_ids]
        feature_values = [entity.features[idx] for idx in indices]
    except KeyError:
        raise KeyError(f"Attempting to access a non-existent feature id for entity {entity.name}.")

    return feature_values


def get_feature_labels_by_id(entity, feature_ids):
    """
    Returns a list of the entity's feature labels of the specified ids

    :param entity: The entity of which the feature labels should be retrieved.
    :param feature_ids: List containing the IDs of the features (as string) that should be retrieved.
    """
    try:
        indices = [G.feature_indices[i] for i in feature_ids]
        feature_values = [entity.labels[idx] for idx in indices]
    except KeyError:
        raise KeyError(f"Attempting to access a non-existent feature id for entity {entity.name}.")

    return feature_values


def resetSimulation():
    # reset all global parameters of the simulation in order to start a clean new one
    global G

    for i in vars(G).keys():
        if i[:2] == '__':
            continue
        t = type(vars(G)[i])
        if t == list:
            setattr(G, i, [])
        elif t == dict:
            setattr(G, i, {})
        elif t == bool:
            setattr(G, i, False)

    G.numberOfReplications = 1
    G.confidenceLevel = 0.9
    G.Base = 1
    G.maxSimTime = 0
    G.traceIndex = 0
    G.sheetIndex = 1
    G.outputIndex = 0
    G.numberOfEntities = 0
    G.totalPulpTime = 0
    G.seed = 1
    G.console = ""
    G.traceFile = xlwt.Workbook()
    G.traceSheet = G.traceFile.add_sheet("sheet " + str(G.sheetIndex), cell_overwrite_ok=True)
    G.outputFile = xlwt.Workbook()
    G.outputSheet = G.outputFile.add_sheet("sheet " + str(G.sheetIndex), cell_overwrite_ok=True)
    G.outputJSONFile = None
    G.db = None
    G.env = simpy.Environment()
