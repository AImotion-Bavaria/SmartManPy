from manpy.simulation.core.Globals import runSimulation, getFeatureData, getTimeSeriesData
from manpy.simulation.core.ProductionLineModule import generate_routing_from_list
from manpy.simulation.imports import Machine, Source, Exit, Failure, Feature, Queue, Timeseries, Assembly, Frame, ContinuosNormalDistribution, RandomDefectStateController

from manpy.simulation.Examples.SolarPanelLine_Machines.SPL_Solar_Cell_Tester import solar_cell_tester_module
from manpy.simulation.Examples.SolarPanelLine_Machines.SPL_Tabber_Str import tabber_str_module
from manpy.simulation.Examples.SolarPanelLine_Machines.SPL_Lamination import lamination_module
from manpy.simulation.Examples.SolarPanelLine_Machines.SPL_Gluing import gluing_module


import time
import matplotlib.pyplot as plt
import pandas as pd

start = time.time()

# produces 16 265Watt Solar Panels/hour. 60 Solar Cells for one Panel, 225sec per Panel
# Details:
# https://www.solarmakingmachine.com/10-30MW-Full-Automatic-Solar-Panel-Assembly-Line/



# Objects
Solar_Cells = Source("S0", "Solar_Cells", interArrivalTime={"Fixed": {"mean": 2}}, entity="manpy.Part")
# Solar_Cell_Tester = Machine("M0", "Solar_Cell_Tester", processingTime={"Fixed": {"mean": 3}}, control=condition)
Q0 = Queue("Q0", "Queue0")
Solar_Cell_Scribing = Machine("M1", "Solar_Cell_Scribing", processingTime={"Fixed": {"mean": 3.75}})
Solar_Strings = Source("S1", "Solar_Strings", interArrivalTime={"Fixed": {"mean": 10}}, entity="manpy.Frame", capacity=60)
Assembly0 = Assembly("A0", "Assembly0")
Q1 = Queue("Q1", "Queue1")
Layup = Machine("M3", "Layup", processingTime={"Fixed": {"mean": 20}})
Q2 = Queue("Q2", "Queue2")
EL_Test = Machine("M4", "EL_Test", processingTime={"Fixed": {"mean": 10}})
Q3 = Queue("Q3", "Queue3")
Q4 = Queue("Q4", "Queue4")

# TODO does the processing time make sense?
# -> times are in seconds!
E1 = Exit("E1", "Exit")
# EVA_TPT = Source("S2", "EVA_TPT", interArrivalTime={"Fixed": {"mean": 100}}, entity="manpy.Frame")
# EVA_TPT_Cutter = Machine("M4", "EVA_TPT_Cutter", processingTime={"Fixed": {"mean": 150}})



# Welding (Tabber/Stringer)
# similar to soldering from example line

# Cutting
# TODO since it's probably a laser
# --> Similar to pick & place: just a failure

# Gluing

# ObjectInterruption
# Layup
Visual_Fail = Failure("Flr0", "Visual_Fail", victim=Layup, entity=True, remove=True, distribution={"TTF": {"Fixed": {"mean": 0.8}}, "TTR": {"Normal": {"mean": 300, "stdev": 40, "min":0, "probability": 0.008}}})
# EL_Tester
Crack = Failure("Flr1", "Crack", victim=EL_Test, entity=True, distribution={"TTF": {"Fixed": {"mean": 0.9}}, "TTR": {"Fixed": {"mean": 0, "probability": 0.01}}})
Black_spot = Failure("Flr2", "Black_spot", victim=EL_Test, entity=True, distribution={"TTF": {"Fixed": {"mean": 0.9}}, "TTR": {"Fixed": {"mean": 0, "probability": 0.01}}})
Mixed_Wafers = Failure("Flr3", "Mixed_Wafers", victim=EL_Test, entity=True, distribution={"TTF": {"Fixed": {"mean": 0.9}}, "TTR": {"Fixed": {"mean": 0, "probability": 0.01}}})
Process_Defect = Failure("Flr4", "Process_Defect", victim=EL_Test, entity=True, distribution={"TTF": {"Fixed": {"mean": 0.9}}, "TTR": {"Fixed": {"mean": 0, "probability": 0.01}}})
Cold_Soder_Joint = Failure("Flr5", "Cold_Soder_Joint", victim=EL_Test, entity=True, distribution={"TTF": {"Fixed": {"mean": 0.9}}, "TTR": {"Fixed": {"mean": 0, "probability": 0.01}}})

