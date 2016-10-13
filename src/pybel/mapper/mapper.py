import database_models, urllib.request, gzip, time

from defaults import default_namespaces

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session
from sqlalchemy.ext.declarative import declarative_base

# TODO: Change print('[INFO] ...') to logging!

class Mapper:
    
    def __init__(self, connection_string, sql_echo=False):
        """
        :param: connection_string: Database connection.
        :param: sql_echo: Shows SQL queries on console if True.
        """
        self.__db_engine = create_engine(connection_string,echo=sql_echo)
        self.__db_session = scoped_session(sessionmaker(bind=self.__db_engine,autoflush=False,expire_on_commit=False))
    
    def create_tables(self):
        """
        Creates empty tables for mapping in given database (connection_string).
        :note: Existing tables will be droped!
        """
        database_models.Base.metadata.drop_all(self.__db_engine)
        database_models.Base.metadata.create_all(self.__db_engine)
        
    
    def insert_mapping(self, source_dict=default_namespaces):
        """
        Populates database with data (connection_string). Sources are defined in defaults.py
        """
        for namespace, source_url in source_dict.items():
            start_time = time.time()
            print("[INFO] Start parsing '{}'".format(namespace))
            tmp_file, headers = urllib.request.urlretrieve(source_url)
            print("[INFO] Download ({download_time:3.2f}s)".format(download_time=(time.time()-start_time)))
            tmp_time = time.time()
            
            if source_url.endswith('.dat.gz'):
                decompressed_file = gzip.open(tmp_file)
                entries = decompressed_file.readlines()
                
                #TODO: Check if source is uniprot!
                uniprot_dict = {}
                
                insert_values = []
                
                print("[INFO] Number of rows: {}".format(len(entries)))
                
                for entry in entries:
                    uniprot_id, reference, reference_id = entry.decode('utf-8').strip().split("\t")
                    reference_id = reference_id.lower() if reference == 'Gene_Name' else reference_id
                    insert_values.append({'uniprot':uniprot_id, 'reference':reference, 'xref':reference_id})
                
                print("[INFO] Done creating value_dict_list ({runtime:3.2f}s)".format(runtime=(time.time()-tmp_time)))
                tmp_time = time.time()
                
                self.__db_engine.execute(database_models.Uniprot_Map.__table__.insert(),insert_values)

                print("[INFO] Done insert ({runtime:3.2f}s)".format(runtime=(time.time()-tmp_time)))
                tmp_time = time.time()
            
            print("[INFO] Done parsing '{ns}'. \n[RUNTIME] {runtime:3.2f}s".format(ns=namespace,runtime=(time.time()-start_time)))      
                  
    def create_namespace_map(self, namespace):
        """
        :param: namespace: Identifier for namespaces that should be mapped to. Use get_namespace_list() to get a list of available namespaces.
        :param: nested_map: Flag for a nested namespace mapping dict like: dict[Namespace][Namespace_id][other_Namespace]
        
        """
        start_time = time.time()
        uniprot_orm = database_models.Uniprot_Map
        mapping_data = self.__db_session.query(uniprot_orm).filter_by(reference=namespace).all()
        
        uniprot_dict = {}
        namespace_dict = {}
        
        for entry in mapping_data:
            uniprot_id = entry.uniprot
            ref = entry.reference
            reference_id = entry.xref
            
            if uniprot_id in uniprot_dict:
                uniprot_dict[uniprot_id].add(reference_id)
             
            else:
                uniprot_dict[uniprot_id] = set([reference_id])
            
            if reference_id in namespace_dict:
                namespace_dict[reference_id].add(uniprot_id)
                    
            else:
                namespace_dict[reference_id] = set([uniprot_id])
                
        result_dict = {'UniProt':uniprot_dict,
                       namespace:namespace_dict}
        
        print('[INFO] Map for "{mapped_namespace}" created ({runtime:3.2f}s)'.format(mapped_namespace=namespace,runtime=(time.time()-start_time)))
        
        return result_dict
    
    def create_complete_map(self):
        """
        Creates mapping dictionary. i.e. {namespace_A: {namespace_A:{Identifier:{uniprot, id, set, ...}}, 'UniProt':{Identifier:{namespace, id, set, ...}, ...}}, ...}
        To access uniprot identifiers in namespace 'HGNC' for 'HGNC:620' (APP) use: map_dict['HGNC']['HGNC:620']
        """
        start_time = time.time()
        tmp_map_dict = {}
        map_dict = {}
        uniprot_dict = {}
        
        for namespace in self.get_namespace_list():
            tmp_map_dict = self.create_namespace_map(namespace)
            
            for uni_id in tmp_map_dict['UniProt']:
                if uni_id in uniprot_dict and namespace in uniprot_dict[uni_id]:
                    uniprot_dict[uni_id][namespace] |= tmp_map_dict['UniProt'][uni_id]
                elif uni_id in uniprot_dict:
                    uniprot_dict[uni_id][namespace] = tmp_map_dict['UniProt'][uni_id]
                else:
                    uniprot_dict[uni_id] = {namespace:tmp_map_dict['UniProt'][uni_id]}

            del(tmp_map_dict['UniProt'])
            map_dict.update(tmp_map_dict)
        
        map_dict['UniProt'] = uniprot_dict  
        print('[INFO] Created mapping dictionary ({runtime:3.2f}s)'.format(runtime=(time.time()-start_time)))
        
        return map_dict
    
    def get_namespace_list(self):
        """
        Returns a list of all mapped to namespaces.
        
        :return: List of namespaces available in database.
        """
        namespaces_nested = self.__db_engine.query(database_models.Uniprot_Map.reference).distinct().all()
        return [namespace for namespaces_listed in namespaces_nested for namespace in namespaces_listed]
    
    def map(self, source_namespace, identifier, target_namespace, use_uniprot_api=False):
        """
        :param: source_namespace: Namespace name is valid in.
        :param: name: Name that should be mapped to target_namespace.
        :param: target_namespace: Namespace name should be translated to.
        :param: use_uniprot_api: Describes if online api of uniprot or local database should be used for mapping. [This is a placeholder and not used yet!]
        
        :return: Name in target_namespace.
        
        Get map for name in source_namespace to target_namespace.
        """
        start_time = time.time()
        uniprot_orm = database_models.Uniprot_Map
        
        uniprot_nested = self.__db_session.query(uniprot_orm.uniprot).filter_by(reference=source_namespace,xref=identifier).all()
        
        uniprot_ids = [uniprot_id for listed in uniprot_nested for uniprot_id in listed]
        
        desired_targets = self.__db_session.query(uniprot_orm.xref).filter_by(reference=target_namespace).filter(uniprot_orm.uniprot.in_(uniprot_ids)).all()

        print("[INFO] Mapped '{entity_name}' from '{source_name}' to '{target_name}' ({runtime:3.2f}s)".format(entity_name=identifier,
                                                                                                               source_name=source_namespace,
                                                                                                               target_name=target_namespace,
                                                                                                               runtime=(time.time()-start_time)))
        
        return [target_id for listed in desired_targets for target_id in listed]