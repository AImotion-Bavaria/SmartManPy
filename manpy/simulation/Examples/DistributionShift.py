from manpy.simulation.imports import Machine, Source, Exit, Failure, Feature, Queue, SimpleStateController, Repairman
from manpy.simulation.core.Globals import runSimulation, getFeatureData, G

import time

start = time.time()

def M_condition(machine):
    activeEntity = machine.Res.users[0]
    means = [1.6, 3500, 450, 180, 400, 50, 190, 400, 1]
    stdevs = [0.2, 200, 50, 30, 50, 5, 10, 50, 2]
    for idx, feature in enumerate(activeEntity.features):
        if feature != None:
            min = means[idx] - 2 * stdevs[idx]
            max = means[idx] + 2 * stdevs[idx]
            if feature < min or feature > max:
                return True
    return False


def F_condition(self):
    value_1 = Test.featureValue
    if value_1 > 10:
        print("Failure!")
        Test.start_time = G.env.now
        return True
    else:
        return False


# Objects
R = Repairman("R1", "Sascha")
S = Source("S1", "Source", interArrivalTime={"Fixed": {"mean": 0.4}}, entity="manpy.Part", capacity=100)
Löten = Machine("M0", "Löten", processingTime={"Normal": {"mean": 0.8, "stdev": 0.075, "min": 0.425, "max": 1.175}})
Q = Queue("Q", "Queue")
Kleben = Machine("M1", "Kleben",
                         processingTime={"Fixed": {"mean": 0.8, "stdev": 0.075, "min": 0.425, "max": 1.175}},
                         # processingTime={"Fixed": {"mean": 0.8}},
                         control=M_condition)

# Kleben = Machine("M1", "Kleben", processingTime={"Normal": {"mean": 0.8, "stdev": 0.075, "min": 0.425, "max": 1.175}})
E1 = Exit("E1", "Exit1")


# ObjectInterruption
# Löten
Spannung = Feature("Ftr0", "Feature1", victim=Löten,
               distribution={"Feature": {"Normal": {"mean": 1.6, "stdev": 0.2}}})
Strom = Feature("Ftr1", "Feature2", victim=Löten,
               distribution={"Feature": {"Normal": {"mean": 3500, "stdev": 200}}})
Widerstand = Feature("Ftr2", "Feature3", victim=Löten,
               distribution={"Feature": {"Normal": {"mean": 450, "stdev": 50}}})
Kraft = Feature("Ftr3", "Feature4", victim=Löten,
               distribution={"Feature": {"Normal": {"mean": 180, "stdev": 30}}})
Einsinktiefe = Feature("Ftr4", "Feature5", victim=Löten,
               distribution={"Feature": {"Normal": {"mean": 400, "stdev": 50}}})

#Kleben
Durchflussgeschwindigkeit = Feature("Ftr5", "Feature6", victim=Kleben,
               distribution={"Feature": {"Normal": {"mean": 50, "stdev": 5}}})
Temperatur = Feature("Ftr6", "Feature7", victim=Kleben,
               distribution={"Feature": {"Normal": {"mean": 190, "stdev": 10}}})
Menge = Feature("Ftr7", "Feature8", victim=Kleben,
               distribution={"Feature": {"Normal": {"mean": 400, "stdev": 50}}})

StecktFest = Failure("Flr0", "Failure0", victim=Kleben, conditional=F_condition,
            distribution={"TTF": {"Fixed": {"mean": 0}}, "TTR": {"Fixed": {"mean": 20}}}, waitOnTie=True)

# StecktFest = Failure("Flr0", "Failure0", victim=Kleben, entity=True, deteriorationType="working",
#                distribution={"TTF": {"Fixed": {"mean": 0}},
#                              "TTR": {"Normal": {"mean": 2,"stdev": 0.2, "min":0, "probability": 0.05}}})

dists = [{"Feature": {"Normal": {"mean": 1, "stdev":2}}},
         {"Feature": {"Normal": {"mean": 100, "stdev":2}}}]
boundaries = {(0, 10): 0, (10, None): 1}
distribution_controller = SimpleStateController(states=dists, labels=["ok", "defect"], boundaries=boundaries, wear_per_step=1.0, reset_amount=40)

Test = Feature("Ftr8", "Feature9", victim=Kleben,
               distribution_state_controller=distribution_controller
               )



# Routing
S.defineRouting([Löten])
Löten.defineRouting([S], [Q])
Q.defineRouting([Löten], [Kleben])
Kleben.defineRouting([Q], [E1])
E1.defineRouting([Kleben])


def main():
    maxSimTime = 150
    objectList = [S, R, Löten, Q, Kleben, E1, StecktFest, Spannung, Strom, Widerstand, Kraft, Einsinktiefe, Durchflussgeschwindigkeit, Temperatur, Menge, Test]

    runSimulation(objectList, maxSimTime)

    df = getFeatureData([Kleben], time=True)[["M1_Ftr8_v", "Result"]]
    print(df)
    # df.to_csv("DistributionShift.csv", index=False, encoding="utf8")

    ent = Löten.entities
    for e in ent:
        print(e.labels)

    print("""
            Ausschuss:          {}
            Produziert:         {}
            Blockiert für:      {:.2f}
            Simulationszeit:    {}
            Laufzeit:           {:.2f}
            """.format(len(Kleben.discards), E1.numOfExits, Kleben.totalBlockageTime, maxSimTime, time.time() - start))

if __name__ == "__main__":
    main()
