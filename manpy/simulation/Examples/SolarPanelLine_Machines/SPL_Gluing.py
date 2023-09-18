from manpy.simulation.imports import Machine, Feature
from manpy.simulation.core.StateController import ContinuosNormalDistribution, RandomDefectStateController
from manpy.simulation.core.ProductionLineModule import SequentialProductionLineModule

Gluing = Machine("M5", "Gluing", processingTime={"Fixed": {"mean": 10}})
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
Amount = Feature("Amount", "Amount", victim=Gluing, distribution_state_controller=Amount_StateController)

flow_rate = Feature("Flow_Rate", "Flow_Rate", victim=Gluing,
                    dependent={"Function": "0.9*Amount+0.001", "Amount": Amount},
                    distribution={"Feature": {"Normal": {"stdev": 0.0135}}})

routing = [
    [Gluing]
]

features = [Amount, glue_temperature, flow_rate]

gluing_module = SequentialProductionLineModule(routing, features, "Gluing_Module")
