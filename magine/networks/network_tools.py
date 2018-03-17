# -*- coding: utf-8 -*-
import itertools
import os

import networkx as nx
import pathos.multiprocessing as mp

from magine.networks.utils import nx_to_dot

try:
    from IPython.display import Image, display

    IPYTHON = True
except:
    IPYTHON = False

try:
    import pygraphviz as pyg
except ImportError:
    pyg = None


def delete_disconnected_network(full_graph):
    """
    Delete disconnected parts of a provided network

    Parameters
    ----------
    full_graph : networkx.DiGraph
    """

    tmp_g = full_graph.to_undirected()
    sorted_graphs = sorted(nx.connected_component_subgraphs(tmp_g), key=len,
                           reverse=True)
    for i in range(1, len(sorted_graphs)):
        full_graph.remove_nodes_from(sorted_graphs[i].nodes())


def paint_network_overtime(graph, list_of_lists, color_list, save_name,
                           labels=None, create_gif=False):
    """
    Adds color attribute to network over time.
    
    Parameters
    ----------
    graph : pygraphviz.AGraph
        Network
    list_of_lists : list_like
        List of lists, where the inner list contains the node to add the
        color 
    color_list : list_like
        list of colors for each time point
    save_name : str
        prefix for images to be saved
    labels: list_like
        list of labels to add to graph per sample
    
    Returns
    -------

    """

    if len(list_of_lists) != len(color_list):
        print('Length of list of data must equal len of color list')
        return
    if labels is not None:
        if len(labels) != len(list_of_lists):
            print('Length of labels must be equal to len of data')
            return

    string = 'convert -delay 100 '
    tmp_graph = graph.copy()

    tmp_graph = _check_graphviz(tmp_graph)

    if tmp_graph is None:
        return

    for n, i in enumerate(list_of_lists):
        graph2 = paint_network(tmp_graph, i, color_list[n])

        if labels is not None:
            graph2.graph_attr.update(label=labels[n], fontsize=13)

        s_name = '%s_%04i.png' % (save_name, n)
        graph2.draw(s_name, prog='dot')
        if IPYTHON and _is_running_in_ipython():
            display(Image(s_name))

        string += s_name + ' '
    string1 = string + '  %s.gif' % save_name
    string2 = string + '  %s.pdf' % save_name
    if create_gif:
        os.system(string1)
        os.system(string2)


def paint_network_overtime_up_down(graph, list_up, list_down, save_name,
                                   color_up='red', color_down='blue',
                                   labels=None, create_gif=False):
    """
    Adds color attribute to network over time.

    Parameters
    ----------
    graph : pygraphviz.AGraph
        Network
    list_up : list_like
        List of lists, where the inner list contains the node to add the
        color 
    list_down : list_like
        list of colors for each time point
    color_up : str
        color for first list of species
    color_down : str
        color of second list of species
    save_name : str
        prefix for images to be saved
    labels: list_like
        list of labels to add to graph per sample

    Returns
    -------

    """

    if len(list_up) != len(list_down):
        print('Length of list of data must equal len of color list')
        return
    if labels is not None:
        if len(labels) != len(list_down):
            print('Length of labels must be equal to len of data')
            return
    string = 'convert -delay 100 '
    tmp_graph = graph.copy()
    tmp_graph = _check_graphviz(tmp_graph)

    if tmp_graph is None:
        return

    for n, (up, down) in enumerate(zip(list_up, list_down)):
        graph2 = paint_network(tmp_graph, up, color_up)
        graph2 = paint_network(graph2, down, color_down)
        both = set(up).intersection(set(down))
        graph2 = paint_network(graph2, both, 'yellow')

        if labels is not None:
            graph2.graph_attr.update(label=labels[n], fontsize=13)
        s_name = '%s_%04i.png' % (save_name, n)
        graph2.draw(s_name, prog='dot')
        string += s_name + ' '
        if IPYTHON and _is_running_in_ipython():
            display(Image(s_name))

    string1 = string + '  %s.gif' % save_name
    string2 = string + '  %s.pdf' % save_name
    if create_gif:
        os.system(string1)
        os.system(string2)



def _check_graphviz(network):
    if isinstance(network, nx.DiGraph):
        if pyg is None:
            print("Please install pygraphviz in order to use "
                  "paint_network_overtime_up_down ")
            return

        network = _format_to_directions(network)

    return nx_to_dot(network)


