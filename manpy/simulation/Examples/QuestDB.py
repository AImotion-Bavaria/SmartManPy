from manpy.simulation.imports import Machine, Source, Exit, Failure, Feature, Queue
from manpy.simulation.Globals import runSimulation, ExcelPrinter, G
import time

start = time.time()

class Machine_control(Machine):
    def condition(self):
        # activeEntity = self.Res.users[0]
        # means = [1.6, 3500, 450, 180, 400, 50, 190, 400]
        # stdevs = [0.2, 200, 50, 30, 50, 5, 10, 50]
        # for idx, feature in enumerate(activeEntity.features):
        #     min = means[idx] - 2 * stdevs[idx]
        #     max = means[idx] + 2 * stdevs[idx]
        #     if feature < min or feature > max:
                return False


# Objects
S = Source("S1", "Source", interArrivalTime={"Fixed": {"mean": 0.4}}, entity="manpy.Part", capacity=1)
Löten = Machine("M0", "Löten", processingTime={"Normal": {"mean": 0.8, "stdev": 0.075, "min": 0.425, "max": 1.175}})
Q = Queue("Q", "Queue")
Kleben = Machine_control("M1", "Kleben", processingTime={"Fixed": {"mean": 0.8, "stdev": 0.075, "min": 0.425, "max": 1.175}}, control=True)
E1 = Exit("E1", "Exit1")

# ObjectInterruption
# Löten
Spannung = Feature("Ftr0", "Spannung", victim=Löten, entity=True,
               timeseries={"Function" : "1.6", "I_value" : (0, 1),"I_time" : (0.6, 0.8), "DataPoints" : 20},
               distribution={"Feature": {"Normal": {"stdev": 0.01}}})
Strom = Feature("Ftr1", "Strom", victim=Löten, entity=True,
               timeseries={"Interval" : (0.6, 0.8), "DataPoints" : 20},
               dependent={"Function" : "1000*x + 1900", "x" : Spannung},
               distribution={"Time": {"Fixed": {"mean": 1}}, "Feature": {"Normal": {"stdev": 2}}})
Widerstand = Feature("Ftr2", "Widerstand", victim=Löten, entity=True,
               timeseries={"Interval" : (0.6, 0.8), "DataPoints" : 20},
               dependent={"Function" : "(V/I)*1000000", "V" : Spannung, "I" : Strom},
               distribution={"Time": {"Fixed": {"mean": 1}}})
Kraft = Feature("Ftr3", "Kraft", victim=Löten, entity=True,
               distribution={"Time": {"Fixed": {"mean": 1}}, "Feature": {"Normal": {"mean": 180, "stdev": 30}}})
Einsinktiefe = Feature("Ftr4", "Einsinktiefe", victim=Löten, entity=True,
               distribution={"Time": {"Fixed": {"mean": 1}}, "Feature": {"Normal": {"mean": 400, "stdev": 50}}})

#Kleben
Durchflussgeschwindigkeit = Feature("Ftr5", "Durchflussgeschwindigkeit", victim=Kleben, entity=True,
               distribution={"Time": {"Fixed": {"mean": 1}}, "Feature": {"Normal": {"mean": 50, "stdev": 5}}})
Temperatur = Feature("Ftr6", "Temperatur", victim=Kleben, entity=True, dependent={"Function" : "2*x + 90", "x" : Durchflussgeschwindigkeit},
               distribution={"Time": {"Fixed": {"mean": 1}}, "Feature": {"Normal": {"stdev": 1}}})
Menge = Feature("Ftr7", "Menge", victim=Kleben, entity=True,
               distribution={"Time": {"Fixed": {"mean": 1}}, "Feature": {"Normal": {"mean": 400, "stdev": 50}}})

StecktFest = Failure("Flr0", name="StecktFest", victim=Kleben, entity=True,
               distribution={"TTF": {"Fixed": {"mean": 0}}, "TTR": {"Normal": {"mean": 2,"stdev": 0.2, "min":0, "probability": 0.05}}})


# Routing
S.defineRouting([Löten])
Löten.defineRouting([S], [Q])
Q.defineRouting([Löten], [Kleben])
Kleben.defineRouting([Q], [E1])
E1.defineRouting([Kleben])


def main(test=0):
    maxSimTime = 1000
    objectList = [S, Löten, Q, Kleben, E1, StecktFest, Spannung, Strom, Widerstand, Kraft, Einsinktiefe, Durchflussgeschwindigkeit, Temperatur, Menge]

    runSimulation(objectList, maxSimTime, db=True, trace=True)

    # df = getEntityData()
    # df.to_csv("Dependency.csv", index=False, encoding="utf8")

    df = G.get_simulation_results_dataframe().drop(columns=["entity_name", "station_name"])
    ExcelPrinter(df, "Quality_Control")

    print("""
            Ausschuss:          {}
            Produziert:         {}
            Blockiert für:      {:.2f}
            Simulationszeit:    {}
            Laufzeit:           {:.2f}
            """.format(len(Kleben.discards), E1.numOfExits, Kleben.totalBlockageTime, maxSimTime, time.time() - start))

if __name__ == "__main__":
    main()
