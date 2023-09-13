from abc import ABC, abstractmethod
from itertools import chain


class AbstractProductionLineModule(ABC):

    @abstractmethod
    def defineRouting(self, predecessorList=[], successorList=[]):
        pass

    @abstractmethod
    def defineNext(self, successorList=[]):
        pass

    @abstractmethod
    def appendPrevious(self, previous):
        pass

    @abstractmethod
    def getObjectList(self):
        pass

    @abstractmethod
    def get_routing_target(self):
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
