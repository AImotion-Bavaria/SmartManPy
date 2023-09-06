import sys
from manpy.simulation.core import Source, Exit, Machine, CoreObject
from dataclasses import dataclass


# TODO add to docs!

def check_config_dict(config_dict: dict, keys: list, object_name: str):
    """
    Function to check if config dictionaries contain a mistake.
    I.e., it checks if certain keys are contained in the dict and warns the user if some are missing.
    Is used to prevent accidental misconfigurations.

    :param config_dict: The config dict to be checked
    :param keys: A list with the keys in config_dict that should be checked
    :param object_name: The name of the object in which the check is done. Is used for the print statement
    """

    for k in keys:
        if k not in config_dict:
            print(f"ATTENTION: {k} was not found in a config dict for {object_name}.")
            answer = input("Was this intentional? Enter 'Yes' or 'y' to continue.... ")
            if answer == "Yes" or answer == "y" or answer == "Y":
                continue
            else:
                print("Exiting program...")
                sys.exit(1)

    print(f"Checked a config dict of {object_name} for {keys}. No issues were found.")


def info(text):
    """
    Puts "INFO: " in front of a text.

    :param text: The text to which "INFO: " should be added.
    """
    print(f"INFO: {text}")


class ProductionLineStation:
    def __init__(self, predecessors, object, successors):
        self.predecessors = predecessors
        self.object = object
        self.successors = successors


class SequentialProductionLine:

    def __init__(self):
        self.stations = []

    def add_source(self, source: Source, successors: list):
        self.stations.append(ProductionLineStation(None, source, successors))

    def add_exit(self, predecessors: list, exit: Exit):
        self.stations.append(ProductionLineStation(predecessors, exit, None))

    # TODO it's possible that machine is eg an Assembly...
    def add_machine(self, predecessors: list, machine: Machine, successors: list):
        self.stations.append(ProductionLineStation(predecessors, machine, successors))

    def __check_basic_line_consistency(self):
        assert(isinstance(self.stations[0].object, Source), True)
        assert(isinstance(self.stations[-1].object, Exit), True)

    def generate_routing(self, print_routing=True):
        self.__check_basic_line_consistency()

        for station in self.stations:
            if station.predecessors is None:
                station.object.defineRouting(station.successors)
                if print_routing:
                    print(f"Added {station.object} as source. Successors: {station.successors}")

            elif station.successors is None:
                station.object.defineRouting(station.predecessors)
                if print_routing:
                    print(f"Added {station.object} as exit. Predecessors: {station.predecessors}")

            else:
                station.object.defineRouting(station.predecessors, station.successors)
                if print_routing:
                    print(f"Added {station.object} as machine. Successors: {station.successors}. Predecessors: {station.predecessors}")
