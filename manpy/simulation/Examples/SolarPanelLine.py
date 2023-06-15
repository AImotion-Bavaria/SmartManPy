from manpy.simulation.imports import Machine, Source, Exit, Failure, Feature, Queue, Timeseries, Assembly, Frame, ContinuosNormalDistribution, RandomDefectStateController
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

def resistance_failure_condition(self):
    r = Tab_Str_Resistance.get_feature_value()

    if r is not None and r > 535:
        print("Too much resistance!")
        return True
    else:
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
EL_Test = Machine("M4", "Solar_Cell_Scribing", processingTime={"Fixed": {"mean": 100}})
Q3 = Queue("Q3", "Queue3")
Q4 = Queue("Q4", "Queue4")

# TODO does the processing time make sense?
# -> times are in seconds!
Gluing = Machine("M5", "Gluing", processingTime={"Fixed": {"mean": 100}})
Lamination = Machine("m9", "M_Lamination", processingTime={"Fixed": {"mean": 100}})
E1 = Exit("E1", "Exit")
#Frame.capacity = 1 TODO: Allow different Frame capacities -> WIP!
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
                         # Interval values are acutal x values
                         # Interval from (0, 0.46) is a function, not interpolated
                      distribution={"Function": {(0, 0.46): "((Pmax-0.05)/0.46)*x",
                                                 # from 0.46 to 0.8 the features are interpolated
                                                 # first list is x, second list is y -> 4 datapoints overall
                                                 # 4 datapoints at least
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


# Welding (Tabber/Stringer)
# similar to soldering from example line
Tab_Str_Resistance_Too_High = Failure("Flr1", "RTooHigh", victim=Tabber_Stringer, conditional=resistance_failure_condition,
                                      distribution={"TTF": {"Fixed": {"mean": 0}}, "TTR": {"Fixed": {"mean": 5}}}, waitOnTie=True)

Tab_Str_Voltage = Feature("Tab_Str_Voltage", "Tab_Str_Voltage", victim=Tabber_Stringer, entity=True,
                          distribution_state_controller=ContinuosNormalDistribution(mean_change_per_step=0.0001, initial_mean=1.6,
                                                                         std=0.1, wear_per_step=1, break_point=1000,
                                                                         defect_mean=2.0, defect_std=0.1))
Tab_Str_Power = Feature("Tab_Str_Power", "Tab_Str_Power", victim=Tabber_Stringer, entity=True, dependent={"Function" : "1000*x + 1900", "x" : Tab_Str_Voltage}, distribution={"Feature": {"Normal": {"stdev": 30}}})

Tab_Str_Resistance = Feature("Tab_Str_Resistance", "Tab_Str_Resistance", victim=Tabber_Stringer, entity=True, dependent={"Function" : "(V/I)*1000000", "V" : Tab_Str_Voltage, "I" : Tab_Str_Power}, distribution={"Feature": {"Normal": {"stdev": 5}}}, contribute=[Tab_Str_Resistance_Too_High])

Tab_Str_Force = Feature("Tab_Str_Force", "Tab_Str_Force", victim=Tabber_Stringer,
                        distribution={"Feature": {"Normal": {"mean": 180, "stdev": 30}}})
# Cutting
# TODO since it's probably a laser

# Gluing
glue_temperature = Feature("glue_temp", "Glue_Temperature", victim=Gluing, random_walk=True, start_value=190,
               distribution={"Feature": {"Normal": {"mean": 0, "stdev": 0.3}}})

sG_1 = ContinuosNormalDistribution(
                                   mean_change_per_step=0.0,
                                   initial_mean=400,
                                   std=50,
                                   )

sG_2 = ContinuosNormalDistribution(
                                    mean_change_per_step=0.0,
                                    initial_mean=500,
                                    std=50,
                                    )

s6_3 = ContinuosNormalDistribution(
                                    mean_change_per_step=0.0,
                                    initial_mean=300,
                                    std=50,
                                   )

Amount_StateController = RandomDefectStateController(failure_probability=0.02,
                                                     ok_controller=sG_1,
                                                     defect_controllers=[sG_2, s6_3])
Amount = Feature("Menge", "Menge", victim=Gluing, distribution_state_controller=Amount_StateController)

flow_rate = Feature("Flow_Rate", "Flow_Rate", victim=Gluing,
                    dependent={"Function": "0.9*X", "X": Amount}, dependent_noise_std=10)

# Lamination
# Two timeseries: pressure and temperature, interpolation based on features
# Lamination_Pressure = Feature("Lamination_Pressure", "Lamination_Pressure", victim=Lamination, distribution={"Feature": {"Normal": {"mean": 50, "stdev": 2}}})
# Lamination_Temperature = Feature("Lamination_Temperature", "Lamination_Temperature", victim=Lamination, distribution={"Feature": {"Normal": {"mean": 400, "stdev": 10}}})

# upper interval bound is process time -> how long does the process take, e.g. 200 seconds. Not necessarily the
# same timne unit like in manpy
a = Feature("a", "L1", victim=Lamination,
                        distribution={"Feature": {"Normal": {"mean": 1, "stdev": 2}}})
b = Feature("b", "L2", victim=Lamination,
                        distribution={"Feature": {"Normal": {"mean": 60, "stdev": 2}}})
c = Feature("c", "L3", victim=Lamination,
                        distribution={"Feature": {"Normal": {"mean": 80, "stdev": 2}}})
d = Feature("d", "L4", victim=Lamination,
                        distribution={"Feature": {"Normal": {"mean": 85, "stdev": 2}}})
e = Feature("e", "L5", victim=Lamination,
                        distribution={"Feature": {"Normal": {"mean": 20, "stdev": 2}}})
f = Feature("f", "L6", victim=Lamination,
                        distribution={"Feature": {"Normal": {"mean": 5, "stdev": 2}}})
g = Feature("g", "L7", victim=Lamination,
                        distribution={"Feature": {"Normal": {"mean": 0, "stdev": 2}}})

Lamination_Pressure_Curve = Timeseries("Ts_Lamination_Pressure", "Ts_Lamination_Pressure", victim=Lamination,
                                       no_negative=True, distribution={"Function": {(0, 20): "(2*x)+a",
                                                                                    (20, 60): [[20, 30, 40, 60], ["40+a", "b", "c", "d"]],
                                                                                    (60, 100): [[60, 70, 80, 100], ["d", "e", "f", 0]]},
                                                                       "a": a, "b": b, "c": c, "d": d, "e": e, "f": f,
                                                                       "DataPoints": 100})
# first port is a linear function, second part interpolates log-like curve
# third part interpolates exp-like curve
# we need more features


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
# Q2.defineRouting([Layup], [EL_Test])
# EL_Test.defineRouting([Q2], [E1])
Q2.defineRouting([Layup], [Lamination])
Lamination.defineRouting([Q2], [Q3])
Q3.defineRouting([Lamination], [EL_Test])
EL_Test.defineRouting([Q3], [E1])
E1.defineRouting([EL_Test])


def main(test=0):
    maxSimTime = 50000
    objectList = [Solar_Cells, Solar_Cell_Tester, Isc, Voc, Vm, Im, Pmax, IV_Curve, Power_Curve, FF, EFF, Temp, Q0,
                  Solar_Cell_Scribing, Solar_Strings, Assembly0, Tabber_Stringer, Tab_Str_Resistance_Too_High,
                  Tab_Str_Voltage, Tab_Str_Power, Tab_Str_Resistance, Tab_Str_Force, Gluing, glue_temperature, Amount,
                  flow_rate,  Q1, Layup, Visual_Fail, Q2,
                  EL_Test, E1, Lamination, a, b, c, d, e, f, Lamination_Pressure_Curve, Q3]

    runSimulation(objectList, maxSimTime, trace=False)

    sct = getFeatureData([Solar_Cell_Tester, Layup])
    TS = getTimeSeriesData([Solar_Cell_Tester])
    sct.to_csv("Solar_Cell_Tester.csv", index=False, encoding="utf8")
    TS[0].to_csv("IV_Curve.csv", index=False, encoding="utf8")
    TS[1].to_csv("PV_Curve.csv", index=False, encoding="utf8")
    lamination_ts = getTimeSeriesData([Lamination])
    print(lamination_ts)
    lamination_ts[0].to_csv("TS_Lamination_Pressure.csv", index=False, encoding="utf8")

    with pd.option_context('display.max_columns', None):
        print(sct.drop(["ID"], axis=1).describe())

    # use this code for plotting -> change machine in for loop

    for i in Lamination.entities:
        # print(" Isc: ", [i.features[0]], "\n",
        #       "Voc: ", [i.features[1]], "\n",
        #       "MPP: ", [i.features[2]], [i.features[3]], "\n",
        #       "Pmax: ", [i.features[4]], "\n",
        #       )
        # plt.plot([0], [i.features[0]], "o", c="orange", label="Isc")
        # plt.plot([i.features[1]], [0], "o", c="blue", label="Voc")
        # plt.plot([i.features[2]], [i.features[3]], "^", c="purple", label="MPP")
        # plt.plot([i.features[2]], [i.features[4]], "^", c="purple")
        plt.plot(i.timeseries_times[0], i.timeseries[0], c="red", label="IV")
        plt.plot(i.timeseries_times[1], i.timeseries[1], c="green", label="PV")
        plt.legend()
        plt.show()


    print("""
            Ausschuss:          {}
            Produziert:         {}
            Simulationszeit:    {}
            Laufzeit:           {:.2f}
            """.format(len(Solar_Cell_Tester.discards) + len(Layup.discards), len(E1.entities), maxSimTime, time.time() - start))

if __name__ == "__main__":
    main()