def _is_running_in_ipython():
    """Internal function that determines whether igraph is running inside
    IPython or not."""
    try:
        # get_ipython is injected into the Python builtins by IPython so
        # this should succeed in IPython but throw a NameError otherwise
        get_ipython
        return True
    except NameError:
        return False



def paint_network(graph, list_to_paint, color):
    """
    
    Parameters
    ----------
    graph: pygraphviz.AGraph
    list_to_paint : list_like
        
    color : str

    Returns
    -------

    """
    tmp_g = graph.copy()
    nodes1 = set(tmp_g.nodes())
    for i in list_to_paint:
        if i in nodes1:
            n = tmp_g.get_node(i)
            n.attr['measured'] = 'True'
            n.attr['color'] = 'black'
            n.attr['fillcolor'] = color
            n.attr['style'] = 'filled'
    return tmp_g


def _format_to_directions(network):
    activators = ['activate', 'expression', 'phosphorylate']
    inhibitors = [
        'inhibit', 'repression', 'dephosphorylate', 'deubiquitinate',
        'ubiquitinate'
    ]
    physical_contact = ['binding', 'dissociation', 'stateChange',
                        'compound', 'glycosylation']
    indirect_types = ['indirect']
    for source, target, data in network.edges(data=True):
        if 'interactionType' in data:
            edge_type = data['interactionType']
            for j in activators:
                if j in edge_type:
                    network[source][target]['arrowhead'] = 'normal'
            for j in inhibitors:
                if j in edge_type:
                    network[source][target]['arrowhead'] = 'tee'

            for j in physical_contact:
                if j in edge_type:
                    network[source][target]['dir'] = 'both'
                    network[source][target]['arrowtail'] = 'diamond'
                    network[source][target]['arrowhead'] = 'diamond'

            for j in indirect_types:
                if j in edge_type:
                    network[source][target]['arrowhead'] = 'diamond'
                    network[source][target]['style'] = 'dashed'
    return network


def create_legend(graph):
    """
    adds a legend to a graph
    :param graph:
    :return:
    """
    dict_of_types = {
        'activate': 'onormal',
        'indirect effect': 'odiamondodiamond',
        'expression': 'normal',
        'inhibit': 'tee',
        'binding': 'curve',
        'phosphorylate': 'dot',
        'chemical': 'dotodot',
        'dissociation': 'diamond',
        'ubiquitination': 'oldiamond',
        'state change': 'teetee',
        'dephosphorylation': 'onormal',
        'repression': 'obox',
        'glycosylation': 'dot'
    }
    subgraph = []
    len_dic = len(dict_of_types)
    for n, i in enumerate(dict_of_types):
        subgraph.append(n)
        subgraph.append(n + len_dic)
        graph.add_node(n, label="")
        graph.add_node(n + len_dic, label="")
        graph.add_edge(n, n + len_dic, dir='both', arrowhead=dict_of_types[i],
                       arrowtail="none", label=i)

    graph.add_subgraph(subgraph, name='cluster_legend', rank="LR")


def add_attribute_to_network(graph, list_to_add_attribute, attribute,
                             true_term, false_term='false'):
    """

    Parameters
    ----------
    graph : networkx graph
    list_to_add_attribute : list
        list of nodes in graph to add attribute to
    attribute : str
        attribute to add to graph
    true_term : str
        value to add for the attribute provided True
    false_term : str
        value to add if attribute is false

    Returns
    -------
    out : networkx graph


    >>> from networkx import DiGraph
    >>> from magine.networks.network_tools import add_attribute_to_network
    >>> g = DiGraph()
    >>> g.add_nodes_from(['a', 'b', 'c'])
    >>> new_g = add_attribute_to_network(g, ['a','b'], 'inTest', 'true')
    >>> new_g.node['a']
    {'inTest': 'true'}
    >>> new_g.node['c']
    {'inTest': 'false'}

    """
    tmp_g = graph.copy()
    nodes = set(tmp_g.nodes())
    set_of_positive = set(list_to_add_attribute)
    for i in nodes:
        if i in set_of_positive:
            tmp_g.node[i][attribute] = true_term
        else:
            tmp_g.node[i][attribute] = false_term

    return tmp_g


