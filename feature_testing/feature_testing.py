from manpy.simulation.imports import Repairman, Queue, Machine, Source, Exit, Failure
from manpy.simulation.Globals import runSimulation, G
import os
os.chdir("..")
from Machine_features import Machine_features

def ExcelPrinter(filename):
    df = G.get_simulation_results_dataframe()
    # df = G.get_simulation_entities_history()
    number_sheets = df.shape[0]//65535 + 1
    
    if number_sheets > 1:
        for i in range(number_sheets):
            file = "{}({}).xls".format(filename, i)
            df[65535*(i): 65535*(i+1)].to_excel(file)
    else:
        df.to_excel("{}.xls".format(filename))

f1 = ({"Fixed": {"mean": 0}}, {"Normal": {"mean": 120, "stdev": 30, "min": 60, "max": 180}})
f2 = ({"Normal": {"mean": 0.5, "stdev": 0.2, "min": 0.1, "max": 0.9}}, {"Fixed": {"mean": 1}})
f3 = ({"Fixed": {"mean": 1}}, {"Normal": {"mean": 3460, "stdev": 1800, "min": 800, "max": 6000}})

#Objects
#R = Repairman("R1", "Sascha")
S = Source("S1", "Source", interArrivalTime={"Fixed": {"mean": 0.1}}, entity="manpy.Part", capacity=100)
M1 = Machine_features("M1", "Machine1", processingTime={"Normal": {"mean": 0.2, "stdev": 0.1, "min": 0.08, "max": 0.34}}, features=[f1, f2, f3])
E1 = Exit("E1", "Exit1")

#Failures
#F1 = Failure(victim=M1, distribution={"TTF": {"Normal": {"mean": 120, "stdev": 45, "min": 60, "max": 200}}, "TTR":{"Normal": {"mean": 10, "stdev": 3, "min": 5, "max": 18}}}, repairman=R)

#Routing
S.defineRouting([M1])
M1.defineRouting([S], [E1])
E1.defineRouting([M1])

def main(test=0):
    maxSimTime =  600
    
    #runSim with trace
    runSimulation([S, M1, E1], maxSimTime, trace="Yes")
    
    #Metrics
    failure_ratio1 = (M1.totalFailureTime/maxSimTime)*100
    #working_ratio = (R.totalWorkingTime/maxSimTime)*100
    
    #pass results
    if test:
        return {"parts_1": E1.numOfExits,
                "failure_ratio1": failure_ratio1,
                #"working_ratio": working_ratio
                }

    #print
    print("""
          Number of {}: {:5d} \n
          {:8s} | failure : {:5.2f} % \n
          """.format(E1.objName, E1.numOfExits, M1.objName, failure_ratio1))
    
    #ExcelHandler is not working, outputs an empty xls file
    #ExcelHandler.outputTrace("trace_testing")
    
    #workaround through a static function from the class G in Globals, that outputs the tracing as a DataFrame
    ExcelPrinter("feature_testing/feature_testing")

if __name__=="__main__":
    main()