# TODO IV Test?

# Routing
routing = [
    [Solar_Cells],
    [solar_cell_tester_module],
    [Q0],
    [Solar_Cell_Scribing, Solar_Strings],
    [Assembly0],
    [tabber_str_module],
    [Q1],
    [Layup],
    [Q2],
    [lamination_module],
    [Q3],
    [gluing_module],
    [Q4],
    [EL_Test],
    [E1]
]


lamination_objects = lamination_module.getObjectList()
tester_objects = solar_cell_tester_module.getObjectList()
tabber_objects = tabber_str_module.getObjectList()
gluing_objects = gluing_module.getObjectList()

generate_routing_from_list(routing)

def main(test=0):
    maxSimTime = 15000

    objectList = [Solar_Cells]

    objectList.extend(tester_objects)
    objectList.extend(
                  [Q0,
                  Solar_Cell_Scribing, Solar_Strings, Assembly0,
                Q1, Layup, Visual_Fail, Q2,
                Q3, Q4,
                  EL_Test, E1])

    objectList.extend(tabber_objects)
    objectList.extend(lamination_objects)
    objectList.extend(gluing_objects)

    # from manpy.simulation.core.Database import ManPyQuestDBDatabase
    # db = ManPyQuestDBDatabase()
    # runSimulation(objectList, maxSimTime, db=db)
    runSimulation(objectList, maxSimTime, db=None)

    # sct = getFeatureData([Solar_Cell_Tester, Layup])
    # TS = getTimeSeriesData(IV_Curve)
    # sct.to_csv("Solar_Cell_Tester.csv", index=False, encoding="utf8")
    # TS.to_csv("IV_Curve.csv", index=False, encoding="utf8")
    # TS[1].to_csv("PV_Curve.csv", index=False, encoding="utf8")

    # lamination_ts = getTimeSeriesData(Lamination_Pressure_Curve)
    # print(lamination_ts)
    # lamination_ts.to_csv("TS_Lamination_Pressure.csv", index=False, encoding="utf8")

    # with pd.option_context('display.max_columns', None):
    #     print(sct.drop(["ID"], axis=1).describe())

    # use this code for plotting -> change machine in for loop

    # for i in Lamination.entities:
        # print(" Isc: ", [i.features[0]], "\n",
        #       "Voc: ", [i.features[1]], "\n",
        #       "MPP: ", [i.features[2]], [i.features[3]], "\n",
        #       "Pmax: ", [i.features[4]], "\n",
        #       )
        # plt.plot([0], [i.features[0]], "o", c="orange", label="Isc")
        # plt.plot([i.features[1]], [0], "o", c="blue", label="Voc")
        # plt.plot([i.features[2]], [i.features[3]], "^", c="purple", label="MPP")
        # plt.plot([i.features[2]], [i.features[4]], "^", c="purple")
        # plt.plot(i.timeseries_times[0], i.timeseries[0], c="red", label="IV")
        # plt.plot(i.timeseries_times[1], i.timeseries[1], c="green", label="PV")
        # plt.legend()
        # plt.plot(i.timeseries[-1])
        # plt.plot(i.timeseries[-2])
        # plt.show()



    print("""
            Ausschuss:          {}
            Produziert:         {}
            Simulationszeit:    {}
            Laufzeit:           {:.2f}
            """.format(len(solar_cell_tester_module.first[0].discards) + len(Layup.discards), len(E1.entities), maxSimTime, time.time() - start))




if __name__ == "__main__":
    main()
