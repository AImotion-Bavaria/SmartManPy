from manpy.simulation.imports import Machine, Source, Exit, Failure, Feature, Queue, Timeseries
from manpy.simulation.core.Globals import runSimulation, G, ExcelPrinter, getFeatureData
import time
import matplotlib.pyplot as plt

start = time.time()

# Objects
S = Source("S1", "Source", interArrivalTime={"Fixed": {"mean": 0.4}}, entity="manpy.Part", capacity=1)
Löten = Machine("M0", "Löten", processingTime={"Normal": {"mean": 0.8, "stdev": 0.075, "min": 0.425, "max": 1.175}})
Q = Queue("Q", "Queue")
Kleben = Machine("M1", "Kleben", processingTime={"Fixed": {"mean": 0.8, "stdev": 0.075, "min": 0.425, "max": 1.175}})
E1 = Exit("E1", "Exit1")

# ObjectProperty
# Löten
Spannung = Timeseries("Ftr0", "Feature0", victim=Löten, no_negative=True, step_time=0.03,
                      distribution={"Function" : {(-1, 0) : "-1.6*x**2+1.6", (0, 1) : "-1.6*x**2+2"}, "DataPoints" : 20, "Feature": {"Normal": {"stdev": 0.02}}})
Strom = Timeseries("Ftr1", "Feature1", victim=Löten,
               distribution={"Function" : {(-1, 1) : "1000*V + 1900"}, "V" : Spannung, "DataPoints" : 20, "Feature": {"Normal": {"stdev": 20}}})
Widerstand = Timeseries("Ftr2", "Feature2", victim=Löten,
               distribution={"Function" : {(-1, 1) : "(V/I)*1000000"}, "V" : Spannung, "I" : Strom, "DataPoints" : 20})
Kraft = Feature("Ftr3", "Feature3", victim=Löten,
               distribution={"Feature": {"Normal": {"mean": 180, "stdev": 30}}})
Einsinktiefe = Feature("Ftr4", "Feature4", victim=Löten,
               distribution={"Feature": {"Normal": {"mean": 400, "stdev": 50}}})

#Kleben
Durchflussgeschwindigkeit = Feature("Ftr5", "Feature5", victim=Kleben,
               distribution={"Feature": {"Normal": {"mean": 50, "stdev": 5}}})
Temperatur = Feature("Ftr6", "Feature6", victim=Kleben,
               distribution={"Feature": {"Normal": {"mean": 190, "stdev": 10}}})
Menge = Feature("Ftr7", "Feature7", victim=Kleben,
               distribution={"Feature": {"Normal": {"mean": 400, "stdev": 50}}})

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
    objectList = [S, Löten, Q, Kleben, E1, Spannung, Strom, Widerstand, Kraft, Einsinktiefe, Durchflussgeschwindigkeit, Temperatur, Menge]

    runSimulation(objectList, maxSimTime, trace=True)

    if test:
        return E1.entities[0]

    # df = G.get_simulation_results_dataframe()
    # ExcelPrinter(df, "ExampleTS")

    plt.plot(E1.entities[0].timeseries_times[0], E1.entities[0].timeseries[0])
    plt.show()
    plt.plot(E1.entities[0].timeseries_times[1], E1.entities[0].timeseries[1], c="orange")
    plt.show()
    plt.plot(E1.entities[0].timeseries_times[2], E1.entities[0].timeseries[2], c="g")
    plt.show()

    print("""
            Produziert:         {}
            Blockiert für:      {:.2f}
            Simulationszeit:    {}
            Laufzeit:           {:.2f}
            """.format(E1.numOfExits, Kleben.totalBlockageTime, maxSimTime, time.time() - start))

if __name__ == "__main__":
    main()
