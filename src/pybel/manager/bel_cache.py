import _pickle
import logging
import os
import time
from copy import deepcopy

import pandas as pd
from sqlalchemy import create_engine, exists
from sqlalchemy.orm import sessionmaker, scoped_session

from . import database_models
from . import defaults
from .definitions_cache import DefinitionCacheManager
from .. import graph as PyBEL_Graph
from .. import utils

# ToDo: Exclude log, pybel_data, DEFAULT_BEL_DATA_NAME, DEFAULT_BEL_DATA_LOCATION to a definition file (used in here and in namespace cache)

log = logging.getLogger('pybel')


class BelDataManager:
    def __init__(self, conn=None, definition_cache_manager=None, setup_default_cache=True, log_sql=False):
        conn = conn if conn is not None else 'sqlite:///' + defaults.DEFAULT_BEL_DATA_LOCATION

        self.eng = create_engine(conn, echo=log_sql)
        self.sesh = scoped_session(sessionmaker(bind=self.eng, autoflush=False, expire_on_commit=False))
        self.definitionCacheManager = definition_cache_manager if definition_cache_manager else DefinitionCacheManager(
            setup_default_cache=setup_default_cache)

        self.citation_cache = {}
        self.attribute_cache = {}
        self.statement_cache = {}  # ToDo: check if this is same as edge_cache?

        self.cache = {'citation': {},
                      'attribute': {},
                      'edge': {},
                      'node': {}}

        # ToDo: Add these caches:
        # self.node_cache = {}
        # self.edge_cache = {}

        # self.setup_caches()

    def setup_caches(self, citation_cache=True, attribute_cache=True, statement_cache=True):
        # ToDo: Check if a flag is needed so these would not be setup at instantiation but with flag (timesaving?)
        """Initiates the caches of BelDataManager object so they will be available at initiation."""

        if citation_cache and len(self.citation_cache) == 0:
            citation_dataframe = pd.read_sql_table(database_models.CITATION_TABLE_NAME, self.eng).groupby(
                'citationType')
            self.citation_cache = {citType: pd.Series(group.id.values, index=group.reference).to_dict() for
                                   citType, group in citation_dataframe}

        if attribute_cache and len(self.attribute_cache) == 0:
            attributes_dataframe = pd.read_sql_table(database_models.PROPERTY_TABLE_NAME, self.eng).groupby('propKey')
            self.attribute_cache = {propKey: pd.Series(group.id.values, index=group.propValue).to_dict() for
                                    propKey, group in attributes_dataframe}

        if statement_cache and len(self.statement_cache) == 0:
            statement_attrib_dataframe = pd.read_sql_table(database_models.EDGE_PROPERTIES_TABLE_NAME,
                                                           self.eng).groupby('edge_id')
            self.statement_cache = {statement_id: set(group.property_id.values) for
                                    statement_id, group in statement_attrib_dataframe}

    def setup_cache(self, cacheType):
        """Creates cache of the given type.
        Possible types of caches are:
        - citation
        - attribute
        - edge
        - node"""
        cache_resolving = {
            'citation': {
                'database': database_models.CITATION_TABLE_NAME,
                'grouping': 'citationType'
            },
            'attribute': {
                'database': database_models.PROPERTY_TABLE_NAME,
                'grouping': "propKey",
            },
            'edge': {
                'database': database_models.EDGE_TABLE_NAME,
                'grouping': "",
            },
            'node': {
                'database': database_models.NODE_TABLE_NAME,
                'grouping': ""
            }
        }

        if cacheType in self.cache:
            cache_dataframe = pd.read_sql_table(cache_resolving[cacheType]['database'], self.eng).groupby(
                cache_resolving[cacheType]['grouping'])

        else:
            log.error(
                "The cacheType '{}' does not exist. Use: (citation, attribute, edge or node) as cacheType.".format(
                    cacheType))

    def store_graph(self, pybel_graph, graph_label, graph_description=None, extract_information=True):
        """Stores PyBEL Graph object into given database.

        :param pybel_graph: PyBEL Graph object to store in database.

        :param graph_label: Label that should be used to identify the stored Graph.
        :type graph_label: str
        :param graph_description: Description of the stored graph.
        :type graph_description: str

        :param extract_information: Indicates if BEL information should be extracted from PyBEL Graph object and
        stored into relational database schema.
        :type extract_information: bool

        """
        if self.sesh.query(exists().where(database_models.Graphstore.label == graph_label)).scalar():
            logging.error("A graph with the label '{}' allready exists in the graph-store!".format(graph_label))
        else:
            pyGraph_data = {
                'description': graph_description,
                'label': graph_label,
                'graph': _pickle.dumps(utils.flatten_graph_data(pybel_graph))
            }
            g = self.eng.execute(database_models.Graphstore.__table__.insert(), pyGraph_data)
            g_id = g.inserted_primary_key[0]
            self.extract_information(pybel_graph, g_id)

    def load_graph(self, graph_label):
        """Loads stored graph from relational database.

        :param graph_label: Label used to identify the stored graph.
        :type graph_label: str

        """
        graph_data = self.sesh.query(database_models.Graphstore).filter_by(label=graph_label).first()
        if graph_data:
            return PyBEL_Graph.expand_edges(_pickle.loads(graph_data.graph))

        else:
            logging.error(
                "Graph with label '{}' does not exist. Use 'show_stored_graphs()' to get a list of all stored Graph-Labels.".format(
                    graph_label))

    def __store_list(self, list_node):
        node_id = None
        return node_id

    def store_node(self, nodeHash, node_data, namespace_dict, namespace_id_cache):
        """Stores Node into relational database.
        Uses get_or_create() to either make a new entry in db or return existing one."""
        node_type = node_data['type']
        node_dict = {
            'function': node_type,
            'nodeHash': str(nodeHash),
        }

        if node_type not in ('Complex', 'Composite', 'Reaction'):
            if 'namespace' in node_data:
                node_dict.update({
                    'nodeIdentifier_id': int(namespace_id_cache[namespace_dict[node_data['namespace']]['url']][
                                                 node_data['name']]),
                })
            else:
                print(nodeHash, "\t", node_data)

        node = self.get_or_create(database_models.Node, node_dict)

        if node_type == 'ProteinVariant':
            for variant in node_data['variants']:
                modification_dict = {
                    'modType': variant[0],
                    'variantType': variant[1],
                    'pmodName_id': None,
                    'pmodName': None,
                    'aminoA': variant[2],
                    'aminoB': variant[4],
                    'position': variant[3],
                }
                modification = self.get_or_create(database_models.Modification, modification_dict)

                self.get_or_create(database_models.AssociationNodeMod, {
                    'node_id': node.id,
                    'modification_id': modification.id
                })

        # ToDo: Add Modification handling for pmod!

        return node

    def extract_information(self, pybel_graph, graph_id):
        """Extracts BEL information from PyBEL Graph object and inserts it into relational database schema.

        :param pybel_graph: PyBEL Graph object that contains the information to store.
        :type pybel_graph:
        :param graph_id: Identifier of PyBEL Graph stored in relational database.
        :type graph_id: int
        """
        id_cache = self.definitionCacheManager.get_cache_with_id()
        namespace_id_cache = id_cache['namespace_cache']
        annotation_id_cache = id_cache['annotation_cache']

        namespace_dict = {}
        annotation_dict = {}

        st = time.time()
        for namespace_url in namespace_id_cache:
            def_info = self.definitionCacheManager.get_definition_info(namespace_url)
            keyword = def_info['keyword']
            if keyword not in namespace_dict:
                namespace_dict[keyword] = def_info
                #     namespace_dict[keyword] = [namespace_url]
                #
                # elif namespace_url not in namespace_dict[keyword]:
                #     namespace_dict[keyword].append(namespace_url)

        for annotation_url in annotation_id_cache:
            def_info = self.definitionCacheManager.get_definition_info(annotation_url)
            keyword = def_info['keyword']
            if keyword not in annotation_dict:
                annotation_dict[keyword] = def_info
                #     annotation_dict[keyword] = [annotation_url]
                # elif annotation_url not in annotation_dict[keyword]:
                #     annotation_dict[keyword].append(annotation_url)

                # ToDo: Clarify handling of multiple namespaces (different pub dates)
                # elif len(namespace_dict[keyword]) == 1:
                #    namespace_dict[keyword] = {
                #        namespace_dict[keyword]['url']: namespace_dict[keyword],
                #        def_info['url']: def_info
                #    }
                # else:
                #    namespace_dict[keyword][def_info['url']] = def_info

        for sub, obj, identifier, data in pybel_graph.edges_iter(data=True, keys=True):
            subject_node = self.store_node(sub, pybel_graph.node[sub], namespace_dict, namespace_id_cache)
            object_node = self.store_node(obj, pybel_graph.node[obj], namespace_dict, namespace_id_cache)
            # ToDo: Evidence will be called supporting text in future!
            supporting_text = None  # = data['Evidence'] if 'Evidence' in data else None
            citation = None

            attribute_data = deepcopy(data)

            if 'citation' in attribute_data:
                citation_dict = {
                    'citationType': attribute_data['citation']['type'],
                    'reference': attribute_data['citation']['reference'],
                    'name': attribute_data['citation']['name'],
                }

                # ToDo: Use own method to provide enrichted citation??
                citation = self.get_or_create(database_models.Citation, citation_dict)
                del (attribute_data['citation'])

                if 'Evidence' in attribute_data:
                    evidence_dict = {
                        'supportingText': attribute_data['Evidence'],
                        'citation_id': citation.id
                    }
                    supporting_text = self.get_or_create(database_models.Evidence, evidence_dict)
                    del (attribute_data['Evidence'])

            # modification = self.get_or_create(database_models.Modification, modification_dict)

            relation = attribute_data['relation']
            del (attribute_data['relation'])

            edge_dict = {
                'subject_id': int(subject_node.id),
                'object_id': int(object_node.id),
                'relation': relation,
                'citation_id': int(citation.id) if citation else citation,
                'supportingText_id': int(supporting_text.id) if supporting_text else supporting_text
            }

            edge = self.get_or_create(database_models.Edge, edge_dict)

            self.get_or_create(database_models.AssociationEdgeGraph, {
                'edge_id': int(edge.id),
                'graph_id': int(graph_id)
            })

            # =========================================================================================
            # =========================================================================================


            for attribute_key, attribute_value in attribute_data.items():
                attributes = []

                if attribute_key in ('subject', 'object'):
                    modifier = attribute_value['modifier']
                    attribute_dict = {
                        'participant': attribute_key,
                        'modifier': modifier,
                    }

                    if modifier in ('Translocation', 'Activity'):
                        for effect_key, effect_value in attribute_value['effect'].items():
                            attribute_dict['relativeKey'] = effect_key
                            if 'namespace' in effect_value:
                                # ToDo: Simplify this after merge from develop -> manager!
                                # if len(namespace_dict[effect_value['namespace']]) == 1:
                                #     attribute_dict['name_id'] = int(namespace_id_cache[namespace_dict[effect_value['namespace']][0]][effect_value['name']])
                                # else:
                                #     for url in namespace_dict[effect_value['namespace']]:
                                #         if effect_value['name'] in namespace_id_cache[namespace_dict[url]]:
                                #             attribute_dict['name_id'] = int(namespace_id_cache[namespace_dict[url][effect_value['name']]])
                                attribute_dict['name_id'] = int(
                                    namespace_id_cache[namespace_dict[effect_value['namespace']]['url']][
                                        effect_value['name']])
                            else:
                                attribute_dict['propValue'] = effect_value

                            attributes.append(self.get_or_create(database_models.Property, attribute_dict))
                    else:
                        attributes.append(self.get_or_create(database_models.Property, attribute_dict))

                    for attribute in attributes:
                        self.get_or_create(database_models.AssociationEdgeProperty, {
                            'edge_id': int(edge.id),
                            'attribute_id': int(attribute.id)
                        })

                elif attribute_key in annotation_dict:
                    annotationName_id = int(annotation_id_cache[annotation_dict[attribute_key]['url']][attribute_value])
                    edge_annotation_dict = {
                        'edge_id': int(edge.id),
                        'annotationName_id': annotationName_id
                    }
                    self.get_or_create(database_models.AssociationEdgeAnnotation, edge_annotation_dict)

            self.sesh.commit()

    def show_stored_graphs(self):
        """Shows stored graphs in relational database."""
        stored_graph_label = self.sesh.query(database_models.Graphstore.label).all()
        return [g_label for labels_listed in stored_graph_label for g_label in labels_listed]

    def get_or_create(self, database_model, insert_dict):
        """Method to insert a new instance into the relational database or to return the instance if it allready
        exists in database.
        """

        instance = self.sesh.query(database_model).filter_by(**insert_dict).first()
        if instance:
            return instance
        else:
            instance = database_model(**insert_dict)
            self.sesh.add(instance)
            self.sesh.flush()
            return instance
