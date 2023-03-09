from manpy.simulation.imports import Machine, Source, Exit, Failure, Feature, Queue, RandomDefectStateController, ContinuosNormalDistribution
from manpy.simulation.Database import ManPyQuestDBDatabase
from manpy.simulation.Globals import runSimulation, getEntityData, G, ExcelPrinter
import time

start = time.time()

class Machine_control(Machine):
    def condition(self):
        activeEntity = self.Res.users[0]
        means = [1.6, 3500, 450, 180, 400, 50, 190, 400]
        stdevs = [0.2, 200, 50, 30, 50, 5, 10, 50]
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
        num_stds = 3
        activeEntity = self.Res.users[0]

        if any(activeEntity.labels):
            return True
        else:
            # TODO this needs to be done better!
            means = [1.6, None, None, 180, None, 190, None, None]
            stdevs = [0.2, None, None, 30, None, 10, None, None]
            influence = [False, False, False, False, False, False, False, False, False]
            for idx, feature in enumerate(activeEntity.features):
                if feature != None and influence[idx]:
                    min = means[idx] - num_stds * stdevs[idx]
                    max = means[idx] + num_stds * stdevs[idx]
                    if feature < min or feature > max:
                        return True

# todo this is still not ideal --> very few values are actually defect
class Widerstand_FailureConditional(Failure):

    def condition(self):
        r = Widerstand.get_feature_value()

        if r is not None and r > 515:
            print("Too much resistance!")
            return True
        else:
            return False

# TODO are the names in the csv correct?
# Objects
S = Source("S1", "Source", interArrivalTime={"Fixed": {"mean": 0.4}}, entity="manpy.Part", capacity=1)
Löten = Machine("M0", "Löten", processingTime={"Normal": {"mean": 0.8, "stdev": 0.075, "min": 0.425, "max": 1.175}})
Q = Queue("Q", "Queue")
Kleben = Machine_control2("M1", "Kleben", processingTime={"Fixed": {"mean": 0.8, "stdev": 0.075, "min": 0.425, "max": 1.175}}, control=True)
E1 = Exit("E1", "Exit1")
# ObjectInterruption
# Löten

WiderstandZuHoch = Widerstand_FailureConditional("Flr1", "RTooHigh", victim=Löten, conditional=True,
            distribution={"TTF": {"Fixed": {"mean": 0}}, "TTR": {"Fixed": {"mean": 5}}}, waitOnTie=True)

Spannung = Feature("Spannung", "Spannung", victim=Löten, entity=True,
               distribution_state_controller=ContinuosNormalDistribution(mean_change_per_step=0.0001, initial_mean=1.6,
                                                                         std=0.1, wear_per_step=1, break_point=1000,
                                                                         defect_mean=2.0, defect_std=0.1))
Strom = Feature("Strom", "Strom", victim=Löten, entity=True, dependent={"Function" : "1000*x + 1900", "x" : Spannung}, dependent_noise_std=30)
Widerstand = Feature("Widerstand", "Widerstand", victim=Löten, entity=True, dependent={"Function" : "(V/I)*1000000", "V" : Spannung, "I" : Strom}, dependent_noise_std=5, contribute=[WiderstandZuHoch])

Kraft = Feature("Kraft", "Kraft", victim=Löten,
               distribution={"Feature": {"Normal": {"mean": 180, "stdev": 30}}})
# random defect controller
s4_1 = ContinuosNormalDistribution(
                                    mean_change_per_step=0.0,
                                    initial_mean=400,
                                    std=50,
                                    )

s4_2 = ContinuosNormalDistribution(
                                    mean_change_per_step=0.0,
                                    initial_mean=300,
                                    std=50,
                                   )
s4_3 = ContinuosNormalDistribution(
                                    mean_change_per_step=0.0,
                                    initial_mean=500,
                                    std=50
                                   )
Einsinktiefe_StateController = RandomDefectStateController(failure_probability=0.02,
                                                           ok_controller=s4_1,
                                                           defect_controllers=[s4_2, s4_3])
Einsinktiefe = Feature("Einsinktiefe", "Einsinktiefe", victim=Löten,
               distribution_state_controller=Einsinktiefe_StateController)



#Kleben

# random walk
Temperatur = Feature("Temperatur", "Temperatur", victim=Kleben, random_walk=True, start_value=190,
               distribution={"Feature": {"Normal": {"mean": 0, "stdev": 0.3}}})

# random defect controller
s7_1 = ContinuosNormalDistribution(
                                           mean_change_per_step=0.0,
                                           initial_mean=400,
                                           std=50,
                                           )

s7_2 = ContinuosNormalDistribution(
                                    mean_change_per_step=0.0,
                                    initial_mean=500,
                                    std=50,
                                    )

s7_3 = ContinuosNormalDistribution(
                                    mean_change_per_step=0.0,
                                    initial_mean=300,
                                    std=50,
                                   )

Menge_StateController = RandomDefectStateController(failure_probability=0.02,
                                                    ok_controller=s7_1,
                                                    defect_controllers=[s7_2, s7_3])
Menge = Feature("Menge", "Menge", victim=Kleben, distribution_state_controller=Menge_StateController)

# evtl verwandt mit menge?
Durchflussgeschwindigkeit = Feature("Durchfluss", "Durchflussg.", victim=Kleben,
               dependent={"Function": "0.9*X", "X": Menge}, dependent_noise_std=10)

# TODO add feature prozesszeit: wie lange dauert es den kleber aufzubringen? -> verwandt mit menge

StecktFest = Failure("Flr0", "StecktFest", victim=Kleben, entity=True,
               distribution={"TTF": {"Fixed": {"mean": 0.5}}, "TTR": {"Normal": {"mean": 2,"stdev": 0.2, "min":0, "probability": 0.01}}})


# Routing
S.defineRouting([Löten])
Löten.defineRouting([S], [Q])
Q.defineRouting([Löten], [Kleben])
Kleben.defineRouting([Q], [E1])
E1.defineRouting([Kleben])


def main(test=0):
    # TODO why are there so many discards when sim time is large (e.g. 20 000)????
    maxSimTime = 10000
    objectList = [S, Löten, Q, Kleben, E1, Spannung, Strom, Widerstand, Kraft, Einsinktiefe, Durchflussgeschwindigkeit, Temperatur, Menge, StecktFest, WiderstandZuHoch]
    db = ManPyQuestDBDatabase()


    runSimulation(objectList, maxSimTime, db=None)

    # return Results for test
    if test:
        result = {}
        for o in objectList:
            if type(o) == Feature:
                result[o.id] = o.featureHistory
        result["Discards"] = Kleben.discards
        result["Exits"] = E1.numOfExits
        result["Entities"] = G.EntityList

        return result

    # df = G.get_simulation_results_dataframe()
    # ExcelPrinter(df, "EnahncedExampleLine")
    df = getEntityData([E1], discards=[Kleben])
    df.to_csv("EnhancedExampleLine.csv", index=False, encoding="utf8")

    num_discards = len(Kleben.discards)
    total_produced = E1.numOfExits + num_discards

    print("""
            Ausschuss:          {}
            Ausschuss (%):      {:.2f}
            Produziert:         {}
            Blockiert für:      {:.2f}
            Simulationszeit:    {}
            Laufzeit:           {:.2f}
            """.format(len(Kleben.discards), 100*(num_discards / total_produced),  E1.numOfExits, Kleben.totalBlockageTime,
                       maxSimTime, time.time() - start))

if __name__ == "__main__":
    main()
