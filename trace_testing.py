from manpy.simulation.imports import (Repairman, Source, Machine, Queue, Exit, Failure, ExcelHandler)
from manpy.simulation.Globals import runSimulation, G

def excelPrinter(filename):
    df = G.get_simulation_results_dataframe()
    number_sheets = df.shape[0]//65535 + 1
    
    if number_sheets > 1:
        for i in range(number_sheets):
            file = "{}({}).xls".format(filename, i)
            df[65535*(i): 65535*(i+1)].to_excel(file)
    else:
        df.to_excel("{}.xls".format(filename))

#Objects
R = Repairman("R1", "Sascha")
S = Source("S1", "Source", interArrivalTime={"Fixed": {"mean": 0.2}}, entity="manpy.Part")
M1 = Machine("M1", "Machine1", processingTime={"Normal": {"mean": 0.2, "stdev": 0.1, "min": 0.08, "max": 0.34}})
M2 = Machine("M2", "Machine2", processingTime={"Normal": {"mean": 0.25, "stdev": 0.15, "min": 0.1, "max": 0.4}})
M3 = Machine("M3", "Machine3", processingTime={"Normal": {"mean": 0.8, "stdev": 0.2, "min": 0.58, "max": 1.5}})
Q = Queue("Q", "Queue", capacity = 100)
E1 = Exit("E1", "Exit1")
E2 = Exit("E2", "Exit2")

#Failures
F1 = Failure(victim=M1, distribution={"TTF": {"Normal": {"mean": 120, "stdev": 45, "min": 60, "max": 200}}, "TTR":{"Normal": {"mean": 10, "stdev": 3, "min": 5, "max": 18}}}, repairman=R)
F2 = Failure(victim=M2, distribution={"TTF": {"Fixed": {"mean": 20}}, "TTR":{"Normal": {"mean": 0.5, "stdev": 0.5, "min": 0.2, "max": 1.5}}}, repairman=R)
F3 = Failure(victim=M2, distribution={"TTF": {"Normal": {"mean": 90, "stdev": 18, "min": 15, "max": 180}}, "TTR":{"Normal": {"mean": 6, "stdev": 3, "min": 1, "max": 12}}}, repairman=R)
F4 = Failure(victim=M3, distribution={"TTF": {"Normal": {"mean": 300, "stdev": 100, "min": 75, "max": 1000}}, "TTR":{"Normal": {"mean": 30, "stdev": 10, "min": 15, "max": 50}}}, repairman=R)

#Routing
S.defineRouting([M1])
M1.defineRouting([S], [Q])
Q.defineRouting([M1], [M2, M3])
M2.defineRouting([Q], [E1])
M3.defineRouting([Q], [E2])
E1.defineRouting([M2])
E2.defineRouting([M3])


def main(test=0):
    maxSimTime =  2880
    
    #runSim with trace
    runSimulation([S, M1, Q, M2, M3, E1, E2, R, F1, F2, F3, F4], maxSimTime, trace="Yes")
    
    #runSim no trace
    #runSimulation([S, M1, Q, M2, M3, E1, E2, R, F1, F2, F3, F4], maxSimTime)
    
    #Metrics
    failure_ratio1 = (M1.totalFailureTime/maxSimTime)*100
    failure_ratio2 = (M2.totalFailureTime/maxSimTime)*100
    failure_ratio3 = (M3.totalFailureTime/maxSimTime)*100
    working_ratio = (R.totalWorkingTime/maxSimTime)*100
    
    #pass results
    if test:
        return {"parts_1": E1.numOfExits,
                "parts_2": E2.numOfExits,
                "failure_ratio1": failure_ratio1,
                "failure_ratio2": failure_ratio2,
                "failure_ratio3": failure_ratio3,
                "working_ratio": working_ratio
                }

    #print
    print("""
          Number of {}: {:5d} \n
          Number of {}: {:5d} \n
          {:8s} | failure : {:5.2f} % \n
          {:8s} | failure : {:5.2f} % \n
          {:8s} | failure : {:5.2f} % \n
          {:8s} | worktime: {:5.2f} % \n
          """.format(E1.objName, E1.numOfExits, E2.objName, E2.numOfExits, M1.objName, failure_ratio1, M2.objName, failure_ratio2, M3.objName, failure_ratio3, R.objName, working_ratio))
    
    #ExcelHandler is not working, outputs an empty xls file
    #ExcelHandler.outputTrace("trace_testing")
    
    #workaround through a static function from the class G in Globals, that outputs the tracing as a DataFrame
    excelPrinter("debugging/trace_testing")

if __name__=="__main__":
    main()