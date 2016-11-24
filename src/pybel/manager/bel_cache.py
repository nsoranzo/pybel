import _pickle
import logging
import os
import time
from copy import deepcopy

import pandas as pd
from sqlalchemy import create_engine, exists
from sqlalchemy.orm import sessionmaker, scoped_session

from . import database_models
from .namespace_cache import DefinitionCacheManager
from .. import graph as PyBEL_Graph
from .. import utils

log = logging.getLogger('pybel')

pybel_data = os.path.expanduser('~/.pybel/data')

DEFAULT_BEL_DATA_NAME = 'definitions.db'
DEFAULT_BEL_DATA_LOCATION = os.path.join(pybel_data, DEFAULT_BEL_DATA_NAME)


class BelDataManager:
    def __init__(self, conn=None, definition_cache_manager=None, setup_default_cache=True, log_sql=False):
        conn = conn if conn is not None else 'sqlite:///' + DEFAULT_BEL_DATA_LOCATION

        self.eng = create_engine(conn, echo=log_sql)
        self.sesh = scoped_session(sessionmaker(bind=self.eng, autoflush=False, expire_on_commit=False))
        self.definitionCacheManager = definition_cache_manager if definition_cache_manager else DefinitionCacheManager(
            setup_default_cache=setup_default_cache)

        self.namespace_id_cache = self.definitionCacheManager.get_cache_with_id()['namespace_cache']

        self.citation_cache = {}
        self.attribute_cache = {}
        self.statement_cache = {}

        self.setup_caches()

    def setup_caches(self):
        citation_dataframe = pd.read_sql_table(database_models.CITATION_TABLE_NAME, self.eng).groupby('citationType')
        attributes_dataframe = pd.read_sql_table(database_models.PROPERTY_TABLE_NAME, self.eng).groupby('propKey')

        statement_attrib_dataframe = pd.read_sql_table(database_models.EDGE_PROPERTIES_TABLE_NAME, self.eng).groupby(
            'edge_id')
        self.statement_cache = {statement_id: set(group.property_id.values) for statement_id, group in statement_attrib_dataframe}

        self.citation_cache = {citType: pd.Series(group.id.values, index=group.reference).to_dict() for citType, group in citation_dataframe}
        self.attribute_cache = {propKey: pd.Series(group.id.values, index=group.propValue).to_dict() for propKey, group in attributes_dataframe}

    def store_graph(self, pybel_graph, graph_label, graph_name=None, extract_information=True):
        """Stores PyBEL Graph object into given database.

        :param pybel_graph: PyBEL Graph object to store in database.

        :param graph_label: Label that should be used to identify the stored Graph.
        :type graph_label: str
        :param graph_name: Long name for the stored Graph.
        :type graph_name: str

        :param extract_information: Indicates if BEL information should be extracted from PyBEL Graph object and
        stored into relational database schema.
        :type extract_information: bool

        """
        if self.sesh.query(exists().where(database_models.PyBELGraphStore.label == graph_label)).scalar():
            logging.error("A graph with the label '{}' allready exists in the graph-store!".format(graph_label))
        else:
            pyGraph_data = {
                'name': graph_name,
                'label': graph_label,
                'graph': _pickle.dumps(utils.flatten_graph_data(pybel_graph))
            }
            self.eng.execute(database_models.PyBELGraphStore.__table__.insert(), pyGraph_data)
        self.extract_information(pybel_graph)

    def load_graph(self, graph_label):
        """Loads stored graph from relational database.

        :param graph_label: Label used to identify the stored graph.
        :type graph_label: str

        """
        graph_data = self.sesh.query(database_models.PyBELGraphStore).filter_by(label=graph_label).first()
        if graph_data:
            return PyBEL_Graph.expand_edges(_pickle.loads(graph_data.graph))

        else:
            logging.error(
                "Graph with label '{}' does not exist. Use 'show_stored_graphs()' to get a list of all stored Graph-Labels.".format(
                    graph_label))

    def __store_list(self, list_node):
        node_id = None
        return node_id

    def __store_attributes(self, attributes):
        """Loads attributes of edge into relational database.

        :param edge_attributes: Edge attributes.
        :type edge_attributes: dict

        :returns: Tuple with citation_id and list of attribute ids."""
        edge_attributes = deepcopy(attributes)
        citation_id = None
        attribute_ids = []

        if 'citation' in edge_attributes:
            citation_data = edge_attributes['citation']
            citation_type = citation_data['type']
            citation_ref = citation_data['reference']
            del (edge_attributes['citation'])

            if not citation_type in self.citation_cache or citation_type in self.citation_cache and citation_ref not in self.citation_cache[citation_type]:
                citation = self.get_or_create(database_models.Citation, {
                    'citationType': citation_type,
                    'reference': citation_ref,
                    'name': citation_data['name'],
                    # ToDo: add citation enrichtment
                })
                citation_id = citation[0].id
                if citation_type not in self.citation_cache:
                    self.citation_cache[citation_type] = {citation_ref: citation_id}
                else:
                    self.citation_cache[citation_type][citation_ref] = citation_id

            citation_id = self.citation_cache[citation_type][citation_ref]

        for attribute_key, attribute_value in edge_attributes.items():
            # ToDo: Solve this hack with propper representation of subject and object related attributes
            attribute_value = str(attribute_value)
            if attribute_key not in self.attribute_cache or attribute_key in self.attribute_cache and attribute_value not in self.attribute_cache[attribute_key]:
                attribute = self.get_or_create(database_models.Property, {
                    'propKey': attribute_key,
                    'propValue': attribute_value
                })
                attribute_id = attribute[0].id
                if attribute_key not in self.attribute_cache:
                    self.attribute_cache[attribute_key] = {attribute_value: attribute_id}
                else:
                    self.attribute_cache[attribute_key][attribute_value] = attribute_id

            attribute_ids.append(self.attribute_cache[attribute_key][attribute_value])

        return citation_id, attribute_ids

    def store_node(self, nodeHash, node_data, namespace_dict):
        """Stores Node into relational database.
        Uses get_or_create() to either make a new entry in db or return existing one."""
        node_type = node_data['type']
        node_dict = {
            'function': node_type,
            'nodeHash': str(nodeHash),
        }

        if node_type not in ('Complex', 'Composite', 'Reaction'):
            node_dict.update({
                'nodeIdentifier_id': self.namespace_id_cache[namespace_dict[node_data['namespace']]['url']][
                    node_data['name']],
            })

        return self.get_or_create(database_models.Node, node_dict)

    def extract_information(self, pybel_graph):
        """Extracts BEL information from PyBEL Graph object and inserts it into relational database schema.

        :param pybel_graph: PyBEL Graph object that contains the information to store.
        :type pybel_graph:
        :param graph_id: Identifier of PyBEL Graph stored in relational database.
        :type graph_id: int
        """
        namespace_id_cache = self.definitionCacheManager.get_cache_with_id()['namespace_cache']
        namespace_dict = {}
        st = time.time()
        for namespace_url in namespace_id_cache:
            def_info = self.definitionCacheManager.get_definition_info(namespace_url)
            keyword = def_info['keyword']
            if keyword not in namespace_dict:
                namespace_dict[keyword] = def_info


                # ToDo: Clarify handling of multiple namespaces (different pub dates)
                # elif len(namespace_dict[keyword]) == 1:
                #    namespace_dict[keyword] = {
                #        namespace_dict[keyword]['url']: namespace_dict[keyword],
                #        def_info['url']: def_info
                #    }
                # else:
                #    namespace_dict[keyword][def_info['url']] = def_info

        # node_db = {}
        # edge_db = {}

        # for node_key, node_data in pybel_graph.nodes_iter(data=True):
        #     if node_key not in node_db:
        #         if 'namespace' in node_data:
        #             nsv_id = namespace_id_cache[namespace_dict[node_data['namespace']]['url']][node_data['name']]
        #
        #             insert_values = {
        #                 'function': node_data['type'],
        #                 'nodeIdentifier_id': int(nsv_id),
        #                 'graphKey': str(node_key)
        #             }
        #             term_data = self.get_or_create(database_models.Node, insert_values)
        #             node_db[node_key] = term_data[0].graphKey
        #         elif node_data['type'] in ('Complex', 'Composite', 'Reaction'):
        #             pass
        #         elif node_data['type'] == 'ProteinVariant':
        #             pass

        for sub, obj, identifier, data in pybel_graph.edges_iter(data=True, keys=True):
            subject_node = self.store_node(sub, pybel_graph.node[sub], namespace_dict)
            object_node = self.store_node(obj, pybel_graph.node[obj], namespace_dict)
            supporting_text = data['Evidence'] if 'Evidence' in data else None
            citation = None

            attribute_data = deepcopy(data)

            if 'citation' in data:
                citation_dict = {
                    'citationType': data['citation']['type'],
                    'reference': data['citation']['reference'],
                    'name': data['citation']['name'],
                }

                # ToDo: Use own method to provide enrichted citation??
                citation = self.get_or_create(database_models.Citation, citation_dict)
                del (attribute_data['citation'])

            # modification = self.get_or_create(database_models.Modification, modification_dict)

            relation = attribute_data['relation']
            del (attribute_data['relation'])
            #if 'citation' in edge_data:
            # citation_id, attribute_ids = self.__store_attributes(edge_data)

            edge_dict = {
                'subject_id': subject_node.id,
                'object_id': object_node.id,
                'relation': relation,
                'citation_id': citation.id if citation else citation,
                'supportingText': supporting_text
            }

            edge = self.get_or_create(database_models.Edge, edge_dict)

            for attribute_key, attribute_value in attribute_data.items():
                attribute_dict = {
                    'propKey': attribute_key,
                    'propValue': str(attribute_value)
                }
                attribute = self.get_or_create(database_models.Property, attribute_dict)

                edge.properties.append(attribute)

            self.sesh.commit()

            # if su_type not in ('Complex', 'Reaction','Composite') and ob_type not in ('Complex', 'Reaction', 'Composite') and (sub, obj) not in edge_db:
            #     sub_id = node_db[sub]
            #     obj_id = node_db[obj]
            #
            #     statement_insert_values = {
            #         'subject_id': str(sub),
            #         'object_id': str(obj),
            #         'relation': relation,
            #     }
            #
            #     statement = self.get_or_create(database_models.Edge, statement_insert_values)
            #
            #     statement_id = statement[0].id
            #
            #     if statement[1] or statement_id not in self.statement_cache:
            #         self.statement_cache[statement_id] = set()
            #
            #     if attribute_ids:
            #         for attribute_id in attribute_ids:
            #             if attribute_id not in self.statement_cache[statement_id]:
            #                 self.get_or_create(database_models.AssociationEdgeProperty, {
            #                     'edge_id': statement_id,
            #                     'property_id': attribute_id
            #                 })
            #                 self.statement_cache[statement_id].add(attribute_id)

    def show_stored_graphs(self):
        """Shows stored graphs in relational database."""
        stored_graph_label = self.sesh.query(database_models.PyBELGraphStore.label).distinct().all()
        return [g_label for labels_listed in stored_graph_label for g_label in labels_listed]

    def get_or_create(self, database_model, insert_dict):
        instance = self.sesh.query(database_model).filter_by(**insert_dict).first()
        if instance:
            return instance, False
        else:
            instance = database_model(**insert_dict)
            self.sesh.add(instance)
            self.sesh.flush()
            #self.sesh.commit()
            return instance, True
