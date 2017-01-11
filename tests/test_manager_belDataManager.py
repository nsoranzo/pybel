import _pickle
import hashlib
import os
import unittest

from pybel import graph as pyGraph
from pybel.manager.bel_cache import BelDataManager, DefinitionCacheManager
from pybel.manager.database_models import Node

dir_path = os.path.dirname(os.path.realpath(__file__))

test_bel = os.path.join(dir_path, 'bel', "test_bel_1.bel")


class TestBDM(unittest.TestCase):
    def setUp(self):
        self.test_db = 'sqlite://'

    def test_insertAndLoad(self):
        dcm = DefinitionCacheManager(conn=self.test_db)
        dcm.setup_database(drop_existing=True)
        test_graph = pyGraph.from_path(test_bel, definition_cache_manager=dcm)
        bdm = BelDataManager(conn=self.test_db, definition_cache_manager=dcm, setup_default_cache=True, log_sql=False)

        # Store without information extraction
        store_result = bdm.store_graph(test_graph, 'tg', 'test graph', extract_information=False)
        self.assertTrue(store_result)

        print(store_result)

        store_result_fail = bdm.store_graph(test_graph, 'tg', 'another test graph')
        self.assertFalse(store_result_fail)

        # Show stored graphs
        expected_show_result = ['tg']
        self.assertEqual(expected_show_result, bdm.show_stored_graphs())

        # Load stored graph
        load_result = bdm.load_graph('tg')
        self.assertIsNotNone(load_result)

        self.assertIsInstance(load_result, type(test_graph))

        # Get or create
        test_nodeHash = ('Protein', 'HGNC', 'APP')
        test_node_sha256 = hashlib.sha256(str(test_nodeHash).encode('utf-8')).hexdigest()
        test_node_dict = {
            'function': 'Protein',
            'nodeHashString': str(test_nodeHash),
            'nodeHashTuple': _pickle.dumps(test_nodeHash),
            'sha256': test_node_sha256
        }

        # Creating new instance
        test_instance_A = bdm.get_or_create(database_model=Node, insert_dict=test_node_dict)
        self.assertIsInstance(test_instance_A, Node)

        # Try to create same instance
        test_instance_B = bdm.get_or_create(database_model=Node, insert_dict=test_node_dict)
        self.assertIsInstance(test_instance_B, Node)
        self.assertEqual(test_instance_A.id, test_instance_B.id)

        # Ignore allready existing instance
        test_instance_C = bdm.get_or_create(database_model=Node, insert_dict=test_node_dict, ignore_existing=True)
        self.assertIsInstance(test_instance_C, Node)
        self.assertNotEqual(test_instance_A.id, test_instance_C.id)
        self.assertTrue(test_instance_C.id > test_instance_A.id)

        # Store Node
        id_cache = bdm.definitionCacheManager.get_cache_with_id()
        namespace_id_cache = id_cache['namespace_cache']

        namespace_dict = {}

        for namespace_url in namespace_id_cache:
            def_info = bdm.definitionCacheManager.get_definition_info(namespace_url)
            keyword = def_info['keyword']
            if keyword not in namespace_dict:
                namespace_dict[keyword] = def_info

        edge = test_graph.edges(data=True, keys=True)[0]

        # for sub, obj, identifier, data in self.test_graph.edges_iter(data=True, keys=True):
        test_node_A = bdm.store_node(edge[0], test_graph.node[edge[0]], namespace_dict, namespace_id_cache)
        test_node_B = bdm.store_node(edge[1], test_graph.node[edge[1]], namespace_dict, namespace_id_cache)
        self.assertIsInstance(test_node_A, Node)
        self.assertIsInstance(test_node_B, Node)
        self.assertNotEqual(test_node_A.id, test_node_B.id)

    def test_extractInformation(self):
        # Test if information extraction of a Statement works

        pass

    def test_setupCaches(self):
        # Test the setup of: Node, Edge, Citation, Evidence, Attribute
        pass
