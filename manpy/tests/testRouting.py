from unittest import TestCase
import manpy.simulation.core.ProductionLineModule as plm
from manpy.simulation.core import Machine, Queue, Source, Exit, Assembly


class TestRouting(TestCase):

    def testGenerateRoutingFromList(self):
        s1 = Source.Source("s1", "source1")
        m1 = Machine.Machine("m1", "machine1")
        m2 = Machine.Machine("m2", "machine2")
        q1 = Queue.Queue("q1", "queue1")
        s2 = Source.Source("s2", "source2")
        a1 = Assembly.Assembly("a1", "assembly1")
        e1 = Exit.Exit("e1", "exit1")

        routing = [
            [s1],
            [m1],
            [q1],
            [m2, s2],
            [a1],
            [e1]
        ]

        plm.generate_routing_from_list(routing)

        self.assertEqual(s1.previous, [])
        self.assertEqual(s1.next[0].name, "machine1")

        self.assertEqual(m1.previous[0].name, "source1")
        self.assertEqual(m1.next[0].name, "queue1")

        self.assertEqual(q1.previous[0].name, "machine1")
        self.assertEqual(q1.next[0].name, "machine2")

        self.assertEqual(m2.previous[0].name, "queue1")
        self.assertEqual(m2.next[0].name, "assembly1")
        self.assertEqual(s2.previous, [])
        self.assertEqual(s2.next[0].name, "assembly1")

        self.assertEqual(a1.previous[0].name, "machine2")
        self.assertEqual(a1.previous[1].name, "source2")
        self.assertEqual(a1.next[0].name, "exit1")

        self.assertEqual(e1.previous[0].name, "assembly1")
        self.assertEqual(e1.next, [])

    def testGenerateRoutingFromListWithModule(self):
        s1 = Source.Source("s1", "source1")
        m1 = Machine.Machine("m1", "machine1")
        m2 = Machine.Machine("m2", "machine2")
        q1 = Queue.Queue("q1", "queue1")
        s2 = Source.Source("s2", "source2")
        a1 = Assembly.Assembly("a1", "assembly1")
        e1 = Exit.Exit("e1", "exit1")


        module_routing = [
                [q1],
                [m2, s2],
                [a1]
            ]

        line_module = plm.SequentialProductionLineModule(module_routing, [], "module1")

        routing = [
                [s1],
                [m1],
                [line_module],
                [e1]
            ]

        plm.generate_routing_from_list(routing)

        self.assertEqual(s1.previous, [])
        self.assertEqual(s1.next[0].name, "machine1")

        self.assertEqual(m1.previous[0].name, "source1")
        self.assertEqual(m1.next[0].name, "queue1")

        self.assertEqual(q1.previous[0].name, "machine1")
        self.assertEqual(q1.next[0].name, "machine2")

        self.assertEqual(m2.previous[0].name, "queue1")
        self.assertEqual(m2.next[0].name, "assembly1")
        self.assertEqual(s2.previous, [])
        self.assertEqual(s2.next[0].name, "assembly1")

        self.assertEqual(a1.previous[0].name, "machine2")
        self.assertEqual(a1.previous[1].name, "source2")
        self.assertEqual(a1.next[0].name, "exit1")

        self.assertEqual(e1.previous[0].name, "assembly1")
        self.assertEqual(e1.next, [])

    def testPLMDefineRouting(self):
        s1 = Source.Source("s1", "source1")
        m1 = Machine.Machine("m1", "machine1")
        m2 = Machine.Machine("m2", "machine2")
        q1 = Queue.Queue("q1", "queue1")
        s2 = Source.Source("s2", "source2")
        a1 = Assembly.Assembly("a1", "assembly1")
        e1 = Exit.Exit("e1", "exit1")

        module_routing = [
            [q1],
            [m2, s2],
            [a1]
        ]

        line_module = plm.SequentialProductionLineModule(module_routing, [], "module1")

        s1.defineRouting([m1])
        m1.defineRouting([s1], line_module.getRoutingStart())
        line_module.defineRouting([m1], [e1])
        e1.defineRouting(line_module.getRoutingEnd())


        self.assertEqual(s1.previous, [])
        self.assertEqual(s1.next[0].name, "machine1")

        self.assertEqual(m1.previous[0].name, "source1")
        self.assertEqual(m1.next[0].name, "queue1")

        self.assertEqual(q1.previous[0].name, "machine1")
        self.assertEqual(q1.next[0].name, "machine2")

        self.assertEqual(m2.previous[0].name, "queue1")
        self.assertEqual(m2.next[0].name, "assembly1")
        self.assertEqual(s2.previous, [])
        self.assertEqual(s2.next[0].name, "assembly1")

        self.assertEqual(a1.previous[0].name, "machine2")
        self.assertEqual(a1.previous[1].name, "source2")
        self.assertEqual(a1.next[0].name, "exit1")

        self.assertEqual(e1.previous[0].name, "assembly1")
        self.assertEqual(e1.next, [])





