# -*- coding: utf-8 -*-

import logging

from sqlalchemy.orm.exc import NoResultFound

from . import models
from .cache import BaseCacheManager
from ..canonicalize import decanonicalize_edge, decanonicalize_node
from ..constants import CITATION, EVIDENCE, ANNOTATIONS, RELATION
from ..io import to_bytes, from_bytes
from ..utils import parse_datetime

log = logging.getLogger(__name__)


class GraphCacheManager(BaseCacheManager):
    def insert_graph(self, graph, store_parts=True):
        """Stores a graph in the database

        :param graph: a BEL network
        :type graph: :class:`pybel.BELGraph`
        """
        graph_bytes = to_bytes(graph)

        network = models.Network(blob=graph_bytes, **graph.document)

        if store_parts:
            self.store_graph_parts(network, graph)

        self.session.add(network)
        self.session.commit()

        return network

    def store_graph_parts(self, network, graph):
        nc = {node: self.get_or_create_node(graph, node) for node in graph}

        for u, v, k, data in graph.edges_iter(data=True, keys=True):
            source, target = nc[u], nc[v]

            citation = self.get_or_create_citation(**data[CITATION])
            evidence = self.get_or_create_evidence(citation, data[EVIDENCE])

            bel = decanonicalize_edge(graph, u, v, k)
            edge = models.Edge(source=source, target=target, relation=data[RELATION], evidence=evidence, bel=bel)

            for key, value in data[ANNOTATIONS].items():
                if key in graph.annotation_url:
                    url = graph.annotation_url[key]
                    edge.annotations.append(self.get_or_create_bel_annotation(url, value))

            network.edges.append(edge)

    def get_or_create_bel_annotation(self, url, value):
        a = self.session.query(models.Annotation).filter_by(url=url).one()
        return self.session.query(models.AnnotationEntry).filter_by(annotation=a, name=value).one()

    def get_or_create_evidence(self, citation, text):
        """Creates entry for given evidence if it does not exist.

        :param citation: Citation object obtained from get_or_create_citation()
        :type citation: models.Citation
        :param text: Evidence text
        :type text: str
        :return:
        :rtype: models.Evidence
        """
        try:
            result = self.session.query(models.Evidence).filter_by(text=text).one()
        except NoResultFound:
            result = models.Evidence(text=text, citation=citation)
            self.session.add(result)
            self.session.flush()
            # self.session.commit()  # TODO remove?
        return result

    def get_or_create_node(self, graph, node):
        """Creates entry for given node if it does not exist.

        :param graph: A BEL network
        :type graph: pybel.BELGraph
        :param node: Key for the node to insert.
        :type node: tuple
        :rtype: models.Node
        """
        bel = decanonicalize_node(graph, node)

        try:
            result = self.session.query(models.Node).filter_by(bel=bel).one()
        except NoResultFound:
            result = models.Node(bel=bel)
            self.session.add(result)

        return result

    def get_or_create_edge(self, source, target, evidence, bel, relation):
        """Creates entry for given edge if it does not exist.

        :param source: Source node of the relation
        :type source: models.Node
        :param target: Target node of the relation
        :type target: models.Node
        :param evidence: Evidence object that proves the given relation
        :type evidence: models.Evidence
        :param bel: BEL statement that describes the relation
        :type bel: str
        :param relation: Type of the relation between source and target node
        :type relation: str
        :rtype: models.Edge
        """
        result = self.session.query(models.Edge).filter_by(bel=bel).one_or_none()

        if result:
            return result

        result = models.Edge(source=source, target=target, relation=relation, evidence=evidence, bel=bel)

        return result

    def get_or_create_citation(self, type, name, reference, date=None, authors=None, comments=None):
        """Creates entry for given citation if it does not exist.

        :param type: Citation type (e.g. PubMed)
        :type type: str
        :param name: Title of the publication that is cited
        :type name: str
        :param reference: Identifier of the given citation (e.g. PubMed id)
        :type reference: str
        :param date: Date of publication
        :type date: date
        :param authors: List of authors separated by |
        :type authors: str
        :param comments: Comments on the citation
        :type comments: str
        :return:
        :rtype: models.Citation
        """

        try:
            result = self.session.query(models.Citation).filter_by(type=type, reference=reference).one()
        except NoResultFound:
            if date is not None:
                date = parse_datetime(date)

            result = models.Citation(type=type, name=name, reference=reference, date=date, comments=comments)

            if authors is not None:
                for author in authors.split('|'):
                    result.authors.append(self.get_or_create_author(author))

            self.session.add(result)

        return result

    def get_or_create_author(self, name):
        """

        :param name: An author's name
        :type name: str
        :return:
        """
        result = self.session.query(models.Author).filter_by(name=name).one_or_none()

        if result:
            return result

        result = models.Author(name=name)
        self.session.add(result)

        return result

    def get_graph_versions(self, name):
        """Returns all of the versions of a graph with the given name"""
        return {x for x, in self.session.query(models.Network.version).filter(models.Network.name == name).all()}

    def get_graph(self, name, version=None):
        """Loads most recent graph, or allows for specification of version

        :param name: The name of the graph
        :type name: str
        :param version: The version string of the graph. If not specified, loads most recent graph added with this name
        :type version: None or str
        :return:
        """
        if version is not None:
            n = self.session.query(models.Network).filter(models.Network.name == name,
                                                          models.Network.version == version).one()
        else:
            n = self.session.query(models.Network).filter(models.Network.name == name).order_by(
                models.Network.created.desc()).first()

        return from_bytes(n.blob)

    def get_by_edge_filter(self, **kwargs):
        # TODO implement
        pass

    def drop_graph(self, network_id):
        """Drops a graph by ID"""

        # TODO delete with cascade
        self.session.query(models.Network).filter(models.Network.id == network_id).delete()
        self.session.commit()

    def ls(self):
        return [(network.id, network.name, network.version) for network in self.session.query(models.Network).all()]