def append_attribute_to_network(graph, list_to_add_attribute, attribute,
                                true_term, delimiter=''):
    """

    Parameters
    ----------
    graph : networkx graph
    list_to_add_attribute : list
        list of nodes in graph to add attribute to
    attribute : str
        attribute to add to graph
    true_term : str
        value to add for the attribute provided True
    delimiter : str


    Returns
    -------
    out : networkx graph


    >>> from networkx import DiGraph
    >>> from magine.networks.network_tools import append_attribute_to_network
    >>> g = DiGraph()
    >>> g.add_nodes_from(['a'])
    >>> new_g = append_attribute_to_network(g, ['a'], 'attribute', 'one')
    >>> new_g.node['a']
    {'attribute': 'one'}
    >>> new_g = append_attribute_to_network(new_g, ['a'], 'attribute', 'two', delimiter=',')
    >>> new_g.node['a']
    {'attribute': 'one,two'}

    """
    tmp_g = graph.copy()
    nodes = set(tmp_g.nodes())
    set_of_positive = set(list_to_add_attribute)
    for i in nodes:
        if i in set_of_positive:
            if attribute in tmp_g.node[i].keys():
                new_attr = tmp_g.node[i][attribute] + delimiter + true_term
                tmp_g.node[i][attribute] = new_attr
            else:
                tmp_g.node[i][attribute] = true_term

    return tmp_g


def trim_sink_source_nodes(network, list_of_nodes, remove_self_edge=False):
    """
    Trim graph by removing nodes that are not in provided list if source/sink


    Parameters
    ----------
    network : networkx.DiGraph
    list_of_nodes : list_like
        list of species that are important if sink/source
    remove_self_edge : bool
        Remove self edges
    Returns
    -------

    """
    tmp_network = network.copy()
    if remove_self_edge:
        tmp_network = remove_self_edges(tmp_network)
    tmp1 = _trim(tmp_network, list_of_nodes)
    tmp2 = _trim(tmp_network, list_of_nodes)
    while tmp1 != tmp2:
        tmp2 = tmp1
        tmp1 = _trim(tmp_network, list_of_nodes)
    return tmp_network


def remove_self_edges(network):
    tmp_network = network.copy()
    tmp_network.remove_edges_from(tmp_network.selfloop_edges())
    return tmp_network


def _trim(network, list_of_nodes):
    list_of_nodes = set(list_of_nodes)
    found, not_found = 0., 0.
    nodes = set(network.nodes())
    in_dict = network.in_degree(nbunch=nodes)
    out_dict = network.out_degree(nbunch=nodes)
    for i in nodes:
        if i in list_of_nodes:
            found += 1
        else:
            if in_dict[i] == 1 and out_dict[i] == 0:
                network.remove_node(i)
            elif in_dict[i] == 0 and out_dict[i] == 1:
                network.remove_node(i)
            else:
                not_found += 1

    len_nodes = len(network.nodes())
    print("{} found, {} not found".format(found, not_found))
    print("{}% of {} nodes".format(found / len_nodes * 100, len_nodes))
    return len_nodes


def subtract_network_from_network(net1, net2):
    """
    subtract one network from another

    Parameters
    ----------
    net1 : networkx.DiGraph
    net2 : networkx.DiGraph

    Returns
    -------
    networkx.DiGraph

    """
    copy_graph1 = net1.copy()
    nodes1 = set(net1.nodes())
    nodes2 = set(net2.nodes())
    overlap = nodes2.intersection(nodes1)
    return copy_graph1.remove_edges_from(overlap)


