from manpy.simulation.imports import Machine, Source, Exit, Failure, Feature, Queue
from manpy.simulation.core.Globals import runSimulation, getFeatureData, resetSimulation, G
import time


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


def prepare():
    # Objects
    S = Source("S1", "Source", interArrivalTime={"Fixed": {"mean": 0.4}}, entity="manpy.Part", capacity=1)
    Löten = Machine("M0", "Löten", processingTime={"Normal": {"mean": 0.8, "stdev": 0.075, "min": 0.425, "max": 1.175}})
    Q = Queue("Q", "Queue")
    Kleben = Machine("M1", "Kleben",
                     processingTime={"Fixed": {"mean": 0.8, "stdev": 0.075, "min": 0.425, "max": 1.175}},
                     control=condition)
    E1 = Exit("E1", "Exit1")

    # ObjectInterruption
    # Löten
    Spannung = Feature("Ftr0", "Feature0", victim=Löten,
                       distribution={"Feature": {"Normal": {"mean": 1.6, "stdev": 0.2}}})
    Strom = Feature("Ftr1", "Feature1", victim=Löten,
                    distribution={"Feature": {"Normal": {"mean": 3500, "stdev": 200}}})
    Widerstand = Feature("Ftr2", "Feature2", victim=Löten,
                         distribution={"Feature": {"Normal": {"mean": 450, "stdev": 50}}})
    Kraft = Feature("Ftr3", "Feature3", victim=Löten,
                    distribution={"Feature": {"Normal": {"mean": 180, "stdev": 30}}})
    Einsinktiefe = Feature("Ftr4", "Feature4", victim=Löten,
                           distribution={"Feature": {"Normal": {"mean": 400, "stdev": 50}}})

    # Kleben
    Durchflussgeschwindigkeit = Feature("Ftr5", "Feature5", victim=Kleben,
                                        distribution={"Feature": {"Normal": {"mean": 50, "stdev": 5}}})
    Temperatur = Feature("Ftr6", "Feature6", victim=Kleben,
                         distribution={"Feature": {"Normal": {"mean": 190, "stdev": 10}}})
    Menge = Feature("Ftr7", "Feature7", victim=Kleben,
                    distribution={"Feature": {"Normal": {"mean": 400, "stdev": 50}}})

    StecktFest = Failure("Flr0", "Failure0", victim=Kleben,
                         distribution={"TTF": {"Fixed": {"mean": 0.5}},
                                       "TTR": {"Normal": {"mean": 2, "stdev": 0.2, "min": 0, "probability": 0.5}}})

    # Routing
    S.defineRouting([Löten])
    Löten.defineRouting([S], [Q])
    Q.defineRouting([Löten], [Kleben])
    Kleben.defineRouting([Q], [E1])
    E1.defineRouting([Kleben])

    return [S, Löten, Q, Kleben, E1, Spannung, Strom, Widerstand, Kraft, Einsinktiefe, Durchflussgeschwindigkeit,
            Temperatur, Menge, StecktFest]


def main(test=0):
    maxSimTime = 1000

    # 1
    start = time.time()
    objectList = prepare()
    runSimulation(objectList, maxSimTime)
    df = getFeatureData([objectList[3]])
    print(df)
    print("""
                Ausschuss:          {}
                Produziert:         {}
                Blockiert für:      {:.2f}
                Simulationszeit:    {}
                Laufzeit:           {:.2f}
                """.format(len(objectList[3].discards), objectList[4].numOfExits, objectList[3].totalBlockageTime,
                           G.env.now, time.time() - start))

    # 2
    start = time.time()
    # resetSimulation has to be called before objectList!
    resetSimulation()
    objectList = prepare()
    runSimulation(objectList, maxSimTime)
    df = getFeatureData([objectList[3]])
    print(df)
    print("""
                Ausschuss:          {}
                Produziert:         {}
                Blockiert für:      {:.2f}
                Simulationszeit:    {}
                Laufzeit:           {:.2f}
                """.format(len(objectList[3].discards), objectList[4].numOfExits, objectList[3].totalBlockageTime,
                           G.env.now, time.time() - start))

if __name__ == "__main__":
    main()
