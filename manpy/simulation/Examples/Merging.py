from manpy.simulation.imports import Machine, Source, Exit, Failure, Feature, Assembly, Frame
from manpy.simulation.Globals import runSimulation, getEntityData, ExcelPrinter, G
import time

start = time.time()

def condition(self):
    activeEntity = self.Res.users[0]
    means = [1.6, 3500, 450, 180, 400, 50, 190, 400, 200000]
    stdevs = [0.2, 200, 50, 30, 50, 5, 10, 50, 10000]
    for idx, feature in enumerate(activeEntity.features):
        if feature != None:
            min = means[idx] - 2 * stdevs[idx]
            max = means[idx] + 2 * stdevs[idx]
            if feature < min or feature > max:
                return True
    return False

# Objects
Frame.capacity = 1
S0 = Source("S0", "Source", interArrivalTime={"Fixed": {"mean": 0.4}}, entity="manpy.Part", capacity=1)
S1 = Source("S1", "Source", interArrivalTime={"Fixed": {"mean": 0.4}}, entity="manpy.Frame", capacity=1)
#Löten = Machine("M0", "Löten", processingTime={"Fixed": {"mean": 0.8}})
Löten = Machine("M0", "Löten", processingTime={"Normal": {"mean": 0.8, "stdev": 0.075, "min": 0.425, "max": 1.175}})
Kleben = Machine("M1", "Kleben", processingTime={"Fixed": {"mean": 0.8}})
A = Assembly("A", "Assembly")
Montage = Machine("M2", "Montage", processingTime={"Fixed": {"mean": 0.8, "stdev": 0.075, "min": 0.425, "max": 1.175}}, control=condition)
E = Exit("E", "Exit")

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


# Montage
Druck = Feature("Ftr8", "Feature8", victim=Montage,
               distribution={"Feature": {"Normal": {"mean": 200000, "stdev": 10000}}})

StecktFest = Failure("Flr0","Failure0", victim=Montage, entity=True,
               distribution={"TTF": {"Fixed": {"mean": 0}}, "TTR": {"Normal": {"mean": 2,"stdev": 0.2, "min":0, "probability": 0.05}}})

# Routing
S0.defineRouting([Löten])
S1.defineRouting([Kleben])
Löten.defineRouting([S0], [A])
Kleben.defineRouting([S1], [A])
A.defineRouting([Löten, Kleben], [Montage])
Montage.defineRouting([A], [E])
E.defineRouting([Montage])


def main(test=0):
    maxSimTime = 200
    objectList = [S0, S1, Löten, Kleben, A, Montage, E, Spannung, Strom, Widerstand, Kraft, Einsinktiefe, Durchflussgeschwindigkeit, Temperatur, Menge, Druck]

    runSimulation(objectList, maxSimTime)

    if test:
        result = {}
        result["Exits"] = E.entities
        result["FirstEntity"] = G.EntityList[0]
        print(G.ftr_st)
        print(len(G.FeatureList))
        return result

    df = getEntityData([E], discards=[Montage])
    df.to_csv("Merging.csv", index=False, encoding="utf8")

    df = getEntityData([Montage], time=True)
    df.to_csv("Merging_Test.csv", index=False, encoding="utf8")

    print("""
            Ausschuss:          {}
            Produziert:         {}
            Blockiert für:      {:.2f}
            Simulationszeit:    {}
            Laufzeit:           {:.2f}
            """.format(len(Montage.discards), E.numOfExits, Montage.totalBlockageTime, maxSimTime, time.time() - start))

if __name__ == "__main__":
    main()
