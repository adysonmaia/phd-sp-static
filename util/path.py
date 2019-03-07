# Python Program for Floyd Warshall Algorithm
# This code is contributed by Nikhil Kumar Singh(nickzuck_007)

INF = float("inf")


def calc_net_delay(graph):
    return floyd_warshall(graph)


# Solves all pair shortest path via Floyd Warshall Algorithm
def floyd_warshall(graph):
    # https://www.geeksforgeeks.org/dynamic-programming-set-16-floyd-warshall-algorithm/
    dist = [[j for j in i] for i in graph]

    nodes = range(len(graph))
    for k in nodes:
        for i in nodes:
            for j in nodes:
                dist[i][j] = min(dist[i][j], dist[i][k] + dist[k][j])
    return dist


# A utility function to print the solution
# def print_solution(dist):
#     print "Following matrix shows the shortest distances\
#  between every pair of vertices"
#     nb_nodes = len(dist)
#     nodes = range(nb_nodes)
#     for i in nodes:
#         for j in nodes:
#             if(dist[i][j] == INF):
#                 print "%7s" % ("INF"),
#             else:
#                 print "%7d\t" % (dist[i][j]),
#             if j == nb_nodes-1:
#                 print ""
