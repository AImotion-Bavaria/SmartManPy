from manpy.simulation.imports import Machine, Source, Exit, Failure, Feature, Queue
from manpy.simulation.core.Globals import runSimulation

# condition for quality control
def condition(self):
    activeEntity = self.Res.users[0]
    means = [1.6, 3500, 450, 180, 400, 50, 190, 400]
    stdevs = [0.2, 200, 50, 30, 50, 5, 10, 50]
    for idx, feature in enumerate(activeEntity.features):
        if feature != None:
            min = means[idx] - 2 * stdevs[idx]
            max = means[idx] + 2 * stdevs[idx]
            if feature < min or feature > max:
                return True
    return False


# Objects
S = Source("S1", "Source", interArrivalTime={"Fixed": {"mean": 0.4}}, entity="manpy.Part", capacity=1)
Soldering = Machine("M0", "Löten", processingTime={"Normal": {"mean": 0.8, "stdev": 0.075, "min": 0.425, "max": 1.175}})
Q = Queue("Q", "Queue")
Gluing = Machine("M1", "Kleben", processingTime={"Fixed": {"mean": 0.8, "stdev": 0.075, "min": 0.425, "max": 1.175}}, control=condition)
E1 = Exit("E1", "Exit1")


# ObjectProperty

# With the "dependent" parameter, you can create Features based on the values of other features
# Dependent takes a function and populates variables with the last feature value of the corresponding Feature whenever a feature value is generated
# It is also possible to choose a distribution on top of a dependency (see Temperature example)
# Always use x1, x2, ... or similar variables to avoid complications

# Soldering
Voltage = Feature("Ftr0", "Feature0", victim=Soldering, distribution={"Feature": {"Normal": {"mean": 1.6, "stdev": 0.2}}})
Current = Feature("Ftr1", "Feature1", victim=Soldering, dependent={"Function" : "1000*x1 + 1900", "x1" : Voltage})
Resistance = Feature("Ftr2", "Feature2", victim=Soldering, dependent={"Function" : "(x1/x2)*1000000", "x1" : Voltage, "x2" : Current})
Pressure = Feature("Ftr3", "Feature3", victim=Soldering, distribution={"Feature": {"Normal": {"mean": 180, "stdev": 30}}})
Insertion_depth = Feature("Ftr4", "Feature4", victim=Soldering, distribution={"Feature": {"Normal": {"mean": 400, "stdev": 50}}})

# Gluing
Flow_rate = Feature("Ftr5", "Feature5", victim=Gluing, distribution={"Feature": {"Normal": {"mean": 50, "stdev": 5}}})
# The calculated value from "dependent" becomes the distribution's mean, allowing you to apply any desired dispersion
Temperature = Feature("Ftr6", "Feature6", victim=Gluing, dependent={"Function" : "2*x3 + 90", "x3" : Flow_rate}, distribution={"Feature": {"Normal": {"stdev": 1}}})
Mass = Feature("Ftr7", "Feature7", victim=Gluing, distribution={"Feature": {"Normal": {"mean": 400, "stdev": 50}}})


# ObjectInterruption

# With the parameter entity=True, the Time-to-Failure (TTF) is calculated based on the processing time of the entity within the machine
# The time of failure can be modified on a scale from 0 to 1, where 0 represents the beginning of processing, and 1 represents the end
# By adding "probability" to TTR, the occurrence of failure will be probabilistic, determined by chance.
Stuck = Failure("Flr0", "Failure0", victim=Gluing, entity=True,
                distribution={"TTF": {"Fixed": {"mean": 0}}, "TTR": {"Normal": {"mean": 2,"stdev": 0.2, "min":0, "probability": 0.05}}})


# Routing
S.defineRouting([Soldering])
Soldering.defineRouting([S], [Q])
Q.defineRouting([Soldering], [Gluing])
Gluing.defineRouting([Q], [E1])
E1.defineRouting([Gluing])


def main(test=0):
    maxSimTime = 100
    objectList = [S, Soldering, Q, Gluing, E1, Stuck, Voltage, Current, Resistance, Pressure, Insertion_depth, Flow_rate, Temperature, Mass]

    runSimulation(objectList, maxSimTime)

    # show dependency
    print("Voltage:  {:.2f} V\nCurrent:  {:.2f} A\nResistance:  {:.2f} Ohm\nV calculated (I*R):  {:.2f} V\n".format(
        Soldering.entities[0].features[0],
        Soldering.entities[0].features[1]/1000,
        Soldering.entities[0].features[2]/1000,
        (Soldering.entities[0].features[1]/1000)*(Soldering.entities[0].features[2]/1000)))

    # stats
    print("""
            Discards:           {}
            Produced:           {}
            blocked for:        {:.2f}
            """.format(len(Gluing.discards), E1.numOfExits, Gluing.totalBlockageTime))

    # for unittest
    if test:
        result = {}
        result["Spannung"] = Voltage.featureHistory
        result["Strom"] = Current.featureHistory
        result["Widerstand"] = Resistance.featureHistory
        return result

if __name__ == "__main__":
    main()
