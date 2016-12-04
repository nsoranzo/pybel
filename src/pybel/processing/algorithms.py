def prune_genes(graph):
    """Removes all genes in graph (in-place) with only a connection to their transcribed RNA

    :param graph: a BEL network
    :type graph: BELGraph
    """
    pass


def prune_rna(graph):
    """Removes all RNA in graph (in-place) that only has connection to their translated Protein

    :param graph: a BEL network
    :type graph: BELGraph
    """
    pass


def prune(graph):
    """Prunes genes, then RNA in-place

    :param graph: a BEL network
    :type graph: BELGraph

    """
    prune_genes(graph)
    prune_rna(graph)

inferred_inverse = {
    'hasProduct': 'isProductOf',
    'hasReactant': 'isReactantOf',
    'hasVariant': 'isVariantOf',
    'hasComponent': 'isComponentOf',
    'transcribedTo': 'transcribedFrom',
    'translatedTo': 'translatedFrom'
}


def add_inferred_edges(graph, relations):
    """Adds inferred edges based on pre-defined axioms

    :param graph: a BEL network
    :type graph: BELGraph
    :param relation: iterable of relation names to add their inverse inferred edges
    """
    pass
