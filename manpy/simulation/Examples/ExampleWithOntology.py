import owlready2 as owl
import os
from manpy.simulation.imports import Machine, Source, Exit, Feature
from manpy.simulation.core.Globals import runSimulation, G

# Change path to wherever file is
os.chdir(os.path.dirname(__file__))

# Objects
S1 = Source("S1",
            "Source1",
            interArrivalTime={"Fixed": {"mean": 0.4}},
            entity="manpy.Part",
            capacity=1)
M1 = Machine("M1",
             "Machine1",
             processingTime={"Normal": {"mean": 5,
                                       "stdev": 0.5,
                                       "min": 3,
                                       "max": 7}},
             control=False)
E1 = Exit("E1", "Exit")

# ObjectInterruption
# Average temperature of subcomponent C1 of machine M1
Ftr2 = Feature("SensorTM2",
               "SensorTM2",
               start_value=22,
               random_walk=True,
               entity=True,
               victim=M1,
               distribution={"Time": {"Fixed": {"mean": 1}},
                             "Feature": {"Normal": {"mean": 0, "stdev": 2}}})
# Average temperature of whole machine M
# Ftr1(t) = 0.5 * (y(t) + Ftr2(t-1))
Ftr1 = Feature("SensorTM1",
               "SensorTM1",
               entity=True,
               start_value=22,
               victim=M1,
               dependent={"Function": "0.5 * (np.random.normal(22,2) + Ftr2_history[-2])",
                          "Ftr2": Ftr2},
               distribution={"Time": {"Fixed": {"mean": 1}}})

# For using lag greater than 1 do:
# (a[-i] if i in range(len(a)+1) else a[0])

# Routing
S1.defineRouting([M1])
M1.defineRouting([S1], [E1])
E1.defineRouting([M1])

# Object list
objectList = [S1, M1, Ftr1, Ftr2, E1]

def run(objectList, maxSimTime):

    runSimulation(objectList, maxSimTime, trace=True)

    # df = getEntityData()
    df = G.get_simulation_results_dataframe().drop(columns=["entity_name", "station_name"])

    df.to_csv('ExampleWithOntologyData.csv')

    return df

def reason(df):

    # Add current path to owlready
    # Else when reloading owlready tries to download the ontology from the internet
    owl.onto_path.append('')

    # Load ontology
    # my_file = open("example_manpy.owl")
    onto = owl.get_ontology("example_manpy_empty.owl").load(reload=True) # .load(fielobj=my_file)

    # Create and classify individuals
    ind_list = []
    i_list = []
    for i in df.index:
        if df.loc[i, 'station_id'] in ['SensorTM1', 'SensorTM2']:
            i_list.append(i)
            ind_list.append('_'.join(df.loc[i, ['entity_id', 'station_id']].values))
            ind_value = float(df.loc[i, 'message'])
            ind_time = round(float(df.loc[i, 'simulation_time']),2)
            # Create instance/individual of class/type Observation with data properties
            tmp_ind = onto.Observation(ind_list[-1], hasValue=ind_value, hasTimeStamp=ind_time)
            # Connect individual to sensor
            tmp_ind.madeBySensor = [eval('.'.join(['onto', df.loc[i, 'station_id']]))]

    # Infer classification
    # Use pellet reasoner, because Hermit does not understand SWRLB functions.
    owl.sync_reasoner_pellet(infer_property_values=True)

    # Save ontology
    onto.save(file = "example_manpy_populated.owl", format = "rdfxml")

def main():
    reason(run(objectList, maxSimTime=100))

if __name__=='__main__':
    main()
