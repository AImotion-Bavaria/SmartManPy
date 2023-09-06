from manpy.simulation.imports import Machine, Feature, Failure
from manpy.simulation.core.StateController import ContinuosNormalDistribution


def resistance_failure_condition(self):
    r = Tab_Str_Resistance.get_feature_value()

    if r is not None and r > 535:
        print("Too much resistance!")
        return True
    else:
        return False


Tabber_Stringer = Machine("M2", "Tabber_Stringer", processingTime={"Fixed": {"mean": 15}})
# Welding (Tabber/Stringer)
# similar to soldering from example line
Tab_Str_Resistance_Too_High = Failure("Flr1", "RTooHigh", victim=Tabber_Stringer, conditional=resistance_failure_condition,
                                      distribution={"TTF": {"Fixed": {"mean": 0}}, "TTR": {"Fixed": {"mean": 5}}}, waitOnTie=True)

Tab_Str_Voltage = Feature("Tab_Str_Voltage", "Tab_Str_Voltage", victim=Tabber_Stringer,
                          distribution_state_controller=ContinuosNormalDistribution(mean_change_per_step=0.0001, initial_mean=1.6,
                                                                         std=0.1, wear_per_step=1, break_point=1000,
                                                                         defect_mean=2.0, defect_std=0.1))
Tab_Str_Power = Feature("Tab_Str_Power", "Tab_Str_Power", victim=Tabber_Stringer, dependent={"Function" : "1000*x + 1900", "x" : Tab_Str_Voltage}, distribution={"Feature": {"Normal": {"stdev": 30}}})

Tab_Str_Resistance = Feature("Tab_Str_Resistance", "Tab_Str_Resistance", victim=Tabber_Stringer, dependent={"Function" : "(V/I)*1000000", "V" : Tab_Str_Voltage, "I" : Tab_Str_Power}, distribution={"Feature": {"Normal": {"stdev": 5}}}, contribute=[Tab_Str_Resistance_Too_High])

Tab_Str_Force = Feature("Tab_Str_Force", "Tab_Str_Force", victim=Tabber_Stringer,
                        distribution={"Feature": {"Normal": {"mean": 180, "stdev": 30}}})
