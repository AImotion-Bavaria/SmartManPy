import sys
from unittest import TestCase
import manpy.simulation.StateController as sc


class TestStateControllers(TestCase):

    def testSimpleStateController(self):

        # test auto reset via reset_amount
        s = sc.SimpleStateController(states=[0, 1],
                                     boundaries={(0, 3): 0, (3, None): 1},
                                     wear_per_step=1,
                                     labels=["ok", "defect"],
                                     initial_state_index=0,
                                     reset_amount=4,
                                     )

        self.assertEqual((0, "ok"), s.get_and_update())
        self.assertEqual((0, "ok"), s.get_and_update())
        self.assertEqual((0, "ok"), s.get_and_update())
        self.assertEqual((1, "defect"), s.get_and_update())
        self.assertEqual((0, "ok"), s.get_initial_state())
        self.assertEqual((0, "ok"), s.get_and_update())

        for i in range(2):
            s.get_and_update()

        s_reset = sc.SimpleStateController(states=[0, 1],
                                           boundaries={(0, 1): 0, (1, None): 1},
                                           wear_per_step=1,
                                           labels=["ok", "defect"],
                                           initial_state_index=0,
                                           reset_amount=None,
                                           )

        # test behavior of reset function
        s_reset.get_and_update()
        s_reset.get_and_update()
        self.assertEqual((1, "defect"), s_reset.get_and_update())
        s_reset.reset()
        self.assertEqual((0, "ok"), s_reset.get_and_update())

    def testContinuosNormalDistribution(self):
        s = sc.ContinuosNormalDistribution(wear_per_step=1,
                                            break_point=3,
                                            mean_change_per_step=1,
                                            initial_mean=0,
                                            std=1,
                                            defect_mean=10,
                                            defect_std=5
                                            )

        def __extract_mean_and_std(dist_dict):
            return dist_dict["Feature"]["Normal"]["mean"], dist["Feature"]["Normal"]["stdev"]

        dist, label = s.get_and_update()
        self.assertFalse(label)
        mean, std = __extract_mean_and_std(dist)
        self.assertEqual(1, mean)
        self.assertEqual(1, std)

        dist, label = s.get_and_update()
        mean, std = __extract_mean_and_std(dist)
        self.assertFalse(label)
        self.assertEqual(2, mean)
        self.assertEqual(1, std)

        dist, label = s.get_and_update()
        mean, std = __extract_mean_and_std(dist)
        self.assertFalse(label)
        self.assertEqual(3, mean)
        self.assertEqual(1, std)

        # expect defect now
        dist, label = s.get_and_update()
        mean, std = __extract_mean_and_std(dist)
        self.assertTrue(label)
        self.assertEqual(10, mean)
        self.assertEqual(5, std)

        dist, label = s.get_initial_state()
        mean, std = __extract_mean_and_std(dist)
        self.assertEqual(0, mean)
        self.assertEqual(1, std)

        s.reset()

        dist, label = s.get_and_update()
        mean, std = __extract_mean_and_std(dist)
        self.assertFalse(False)
        self.assertEqual(1, mean)
        self.assertEqual(1, std)

    def testRandomDefectsController(self):
        s1 = sc.ContinuosNormalDistribution(wear_per_step=1,
                                           break_point=None,
                                           mean_change_per_step=1,
                                           initial_mean=0,
                                           std=1,
                                           defect_mean=10,
                                           defect_std=5
                                           )

        s2 = sc.ContinuosNormalDistribution(wear_per_step=1,
                                            break_point=None,
                                            mean_change_per_step=1,
                                            initial_mean=100,
                                            std=1,
                                            defect_mean=110,
                                            defect_std=50
                                            )

        r = sc.RandomDefectStateController(failure_probability=0.0,
                                           ok_controller=s1,
                                           defect_controller=s2)

        for i in range(100):
            dist, label = r.get_and_update()
            self.assertFalse(label)

        r = sc.RandomDefectStateController(failure_probability=1.0,
                                           ok_controller=s1,
                                           defect_controller=s2)

        for i in range(100):
            dist, label = r.get_and_update()
            self.assertTrue(label)