def compress_edges(graph):
    """
    compress edges of networks by finding common paths

    Parameters
    ----------
    graph: networkx.DiGraph

    Returns
    -------

    """

    g = graph.copy()
    nodes = set(g.nodes())
    neighbor_dict = {}
    for n in nodes:
        neigh = tuple(g.neighbors(n))
        if tuple(neigh) in neighbor_dict:
            neighbor_dict[tuple(neigh)].append(n)
        else:
            neighbor_dict[tuple(neigh)] = []
            neighbor_dict[tuple(neigh)].append(n)

    for i in neighbor_dict:
        neigh = neighbor_dict[i]
        # print(i,neigh)
        if len(i) != 1:
            continue
        if len(neigh) == 1:
            continue
        interaction_types = {}
        for j in neighbor_dict[i]:
            if g.has_edge(i[0], j):
                direction = 'type1'
                edge = g.get_edge(i[0], j)
            elif g.has_edge(j, i[0]):
                direction = 'type2'
                edge = g.get_edge(j, i[0])
            edge_type = edge.attr['arrowhead']
            if edge_type + direction in interaction_types:
                interaction_types[edge_type + direction].append(j)
            else:
                interaction_types[edge_type + direction] = []
                interaction_types[edge_type + direction].append(j)
        for k in interaction_types:
            if len(interaction_types[k]) > 1:
                # print(i[0],'->',)
                to_join = []
                for each in interaction_types[k]:
                    if len(g.neighbors(each)) == 1:
                        to_join.append(each)
                # print(to_join,k)
                if len(to_join) > 1:
                    label = "{"
                    for node in to_join:
                        g.remove_node(node)
                        label += ' %s |' % str(node)
                    label = label[:-1]
                    label += "}"
                    # print(label)
                    g.add_node(label, shape='record', label=label)
                    if k.endswith('type2'):
                        g.add_edge(label, i[0], dir='both', arrowhead=k[:-5],
                                   arrowtail="none")
                    elif k.endswith('type1'):
                        g.add_edge(i[0], label, dir='both', arrowhead=k[:-5],
                                   arrowtail="none")
    return g


def merge_nodes(graph):
    """ merges nodes into single node if same neighbors

    Parameters
    ----------
    graph: nx.DiGraph

    Returns
    -------
    nx.DiGraph
    """
    neighbors2node = dict()

    nodes = set(graph.nodes())
    edges = set(graph.edges())

    new_g = graph.copy()
    for i in nodes:
        down = '|'.join(sorted(graph.successors(i)))
        up = '|'.join(sorted(graph.predecessors(i)))

        if (down, up) in neighbors2node:
            neighbors2node[(down, up)].add(i)
        else:
            neighbors2node[(down, up)] = {i}

    for node, neigh in neighbors2node.items():
        # print(node, neigh)
        if len(neigh) > 1:
            print(node, neigh)
            new_name = '|'.join(sorted(neigh))
            for x in node[0].split('|'):
                if x != '':
                    for n in neigh:
                        if (x, n) in edges:
                            new_g.remove_edge(x, n)
                            new_g.add_edge(x, new_name, **graph.edge[x][n])
                            edges.remove((x, n))

            for x in node[1].split('|'):
                if x != '':
                    for n in neigh:
                        if (n, x) in edges:
                            new_g.remove_edge(n, x)
                            new_g.add_edge(new_name, x, **graph.edge[n][x])
                            edges.remove((n, x))
    print(
        "{} nodes and {} edges".format(len(graph.nodes()), len(graph.edges())))
    print(
        "{} nodes and {} edges".format(len(new_g.nodes()), len(new_g.edges())))
    for n in new_g.nodes():
        if len(new_g.successors(n)) == 0 and len(new_g.predecessors(n)) == 0:
            new_g.remove_node(n)

    print(
        "{} nodes and {} edges".format(len(new_g.nodes()), len(new_g.edges())))
    return new_g


def remove_unmeasured_nodes(graph, measured):
    new_g = graph.copy()
    edge_info_dict = dict()
    for i, j, data in graph.edges(data=True):
        edge_info_dict[(i, j)] = data
    nodes = set(graph.nodes())
    include = set(measured)
    include.intersection_update(nodes)

    # for i, j in :
    def find(d):
        i, j = d
        paths = []
        if nx.has_path(graph, i, j):
            for p in nx.all_shortest_paths(graph, i, j):
                path = []
                label = []
                for n in p:
                    if n in include:
                        path.append(n)
                    else:
                        label.append(n)
                if len(path) == 2:
                    paths.append((path, '|'.join(l for l in label)))
        return paths

    x = mp.Pool(4)
    paths = x.map(find, itertools.combinations(include, 2))
    to_remove = set()
    for p in paths:
        if len(p) != 2:
            continue
        for path, label in p:
            print(path, label)
            for n in label.split('|'):
                to_remove.add(n)
            new_g.add_edge(path[0], path[1], label=label)
    for n in to_remove:
        new_g.remove_node(n)
    return new_g


