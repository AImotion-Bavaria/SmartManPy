from manpy.simulation.imports import Machine, Source, Exit, Failure, Feature, Queue, Timeseries, Assembly, Frame
from manpy.simulation.Globals import runSimulation, getFeatureData, getTimeSeriesData, G, ExcelPrinter
import time
import matplotlib.pyplot as plt
import pandas as pd

start = time.time()

# produces 16 265Watt Solar Panels/hour. 60 Solar Cells for one Panel, 225sec per Panel

def condition(self):
    activeEntity = self.Res.users[0]
    features = [3.5, 0.62, None, None, 2.3]
    for idx, feature in enumerate(features):
        if feature != None:
            if activeEntity.features[idx] < 0.9*feature or activeEntity.features[idx] > 1.1*feature:
                return True
    return False


# Objects
Solar_Cells = Source("S0", "Solar_Cells", interArrivalTime={"Fixed": {"mean": 2}}, entity="manpy.Part")
Solar_Cell_Tester = Machine("M0", "Solar_Cell_Tester", processingTime={"Fixed": {"mean": 3}}, control=condition)
# Solar_Cell_Tester = Machine("M0", "Solar_Cell_Tester", processingTime={"Fixed": {"mean": 3}})
Q0 = Queue("Q0", "Queue0")
Solar_Cell_Scribing = Machine("M1", "Solar_Cell_Scribing", processingTime={"Fixed": {"mean": 3.75}})
Frame.capacity = 60
Solar_Strings = Source("S1", "Solar_Strings", interArrivalTime={"Fixed": {"mean": 100}}, entity="manpy.Frame")
Assembly0 = Assembly("A0", "Assembly0")
Tabber_Stringer = Machine("M2", "Tabber_Stringer", processingTime={"Fixed": {"mean": 150}})
Q1 = Queue("Q1", "Queue1")
Layup = Machine("M3", "Layup", processingTime={"Fixed": {"mean": 200}})
Q2 = Queue("Q2", "Queue2")
EL_Test = Machine("M1", "Solar_Cell_Scribing", processingTime={"Fixed": {"mean": 100}})
E1 = Exit("E1", "Exit")
#Frame.capacity = 1 TODO: Allow different Frame capacities
# EVA_TPT = Source("S2", "EVA_TPT", interArrivalTime={"Fixed": {"mean": 100}}, entity="manpy.Frame")
# EVA_TPT_Cutter = Machine("M4", "EVA_TPT_Cutter", processingTime={"Fixed": {"mean": 150}})


# ObjectProperty
# SolarCellTester
Isc = Feature("Ftr0", "Isc", victim=Solar_Cell_Tester,                                      # short-circuit current
               distribution={"Feature": {"Normal": {"mean": 3.5, "stdev": 0.04375}}})
Voc = Feature("Ftr1", "Voc", victim=Solar_Cell_Tester,                                      # open circuit voltage
               distribution={"Feature": {"Normal": {"mean": 0.62, "stdev": 0.00155}}})
Vm = Feature("Ftr2", "Vm", victim=Solar_Cell_Tester,                                        # Maximum Power Point Voltage
               dependent={"Function": "Voc-0.14", "Voc": Voc},
               distribution={"Feature": {"Normal": {"stdev": 0.004}}})
Im = Feature("Ftr3", "Im", victim=Solar_Cell_Tester,                                        # Maximum Power Point Current
               dependent={"Function": "Isc-0.133", "Isc": Isc},
               distribution={"Feature": {"Normal": {"stdev": 0.0135}}})
Pmax = Feature("Ftr4", "Pmax", victim=Solar_Cell_Tester,                                    # Peak Power
               dependent={"Function": "2.3+(Isc+Im-6.867)", "Isc": Isc, "Im": Im})
IV_Curve = Timeseries("Ts2", "IV_Curve", victim=Solar_Cell_Tester, no_negative=True,        # Current-Voltage Curve
                      distribution={"Function": {(0, 0.4): "Isc - 0.05*x",
                                                 (0.4, 0.8): [[0.4, 0.41, "Vm", "Voc"], ["Isc-0.02", "Isc-0.023", "Im", 0]]},
                                    "Vm": Vm, "Voc": Voc, "Isc": Isc, "Im": Im,
                                    "DataPoints": 100})
Power_Curve = Timeseries("Ts3", "Power_Curve", victim=Solar_Cell_Tester, no_negative=True,  # Power-Voltage Curve
                      distribution={"Function": {(0, 0.46): "((Pmax-0.05)/0.46)*x",
                                                 (0.46, 0.8): [[0.46, "Vm", "Vm+0.02", "Voc"], ["Pmax-0.05", "Pmax", "Pmax-0.02", 0]]},
                                    "Vm": Vm, "Voc": Voc, "Pmax": Pmax,
                                    "DataPoints": 100})
FF = Feature("Ftr5", "FF", victim=Solar_Cell_Tester,                                        # Fill Factor
               dependent={"Function": "(Vm * Im)/(Isc * Voc)", "Vm": Vm, "Im": Im, "Isc": Isc, "Voc": Voc})
