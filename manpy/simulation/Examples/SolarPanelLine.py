from manpy.simulation.imports import Machine, Source, Exit, Failure, Feature, Queue, Timeseries
from manpy.simulation.Globals import runSimulation, getEntityData, G, ExcelPrinter
import time
import matplotlib.pyplot as plt

start = time.time()

# produces 16 265Watt Solar Panels/hour. 60 Solar Cells for one Panel

def condition(self):
    activeEntity = self.Res.users[0]
    features = [None, None, 3.5, 0.62, 2.3, 0.48, 3.367]
    for idx, feature in enumerate(features):
        if feature is not None:
            if activeEntity.features[idx] < 0.95*feature or activeEntity.features[idx] > 1.05*feature:
                return True
    return False


# Objects
Solar_Cells = Source("S1", "Source", interArrivalTime={"Fixed": {"mean": 0.5}}, entity="manpy.Part", capacity=1)
Solar_Cell_Tester = Machine("M0", "Solar_Cell_Tester", processingTime={"Fixed": {"mean": 1}})
Q = Queue("Q", "Queue")
Machine1 = Machine("M1", "Machine1", processingTime={"Fixed": {"mean": 1}})
E1 = Exit("E1", "Exit")


# ObjectProperty

# SolarCellTester
# IV_Curve = Timeseries("Ts0", "IV_Curve", victim=Solar_Cell_Tester, no_negative=True,
#                       distribution={"Function": {(0, 0.4): "3.5 - 0.05*x", (0.4, 0.8): "-410.354*x**3 + 512.626*x**2 - 213.533*x + 33.1356"}, "DataPoints": 100})
# Power_Curve = Timeseries("Ts1", "Power_Curve", victim=Solar_Cell_Tester, no_negative=True,
#                       distribution={"Function": {(0, 0.46): "4.8913*x", (0.46, 0.8): "-118.304*x**2 + 113.705*x - 25.0214"}, "DataPoints": 100})
Isc = Feature("Ftr0", "Isc", victim=Solar_Cell_Tester, start_value=3.5,         # short-circuit current
               distribution={"Feature" : {"Fixed": {"mean": 3.5}}})
Voc = Feature("Ftr1", "Voc", victim=Solar_Cell_Tester, start_value=0.62,         # open circuit voltage
               distribution={"Feature" : {"Fixed": {"mean": 0.62}}})
Vm = Feature("Ftr2", "Vm", victim=Solar_Cell_Tester, start_value=0.48,          # Maximum Power Point Voltage
               distribution={"Feature" : {"Fixed": {"mean": 0.48}}})
Im = Feature("Ftr3", "Im", victim=Solar_Cell_Tester, start_value=3.367,         # Maximum Power Point Current
               distribution={"Feature" : {"Fixed": {"mean": 3.367}}})
Pmax = Feature("Ftr4", "Pmax", victim=Solar_Cell_Tester, start_value=2.3,       # Peak Power
               distribution={"Feature" : {"Fixed": {"mean": 2.3}}})
IV_Curve = Timeseries("Ts2", "IV_Curve", victim=Solar_Cell_Tester, no_negative=True,
                      distribution={"Function": {(0, 0.4): "3.5 - 0.05*x",
                                                 (0.4, 0.8): [[0.4, 0.41, Vm.featureValue, Voc.featureValue], [Isc.featureValue-0.02, Isc.featureValue-0.023, Im.featureValue, 0]]}, "DataPoints": 100})
Power_Curve = Timeseries("Ts3", "Power_Curve", victim=Solar_Cell_Tester, no_negative=True,
                      distribution={"Function": {(0, 0.46): "4.8913*x",
                                                 (0.46, 0.8): [[0.46, Vm.featureValue, Voc.featureValue-0.02, Voc.featureValue], [Pmax.featureValue-0.05, Pmax.featureValue, 0.61, 0]]}, "DataPoints": 100})
# FF = Feature("Ftr5", "FF", victim=Solar_Cell_Tester,            # Fill Factor
#                dependent={"Function": "(Vm * Im)/(Isc * Voc)", "Vm": Vm, "Im": Im, "Isc": Isc, "Voc": Voc},
#                distribution={})
# EFF = Feature("Ftr6", "EFF", victim=Solar_Cell_Tester,          # Efficiency
#               dependent={"Function": "(Isc * Voc * FF)/1000", "Isc": Isc, "Voc": Voc, "FF": FF},
#               distribution={})
# Temp = Feature("Ftr7", "Temp", victim=Solar_Cell_Tester,        # Temperature
#               distribution={"Feature": {"Normal": {"mean": 25, "stdev": 0}}})
# Rs = Feature("Ftr8", "Rs", victim=Solar_Cell_Tester,            # Series Resistance
#               distribution={})
# Rsh = Feature("Ftr9", "Rsh", victim=Solar_Cell_Tester,          # Shunt Resistance
#               distribution={})


# Routing
Solar_Cells.defineRouting([Solar_Cell_Tester])
Solar_Cell_Tester.defineRouting([Solar_Cells], [Q])
Q.defineRouting([Solar_Cell_Tester], [Machine1])
Machine1.defineRouting([Q], [E1])
E1.defineRouting([Machine1])


def main(test=0):
    maxSimTime = 10
    objectList = [Solar_Cells, Solar_Cell_Tester, E1, Machine1, Q, Isc, Voc, Pmax, Vm, Im, IV_Curve, Power_Curve]

    runSimulation(objectList, maxSimTime, trace=False)

    # df = G.get_simulation_results_dataframe()
    # ExcelPrinter(df, "SolarPanelLine")
    # df = getEntityData([E])
    # df.to_csv("SolarPanelLine.csv", index=False, encoding="utf8")

    print(type(E1.entities[0].features[5]))
    for idx, i in enumerate(E1.entities[0].features[5]):
        print(E1.entities[1].feature_times[5][idx], ": ", i)
    plt.plot([0], [E1.entities[0].features[0]], "o")
    plt.plot([E1.entities[0].features[1]], [0], "o")
    plt.plot([E1.entities[0].features[2]], [0], "o")
    plt.plot([0], [E1.entities[0].features[3]], "o")
    plt.plot([E1.entities[0].features[2]], [E1.entities[0].features[3]], "o")
    plt.plot(E1.entities[0].feature_times[5], E1.entities[0].features[5], c="red")
    plt.plot(E1.entities[0].feature_times[6], E1.entities[0].features[6], c="green")
    plt.show()

    # print("""
    #         Ausschuss:          {}
    #         Produziert:         {}
    #         Blockiert für:      {:.2f}
    #         Simulationszeit:    {}
    #         Laufzeit:           {:.2f}
    #         """.format(maxSimTime, time.time() - start))

if __name__ == "__main__":
    main()
