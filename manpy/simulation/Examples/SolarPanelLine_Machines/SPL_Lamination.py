from manpy.simulation.imports import Machine, Feature, Timeseries


Lamination = Machine("m9", "M_Lamination", processingTime={"Fixed": {"mean": 10}})

# Lamination
# Two timeseries: pressure and temperature, interpolation based on features
# Lamination_Pressure = Feature("Lamination_Pressure", "Lamination_Pressure", victim=Lamination, distribution={"Feature": {"Normal": {"mean": 50, "stdev": 2}}})
# Lamination_Temperature = Feature("Lamination_Temperature", "Lamination_Temperature", victim=Lamination, distribution={"Feature": {"Normal": {"mean": 400, "stdev": 10}}})

# upper interval bound is process time -> how long does the process take, e.g. 200 seconds. Not necessarily the
# same timne unit like in manpy
L_a = Feature("Ftr_La", "L1", victim=Lamination,
                        distribution={"Feature": {"Normal": {"mean": 5, "stdev": 1}}})
L_b = Feature("Ftr_Lb", "L2", victim=Lamination,
              distribution={"Feature": {"Normal": {"mean": 60, "stdev": 1}}})
L_c = Feature("Ftr_Lc", "L3", victim=Lamination,
              distribution={"Feature": {"Normal": {"mean": 80, "stdev": 1}}})
L_d = Feature("Ftr_Ld", "L4", victim=Lamination,
              distribution={"Feature": {"Normal": {"mean": 85, "stdev": 1}}})
L_e = Feature("Ftr_Le", "L5", victim=Lamination,
              distribution={"Feature": {"Normal": {"mean": 40, "stdev": 1}}})
L_f = Feature("Ftr_Lf", "L6", victim=Lamination,
              distribution={"Feature": {"Normal": {"mean": 25, "stdev": 1}}})
L_g = Feature("Ftr_Lg", "L7", victim=Lamination,
              distribution={"Feature": {"Normal": {"mean": 15, "stdev": 1}}})

# TODO better names for intermediate variables
Lamination_Temperature_Curve = Timeseries("Ts_Lamination_Temp", "Ts_Lamination_Temp", victim=Lamination,
                                          no_negative=True, distribution={"Function": {(0, 20): "x+La",
                                                                                    (20, 55): [[20, 30, 40, 50, 55], ["20+La", "Lb", "L_c", "L_c+3", "Ld"]],
                                                                                    (55, 80): "Ld",
                                                                                    (80, 120): [[80, 90, 100, 110, 120], ["Ld", "Le", "Lf", "Lg", "Lg"]]},
                                                                       "La": L_a, "Lb": L_b, "L_c": L_c, "Ld": L_d, "Le": L_e, "Lf": L_f, "Lg": L_g,
                                                                       "DataPoints": 120})

Lamination_Peak_Pressure = Feature("Ftr_Press", "Pr1", victim=Lamination,
              distribution={"Feature": {"Normal": {"mean": 80, "stdev": 1}}})
Lamination_Pressure_Curve = Timeseries("Ts_Lamination_Pressure", "Ts_Lamination_Pressure", victim=Lamination,
                                          no_negative=True, distribution={"Function": {(0, 20): "0.0",
                                                                                    (20, 40): [[20, 25, 30, 35, 40], ["0.0", "0.25*Mp", "0.5*Mp", "0.75*Mp", "Mp"]],
                                                                                    (40, 80): "Mp",
                                                                                    (80, 100): [[80, 85, 90, 95, 100], ["Mp", "0.75*Mp", "0.5*Mp", "0.25*Mp", "0.0"]],
                                                                                    (100, 120): "0.0"},
                                                                       "Mp": Lamination_Peak_Pressure,
                                                                       "DataPoints": 120})
