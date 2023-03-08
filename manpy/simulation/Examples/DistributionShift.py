from manpy.simulation.imports import Machine, Source, Exit, Failure, Feature, Queue, SimpleStateController, Repairman
from manpy.simulation.Globals import runSimulation, getEntityData, G, ExcelPrinter

import time

start = time.time()

class Machine_control(Machine):
    def condition(self):
        activeEntity = self.Res.users[0]
        means = [1.6, 3500, 450, 180, 400, 50, 190, 400, 1]
        stdevs = [0.2, 200, 50, 30, 50, 5, 10, 50, 2]
        for idx, feature in enumerate(activeEntity.features):
            if feature != None:
                min = means[idx] - 2 * stdevs[idx]
                max = means[idx] + 2 * stdevs[idx]
                if feature < min or feature > max:
                    return True

class Machine_control2(Machine):
    """
    Another approach for quality control: label is determined by features. if >= 1 feature has label "defect", the
    entity does not pass the quality inspection
    """
    def condition(self):
        activeEntity = self.Res.users[0]
        if any(activeEntity.labels):
            return True


class Failure_conditional(Failure):
    def condition(self):
        value_1 = Test.featureValue
        if value_1 is not None and value_1 > 10:
            print("Failure!")
            Test.start_time = G.env.now
            return True
        else:
            return False


# Objects
R = Repairman("R1", "Sascha")
S = Source("S1", "Source", interArrivalTime={"Fixed": {"mean": 0.4}}, entity="manpy.Part", capacity=100)
Löten = Machine("M0", "Löten", processingTime={"Normal": {"mean": 0.8, "stdev": 0.075, "min": 0.425, "max": 1.175}})
Q = Queue("Q", "Queue")
Kleben = Machine_control("M1", "Kleben",
                         processingTime={"Fixed": {"mean": 0.8, "stdev": 0.075, "min": 0.425, "max": 1.175}},
                         # processingTime={"Fixed": {"mean": 0.8}},
                         control=True)

# Kleben = Machine("M1", "Kleben", processingTime={"Normal": {"mean": 0.8, "stdev": 0.075, "min": 0.425, "max": 1.175}})
E1 = Exit("E1", "Exit1")

##### CONFIG #####
# TODO Feature Time seems to have huge impact on the event system
# TODO Setting Feature Cycle to values  =!= 1 triggers postInterruption ??????? wtf
feature_cycle_time = 1.0
##################

# ObjectInterruption
# Löten
Spannung = Feature("Ftr0", "Feature1", victim=Löten,
               distribution={"Feature": {"Normal": {"mean": 1.6, "stdev": 0.2}}})
Strom = Feature("Ftr1", "Feature2", victim=Löten,
               distribution={"Feature": {"Normal": {"mean": 3500, "stdev": 200}}})
Widerstand = Feature("Ftr2", "Feature3", victim=Löten,
               distribution={"Feature": {"Normal": {"mean": 450, "stdev": 50}}})
Kraft = Feature("Ftr3", "Feature4", victim=Löten,
               distribution={"Feature": {"Normal": {"mean": 180, "stdev": 30}}})
Einsinktiefe = Feature("Ftr4", "Feature5", victim=Löten,
               distribution={"Feature": {"Normal": {"mean": 400, "stdev": 50}}})

#Kleben
Durchflussgeschwindigkeit = Feature("Ftr5", "Feature6", victim=Kleben,
               distribution={"Feature": {"Normal": {"mean": 50, "stdev": 5}}})
Temperatur = Feature("Ftr6", "Feature7", victim=Kleben,
               distribution={"Feature": {"Normal": {"mean": 190, "stdev": 10}}})
Menge = Feature("Ftr7", "Feature8", victim=Kleben,
               distribution={"Feature": {"Normal": {"mean": 400, "stdev": 50}}})

StecktFest = Failure_conditional("Flr0", "Failure0", victim=Kleben, conditional=True,
            distribution={"TTF": {"Fixed": {"mean": 0}}, "TTR": {"Fixed": {"mean": 20}}}, waitOnTie=True)

# StecktFest = Failure("Flr0", "Failure0", victim=Kleben, entity=True, deteriorationType="working",
#                distribution={"TTF": {"Fixed": {"mean": 0}},
#                              "TTR": {"Normal": {"mean": 2,"stdev": 0.2, "min":0, "probability": 0.05}}})

dists = [{"Feature": {"Normal": {"mean": 1, "stdev":2}}},
         {"Feature": {"Normal": {"mean": 100, "stdev":2}}}]
labels = [False, True]
boundaries = {(0, 25): 0, (25, None): 1}
distribution_controller = SimpleStateController(states=dists, boundaries=boundaries, wear_per_step=1.0,
                                                labels=labels, reset_amount=None)

Test = Feature("Ftr8", "Feature9", victim=Kleben,
               distribution_state_controller=distribution_controller,
               deteriorationType="constant", contribute=[StecktFest], reset_distributions=True,
               )



# Routing
S.defineRouting([Löten])
Löten.defineRouting([S], [Q])
Q.defineRouting([Löten], [Kleben])
Kleben.defineRouting([Q], [E1])
E1.defineRouting([Kleben])


def main():
    maxSimTime = 150
    objectList = [S, R, Löten, Q, Kleben, E1, StecktFest, Spannung, Strom, Widerstand, Kraft, Einsinktiefe, Durchflussgeschwindigkeit, Temperatur, Menge, Test]

    runSimulation(objectList, maxSimTime)

    df = getEntityData([E1], [Kleben], time=True)[["M1_Ftr8_v", "Result"]]
    df.to_csv("DistributionShift.csv", index=False, encoding="utf8")

    print("""
            Ausschuss:          {}
            Produziert:         {}
            Blockiert für:      {:.2f}
            Simulationszeit:    {}
            Laufzeit:           {:.2f}
            """.format(len(Kleben.discards), E1.numOfExits, Kleben.totalBlockageTime, maxSimTime, time.time() - start))

if __name__ == "__main__":
    main()
