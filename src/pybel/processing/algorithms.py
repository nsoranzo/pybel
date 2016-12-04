from ..parser.language import unqualified_edge_code

inferred_inverse = {
    'hasProduct': 'isProductOf',
    'hasReactant': 'isReactantOf',
    'hasVariant': 'isVariantOf',
    'hasComponent': 'isComponentOf',
    'transcribedTo': 'transcribedFrom',
    'translatedTo': 'translatedFrom'
}


def prune_by_type(graph, type):
    """Removes all nodes in graph (in-place) with only a connection to one node. Useful for gene and RNA.

    :param graph: a BEL network
    :type graph: BELGraph
    """
    to_prune = []
    for gene, data in graph.nodes_iter(data=True, type=type):
        if 1 >= len(graph.adj[gene]):
            to_prune.append(gene)
    graph.remove_nodes_from(to_prune)


def prune(graph):
    """Prunes genes, then RNA in-place

    :param graph: a BEL network
    :type graph: BELGraph

    """
    prune_by_type(graph, 'Gene')
    prune_by_type(graph, 'RNA')


def add_inferred_edges(graph, relations):
    """Adds inferred edges based on pre-defined axioms

    :param graph: a BEL network
    :type graph: BELGraph
    :param relation: single or iterable of relation names to add their inverse inferred edges
    """

    if isinstance(relations, str):
        return add_inferred_edges(graph, [relations])

    for relation in relations:
        for u, v in graph.edges_iter(relation=relation):
            graph.add_edge(v, u, key=unqualified_edge_code[relation], relation=inferred_inverse[relation])
