import requests
import networkx
import community
import matplotlib.pyplot as plt
from time import sleep
from config import *

g = networkx.Graph()

names = dict()

source_id = 92137731
x0 = requests.get('https://api.vk.com/method/users.get?user_ids={}&fields=first_name,last_name&access_token={}&v=5.124'.format(source_id, secret))
x1 = requests.get('https://api.vk.com/method/friends.get?user_id={}&fields=first_name,last_name,deactivated,can_access_closed,blacklisted&access_token={}&v=5.124'.format(source_id, secret))
g.add_node(source_id, fname = x0.json()['response'][0]['first_name'], lname = x0.json()['response'][0]['last_name'])
for x in x1.json()['response']['items'] :
    if not 'deactivated' in x and x['blacklisted'] == 0 and x['can_access_closed']:
        g.add_node(x['id'], fname = x['first_name'], lname = x['last_name'])
        names[x['id']] = x['first_name'] + ' ' + x['last_name']
        g.add_edge(source_id, x['id'])

for i in range(1, len(g.nodes), 100):
    friends = ','.join(map(str, list(g.nodes)[i:i+100]))
    x2 = requests.get('https://api.vk.com/method/friends.getMutual?source_uid={}&target_uids={}&&access_token={}&v=5.124'.format(source_id, friends, secret))
    if 'error' in x2.json():
        print(x2.text)
    for curr in x2.json()['response']:
        for comm in curr['common_friends']:
            if comm in g.nodes:
                g.add_edge(curr['id'], comm)
    sleep(0.2)


rm_nodes = set()
for v in g.nodes:
    if g.degree[v] == 1:
        rm_nodes.add(v)
for v in rm_nodes:
    g.remove_node(v)
    names.pop(v)

colors_used = 1
col_for_draw = []
stat = []
colors = {}
dend = community.generate_dendrogram(g)
print(dend)
for i in range(len(dend)):
    if i == 0:
        for v in g.nodes:
            col_for_draw.append(dend[i][v])
            if (dend[i][v] != 0):
                stat.append(0)
            else:
                stat.append(1)
    else:
        for j in range(len(g.nodes)):
            if (stat[j] == 0 and dend[i][col_for_draw[j]] != 0):
                col_for_draw[j] = dend[i][col_for_draw[j]]
            elif (stat[j] == 0 and dend[i][col_for_draw[j]] == 0):
                if col_for_draw[j] not in colors:
                    colors_used += 1
                    colors[col_for_draw[j]] = colors_used
                stat[j] = colors[col_for_draw[j]]
    colors = {}
    print(col_for_draw)
    print(stat)
    print('')
for j in range(len(g.nodes)):
    if (stat[j] == 0):
        if col_for_draw[j] not in colors:
            colors_used += 1
            colors[col_for_draw[j]] = colors_used
        stat[j] = colors[col_for_draw[j]]
print(col_for_draw)
print(stat)
print('')

clusters = list(set() for i in range(colors_used))
j = 0
for v in g.nodes:
    clusters[stat[j] - 1].add(v)
    j += 1
j = 0
for cl in clusters:
    j += 1
    print(str(j) + ':')
    for pers in cl:
        print(g.nodes[pers]['fname']+' '+g.nodes[pers]['lname'])
    print('')

networkx.draw(g, with_labels=True, labels = names, font_size=8, font_color='red', width=0.5, node_size=50, node_color = stat, cmap = 'rainbow')
plt.show()