import _pickle
import hashlib
import logging
import time
from copy import deepcopy

import pandas as pd
from sqlalchemy import exists
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

        self.definitionCacheManager = definition_cache_manager if definition_cache_manager else DefinitionCacheManager(
            conn=conn,
            setup_default_cache=setup_default_cache)

        self.eng = self.definitionCacheManager.eng  # create_engine(conn, echo=log_sql)
        self.sesh = scoped_session(sessionmaker(bind=self.eng, autoflush=False, expire_on_commit=False))

        # self.citation_cache = {}
        # self.attribute_cache = {}
        # self.statement_cache = {}  # ToDo: check if this is same as edge_cache?

        self.cache = {'citation': {},
                      'evidence': {},
                      'attribute': {},
                      'edge': {},
                      'node': {}}

        #self.setup_caches(node_cache=True, evidence_cache=True)

        # ToDo: Add these caches:
        # self.node_cache = {}
        # self.edge_cache = {}

        # self.setup_caches()

    def setup_caches(self, node_cache=False, edge_cache=False, citation_cache=False, evidence_cache=False,
                     attribute_cache=False):
        # ToDo: Check if a flag is needed so these would not be setup at instantiation but with flag (timesaving?)
        """Initiates the caches of BelDataManager object so they will be available at initiation."""

        if citation_cache and len(self.cache['citation']) == 0:
            citation_dataframe = pd.read_sql_table(database_models.CITATION_TABLE_NAME, self.eng).groupby(
                'citationType')
            self.cache['citation'] = {citType: pd.Series(group.id.values, index=group.reference).to_dict() for
                                   citType, group in citation_dataframe}

        if attribute_cache and len(self.cache['attribute']) == 0:
            attributes_dataframe = pd.read_sql_table(database_models.PROPERTY_TABLE_NAME, self.eng).groupby('propKey')
            self.cache['attribute'] = {propKey: pd.Series(group.id.values, index=group.propValue).to_dict() for
                                    propKey, group in attributes_dataframe}

        if edge_cache and len(self.cache['edge']) == 0:
            edge_dataframe = pd.read_sql_table(database_models.EDGE_TABLE_NAME, self.eng).groupby('sha256')
            self.cache['edge'] = {sha256: group.id.values[0] for sha256, group in edge_dataframe}
            # statement_attrib_dataframe = pd.read_sql_table(database_models.EDGE_PROPERTIES_TABLE_NAME,
            #                                               self.eng).groupby('edge_id')
            # self.cache['edge'] = {statement_id: set(group.property_id.values) for
            #                        statement_id, group in statement_attrib_dataframe}

        if evidence_cache and len(self.cache['evidence']) == 0:
            evidence_dataframe = pd.read_sql_table(database_models.EVIDENCE_TABLE_NAME, self.eng).groupby('sha256')
            self.cache['evidence'] = {sha256: group.id.values[0] for sha256, group in evidence_dataframe}

        if node_cache and len(self.cache['node']) == 0:
            node_dataframe = pd.read_sql_table(database_models.NODE_TABLE_NAME, self.eng).groupby('nodeHashString')
            self.cache['node'] = {_pickle.loads(group.nodeHashTuple.values[0]): group.id.values[0] for nodeHash, group
                                  in node_dataframe}

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
            return False
        else:
            pyGraph_data = {
                'description': graph_description,
                'label': graph_label,
                'graph': _pickle.dumps(utils.flatten_graph_data(pybel_graph))
            }
            g = self.eng.execute(database_models.Graphstore.__table__.insert(), pyGraph_data)
            g_id = g.inserted_primary_key[0]
            if extract_information:
                self.extract_information(pybel_graph, g_id)
            return True

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

    # def get_name_id(self,defType ,definition, name):
    #    if defType == 'N':
    #        return int(self.namespace_id_cache[self.namespace_dict[definition]['url']][name])
    #    elif defType == 'A':
    #        return int(self.annotation_id_cache[self.annotation_dict[definition]['url']][name])

    def store_node(self, nodeHash, node_data, namespace_dict, namespace_id_cache):
        """Stores Node into relational database.
        Uses get_or_create() to either make a new entry in db or return existing one."""
        node_type = node_data['type']
        node_sha256 = hashlib.sha256(str(nodeHash).encode('utf-8')).hexdigest()
        node_dict = {
            'function': node_type,
            'nodeHashString': str(nodeHash),
            'nodeHashTuple': _pickle.dumps(nodeHash),
            'sha256': node_sha256
        }

        if node_type not in ('Complex', 'Composite', 'Reaction'):
            if 'namespace' in node_data:
                node_dict.update({
                    'nodeIdentifier_id': int(namespace_id_cache[namespace_dict[node_data['namespace']]['url']][
                                                 node_data['name']]),
                })
            else:
                print(nodeHash, "\t", node_data)

        node = self.get_or_create(database_models.Node, node_dict, discriminator_column='sha256')

        if node_type == 'ProteinVariant':
            for variant in node_data['variants']:
                modificationType = variant[0]
                modification_dict = {
                    'modType': modificationType,
                }

                if modificationType == 'Variant':
                    modification_dict.update({
                        'variantString': variant[1],
                        # ToDo: These will be removed and the variant will not be splited anymore!
                        # 'aminoA': variant[2],
                        # 'aminoB': variant[4],
                        # 'position': variant[3],
                    })

                elif modificationType == 'ProteinModification':
                    if 'namespace' in node_data:
                        modification_dict['pmodName_id'] = int(
                            namespace_id_cache[namespace_dict[node_data['namespace']]['url']][
                                node_data['name']])
                    modification_dict.update({
                        'pmodName': variant[1],
                        'aminoA': variant[2] if len(variant) > 2 else None,
                        'position': variant[3] if len(variant) > 3 else None
                    })

                else:
                    print(nodeHash, "\t", node_data)
                try:
                    modification = self.get_or_create(database_models.Modification, modification_dict)
                except:
                    print(modification_dict)
                    break

                self.get_or_create(database_models.AssociationNodeMod, {
                    'node_id': node.id,
                    'modification_id': modification.id
                })

        elif node_type == 'ProteinFusion':
            # ToDo: Handle ProteinFusion!
            modificationType = node_data['type']
            modification_dict = {
                'modType': modificationType,
                'p3Range': node_data['range_3p'],
                'p5Range': node_data['range_5p'],
                # 'p3Name_id': self.get_name_id('N', node_data['partner_3p']),
                # 'p5Name_id': self.get_name_id('N', node_data['partner_5p'])
            }

            modification = self.get_or_create(database_models.Modification, modification_dict)

            self.get_or_create(database_models.AssociationNodeMod, {
                'node_id': node.id,
                'modification_id': modification.id
            })

        self.cache['node'][nodeHash] = int(node.id)

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

            if sub not in self.cache['node']:
                self.store_node(sub, pybel_graph.node[sub], namespace_dict, namespace_id_cache)

            if obj not in self.cache['node']:
                self.store_node(obj, pybel_graph.node[obj], namespace_dict, namespace_id_cache)

            sub_id = self.cache['node'][sub]
            obj_id = self.cache['node'][obj]

            supporting_text_id = None  # = data['Evidence'] if 'Evidence' in data else None
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
                    evidence_text = attribute_data['Evidence']
                    evidence_sha256 = hashlib.sha256(evidence_text.encode('utf-8')).hexdigest()
                    if evidence_sha256 not in self.cache['evidence']:
                        evidence_dict = {
                            'supportingText': evidence_text,
                            'citation_id': citation.id,
                            'sha256': evidence_sha256
                        }
                        # ToDo: Ignore_existing is used to create entry even if the entry allready exists in the database
                        supporting_text = self.get_or_create(database_models.Evidence, evidence_dict,
                                                             discriminator_column='sha256')
                        self.cache['evidence'][evidence_sha256] = int(supporting_text.id)

                    del (attribute_data['Evidence'])
                    supporting_text_id = self.cache['evidence'][evidence_sha256]

            relation = attribute_data['relation']
            del (attribute_data['relation'])

            edge_sha256 = hashlib.sha256(
                str((sub_id, obj_id, relation, supporting_text_id)).encode('utf-8')).hexdigest()

            if edge_sha256 not in self.cache['edge']:
                edge_dict = {
                    'subject_id': sub_id,
                    'object_id': obj_id,
                    'relation': relation,
                    'citation_id': int(citation.id) if citation else None,
                    'supportingText_id': supporting_text_id,
                    'sha256': edge_sha256
                }
                edge = self.get_or_create(database_models.Edge, edge_dict, discriminator_column='sha256')
                self.cache['edge'][edge_sha256] = edge.id


            self.get_or_create(database_models.AssociationEdgeGraph, {
                'edge_id': self.cache['edge'][edge_sha256],
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
                            'edge_id': self.cache['edge'][edge_sha256],
                            'attribute_id': int(attribute.id)
                        })

                elif attribute_key in annotation_dict:
                    annotationName_id = int(annotation_id_cache[annotation_dict[attribute_key]['url']][attribute_value])
                    edge_annotation_dict = {
                        'edge_id': self.cache['edge'][edge_sha256],
                        'annotationName_id': annotationName_id
                    }
                    self.get_or_create(database_models.AssociationEdgeAnnotation, edge_annotation_dict)

        self.sesh.commit()

    def show_stored_graphs(self):
        """Shows stored graphs in relational database."""
        stored_graph_label = self.sesh.query(database_models.Graphstore.label).all()
        return [g_label for labels_listed in stored_graph_label for g_label in labels_listed]

    def get_or_create(self, database_model, insert_dict, discriminator_column=None, ignore_existing=False):
        """Method to insert a new instance into the relational database or to return the instance if it allready
        exists in database.
        """
        instance = None
        discriminator_dict = {
            discriminator_column: insert_dict[discriminator_column]} if discriminator_column else insert_dict
        if not ignore_existing:
            instance = self.sesh.query(database_model).filter_by(**discriminator_dict).first()
            if instance:
                return instance

        if not instance:
            instance = database_model(**insert_dict)
            self.sesh.add(instance)
            self.sesh.flush()
            return instance
