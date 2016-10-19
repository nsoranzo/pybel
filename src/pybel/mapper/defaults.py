"""
This file contains a dictionary of the default namespaces
and URLs to load into a new PyBEL namespace store.

See: https://wiki.openbel.org/display/BELNA/Namespaces+Overview
"""

default_mapping = {'mapping_uniprot_human':'ftp://ftp.uniprot.org/pub/databases/uniprot/current_release/knowledgebase/idmapping/by_organism/HUMAN_9606_idmapping.dat.gz',
                    'mapping_uniprot_mouse':'ftp://ftp.uniprot.org/pub/databases/uniprot/current_release/knowledgebase/idmapping/by_organism/MOUSE_10090_idmapping.dat.gz',
                    'mapping_uniprot_rat':'ftp://ftp.uniprot.org/pub/databases/uniprot/current_release/knowledgebase/idmapping/by_organism/RAT_10116_idmapping.dat.gz',}

default_namespaces = {'url':'http://resource.belframework.org/belframework/latest-release/namespace/',
                      'namespaces':['affy-probeset-ids.belns','chebi-ids.belns','chebi.belns','disease-ontology-ids.belns','disease-ontology.belns','entrez-gene-ids.belns',
                                    'go-biological-process-ids.belns','go-biological-process.belns','go-cellular-component-ids.belns','go-cellular-component.belns','hgnc-human-genes.belns',
                                    'mesh-cellular-structures-ids.belns','mesh-cellular-structures.belns','mesh-chemicals-ids.belns','mesh-chemicals.belns','mesh-diseases-ids.belns','mesh-diseases.belns',
                                    'mesh-processes-ids.belns','mesh-processes.belns','mgi-mouse-genes.belns','rgd-rat-genes.belns','selventa-legacy-chemicals.belns','selventa-legacy-diseases.belns',
                                    'selventa-named-complexes.belns','selventa-protein-families.belns','swissprot-ids.belns','swissprot.belns']}
