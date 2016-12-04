from __future__ import print_function

import json
import textwrap

import networkx as nx

abundances = {
    'Gene': 'g',
    'GeneVariant': 'gv',
    'Pathology': 'path',
    'BiologicalProcess': 'bp',
    'Protein': 'p',
    'RNA': 'r',
    'miRNA': 'm',
    'Abundance': 'a',
    'ProteinVariant': 'pv',
    'Reaction': 'rxn'
}

node_shape = {
    'p': "diamond",
    'pv': "diamond",
    'a': "star",
    'g': "triangle",
    'gv': "triangle",
    'path': "triangleDown",
    'complex': "square",
    'bp': "dot",
    'rxn': "square",
    'list': "star",
    'composite': "diamond",
    'r': "dot",
    'reaction': "dot",
    'm': "dot",
    None: "dot",
}

relation_color = {
    'decreases': "red",
    'directlyDecreases': "red",
    'increases': "green",
    'directlyIncreases': "green",
    'causesNoChange': "#088A08",
    'negativeCorrelation': "#610B0B",
    'positiveCorrelation': "#5F4C0B",
    'association': "#190710",
    'analogous': "#DF01D7",
    'orthologous': "#243B0B",
    'transcribedTo': "#58FAF4",
    'translatedTo': "#2EFE2E",
    'biomarkerFor': "#2EFE2E",
    'hasMember': "#2EFE2E",
    'hasMembers': "#2EFE2E",
    'hasComponent': "#2EFE2E",
    'hasComponents': "#2EFE2E",
    'isA': "#2EFE2E",
    'prognosticBiomarkerFor': "#2EFE2E",
    'rateLimitingStepOf': "#2EFE2E",
    'subProcessOf': "#2EFE2E"
}

node_color = {
    'p': "red",
    'pv': "blue",
    'a': "purple",
    'g': "green",
    'gv': "blue",
    'path': "orange",
    'complex': "blue",
    'bp': "cyan",
    'rxn': "lime green",
    'list': "green",
    'composite': "Fuchsia",
    'r': "Teal",
    'm': "Gold",
    None: "Gold",
}


def __to_html_helper(nodes, edges):
    html = """<!doctype html>
<html>
    <head>
        <script type="text/javascript" src="https://cdnjs.cloudflare.com/ajax/libs/vis/4.16.1/vis.min.js"></script>
        <link href="https://cdnjs.cloudflare.com/ajax/libs/vis/4.16.1/vis.min.css" rel="stylesheet" type="text/css" />
        <style type="text/css">
        #mynetwork {width: 950px;height: 750px;border: 1px solid lightgray;}
        </style>
    </head>
    <body>
        <div id="mynetwork"></div>
        <script type="text/javascript">
            var visjs_data = {};
            visjs_data.nodes = %s;
            visjs_data.edges = %s;
        </script>
        <script type="text/javascript">
            // color for vis.js networks
            var relColor = {
                'decreases' : "red",
                'directlyDecreases' : "red",
                'increases' : "green",
                'directlyIncreases' : "green",
                'causesNoChange' : "#088A08",
                'negativeCorrelation' : "#610B0B",
                'positiveCorrelation' : "#5F4C0B",
                'association' : "#190710",
                'analogous' : "#DF01D7",
                'orthologous' : "#243B0B",
                'transcribedTo' : "#58FAF4",
                'translatedTo' : "#2EFE2E",
                'biomarkerFor' : "#2EFE2E",
                'hasMember' : "#2EFE2E",
                'hasMembers' : "#2EFE2E",
                'hasComponent' : "#2EFE2E",
                'hasComponents' : "#2EFE2E",
                'isA' : "#2EFE2E",
                'prognosticBiomarkerFor' : "#2EFE2E",
                'rateLimitingStepOf' : "#2EFE2E",
                'subProcessOf' : "#2EFE2E"
            };

            var borderColor = {
                    'gtp' : "#FF0000",
                    'tloc' : "#DBA901",
                    'tscript' : "#04B404",
                    'act' : "#0101DF",
                    'sec' : "#B404AE",
                    'phos' : "#DF013A",
                    'surf' :  "#585858",
                    'tport' : "#01DFA5",
                    'deg' : "#F7819F",
                    'ribo' : "#D0FA58",
                    'kin' : "#9F81F7",
                    'cat' : "purple",
                    'chap' : "#8A0886",
                    'pep' : "#084B8A"
            };
            var nodesColor = {
                    'p' : "red",
                  'pv' : "blue",
                    'a' : "purple",
                    'g' : "green",
                    'path' : "orange",
                    'complex' : "blue",
                    'bp' : "cyan",
                    'rxn' :  "lime green",
                    'list' : "green",
                    'composite' : "Fuchsia",
                    'r' : "Teal",
                    'm' : "Gold",
                    null : "Gold",
            };
            var nodesShape = {
                    'p' : "diamond",
                  'pv' : "diamond",
                    'a' : "star",
                    'g' : "triangle",
                    'path' : "triangleDown",
                    'complex' : "square",
                    'bp' : "dot",
                    'rxn' :  "square",
                    'list' : "star",
                    'composite' : "diamond",
                    'r' : "dot",
                    'reaction' : "dot",
                    'm' : "dot",
                    null : "dot",
            };
        </script>
        <script type="text/javascript">

            function startNetwork(d) {
                for (i = 0; i < d.edges.length; i++) {
                    d.edges[i]["color"] = relColor[d.edges[i].label];
                }

                var nodesDict={};
                for (i = 0; i < d.nodes.length; i++) {
                    nodesDict[d.nodes[i].id] = d.nodes[i].label;
                }


                var nodes = new vis.DataSet(d.nodes);

                // create an array with edges
                var edges = new vis.DataSet(d.edges);

                // create a network
                var container = document.getElementById('mynetwork');
                var data = {
                    nodes : nodes,
                    edges : edges
                };
                var options = {
                    interaction : {
                        hideEdgesOnDrag : false
                    },
                    edges : {
                        arrows : 'to',
                        label : 'middle',
                        font : {
                            align : 'middle'
                        },
                        smooth : {
                            type : 'continuous'
                        }
                    },
                    physics : {
                     stabilization: false,
                        barnesHut : {
                            gravitationalConstant : -10000,
                            springConstant : 0.01,
                            springLength : 150,
                            avoidOverlap : 0.1
                        }
                    }
                };
                var network = new vis.Network(container, data, options);
            }
            startNetwork(visjs_data);
        </script>
    </body>
</html>"""
    return html % (json.dumps(nodes), json.dumps(edges))


