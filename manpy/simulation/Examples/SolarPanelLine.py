from manpy.simulation.imports import Machine, Source, Exit, Failure, Feature, Queue
from manpy.simulation.Globals import runSimulation, getEntityData, G, ExcelPrinter
import time

start = time.time()

class Machine_control(Machine):
    def condition(self):
        return False


# Objects
S = Source("S1", "Source", interArrivalTime={"Fixed": {"mean": 0}}, entity="manpy.Part", capacity=1)
Solar_Cell_Tester = Machine("M0", "Solar_Cell_Tester")
Q0 = Queue("Q0", "Queue0")
Laser_Cutter1 = Machine("M1", "Laser_Cutter1")
Laser_Cutter2 = Machine("M2", "Laser_Cutter2")
Q1 = Queue("Q1", "Queue1")
Tabbing_and_String1 = Machine("M3", "Tabbing_and_String1")
Tabbing_and_String2 = Machine("M4", "Tabbing_and_String2")
Tabbing_and_String3 = Machine("M5", "Tabbing_and_String3")
Q2 = Queue("Q2", "Queue2")
EVA_Cutting = Machine("M6", "EVA_Cutting")
Q3 = Queue("Q3", "Queue3")
Bus_Bar_Cutting = Machine("M7", "Bus_Bar_Cutting")
Q4 = Queue("Q4", "Queue4")
Glass_Loader = Machine("M8", "Glass_loader")
Q5 = Queue("Q5", "Queue5")
LayingUp = Machine("M9", "LayingUp")
Q6 = Queue("Q6", "Queue6")
EL_VI_Test1 = Machine("M10", "EL_VI_Test1")
EL_VI_Test2 = Machine("M12", "EL_VI_Test2")
Q7 = Queue("Q7", "Queue7")
Laminating = Machine("M11", "Laminating")
Q8 = Queue("Q8", "Queue8")
Trimming = Machine("M13", "Trimming")
Q9 = Queue("Q9", "Queue9")
Inspection = Machine("M14", "Inspection")
Q10 = Queue("Q10", "Queue10")
Glueing_Framing = Machine("M15", "Glueing_Framing")
Q11 = Queue("Q11", "Queue11")
Fix_Junction = Machine("M16", "Fix_junction")
Q12 = Queue("Q12", "Queue12")
Soldering = Machine("M17", "Soldering")
Q13 = Queue("Q13", "Queue13")
Inject_Gel = Machine("M18", "Inject_Gel")
Q14 = Queue("Q14", "Queue14")
Unload = Machine("M19", "Unload")
Q15 = Queue("Q15", "Queue15")
Grind = Machine("M20", "Grind")
Q16 = Queue("Q16", "Queue16")
IV_Test = Machine("M21", "IV_Test")
Q17 = Queue("Q17", "Queue17")
HIpot_Resistance_Test = Machine("M22", "HIpot_Resistance_Test")
Q18 = Queue("Q18", "Queue18")
EL_VI_Test3 = Machine("M23", "EL_VI_Test3")
E = Exit("E", "Exit")



# ObjectProperty
# SolarCellTester

# EL_VI_Test1

# EL_VI_Test2

# IV_Test

# # EL_VI_Test3


# Routing
S.defineRouting([Solar_Cell_Tester])
Solar_Cell_Tester.defineRouting([S], [Q0])
Q0.defineRouting([Solar_Cell_Tester], [Laser_Cutter1, Laser_Cutter2])
Laser_Cutter1.defineRouting([Q0], [Q1])
Laser_Cutter2.defineRouting([Q0], [Q1])
Q1.defineRouting([Laser_Cutter1, Laser_Cutter2], [Tabbing_and_String1, Tabbing_and_String2, Tabbing_and_String3])
Tabbing_and_String1.defineRouting([Q1], [Q2])
Tabbing_and_String2.defineRouting([Q1], [Q2])
Tabbing_and_String3.defineRouting([Q1], [Q2])
Q2.defineRouting([Tabbing_and_String1, Tabbing_and_String2, Tabbing_and_String3], [EVA_Cutting])
EVA_Cutting.defineRouting([Q2], [Q3])
Q3.defineRouting([EVA_Cutting], [Bus_Bar_Cutting])
Bus_Bar_Cutting.defineRouting([Q3], [Q4])
Q4.defineRouting([Bus_Bar_Cutting], [Glass_Loader])
Glass_Loader.defineRouting([Q4], [Q5])
Q5.defineRouting([Glass_Loader], [LayingUp])
LayingUp.defineRouting([Q5], [Q6])
Q6.defineRouting([LayingUp], [EL_VI_Test1, EL_VI_Test2])
EL_VI_Test1.defineRouting([Q6], [Q7])
EL_VI_Test2.defineRouting([Q6], [Q7])
Q7.defineRouting([EL_VI_Test1, EL_VI_Test2], [Laminating])
Laminating.defineRouting([Q7], [Q8])
Q8.defineRouting([Laminating], [Trimming])
Trimming.defineRouting([Q8], [Q9])
Q9.defineRouting([Trimming], [Inspection])
Inspection.defineRouting([Q9], [Q10])
Q10.defineRouting([Inspection], [Glueing_Framing])
Glueing_Framing.defineRouting([Q10], [Q11])
Q11.defineRouting([Glueing_Framing], [Fix_Junction])
Fix_Junction.defineRouting([Q11], [Q12])
Q12.defineRouting([Fix_Junction], [Soldering])
Soldering.defineRouting([Q12], [Q13])
Q13.defineRouting([Soldering], [Inject_Gel])
Inject_Gel.defineRouting([Q13], [Q14])
Q14.defineRouting([Inject_Gel], [Unload])
Unload.defineRouting([Q14], [Q15])
Q15.defineRouting([Unload], [Grind])
Grind.defineRouting([Q15], [Q16])
Q16.defineRouting([Grind], [IV_Test])
IV_Test.defineRouting([Q16], [Q17])
Q17.defineRouting([IV_Test], [HIpot_Resistance_Test])
HIpot_Resistance_Test.defineRouting([Q17], [Q18])
Q18.defineRouting([HIpot_Resistance_Test], [EL_VI_Test3])
EL_VI_Test3.defineRouting([Q18], [E])



def main(test=0):
    maxSimTime = 50
    objectList = [S, Q0, Q1, Q2, Q3, Q4, Q5, Q6, Q7, Q8, Q9, Q10, Q11, Q12, Q13, Q14, Q15, Q16, Q17, Q18,
                  Solar_Cell_Tester, Laser_Cutter1, Laser_Cutter2, Tabbing_and_String1, Tabbing_and_String2,
                  Tabbing_and_String3, EVA_Cutting, Bus_Bar_Cutting, Glass_Loader, LayingUp,
                  EL_VI_Test1, EL_VI_Test2, Laminating, Trimming, Inspection, Glueing_Framing, Fix_Junction, Soldering,
                  Inject_Gel, Unload, Grind, IV_Test, HIpot_Resistance_Test, EL_VI_Test3, E]

    runSimulation(objectList, maxSimTime)

    # df = G.get_simulation_results_dataframe()
    # ExcelPrinter(df, "ExampleLine")
    df = getEntityData()
    df.to_csv("ExampleLine.csv", index=False, encoding="utf8")

    print("""
            Ausschuss:          {}
            Produziert:         {}
            Blockiert für:      {:.2f}
            Simulationszeit:    {}
            Laufzeit:           {:.2f}
            """.format(maxSimTime, time.time() - start))

if __name__ == "__main__":
    main()
