"""
This file contains the default paths and urls used by the cache manager and the bel data manager.

See: https://wiki.openbel.org/display/BELNA/Namespaces+Overview
"""
import os

default_pybel_data = os.path.expanduser('~/.pybel/data')
if not os.path.exists(default_pybel_data):
    os.makedirs(default_pybel_data)

DEFAULT_BEL_DATA_NAME = 'beldatacache.db'
DEFAULT_BEL_DATA_LOCATION = os.path.join(default_pybel_data, DEFAULT_BEL_DATA_NAME)

default_namespaces = [
    'http://resource.belframework.org/belframework/20150611/namespace/affy-probeset-ids.belns',
    'http://resource.belframework.org/belframework/20150611/namespace/chebi-ids.belns',
    'http://resource.belframework.org/belframework/20150611/namespace/chebi.belns',
    'http://resource.belframework.org/belframework/20150611/namespace/disease-ontology-ids.belns',
    'http://resource.belframework.org/belframework/20150611/namespace/disease-ontology.belns',
    'http://resource.belframework.org/belframework/20150611/namespace/entrez-gene-ids.belns',
    'http://resource.belframework.org/belframework/20150611/namespace/go-biological-process-ids.belns',
    'http://resource.belframework.org/belframework/20150611/namespace/go-biological-process.belns',
    'http://resource.belframework.org/belframework/20150611/namespace/go-cellular-component-ids.belns',
    'http://resource.belframework.org/belframework/20150611/namespace/go-cellular-component.belns',
    'http://resource.belframework.org/belframework/20150611/namespace/hgnc-human-genes.belns',
    'http://resource.belframework.org/belframework/20150611/namespace/mesh-cellular-structures-ids.belns',
    'http://resource.belframework.org/belframework/20150611/namespace/mesh-cellular-structures.belns',
    'http://resource.belframework.org/belframework/20150611/namespace/mesh-chemicals-ids.belns',
    'http://resource.belframework.org/belframework/20150611/namespace/mesh-chemicals.belns',
    'http://resource.belframework.org/belframework/20150611/namespace/mesh-diseases-ids.belns',
    'http://resource.belframework.org/belframework/20150611/namespace/mesh-diseases.belns',
    'http://resource.belframework.org/belframework/20150611/namespace/mesh-processes-ids.belns',
    'http://resource.belframework.org/belframework/20150611/namespace/mesh-processes.belns',
    'http://resource.belframework.org/belframework/20150611/namespace/mgi-mouse-genes.belns',
    'http://resource.belframework.org/belframework/20150611/namespace/rgd-rat-genes.belns',
    'http://resource.belframework.org/belframework/20150611/namespace/selventa-legacy-chemicals.belns',
    'http://resource.belframework.org/belframework/20150611/namespace/selventa-legacy-diseases.belns',
    'http://resource.belframework.org/belframework/20150611/namespace/selventa-named-complexes.belns',
    'http://resource.belframework.org/belframework/20150611/namespace/selventa-protein-families.belns',
    'http://resource.belframework.org/belframework/20150611/namespace/swissprot-ids.belns',
    'http://resource.belframework.org/belframework/20150611/namespace/swissprot.belns'
]

default_annotations = [
    'http://resource.belframework.org/belframework/20150611/annotation/anatomy.belanno',
    'http://resource.belframework.org/belframework/20150611/annotation/cell-line.belanno',
    'http://resource.belframework.org/belframework/20150611/annotation/cell-structure.belanno',
    'http://resource.belframework.org/belframework/20150611/annotation/cell.belanno',
    'http://resource.belframework.org/belframework/20150611/annotation/disease.belanno',
    'http://resource.belframework.org/belframework/20150611/annotation/mesh-anatomy.belanno',
    'http://resource.belframework.org/belframework/20150611/annotation/mesh-diseases.belanno',
    'http://resource.belframework.org/belframework/20150611/annotation/species-taxonomy-id.belanno'
]