EFF = Feature("Ftr6", "EFF", victim=Solar_Cell_Tester,                                      # Efficiency
              dependent={"Function": "(Isc * Voc * FF)/1000", "Isc": Isc, "Voc": Voc, "FF": FF})
Temp = Feature("Ftr7", "Temp", victim=Solar_Cell_Tester,                                    # Temperature
              distribution={"Feature": {"Normal": {"mean": 25, "stdev": 1.5}}})

# Test = Feature("Ftr", "Test", victim=Solar_Cell_Scribing,
#               distribution={"Feature": {"Fixed": {"mean": 0}}})


# ObjectInterruption
# Layup
Visual_Fail = Failure("Flr0", "Visual_Fail", victim=Layup, entity=True, remove=True, distribution={"TTF": {"Fixed": {"mean": 0.8}}, "TTR": {"Normal": {"mean": 300, "stdev": 40, "min":0, "probability": 0.008}}})
# EL_Tester
Crack = Failure("Flr1", "Crack", victim=EL_Test, entity=True, distribution={"TTF": {"Fixed": {"mean": 0.9}}, "TTR": {"Fixed": {"mean": 0, "probability": 0.01}}})
Black_spot = Failure("Flr2", "Black_spot", victim=EL_Test, entity=True, distribution={"TTF": {"Fixed": {"mean": 0.9}}, "TTR": {"Fixed": {"mean": 0, "probability": 0.01}}})
Mixed_Wafers = Failure("Flr3", "Mixed_Wafers", victim=EL_Test, entity=True, distribution={"TTF": {"Fixed": {"mean": 0.9}}, "TTR": {"Fixed": {"mean": 0, "probability": 0.01}}})
Process_Defect = Failure("Flr4", "Process_Defect", victim=EL_Test, entity=True, distribution={"TTF": {"Fixed": {"mean": 0.9}}, "TTR": {"Fixed": {"mean": 0, "probability": 0.01}}})
Cold_Soder_Joint = Failure("Flr5", "Cold_Soder_Joint", victim=EL_Test, entity=True, distribution={"TTF": {"Fixed": {"mean": 0.9}}, "TTR": {"Fixed": {"mean": 0, "probability": 0.01}}})


# Routing
Solar_Cells.defineRouting([Solar_Cell_Tester])
Solar_Cell_Tester.defineRouting([Solar_Cells], [Q0])
Q0.defineRouting([Solar_Cell_Tester], [Solar_Cell_Scribing])
Solar_Cell_Scribing.defineRouting([Q0], [Assembly0])
Solar_Strings.defineRouting([Assembly0])
Assembly0.defineRouting([Solar_Cell_Scribing, Solar_Strings], [Tabber_Stringer])
Tabber_Stringer.defineRouting([Assembly0], [Q1])
Q1.defineRouting([Tabber_Stringer], [Layup])
Layup.defineRouting([Q1], [Q2])
Q2.defineRouting([Layup], [EL_Test])
EL_Test.defineRouting([Q2], [E1])
E1.defineRouting([EL_Test])


def main(test=0):
    maxSimTime = 2000
    objectList = [Solar_Cells, Solar_Cell_Tester, Isc, Voc, Vm, Im, Pmax, IV_Curve, Power_Curve, FF, EFF, Temp, Q0, Solar_Cell_Scribing, Solar_Strings, Assembly0, Tabber_Stringer, Q1, Layup, Visual_Fail, Q2, EL_Test, E1]

    runSimulation(objectList, maxSimTime, trace=False)

    sct = getFeatureData([Solar_Cell_Tester, Layup])
    TS = getTimeSeriesData([Solar_Cell_Tester])
    sct.to_csv("Solar_Cell_Tester.csv", index=False, encoding="utf8")
    TS[0].to_csv("IV_Curve.csv", index=False, encoding="utf8")
    TS[1].to_csv("PV_Curve.csv", index=False, encoding="utf8")

    with pd.option_context('display.max_columns', None):
        print(sct.drop(["ID"], axis=1).describe())


    # for i in Solar_Cell_Tester.entities:
    #     print(" Isc: ", [i.features[0]], "\n",
    #           "Voc: ", [i.features[1]], "\n",
    #           "MPP: ", [i.features[2]], [i.features[3]], "\n",
    #           "Pmax: ", [i.features[4]], "\n",
    #           )
    #     plt.plot([0], [i.features[0]], "o", c="orange", label="Isc")
    #     plt.plot([i.features[1]], [0], "o", c="blue", label="Voc")
    #     plt.plot([i.features[2]], [i.features[3]], "^", c="purple", label="MPP")
    #     plt.plot([i.features[2]], [i.features[4]], "^", c="purple")
    #     plt.plot(i.timeseries_times[0], i.timeseries[0], c="red", label="IV")
    #     plt.plot(i.timeseries_times[1], i.timeseries[1], c="green", label="PV")
    #     plt.legend()
    #     plt.show()


    print("""
            Ausschuss:          {}
            Produziert:         {}
            Simulationszeit:    {}
            Laufzeit:           {:.2f}
            """.format(len(Solar_Cell_Tester.discards) + len(Layup.discards), len(E1.entities), maxSimTime, time.time() - start))

if __name__ == "__main__":
    main()
