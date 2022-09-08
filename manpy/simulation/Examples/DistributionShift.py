from manpy.simulation.imports import Machine, Source, Exit, Failure, Feature, Queue, SimpleStateController
from manpy.simulation.Globals import runSimulation, getEntityData

import time

start = time.time()

class Machine_control(Machine):
    def condition(self):
        activeEntity = self.Res.users[0]
        means = [1.6, 3500, 450, 180, 400, 50, 190, 400, 1]
        stdevs = [0.2, 200, 50, 30, 50, 5, 10, 50, 2]
        for idx, feature in enumerate(activeEntity.features):
            if feature != None: # TODO why necessary?
                min = means[idx] - 2 * stdevs[idx]
                max = means[idx] + 2 * stdevs[idx]
                if feature < min or feature > max:
                    return True


# Objects
S = Source("S1", "Source", interArrivalTime={"Fixed": {"mean": 0.4}}, entity="manpy.Part", capacity=1)
Löten = Machine("M0", "Löten", processingTime={"Normal": {"mean": 0.8, "stdev": 0.075, "min": 0.425, "max": 1.175}})
Q = Queue("Q", "Queue")
Kleben = Machine_control("M1", "Kleben", processingTime={"Fixed": {"mean": 0.8, "stdev": 0.075, "min": 0.425, "max": 1.175}}, control=True)
E1 = Exit("E1", "Exit1")

# ObjectInterruption
# Löten
Spannung = Feature("Ftr0", "Feature1", victim=Löten, entity=True,
               distribution={"Time": {"Fixed": {"mean": 1}}, "Feature": {"Normal": {"mean": 1.6, "stdev": 0.2}}})
Strom = Feature("Ftr1", "Feature2", victim=Löten, entity=True,
               distribution={"Time": {"Fixed": {"mean": 1}}, "Feature": {"Normal": {"mean": 3500, "stdev": 200}}})
Widerstand = Feature("Ftr2", "Feature3", victim=Löten, entity=True,
               distribution={"Time": {"Fixed": {"mean": 1}}, "Feature": {"Normal": {"mean": 450, "stdev": 50}}})
Kraft = Feature("Ftr3", "Feature4", victim=Löten, entity=True,
               distribution={"Time": {"Fixed": {"mean": 1}}, "Feature": {"Normal": {"mean": 180, "stdev": 30}}})
Einsinktiefe = Feature("Ftr4", "Feature5", victim=Löten, entity=True,
               distribution={"Time": {"Fixed": {"mean": 1}}, "Feature": {"Normal": {"mean": 400, "stdev": 50}}})

#Kleben
Durchflussgeschwindigkeit = Feature("Ftr5", "Feature6", victim=Kleben, entity=True,
               distribution={"Time": {"Fixed": {"mean": 1}}, "Feature": {"Normal": {"mean": 50, "stdev": 5}}})
Temperatur = Feature("Ftr6", "Feature7", victim=Kleben, entity=True,
               distribution={"Time": {"Fixed": {"mean": 1}}, "Feature": {"Normal": {"mean": 190, "stdev": 10}}})
Menge = Feature("Ftr7", "Feature8", victim=Kleben, entity=True,
               distribution={"Time": {"Fixed": {"mean": 1}}, "Feature": {"Normal": {"mean": 400, "stdev": 50}}})

dists = [{"Time": {"Fixed": {"mean": 1}}, "Feature": {"Normal": {"mean": 1, "stdev":2}}},
         {"Time": {"Fixed": {"mean": 1}}, "Feature": {"Normal": {"mean": 100, "stdev":2}}}]
boundaries = {(0, 25): 0, (25, None): 1}
distribution_controller = SimpleStateController(states=dists, boundaries=boundaries, amount_per_step=1)

Test = Feature("Ftr8", "Feature9", victim=Kleben, entity=True, distribution_state_controller=distribution_controller)

StecktFest = Failure("Flr0", "Failure0", victim=Kleben, entity=True,
               distribution={"TTF": {"Fixed": {"mean": 0}}, "TTR": {"Normal": {"mean": 2,"stdev": 0.2, "min":0, "probability": 0.05}}})


# Routing
S.defineRouting([Löten])
Löten.defineRouting([S], [Q])
Q.defineRouting([Löten], [Kleben])
Kleben.defineRouting([Q], [E1])
E1.defineRouting([Kleben])


def main(test=0):
    maxSimTime = 50
    objectList = [S, Löten, Q, Kleben, E1, StecktFest, Spannung, Strom, Widerstand, Kraft, Einsinktiefe, Durchflussgeschwindigkeit, Temperatur, Menge, Test]

    runSimulation(objectList, maxSimTime)

    df = getEntityData([E1], discards=[Kleben])
    df.to_csv("DistributionShift.csv", index=False, encoding="utf8")

    print("""
            Ausschuss:          {}
            Produziert:         {}
            Blockiert für:      {:.2f}
            Simulationszeit:    {}
            Laufzeit:           {:.2f}
            """.format(len(Kleben.discards), E1.numOfExits, Kleben.totalBlockageTime, maxSimTime, time.time() - start))

if __name__ == "__main__":
    main()
