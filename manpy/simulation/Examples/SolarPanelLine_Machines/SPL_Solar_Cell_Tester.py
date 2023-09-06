from manpy.simulation.imports import Machine, Feature, Timeseries


def condition(self):
    activeEntity = self.Res.users[0]
    features = [3.5, 0.62, None, None, 2.3]
    for idx, feature in enumerate(features):
        if feature != None:
            if activeEntity.features[idx] < 0.9*feature or activeEntity.features[idx] > 1.1*feature:
                return True
    return False


Solar_Cell_Tester = Machine("M0", "Solar_Cell_Tester", processingTime={"Fixed": {"mean": 3}}, control=condition)
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
