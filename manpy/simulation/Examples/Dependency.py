from manpy.simulation.imports import Machine, Source, Exit, Failure, Feature, Queue
from manpy.simulation.Globals import runSimulation, getEntityData
#from manpy.simulation.Examples.MLExperiment import SGD_clf
import time

start = time.time()

class Machine_control(Machine):
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


# Objects
S = Source("S1", "Source", interArrivalTime={"Fixed": {"mean": 0.4}}, entity="manpy.Part", capacity=1)
Löten = Machine("M0", "Löten", processingTime={"Normal": {"mean": 0.8, "stdev": 0.075, "min": 0.425, "max": 1.175}})
Q = Queue("Q", "Queue")
Kleben = Machine_control("M1", "Kleben", processingTime={"Fixed": {"mean": 0.8, "stdev": 0.075, "min": 0.425, "max": 1.175}}, control=True)
E1 = Exit("E1", "Exit1")

# ObjectInterruption
# Löten
Spannung = Feature("Ftr0", "Feature0", victim=Löten,
               distribution={"Feature": {"Normal": {"mean": 1.6, "stdev": 0.2}}})
Strom = Feature("Ftr1", "Feature1", victim=Löten, dependent={"Function" : "1000*x + 1900", "x" : Spannung})
Widerstand = Feature("Ftr2", "Feature2", victim=Löten,dependent={"Function" : "(V/I)*1000000", "V" : Spannung, "I" : Strom})
Kraft = Feature("Ftr3", "Feature3", victim=Löten,
               distribution={"Feature": {"Normal": {"mean": 180, "stdev": 30}}})
Einsinktiefe = Feature("Ftr4", "Feature4", victim=Löten,
               distribution={"Feature": {"Normal": {"mean": 400, "stdev": 50}}})

#Kleben
Durchflussgeschwindigkeit = Feature("Ftr5", "Feature5", victim=Kleben,
               distribution={"Feature": {"Normal": {"mean": 50, "stdev": 5}}})
Temperatur = Feature("Ftr6", "Feature6", victim=Kleben,dependent={"Function" : "2*x + 90", "x" : Durchflussgeschwindigkeit},
               distribution={"Feature": {"Normal": {"stdev": 1}}})
Menge = Feature("Ftr7", "Feature7", victim=Kleben,
               distribution={"Feature": {"Normal": {"mean": 400, "stdev": 50}}})

StecktFest = Failure("Flr0","Failure0", victim=Kleben, entity=True,
               distribution={"TTF": {"Fixed": {"mean": 0}}, "TTR": {"Normal": {"mean": 2,"stdev": 0.2, "min":0, "probability": 0.05}}})


# Routing
S.defineRouting([Löten])
Löten.defineRouting([S], [Q])
Q.defineRouting([Löten], [Kleben])
Kleben.defineRouting([Q], [E1])
E1.defineRouting([Kleben])


def main(test=0):
    maxSimTime = 100
    objectList = [S, Löten, Q, Kleben, E1, StecktFest, Spannung, Strom, Widerstand, Kraft, Einsinktiefe, Durchflussgeschwindigkeit, Temperatur, Menge]

    runSimulation(objectList, maxSimTime)

    if test:
        result = {}
        result["Spannung"] = Spannung.featureHistory
        result["Strom"] = Strom.featureHistory
        result["Widerstand"] = Widerstand.featureHistory
        return result

    print(E1)
    df = getEntityData([E1], [Kleben])
    df.to_csv("Dependency.csv", index=False, encoding="utf8")
    #accuracy = SGD_clf(df)

    print("""
            Ausschuss:          {}
            Produziert:         {}
            Blockiert für:      {:.2f}
            Simulationszeit:    {}
            Laufzeit:           {:.2f}
            """.format(len(Kleben.discards), E1.numOfExits, Kleben.totalBlockageTime, maxSimTime, time.time() - start))

if __name__ == "__main__":
    main()
