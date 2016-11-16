import logging
import os
import _pickle, time

from sqlalchemy import create_engine, exists
from sqlalchemy.orm import sessionmaker, scoped_session

from . import database_models
from . import namespace_cache as defManager
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
        self.definitionCacheManager = definition_cache_manager if definition_cache_manager else defManager.DefinitionCacheManager(
            setup_default_cache=setup_default_cache)

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
        # ToDo: Do the pickling here!
        if self.sesh.query(exists().where(database_models.PyBELGraphStore.label == graph_label)).scalar():
            logging.error("A graph with the label '{}' allready exists in the graph-store!".format(graph_label))
        else:
            pyGraph_data = {
                'name': graph_name,
                'label': graph_label,
                'graph': _pickle.dumps(utils.flatten_edges(pybel_graph))
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
            return utils.expand_edges(_pickle.loads(graph_data.graph))

        else:
            logging.error("Graph with label '{}' does not exist. Use 'show_stored_graphs()' to get a list of all stored Graph-Labels.".format(graph_label))

    def extract_information(self, pybel_graph, graph_id=None):
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
            try:
                def_info = self.definitionCacheManager.get_definition_info(namespace_url)
                keyword = def_info['keyword']
            except:
                print(namespace_url)
            if keyword not in namespace_dict:
                namespace_dict[keyword] = def_info

            # ToDo: Clarify handling of multiple namespaces (different pub dates)
            #elif len(namespace_dict[keyword]) == 1:
            #    namespace_dict[keyword] = {
            #        namespace_dict[keyword]['url']: namespace_dict[keyword],
            #        def_info['url']: def_info
            #    }
            #else:
            #    namespace_dict[keyword][def_info['url']] = def_info

        node_db = {}
        edge_db = {}

        for node_key, node_data in pybel_graph.nodes_iter(data=True):
            if node_key not in node_db:
                if 'namespace' in node_data:
                    nsv_id = namespace_id_cache[namespace_dict[node_data['namespace']]['url']][node_data['name']]
                    insert_values = [{'function': node_data['type'], 'nsContext_id': nsv_id}]
                    term_data = self.eng.execute(database_models.BELTerm.__table__.insert(), insert_values)
                    node_db[node_key] = term_data.inserted_primary_key[0]

        for sub, obj, identifier, data in pybel_graph.edges_iter(data=True, keys=True):

            if (sub, obj) not in edge_db:
                sub_id = node_db[sub]
                obj_id = node_db[obj]

                property_insert_values = []
                property_ids = []

                for property in data:
                    property_insert_values.append({
                        'propKey': property,
                        'propValue': str(data[property]),
                    })

                for pro in property_insert_values:
                    props = self.eng.execute(database_models.BELEdgeProperty.__table__.insert(), [pro])
                    prop_id = props.inserted_primary_key[0]
                    property_ids.append(prop_id)

                statement_insert_values = [{
                    'subject_id': sub_id,
                    'object_id': obj_id,
                    'relation': data['relation'],
                }]

                statement = self.eng.execute(database_models.BELStatement.__table__.insert(), statement_insert_values)
                statement_id = statement.inserted_primary_key[0]

                edge_db[(sub, obj)] = statement_id

                self.eng.execute(database_models.association_table.insert(), [{'statement_id': statement_id, 'property_id': property_id} for property_id in property_ids])

        print("INFO:", time.time()-st)

    def show_stored_graphs(self):
        """Shows stored graphs in relational database."""
        stored_graph_label = self.sesh.query(database_models.PyBELGraphStore.label).distinct().all()
        return [g_label for labels_listed in stored_graph_label for g_label in labels_listed]