def print_network_stats(network, exp_data):
    """

    Parameters
    ----------
    network : nx.DiGraph
    exp_data : magine.data.datatypes.ExperimentalData

    Returns
    -------

    """
    nodes = set(network.nodes())
    g_nodes = set()
    m_nodes = set()
    for i, d in network.nodes(data=True):

        if 'speciesType' not in d:
            print("Doesn't have species type... {} = {}".format(i, d))
            continue
        if d['speciesType'] == 'gene':
            g_nodes.add(i)
        elif d['speciesType'] == 'compound' or d[
            'speciesType'] == 'metabolite':
            m_nodes.add(i)
        else:
            g_nodes.add(i)
            print(i, d)

    total_species = set(exp_data.list_species)
    sig_total_species = set(exp_data.list_sig_species)
    sig_genes = set(exp_data.list_sig_proteins)
    genes = set(exp_data.list_proteins)
    sig_met = set(exp_data.list_sig_metabolites)
    met = set(exp_data.list_metabolites)
    n_measured = len(nodes.intersection(total_species))
    n_genes = len(nodes.intersection(sig_genes))
    n_meta = len(nodes.intersection(sig_met))
    n_sig_measured = len(nodes.intersection(sig_total_species))
    n_nodes = len(nodes)
    st = ''
    st += 'Number of nodes = {}\n'.format(n_nodes)
    st += 'Number of edges = {}\n'.format(len(network.edges()))
    st += "Number of total nodes measured = {}\n".format(n_measured)
    st += "Fraction of total nodes measured = {}\n".format(
        100. * n_measured / n_nodes)
    st += "Number of total nodes sig. changed = {}\n".format(n_sig_measured)
    st += "Fraction of total nodes sig. changed = {}\n".format(
        100. * n_sig_measured / n_nodes)
    st += "Number of protein nodes sig. changed = {}\n".format(n_genes)
    st += "Fraction of protein nodes measured = {}\n".format(
        100. * n_genes / len(g_nodes))
    st += "Number of metabolite nodes sig. changed = {}\n".format(n_meta)
    st += "Fraction of total nodes measured = {}\n".format(
        100. * n_meta / len(m_nodes))

    print(st)


def add_pvalue_and_fold_change():
    # -log10pvalue,
    # # log2fold_change,
    return


def _add_nodes(old_network, new_network):
    new_nodes = set(new_network.nodes())
    for i, data in old_network.nodes_iter(data=True):
        if i not in new_nodes:
            new_network.add_node(i, **data)
        else:
            existing_info = new_network.node[i]
            for n, d in data.items():
                if n not in existing_info:
                    new_network.node[i][n] = d
                else:
                    additions = set(d.split('|'))
                    if isinstance(existing_info[n], list):
                        old = set(existing_info[n][0].split('|'))
                    else:
                        old = set(existing_info[n].split('|'))
                    additions.update(old)
                    new_network.node[i][n] = '|'.join(sorted(additions))


def _add_edges(current_network, new_network):
    edges = set(new_network.edges())
    for i, j, data in current_network.edges_iter(data=True):
        if (i, j) not in edges:
            new_network.add_edge(i, j, **data)
        else:
            existing_info = new_network.edge[i][j]
            for n, d in data.items():
                if n not in existing_info:
                    new_network[i][j][n] = d
                else:
                    additions = set(d.split('|'))
                    additions.update(set(existing_info[n].split('|')))
                    new_network[i][j][n] = '|'.join(sorted(additions))


def compose(g, g_1):
    """Return a new graph of G composed with H.

    Composition is the simple union of the node sets and edge sets.
    The node sets of G and H do not need to be disjoint.

    Parameters
    ----------
    g, : nx.DiGraph
    g_1 : nx.DiGraph
       A NetworkX graph

    Returns
    -------
    C: A new graph  with the same type as G

    """

    # new_g = G.copy()
    new_g = nx.DiGraph()

    _add_nodes(g, new_g)
    _add_nodes(g_1, new_g)

    _add_edges(g, new_g)
    _add_edges(g_1, new_g)

    return new_g


