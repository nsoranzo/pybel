import database_models, urllib.request, gzip, time

from defaults import default_namespaces

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session
from sqlalchemy.ext.declarative import declarative_base

class Mapper:
    
    def __init__(self, connection_string, sql_echo=False):
        """
        :param: connection_string: Database connection.
        :param: sql_echo: Shows SQL queries on console if True.
        """
        self.db_engine = create_engine(connection_string,echo=sql_echo)
        self.db_session = scoped_session(sessionmaker(bind=self.db_engine,autoflush=False,expire_on_commit=False))
        self.map_dict = {}
    
    def create_tables(self):
        """
        Creates empty tables for mapping in given database (connection_string).
        :note: Existing tables will be droped!
        """
        database_models.Base.metadata.drop_all(self.db_engine)
        database_models.Base.metadata.create_all(self.db_engine)
        
    
    def insert_mapping(self):
        """
        Populates database with data (connection_string). Sources are defined in defaults.py
        """
        for namespace, source_url in default_namespaces.items():
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
                    insert_values.append({'uniprot':uniprot_id, 'reference':reference, 'xref':reference_id})
                    
#                     if uniprot_id in uniprot_dict and reference in uniprot_dict[uniprot_id]:
#                         if reference_id not in uniprot_dict[uniprot_id][reference]:
#                             uniprot_dict[uniprot_id][reference].append(reference_id)
#                     
#                     elif uniprot_id in uniprot_dict:
#                         uniprot_dict[uniprot_id][reference] = [reference_id]
#                     
#                     else:
#                         uniprot_dict[uniprot_id] = {reference:[reference_id]}
#                         
#                     if reference in self.map_dict and reference_id in self.map_dict[reference]:
#                         if uniprot_id not in self.map_dict[reference][reference_id]['uniprot']:
#                             self.map_dict[reference][reference_id]['uniprot'].append(uniprot_id)
#                     
#                     elif reference in self.map_dict:
#                         self.map_dict[reference][reference_id] ={'uniprot':[uniprot_id]}
#                     
#                     else:
#                         self.map_dict[reference] = {reference_id:{'uniprot':[uniprot_id]}}
                
                print("[INFO] Done creating value_dict_list ({runtime:3.2f}s)".format(runtime=(time.time()-tmp_time)))
                tmp_time = time.time()
                
                self.db_session.bulk_insert_mappings(database_models.Uniprot_Map,insert_values)
                self.db_session.commit()
                
                print("[INFO] Done bulk_insert ({runtime:3.2f}s)".format(runtime=(time.time()-tmp_time)))
                tmp_time = time.time()
                
                self.map_dict['uniprot'] = uniprot_dict
                
            elif source_url.endswith('.json'):
                pass
            
            print("[INFO] Done parsing '{ns}'. \n[RUNTIME] {runtime:3.2f}s".format(ns=namespace,runtime=(time.time()-start_time)))
            
    def __create_mapping(self, reference, reference_id, uniprot_id):        
            map = {}
            pass
        
    def create_namespace_map(self, namespace):
        """
        Returns dictionary for mapping between UniProt and namespace.
        """
        start_time = time.time()
        mapping_data = self.db_session.query(database_models.Uniprot_Map).filter_by(reference=namespace).all()
        
        uniprot_dict = {}
        namespace_dict = {}
        
        for entry in mapping_data:
            uniprot_id = entry.uniprot
            reference = entry.reference
            reference_id = entry.xref
            
            if uniprot_id in uniprot_dict and reference in uniprot_dict[uniprot_id]:
                if reference_id not in uniprot_dict[uniprot_id][reference]:
                    uniprot_dict[uniprot_id][reference].append(reference_id)
             
            elif uniprot_id in uniprot_dict:
                uniprot_dict[uniprot_id][reference] = [reference_id]
             
            else:
                uniprot_dict[uniprot_id] = {reference:[reference_id]}
            
        #TODO: Add Namespace -> Uniprot
            
        mapping_dict = {'UniProt':uniprot_dict,
                        namespace:namespace_dict}
        
        print('[INFO] Mapping_Data type: {mapping_data_type} ({runtime:3.2f}s)'.format(mapping_data_type=type(mapping_data),runtime=(time.time()-start_time)))
        
        return mapping_dict

    def map(self, source_namespace, name, target_namesapce, use_uniprot_api=False):
        """
        :param: source_namespace: Namespace name is valid in.
        :param: name: Name that should be mapped to target_namespace.
        :param: target_namespace: Namespace name should be translated to.
        :param: use_uniprot_api: Describes if online api of uniprot or local database should be used for mapping.
        
        :return: Name in target_namespace.
        
        Get map for name in source_namespace to target_namespace.
        """
        pass
    
    
if __name__ == '__main__':
#     connection_string = 'mysql+pymysql://root:motale2@localhost/pybel'
    connection_string = 'sqlite:///pybel.db'
    mapper = Mapper(connection_string)
#     mapper.create_tables()
#     mapper.insert_mapping()

    md = mapper.create_namespace_map('HGNC')
    print(md)
#     print(type(md[0]))
    #print(mapper.get_namespace_map())
    