from abc import ABC, abstractmethod
from itertools import chain


class AbstractProductionLineModule(ABC):

    @abstractmethod
    def defineRouting(self, predecessorList=[], successorList=[]):
        """
        Method for defining routing.

        :param predecessorList: List containing the previous Objects
        :param successorList: List containing the next Objects
        """

        pass

    @abstractmethod
    def get_routing_start(self):
        """
        Returns a list with the starting point of the module, i.e. the first objects.
        This list can be used as an input for defineRouting.
        :return: List containing the object(s) of the first stage in the module
        """
        pass

    @abstractmethod
    def get_routing_end(self):
        """
        Returns a list with the end point of the module, i.e. the last objects.
        This list can be used as an input for defineRouting.
        :return: List containing the object(s) of the last stage in the module
        """
        pass

    @abstractmethod
    def defineNext(self, successorList=[]):
        """
        Adds the objects in successorList as successor of the last object(s) in the module.
        :param successorList: list containing the successor(s)
        """
        pass

    @abstractmethod
    def appendPrevious(self, previous):
        """
        Appends an object to the previous objects of the first object(s) in the module.
        :param previous: The object to append the previous list of the first object(s) in the module
        """
        pass

    @abstractmethod
    def getObjectList(self):
        """
        :return: All objects in the module relevant for simulation.
        """
        pass

    @abstractmethod
    def get_routing_target(self):
        """
        This method is used for dynamic routing in order to handle CoreObjects and ProductionLineModules differently
        :return: Returns the actually relevant objects for external routing, e.g. the first stage of the module.
        """
        pass


class SequentialProductionLineModule(AbstractProductionLineModule):
    def __init__(self, routing: list, features: list, name=""):
        self.routing = routing
        # TODO rename, doesnt include failures etc
        self.features = features
        self.first = self.routing[0]
        self.last = self.routing[-1]

        self.isNext = True
        self.isPrevious = True

        self.name = name

    def defineRouting(self, predecessorList=[], successorList=[]):
        for p in predecessorList:
            self.appendPrevious(p)

        generate_routing_from_list(self.routing)

        for l in self.last:
            l.next.extend(successorList)

    def get_routing_start(self):
        return self.first

    def get_routing_end(self):
        return self.last

    def defineNext(self, successorList=[]):
        generate_routing_from_list(self.routing)
        for l in self.last:
            l.defineNext(successorList)

    def appendPrevious(self, previous):
        for f in self.first:
            f.appendPrevious(previous)

    def getObjectList(self):
        routing_objects = list(chain.from_iterable(self.routing))

        object_list = routing_objects + self.features
        return object_list

    def get_routing_target(self):
        return self.first


def generate_routing_from_list(routing_list: list):
    """
    Takes a list containing the objects for routing and defines the routing in the provided order.
    :param routing_list: List containing the objects for routing in the correct order.
    Each "stage" of the production line is defined in its own list. Each stage can consist of multiple objects.
    Example: `routing_list=[[source1], [machine1], [machine2, source2], [assembly], [exit]]`
    """

    print(15*"#")
    print("Start routing...")

    for idx, stage in enumerate(routing_list):
        for obj in stage:
            try:
                next_stage = routing_list[idx+1]
                obj.defineNext(next_stage)
                print(f"Added Routing for {obj.name}. Successor(s): {[s.name for s in next_stage]}")
            except IndexError:
                continue

    print(15*"#")