def compose_all(graphs):
    """Return the composition of all graphs.

    Composition is the simple union of the node sets and edge sets.
    The node sets of the supplied graphs need not be disjoint.

    Parameters
    ----------
    graphs : list
       List of NetworkX graphs

    Returns
    -------
    C : A graph with the same type as the first graph in list

    """
    graphs = iter(graphs)
    g = next(graphs)
    for h in graphs:
        g = compose(g, h)
    return g


_maps = {
    'activation': 'activate',
    'activator': 'activate',
    'potentiator': 'activate',

    'inducer': 'expression',
    'stimulator': 'expression',
    'suppressor': 'repression',

    'blocker': 'inhibit',
    'inhibitor': 'inhibit',
    'inhibition': 'inhibit',
    'inhibitor, competitive': 'inhibit',

    'proteolytic processing': 'cleavage',

    # binding
    'binding/association': 'binding',
    'binder': 'binding',
    'complex': 'binding',
    'dissociation': 'binding',

    # indirect/missing
    'indirect effect': 'indirect',
    'missing interaction': 'indirect',

    'state change': 'stateChange',

    'ubiquitination': 'ubiquitinate',
    'methylation': 'methylate',
    'glycosylation': 'glycosylate',
    'sumoylation': 'sumoylate',
    'ribosylation': 'ribosylate',
    'neddylation': 'neddylate',
    'desumoylation': 'desumoylate',
    'deneddylation': 'deneddylate',
    'demethylation': 'demethylate',
    'deacetylation': 'deacetylate',
    'desensitize the target': 'inhibit',
    'deubiquitination': 'deubiquitinate',
    'nedd(rub1)ylation': 'neddy(rub1)late',

    'dephosphorylation': 'dephosphorylate',
    'phosphorylation': 'phosphorylate',

    'negative modulator': 'inhibit',
    'inhibitory allosteric modulator': 'allosteric|inhibit',
    'allosteric modulator': 'allosteric|modulate',
    'positive allosteric modulator': 'activate|allosteric',
    'positive modulator': 'activate',
    'partial agonist': 'activate|chemical',
    'inverse agonist': 'activate|chemical',
    'agonist': 'activate|chemical',

    'antagonist': 'inhibit|chemical',
    'partial antagonist': 'inhibit|chemical',

    # chemical related
    'compound': 'chemical',
    'product of': 'chemical',
    'ligand': 'chemical',
    'cofactor': 'chemical',
    'multitarget': 'chemical',
}


def standardize_edge_types(network):
    to_remove = set()
    for source, target, data in network.edges_iter(data=True):
        if 'interactionType' in data:
            edge_type = data['interactionType']
            edge_type = set(i for i in edge_type.split('|'))

            for k, v in _maps.items():
                if k in edge_type:
                    edge_type.remove(k)
                    edge_type.add(v)
            for i in ['', ' ']:
                if i in edge_type:
                    edge_type.remove(i)

            if 'reaction' in edge_type:
                if len(edge_type) != 1:
                    edge_type.remove('reaction')
            if 'catalyze' in edge_type:
                if len(edge_type) != 1:
                    edge_type.remove('catalyze')
            edge_type = '|'.join(sorted(edge_type))
            if edge_type == '':
                # network.remove_edge(source, target)
                to_remove.add((source, target))
            else:
                network[source][target]['interactionType'] = edge_type
    for source, target in to_remove:
        network.remove_edge(source, target)

if __name__ == '__main__':
    g = nx.DiGraph()
    g.add_edge('A', 'B')
    g.add_edge('B', 'C')
    g.add_edge('B', 'E')
    g.add_edge('C', 'D')
    # test_g = remove_unmeasured_nodes(g, ['A', 'D', 'E'])
    # export_to_dot(test_g, 'merged_node')
    # new_g = remove_unmeasured_nodes(g, ['A', 'C', 'D'])
    # export_to_dot(new_g, 'merged_node2')
    g = nx.DiGraph()
    g.add_node('A', color='red', intType='ugly')
    g.add_edge('A', 'B', iType='no')
    gg = nx.DiGraph()
    gg.add_node('A', color='green', intType='ugly')
    gg.add_edge('A', 'B', iType='yes')
    fg = compose(g, gg)
    for i in fg.nodes(data=True):
        print(i)
    for i in fg.edges(data=True):
        print(i)
