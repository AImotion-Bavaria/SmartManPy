from manpy.simulation.imports import Machine, Source, Exit, Timeseries
from manpy.simulation.core.Globals import runSimulation, getEntityData, ExcelPrinter, G
import time
import matplotlib.pyplot as plt
start = time.time()

# produces 16 265Watt Solar Panels/hour. 60 Solar Cells for one Panel

def condition(self):
    activeEntity = self.Res.users[0]
    features = [None, None, 3.5, 6.2, 2.3, 0.48, 3.367]
    for idx, feature in enumerate(features):
        if feature is not None:
            if activeEntity.features[idx] < 0.95*feature or activeEntity.features[idx] > 1.05*feature:
                return True
    return False




# Objects
Solar_Cells = Source("S1", "Source", interArrivalTime={"Fixed": {"mean": 0.5}}, entity="manpy.Part", capacity=1)
Solar_Cell_Tester = Machine("M0", "Solar_Cell_Tester", processingTime={"Fixed": {"mean": 1}})
E = Exit("E", "Exit")



# ObjectProperty

# SolarCellTester
IV_Curve = Timeseries("Ts0", "IV_Curve", victim=Solar_Cell_Tester, no_negative=True,
                      distribution={"Function": {(0, 0.4): "3.5 - 0.05*x", (0.4, 0.8): "-410.354*x**3 + 512.626*x**2 - 213.533*x + 33.1356"}, "DataPoints": 100})
Power_Curve = Timeseries("Ts1", "Power_Curve", victim=Solar_Cell_Tester, no_negative=True,
                      distribution={"Function": {(0, 0.46): "4.8913*x", (0.46, 0.8): "-118.304*x**2 + 113.705*x - 25.0214"}, "DataPoints": 100})
# Isc = Feature("Ftr0", "Isc", victim=Solar_Cell_Tester,          # short-circuit current
#                dependent={"Function": "IV_Curve[0]", "IV_Curve": IV_Curve},
#                distribution={})
# Voc = Feature("Ftr1", "Voc", victim=Solar_Cell_Tester,          # open circuit voltage
#                distribution={"Fixed": 6.2})
# Pmax = Feature("Ftr2", "Pmax", victim=Solar_Cell_Tester,        # Peak Power
#                dependent={"Function": "max(Power_Curve)]", "Power_Curve": Power_Curve},
#                distribution={})
# Vm = Feature("Ftr3", "Vm", victim=Solar_Cell_Tester,            # Maximum Power Point Voltage
#                distribution={})
# Im = Feature("Ftr4", "Im", victim=Solar_Cell_Tester,            # Maximum Power Point Current
#                distribution={})
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
Solar_Cell_Tester.defineRouting([Solar_Cells], [E])
E.defineRouting([Solar_Cell_Tester])


def main(test=0):
    maxSimTime = 10
    objectList = [Solar_Cells, Solar_Cell_Tester, IV_Curve, Power_Curve, E]

    runSimulation(objectList, maxSimTime, trace=True)

    df = G.get_simulation_results_dataframe()
    ExcelPrinter(df, "SolarPanelLine")
    df = getEntityData([E])
    df.to_csv("SolarPanelLine.csv", index=False, encoding="utf8")

    print(E.entities)
    plt.plot(E.entities[0].feature_times[0], E.entities[0].features[0])
    plt.plot(E.entities[0].feature_times[1], E.entities[0].features[1], c="orange")
    plt.show()

    print("""
            Ausschuss:          {}
            Produziert:         {}
            Blockiert für:      {:.2f}
            Simulationszeit:    {}
            Laufzeit:           {:.2f}
            """.format(maxSimTime, time.time() - start))

if __name__ == "__main__":
    main()
