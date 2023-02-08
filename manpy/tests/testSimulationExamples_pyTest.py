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

import pytest



class TestClass:

    # @pytest.fixture
    # def cleanup(self):
    #     yield

    def test_TwoServers(self, cleanup):
        from manpy.simulation.Examples.Old.TwoServers import main

        result = main(test=1)
        assert result["parts"] == 732
        assert 78.17 < result["blockage_ratio"] < 78.18
        assert 26.73 < result["working_ratio"] < 27.74

    def test_AssemblyLine(self, cleanup):
        from manpy.simulation.Examples.Old.AssemblyLine import main

        result = main(test=1)
        assert result["frames"] == 664
        assert 92.36 < result["working_ratio"] < 93.37

    def test_SingleServer(self, cleanup):
        from manpy.simulation.Examples.Old.SingleServer import main

        result = main(test=1)
        assert result["parts"] == 2880
        assert 49.99 < result["working_ratio"] < 50.01

    def test_ClearBatchLines(self, cleanup):
        from manpy.simulation.Examples.Old.ClearBatchLines import main

        result = main(test=1)
        assert result["batches"] == 89
        assert 0.069 < result["waiting_ratio_M1"] < 0.07
        assert 0.104 < result["waiting_ratio_M2"] < 0.105
        assert 93.81 < result["waiting_ratio_M3"] < 93.82

    def test_DecompositionOfBatches(self, cleanup):
        from manpy.simulation.Examples.Old.DecompositionOfBatches import main

        result = main(test=1)
        assert result["subbatches"] == 2302
        assert 79.96 < result["working_ratio"] < 79.97
        assert result["blockage_ratio"] == 0.0
        assert 20.03 < result["waiting_ratio"] < 20.04

    def test_SerialBatchProcessing(self, cleanup):
        from manpy.simulation.Examples.Old.SerialBatchProcessing import main

        result = main(test=1)
        assert result["batches"] == 359
        assert 0.104 < result["waiting_ratio_M1"] < 0.105
        assert 0.104 < result["waiting_ratio_M2"] < 0.105
        assert 75.06 < result["waiting_ratio_M3"] < 75.07

    def test_JobShop1(self, cleanup):
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
        assert result == expectedResult

    def test_JobShop2EDD(self, cleanup):
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
        assert result == expectedResult

    def test_JobShop2MC(self, cleanup):
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
        assert result == expectedResult

    def test_JobShop2Priority(self, cleanup):
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
        assert result == expectedResult

    def test_JobShop2RPC(self, cleanup):
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
        assert result == expectedResult

    def test_ParallelServers1(self, cleanup):
        from manpy.simulation.Examples.Old.ParallelServers1 import main

        result = main(test=1)
        assert result["parts"] == 2880
        assert 23.09 < result["working_ratio_M1"] < 23.1
        assert 26.9 < result["working_ratio_M2"] < 26.91

    def test_ParallelServers2(self, cleanup):
        from manpy.simulation.Examples.Old.ParallelServers3 import main

        result = main(test=1)
        assert result["parts"] == 2880
        assert 46.18 < result["working_ratio_M1"] < 46.19
        assert 3.81 < result["working_ratio_M2"] < 3.82

    # NOTE: testParallelServers4 is extension of testParallelServers4 so this test really tests if they both run
    def test_ParallelServers4(self, cleanup):
        from manpy.simulation.Examples.Old.ParallelServers4 import main

        result = main(test=1)
        assert result["parts"] == 2880
        assert 46.18 < result["working_ratio_M1"] < 46.19
        assert 3.81 < result["working_ratio_M2"] < 3.82
        assert result["NumM1"] == 2660
        assert result["NumM2"] == 220

    def test_ServerWithShift1(self, cleanup):
        from manpy.simulation.Examples.Old.ServerWithShift1 import main

        result = main(test=1)
        assert result["parts"] == 3
        assert 49.99 < result["working_ratio"] < 50.01

    def test_ServerWithShift2(self, cleanup):
        from manpy.simulation.Examples.Old.ServerWithShift2 import main

        result = main(test=1)
        assert result["parts"] == 16
        assert 49.99 < result["working_ratio"] < 50.01

    def test_ServerWithShift3(self, cleanup):
        from manpy.simulation.Examples.Old.ServerWithShift3 import main

        result = main(test=1)
        assert result["parts"] == 4
        assert 59.99 < result["working_ratio"] < 60.01

    def test_ServerWithShift4(self, cleanup):
        from manpy.simulation.Examples.Old.ServerWithShift4 import main

        result = main(test=1)
        assert result["parts"] == 2
        assert 29.99 < result["working_ratio"] < 30.01

    def test_SettingWip1(self, cleanup):
        from manpy.simulation.Examples.Old.SettingWip1 import main

        result = main(test=1)
        assert result["parts"] == 1
        assert result["simulationTime"] == 0.25
        assert result["working_ratio"] == 100

    def test_SettingWip2(self, cleanup):
        from manpy.simulation.Examples.Old.SettingWip2 import main

        result = main(test=1)
        assert result["parts"] == 2
        assert result["simulationTime"] == 0.50
        assert result["working_ratio"] == 100

    def test_SettingWip3(self, cleanup):
        from manpy.simulation.Examples.Old.SettingWip3 import main

        result = main(test=1)
        assert result["parts"] == 2
        assert result["simulationTime"] == 0.35
        assert result["working_ratio"] == 100

    def test_BalancingABuffer(self, cleanup):
        from manpy.simulation.Examples.Old.BalancingABuffer import main

        result = main(test=1)
        assert result["parts"] == 13
        assert result["working_ratio"] == 80

    def test_ChangingPredecessors(self, cleanup):
        from manpy.simulation.Examples.Old.ChangingPredecessors import main

        result = main(test=1)
        assert result["parts"] == 10
        assert result["simulationTime"] == 36.0
        assert 83.32 < result["working_ratio"] < 83.34

    def test_SettingWip3(self, cleanup):
        from manpy.simulation.Examples.Old.SettingWip3 import main

        result = main(test=1)
        assert result["parts"] == 2
        assert result["simulationTime"] == 0.35
        assert result["working_ratio"] == 100

    def test_NonStarvingLine(self, cleanup):
        from manpy.simulation.Examples.Old.NonStarvingLine import main

        result = main(test=1)
        assert result["parts"] == 9
        assert result["working_ratio"] == 100

    def test_NonStarvingLineBatches(self, cleanup):
        from manpy.simulation.Examples.Old.NonStarvingLineBatches import main

        result = main(test=1)
        assert result["batches"] == 4
        assert result["working_ratio"] == 100

    def test_CompoundMachine(self, cleanup):
        from manpy.simulation.Examples.Old.CompoundMachine import main

        result = main(test=1)
        assert 5.8 < result < 5.92

    def test_JobShop2ScenarioAnalysis(self, cleanup):
        from manpy.simulation.Examples.Old.JobShop2ScenarioAnalysis import main

        result = main(test=1)
        assert result == 2

    def test_BufferAllocation(self, cleanup):
        from manpy.simulation.Examples.Old.BufferAllocation import main

        result = main(test=1)
        assert 80 < result["parts"] < 1000

    def test_ExampleLine(self, cleanup):
        from manpy.simulation.Examples.ExampleLine import main

        result = main(test=1)

        assert len(result["Entities"]) >= len(result["Discards"]) + result["Exits"], \
            "Number of Entities should be higher than Discards+Exits\nEntities: {}\nDiscards: {}\nExits: {}".format(len(result["Entities"]), len(result["Discards"]), result["Exits"])
        for key in result:
            if key.__contains__("Ftr"):
                assert len(result[key]) >= len(result["Discards"]) + result["Exits"], \
                    "Number of Features should be higher than Discards+Exits\nFeatures: {}\nDiscards: {}\nExits: {}".format(len(result[key]), len(result["Discards"]), result["Exits"])

    def test_RandomWalk(self, cleanup):
        from manpy.simulation.Examples.Random_Walk import main

        result = main(test=1)

        for idx in range(1, len(result["Ftr1"])):
            assert result["Ftr1"][idx] - result["Ftr1"][idx - 1] >= -10, \
                                    "RandomWalk should be higher than -10\nIt instead is: ".format(result["Ftr1"][idx])
            assert result["Ftr1"][idx] - result["Ftr1"][idx - 1] <= 10, \
                                    "RandomWalk should be lower than 10\nIt instead is: ".format(result["Ftr1"][idx])
    def test_Dependency(self, cleanup):
        from manpy.simulation.Examples.Dependency import main

        result = main(test=1)

        for idx in range(len(result["Spannung"])):
            assert result["Strom"][idx] == 1000*result["Spannung"][idx] + 1900, \
                             "Strom should be: {}\nIt instead is: {}".format(result["Strom"][idx], 1000*result["Spannung"][idx] + 1900)
            assert result["Widerstand"][idx] == (result["Spannung"][idx]/result["Strom"][idx]*1000000), \
                             "Widerstand should be: {}\nIt instead is: {}".format(result["Widerstand"][idx], (result["Spannung"][idx]/result["Strom"][idx]*1000000))

    def test_Merging(self, cleanup):
        from manpy.simulation.Examples.Merging import main

        result = main(test=1)

        for e in result["Exits"]:
            assert None not in e.features, \
                             "Features have not been merged completeply: {}".format(e.features)
        assert None in result["FirstEntity"].features, \
                      "First Entity should not contain all Features: {}".format(result["FirstEntity"].features)
