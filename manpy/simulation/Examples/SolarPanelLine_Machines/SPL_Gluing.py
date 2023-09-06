from manpy.simulation.imports import Machine, Feature, Failure
from manpy.simulation.core.StateController import ContinuosNormalDistribution, RandomDefectStateController

Gluing = Machine("M5", "Gluing", processingTime={"Fixed": {"mean": 10}})
# Gluing
glue_temperature = Feature("glue_temp", "Glue_Temperature", victim=Gluing, random_walk=True, start_value=190,
               distribution={"Feature": {"Normal": {"mean": 0, "stdev": 0.3}}}, start_time=1000, end_time=5000)

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
                    dependent={"Function": "0.9*X", "X": Amount},
                    distribution={"Feature": {"Normal": {"stdev": 0.0135}}})