def __to_bel(n):
    n = list(n)
    if n[0] in abundances:
        n[0] = abundances[n[0]]
        bel = "{}({}:{})".format(*n)
    elif n[0] in ['Complex', 'Composite']:
        n[0] = n[0].lower()
        bel = n[0]
    else:
        bel = str(n)
    return n[0], bel


def to_html(g, with_labels=True, nodes=None):
    """Outputs HTML for viewing the network

    :param g: graph to display
    :param with_labels: should the labels be displayed?
    :param nodes: iterable of nodes to keep. Keeps all nodes if None
    :return: HTML for displaying the network
    :rtype: str

    For example, this could be used in a Jupyter Notebook like this:

.. code-block:: python

    >>> from pybel.processing import visualization
    >>> from IPython.display import IFrame
    >>> path = 'temp.html'
    >>> with open(path, 'w') as f:
    >>>    print(visualization.to_html(graph), file=f)
    >>> IFrame(path, width=950, height=750)
    """
    nodes = [] if nodes is None else nodes

    if nodes:
        g = nx.MultiDiGraph(g.subgraph(nodes).edges(data=True))

    if g.number_of_nodes() > 2000:
        return "<html>Graph have more than 2000 nodes. Reduce the number of nodes!</html>"

    node_list = []
    edge_list = []

    node_id_dict = {n[0]: (i, n[1]) for i, n in enumerate(g.nodes(data=True))}

    for node_tuple, (node_id, node_data) in node_id_dict.items():
        node_type, label = __to_bel(node_tuple)

        node_dict = {
            'id': node_id,
            'shape': node_shape[node_type],
            'color': node_color[node_type],
            'title': node_tuple
        }

        if with_labels:
            node_dict['label'] = label
        node_list.append(node_dict)

    for source, target, edge_attribs in g.edges_iter(data=True):
        edge_dict = {
            'from': node_id_dict[source][0],
            'to': node_id_dict[target][0],
            'color': relation_color.get(edge_attribs['relation'], None)
        }

        if 'SupportingText' not in edge_attribs:
            edge_dict['title'] = 'added by PyBEL'
        else:
            statement = ["<b>subject</b>: {}".format(source)]
            if 'subject' in edge_attribs:
                statement.append(str(edge_attribs['subject']))
            statement.append("<b>relation</b>: {}".format(edge_attribs['relation']))
            statement.append("<b>object</b>: {}".format(target))
            if 'object' in edge_attribs:
                statement.append(str(edge_attribs['object']))

            title = ["<b>evidence</b>: {}".format(edge_attribs['SupportingText'])]
            if 'citation' in edge_attribs:
                title.append("<b>reference:</b> {type}: {name}; {reference}".format_map(edge_attribs['citation']))

            edge_dict['title'] = '<br>'.join(statement) + '<br>'
            edge_dict['title'] += '<br>'.join(textwrap.wrap('<br>'.join(title), 60))

        edge_dict['label'] = edge_attribs.get('relation', None)

        edge_list.append(edge_dict)

    return __to_html_helper(node_list, edge_list)
