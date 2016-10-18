# 1. Create tables
# 2. NS cache on the fly
# 3. NS cache from DB
import unittest

from pybel.mapper import Mapper

class TestImport(unittest.TestCase):
    
    expected_cache_dict = {'TESTNS1':{'TestValue1':'O',
                                      'TestValue2':'O',
                                      'TestValue3':'O',
                                      'TestValue4':'O',
                                      'TestValue5':'O'}}
    
    test_db = Mapper('sqlite:///test_db.db')
    test_db.create_tables()
    
    test_namespace = {'url':'file:/home/akonotopez/workspace/Eclipse/pybel/tests/bel/',
                      'namespaces':['test_ns_1.belns']}
    
    def test_onFly(self):
        
        onFly_cache_dict = test_db.insert_latest_bel_namespaces(test_namespace)
        self.assertEqual(expected_cache_dict, onFly_cache_dict)
    
    def test_fromDB(self):
        
        fromDB_cache_dict = test_db.get_cached_namespaces()
        self.assertEqual(expected_cache_dict, onFly_cache_dict)