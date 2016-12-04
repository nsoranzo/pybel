import unittest

import pybel
from pybel.processing import *
from tests.constants import test_bel_1


class TestProcessing(unittest.TestCase):
    def setUp(self):
        self.graph = pybel.from_path(test_bel_1)
        self.graph.add_edge(('Gene', 'HGNC', 'AKT1'), 'dummy')
        self.graph.add_edge(('RNA', 'HGNC', 'EGFR'), 'dummy2')

    def test_base(self):
        self.assertEqual(14, self.graph.number_of_nodes())
        self.assertEqual(16, self.graph.number_of_edges())

    def test_prune_by_type(self):
        prune_by_type(self.graph, 'Gene')
        self.assertEqual(11, self.graph.number_of_nodes())

    def test_prune(self):
        prune(self.graph)
        self.assertEqual(8, self.graph.number_of_nodes())

    def test_infer(self):
        add_inferred_edges(self.graph, 'translatedTo')
        self.assertEqual(20, self.graph.number_of_edges())
