from manpy.simulation.imports import Machine, Source, Exit, Failure, Feature, Queue, Timeseries
from manpy.simulation.Globals import runSimulation, getEntityData, G, ExcelPrinter
import time
import matplotlib.pyplot as plt

start = time.time()

# produces 16 265Watt Solar Panels/hour. 60 Solar Cells for one Panel

def condition(self):
    activeEntity = self.Res.users[0]
    features = [3.5, 0.62, 0.48, 3.367, 2.3]
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
Isc = Feature("Ftr0", "Isc", victim=Solar_Cell_Tester,                          # short-circuit current
               distribution={"Feature": {"Normal": {"mean": 3.5, "stdev": 0.0875}}})
Voc = Feature("Ftr1", "Voc", victim=Solar_Cell_Tester,                          # open circuit voltage
               distribution={"Feature": {"Normal": {"mean": 0.62, "stdev": 0.00155}}})
Vm = Feature("Ftr2", "Vm", victim=Solar_Cell_Tester,                            # Maximum Power Point Voltage
               dependent={"Function": "Voc-0.14", "Voc": Voc},
               distribution={"Feature": {"Normal": {"stdev": 0.004}}})
Im = Feature("Ftr3", "Im", victim=Solar_Cell_Tester,                            # Maximum Power Point Current
               dependent={"Function": "Isc-0.133", "Isc": Isc},
               distribution={"Feature": {"Normal": {"stdev": 0.03325}}})
Pmax = Feature("Ftr4", "Pmax", victim=Solar_Cell_Tester,                        # Peak Power
               dependent={"Function": "2.3-(Isc-Im)", "Isc": Isc, "Im": Im})
IV_Curve = Timeseries("Ts2", "IV_Curve", victim=Solar_Cell_Tester, no_negative=True,
                      distribution={"Function": {(0, 0.4): "Isc - 0.05*x",
                                                 (0.4, 0.8): [[0.4, 0.41, "Vm", "Voc"], ["Isc-0.02", "Isc-0.023", "Im", 0]]},
                                    "Vm": Vm, "Voc": Voc, "Isc": Isc, "Im": Im,
                                    "DataPoints": 100})
Power_Curve = Timeseries("Ts3", "Power_Curve", victim=Solar_Cell_Tester, no_negative=True,
                      distribution={"Function": {(0, 0.46): "((Pmax-0.05)/0.46)*x",
                                                 (0.46, 0.8): [[0.46, "Vm", "Vm+0.02", "Voc"], ["Pmax-0.05", "Pmax", "Pmax-0.02", 0]]},
                                    "Vm": Vm, "Voc": Voc, "Pmax": Pmax,
                                    "DataPoints": 100})
#
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
    objectList = [Solar_Cells, Solar_Cell_Tester, E1, Machine1, Q, Isc, Voc, Vm, Im, Pmax, IV_Curve, Power_Curve]

    runSimulation(objectList, maxSimTime, trace=False)

    # df = G.get_simulation_results_dataframe()
    # ExcelPrinter(df, "SolarPanelLine")
    # df = getEntityData([E])
    # df.to_csv("SolarPanelLine.csv", index=False, encoding="utf8")




    for i in E1.entities:
        print(" Isc: ", [i.features[0]], "\n",
              "Voc: ", [i.features[1]], "\n",
              "MPP: ", [i.features[2]], [i.features[3]], "\n",
              "Pmax: ", [i.features[4]], "\n",
              )

        plt.plot([0], [i.features[0]], "o", c="orange", label="Isc")
        plt.plot([i.features[1]], [0], "o", c="blue", label="Voc")
        plt.plot([i.features[2]], [i.features[3]], "^", c="purple", label="MPP")
        plt.plot([i.features[2]], [i.features[4]], "^", c="purple")
        plt.plot(i.feature_times[5], i.features[5], c="red", label="IV")
        plt.plot(i.feature_times[6], i.features[6], c="green", label="PV")
        plt.legend()
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
