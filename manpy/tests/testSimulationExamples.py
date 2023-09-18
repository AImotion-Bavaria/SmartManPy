# ===========================================================================
# Copyright 2014 Nexedi SA
#
# This file is part of DREAM.
#
# DREAM is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# DREAM is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with DREAM.  If not, see <http://www.gnu.org/licenses/>.
# ===========================================================================

from unittest import TestCase


class SimulationExamples(TestCase):
    """
    Test topology files. The simulation is launched with files Topology01.json,
    Topology02.json, etc, and every time we look if the result is like we expect.

    If the result format or content change, it is required to dump again all
    result files. But this is easy to do :

    dump=1 python setup.py test

    This will regenerate all dump files in manpy/tests/dump/.
    Then you can check carefully if all outputs are correct. You could use git
    diff to check what is different. Once you are sure that your new dumps are
    correct, you could commit, your new dumps will be used as new reference.
    """

    def tearDown(self):
        from manpy.simulation.core.Globals import G

        G.objectList = []
        G.EntityList = []
        G.FeatureList = []

        del G

    def testTwoServers(self):
        from manpy.simulation.Examples.Old.TwoServers import main

        result = main(test=1)
        self.assertAlmostEquals(result["parts"], 750, delta=25)
        self.assertAlmostEquals(78.0, result["blockage_ratio"], delta=1.0)
        self.assertAlmostEquals(27.0, result["working_ratio"], delta=1.0)

    def testAssemblyLine(self):
        from manpy.simulation.Examples.Old.AssemblyLine import main

        result = main(test=1)
        self.assertEqual(result["frames"], 664)
        self.assertTrue(92.36 < result["working_ratio"] < 93.37)

    def testSingleServer(self):
        from manpy.simulation.Examples.Old.SingleServer import main

        result = main(test=1)
        self.assertEqual(result["parts"], 2880)
        self.assertTrue(49.99 < result["working_ratio"] < 50.01)

    def testClearBatchLines(self):
        from manpy.simulation.Examples.Old.ClearBatchLines import main

        result = main(test=1)
        self.assertEqual(result["batches"], 89)
        self.assertTrue(0.069 < result["waiting_ratio_M1"] < 0.07, "\nwaiting ratio: {}".format(result["waiting_ratio_M1"]))
        self.assertTrue(0.104 < result["waiting_ratio_M2"] < 0.105, "\nwaiting ratio: {}".format(result["waiting_ratio_M2"]))
        self.assertTrue(93.81 < result["waiting_ratio_M3"] < 93.82, "\nwaiting ratio: {}".format(result["waiting_ratio_M3"]))

    def testDecompositionOfBatches(self):
        from manpy.simulation.Examples.Old.DecompositionOfBatches import main

        result = main(test=1)
        self.assertEqual(result["subbatches"], 2302)
        self.assertTrue(79.96 < result["working_ratio"] < 79.97)
        self.assertEqual(result["blockage_ratio"], 0.0)
        self.assertTrue(20.03 < result["waiting_ratio"] < 20.04)

    def testSerialBatchProcessing(self):
        from manpy.simulation.Examples.Old.SerialBatchProcessing import main

        result = main(test=1)
        self.assertEqual(result["batches"], 359)
        self.assertTrue(0.104 < result["waiting_ratio_M1"] < 0.105)
        self.assertTrue(0.104 < result["waiting_ratio_M2"] < 0.105)
        self.assertTrue(75.06 < result["waiting_ratio_M3"] < 75.07)

    def testJobShop1(self):
        from manpy.simulation.Examples.Old.JobShop1 import main

        result = main(test=1)
        expectedResult = [
            ["Queue1", 0],
            ["Machine1", 0],
            ["Queue3", 1.0],
            ["Machine3", 1.0],
            ["Queue2", 4.0],
            ["Machine2", 4.0],
            ["Exit", 6.0],
        ]
        self.assertEqual(result, expectedResult)

    def testJobShop2EDD(self):
        from manpy.simulation.Examples.Old.JobShop2EDD import main

        result = main(test=1)
        expectedResult = [
            ["Queue1", 0],
            ["Machine1", 2.0],
            ["Queue3", 3.0],
            ["Machine3", 3.0],
            ["Queue2", 6.0],
            ["Machine2", 6.0],
            ["Exit", 8.0],
            ["Queue1", 0],
            ["Machine1", 0],
            ["Queue2", 2.0],
            ["Machine2", 2.0],
            ["Queue3", 6.0],
            ["Machine3", 6.0],
            ["Exit", 12.0],
            ["Queue1", 0],
            ["Machine1", 3.0],
            ["Queue3", 13.0],
            ["Machine3", 13.0],
            ["Exit", 16.0],
        ]
        self.assertEqual(result, expectedResult)

    def testJobShop2MC(self):
        from manpy.simulation.Examples.Old.JobShop2MC import main

        result = main(test=1)
        expectedResult = [
            ["Queue1", 0],
            ["Machine1", 12.0],
            ["Queue3", 13.0],
            ["Machine3", 13.0],
            ["Queue2", 16.0],
            ["Machine2", 16.0],
            ["Exit", 18.0],
            ["Queue1", 0],
            ["Machine1", 10.0],
            ["Queue2", 12.0],
            ["Machine2", 12.0],
            ["Queue3", 16.0],
            ["Machine3", 16.0],
            ["Exit", 22.0],
            ["Queue1", 0],
            ["Machine1", 0],
            ["Queue3", 10.0],
            ["Machine3", 10.0],
            ["Exit", 13.0],
        ]
        self.assertEqual(result, expectedResult)

    def testJobShop2Priority(self):
        from manpy.simulation.Examples.Old.JobShop2Priority import main

        result = main(test=1)
        expectedResult = [
            ["Queue1", 0],
            ["Machine1", 10.0],
            ["Queue3", 11.0],
            ["Machine3", 13.0],
            ["Queue2", 16.0],
            ["Machine2", 17.0],
            ["Exit", 19.0],
            ["Queue1", 0],
            ["Machine1", 11.0],
            ["Queue2", 13.0],
            ["Machine2", 13.0],
            ["Queue3", 17.0],
            ["Machine3", 17.0],
            ["Exit", 23.0],
            ["Queue1", 0],
            ["Machine1", 0],
            ["Queue3", 10.0],
            ["Machine3", 10.0],
            ["Exit", 13.0],
        ]
        self.assertEqual(result, expectedResult)

    def testJobShop2RPC(self):
        from manpy.simulation.Examples.Old.JobShop2RPC import main

        result = main(test=1)
        expectedResult = [
            ["Queue1", 0],
            ["Machine1", 12.0],
            ["Queue3", 13.0],
            ["Machine3", 13.0],
            ["Queue2", 16.0],
            ["Machine2", 16.0],
            ["Exit", 18.0],
            ["Queue1", 0],
            ["Machine1", 10.0],
            ["Queue2", 12.0],
            ["Machine2", 12.0],
            ["Queue3", 16.0],
            ["Machine3", 16.0],
            ["Exit", 22.0],
            ["Queue1", 0],
            ["Machine1", 0],
            ["Queue3", 10.0],
            ["Machine3", 10.0],
            ["Exit", 13.0],
        ]
        self.assertEqual(result, expectedResult)

    def testParallelServers1(self):
        from manpy.simulation.Examples.Old.ParallelServers1 import main

        result = main(test=1)
        self.assertEqual(result["parts"], 2880)
        self.assertTrue(23.09 < result["working_ratio_M1"] < 23.1)
        self.assertTrue(26.9 < result["working_ratio_M2"] < 26.91)

    def testParallelServers2(self):
        from manpy.simulation.Examples.Old.ParallelServers3 import main

        result = main(test=1)
        self.assertEqual(result["parts"], 2880)
        self.assertTrue(46.18 < result["working_ratio_M1"] < 46.19)
        self.assertTrue(3.81 < result["working_ratio_M2"] < 3.82)

    # NOTE: testParallelServers4 is extension of testParallelServers4 so this test really tests if they both run
    def testParallelServers4(self):
        from manpy.simulation.Examples.Old.ParallelServers4 import main

        result = main(test=1)
        self.assertEqual(result["parts"], 2880)
        self.assertTrue(46.18 < result["working_ratio_M1"] < 46.19)
        self.assertTrue(3.81 < result["working_ratio_M2"] < 3.82)
        self.assertEqual(result["NumM1"], 2660)
        self.assertEqual(result["NumM2"], 220)

    def testServerWithShift1(self):
        from manpy.simulation.Examples.Old.ServerWithShift1 import main

        result = main(test=1)
        self.assertEqual(result["parts"], 3)
        self.assertTrue(49.99 < result["working_ratio"] < 50.01)

    def testServerWithShift2(self):
        from manpy.simulation.Examples.Old.ServerWithShift2 import main

        result = main(test=1)
        self.assertEqual(result["parts"], 16)
        self.assertTrue(49.99 < result["working_ratio"] < 50.01)

    def testServerWithShift3(self):
        from manpy.simulation.Examples.Old.ServerWithShift3 import main

        result = main(test=1)
        self.assertEqual(result["parts"], 4)
        self.assertTrue(59.99 < result["working_ratio"] < 60.01)

    def testServerWithShift4(self):
        from manpy.simulation.Examples.Old.ServerWithShift4 import main

        result = main(test=1)
        self.assertEqual(result["parts"], 2)
        self.assertTrue(29.99 < result["working_ratio"] < 30.01)

    def testSettingWip1(self):
        from manpy.simulation.Examples.Old.SettingWip1 import main

        result = main(test=1)
        self.assertEqual(result["parts"], 1)
        self.assertEqual(result["simulationTime"], 0.25)
        self.assertEqual(result["working_ratio"], 100)

    def testSettingWip2(self):
        from manpy.simulation.Examples.Old.SettingWip2 import main

        result = main(test=1)
        self.assertEqual(result["parts"], 2)
        self.assertEqual(result["simulationTime"], 0.50)
        self.assertEqual(result["working_ratio"], 100)

    def testSettingWip3(self):
        from manpy.simulation.Examples.Old.SettingWip3 import main

        result = main(test=1)
        self.assertEqual(result["parts"], 2)
        self.assertEqual(result["simulationTime"], 0.35)
        self.assertEqual(result["working_ratio"], 100)

    def testBalancingABuffer(self):
        from manpy.simulation.Examples.Old.BalancingABuffer import main

        result = main(test=1)
        self.assertEqual(result["parts"], 13)
        self.assertEqual(result["working_ratio"], 80)

    def testChangingPredecessors(self):
        from manpy.simulation.Examples.Old.ChangingPredecessors import main

        result = main(test=1)
        self.assertEqual(result["parts"], 10)
        self.assertEqual(result["simulationTime"], 36.0)
        self.assertTrue(83.32 < result["working_ratio"] < 83.34)

    def testSettingWip3(self):
        from manpy.simulation.Examples.Old.SettingWip3 import main

        result = main(test=1)
        self.assertEqual(result["parts"], 2)
        self.assertEqual(result["simulationTime"], 0.35)
        self.assertEqual(result["working_ratio"], 100)

    def testNonStarvingLine(self):
        from manpy.simulation.Examples.Old.NonStarvingLine import main

        result = main(test=1)
        self.assertEqual(result["parts"], 9)
        self.assertEqual(result["working_ratio"], 100)

    def testNonStarvingLineBatches(self):
        from manpy.simulation.Examples.Old.NonStarvingLineBatches import main

        result = main(test=1)
        self.assertEqual(result["batches"], 4)
        self.assertEqual(result["working_ratio"], 100)

    def testCompoundMachine(self):
        from manpy.simulation.Examples.Old.CompoundMachine import main

        result = main(test=1)
        self.assertEqual(result, 6.5, "\nresult: {}".format(result))

    def testJobShop2ScenarioAnalysis(self):
        from manpy.simulation.Examples.Old.JobShop2ScenarioAnalysis import main

        result = main(test=1)
        self.assertEqual(result, 2)

    def testBufferAllocation(self):
        from manpy.simulation.Examples.Old.BufferAllocation import main

        result = main(test=1)
        self.assertTrue(50 < result["parts"] < 1000, "\nParts: {}".format(result["parts"]))

    def testExampleLine(self):
        from manpy.simulation.Examples.ExampleLine import main

        result = main(test=1)

        self.assertGreaterEqual(len(result["Entities"]), len(result["Discards"]) + result["Exits"],
                                "\nNumber of Entities should be higher than Discards+Exits\nEntities: {}\nDiscards: {}\nExits: {}".format(len(result["Entities"]), len(result["Discards"]), result["Exits"]))
        for key in result:
            if key.__contains__("Ftr"):
                self.assertGreaterEqual(len(result[key]), len(result["Discards"]) + result["Exits"],
                                        "\nNumber of Features should be higher than Discards+Exits\nFeatures: {}\nDiscards: {}\nExits: {}".format(len(result[key]), len(result["Discards"]), result["Exits"]))

        self.assertGreaterEqual(result["Exits"] + len(result["Discards"]), 0,
                                "Should have at least one finished Entity. Entity Failure could be the Problem.")

    def testRandomWalk(self):
        from manpy.simulation.Examples.Random_Walk import main

        result = main(test=1)

        for idx in range(1, len(result["Ftr1"])):
            self.assertGreaterEqual(result["Ftr1"][idx] - result["Ftr1"][idx - 1], -10,
                                    "\nRandomWalk should be higher than -10\nIt instead is: ".format(result["Ftr1"][idx]))
            self.assertLessEqual(result["Ftr1"][idx] - result["Ftr1"][idx - 1], 10,
                                    "\nRandomWalk should be lower than 10\nIt instead is: ".format(result["Ftr1"][idx]))
    def testDependency(self):
        from manpy.simulation.Examples.Dependency import main

        result = main(test=1)

        for idx in range(len(result["Spannung"])):
            self.assertEqual(1000*result["Spannung"][idx] + 1900, result["Strom"][idx],
                             "\nStrom should be: {}\nIt instead is: {}".format(1000*result["Spannung"][idx] + 1900, result["Strom"][idx], idx,result["Spannung"][idx]))
            self.assertEqual((result["Spannung"][idx]/result["Strom"][idx]*1000000), result["Widerstand"][idx],
                             "\nWiderstand should be: {}\nIt instead is: {}".format((result["Spannung"][idx]/result["Strom"][idx]*1000000), result["Widerstand"][idx]))

    def testMerging(self):
        from manpy.simulation.Examples.Merging import main

        result = main(test=1)

        self.assertEqual(result["M1"]//20, result["E1"],
                         "\nProduction of M1 does not match the output of the Assembly")

    def testExampleTS(self):
        from manpy.simulation.Examples.ExampleTS import main

        result = main(test=1)

        for t in range(3):
            self.assertEqual(len(result.timeseries[t]), 20,
                             "\nDataPoints: {}".format(len(result.timeseries[t])))
            self.assertEqual(format(result.timeseries_times[t][2] - result.timeseries_times[t][1], ".2f"), format(result.timeseries_times[t][1] - result.timeseries_times[t][0], ".2f"))
