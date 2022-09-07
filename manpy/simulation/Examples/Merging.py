from manpy.simulation.imports import Machine, Source, Exit, Failure, Feature, Assembly, Frame
from manpy.simulation.Globals import runSimulation, getEntityData, ExcelPrinter, G
import time

start = time.time()

class Machine_control(Machine):
    def condition(self):
        activeEntity = self.Res.users[0]
        means = [1.6, 3500, 450, 180, 400, 50, 190, 400]
        stdevs = [0.2, 200, 50, 30, 50, 5, 10, 50]
        for idx, feature in enumerate(activeEntity.features):
            min = means[idx] - 2 * stdevs[idx]
            max = means[idx] + 2 * stdevs[idx]
            if feature < min or feature > max:
                return True


# Objects
Frame.capacity = 1
S0 = Source("S0", "Source", interArrivalTime={"Fixed": {"mean": 0.4}}, entity="manpy.Part", capacity=1)
S1 = Source("S1", "Source", interArrivalTime={"Fixed": {"mean": 0.4}}, entity="manpy.Frame", capacity=1)
Löten = Machine("M0", "Löten", processingTime={"Normal": {"mean": 0.8, "stdev": 0.075, "min": 0.425, "max": 1.175}})
Kleben = Machine("M1", "Kleben", processingTime={"Fixed": {"mean": 0.8, "stdev": 0.075, "min": 0.425, "max": 1.175}})
A = Assembly("A", "Assembly")
Montage = Machine_control("M2", "Montage", processingTime={"Fixed": {"mean": 0.8, "stdev": 0.075, "min": 0.425, "max": 1.175}})
E = Exit("E", "Exit")

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

# Kleben
Durchflussgeschwindigkeit = Feature("Ftr5", "Feature6", victim=Kleben, entity=True,
               distribution={"Time": {"Fixed": {"mean": 1}}, "Feature": {"Normal": {"mean": 50, "stdev": 5}}})
Temperatur = Feature("Ftr6", "Feature7", victim=Kleben, entity=True,
               distribution={"Time": {"Fixed": {"mean": 1}}, "Feature": {"Normal": {"mean": 190, "stdev": 10}}})
Menge = Feature("Ftr7", "Feature8", victim=Kleben, entity=True,
               distribution={"Time": {"Fixed": {"mean": 1}}, "Feature": {"Normal": {"mean": 400, "stdev": 50}}})


# Montage
Druck = Feature("Ftr8", "Feature9", victim=Montage, entity=True,
               distribution={"Time": {"Fixed": {"mean": 1}}, "Feature": {"Normal": {"mean": 200000, "stdev": 10000}}})

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
    objectList = [S0, S1, Löten, Kleben, A, Montage, E, StecktFest, Spannung, Strom, Widerstand, Kraft, Einsinktiefe, Durchflussgeschwindigkeit, Temperatur, Menge, Druck]

    runSimulation(objectList, maxSimTime, trace=True)

    df = getEntityData(time=False)
    df.to_csv("Merging.csv", index=False, encoding="utf8")

    print("""
            Ausschuss:          {}
            Produziert:         {}
            Blockiert für:      {:.2f}
            Simulationszeit:    {}
            Laufzeit:           {:.2f}
            """.format(len(Montage.discards), E.numOfExits, Montage.totalBlockageTime, maxSimTime, time.time() - start))

if __name__ == "__main__":
    main()
