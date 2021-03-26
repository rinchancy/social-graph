import requests
import networkx
import community
import matplotlib.pyplot as plt
from time import sleep
from config import *

g = networkx.Graph()

data = {}
city_base = {}

# add all nodes + their data
source_id = 153351578
x0 = requests.get('https://api.vk.com/method/users.get?user_ids={}&fields=first_name,last_name,'
                  'career,city,schools,universities&access_token={}&v=5.124'.format(source_id, secret))
x1 = requests.get('https://api.vk.com/method/friends.get?user_id={}&fields=first_name,last_name,deactivated,can_access_closed,blacklisted,'
                  'career,city,schools,universities&access_token={}&v=5.124'.format(source_id, secret))
me = x0.json()['response'][0]
g.add_node(source_id, fname=me['first_name'], lname=me['last_name'])
data[me['id']] = {}
if 'city' in me:
    data[me['id']]['city'] = me['city']['title']
else:
    data[me['id']]['city'] = ''
if 'career' in me:
    data[me['id']]['career'] = me['career']
else:
    data[me['id']]['career'] = []
if 'universities' in me:
    data[me['id']]['universities'] = me['universities']
else:
    data[me['id']]['universities'] = []
if 'schools' in me:
    data[me['id']]['schools'] = me['schools']
else:
    data[me['id']]['schools'] = []
for x in x1.json()['response']['items']:
    if not 'deactivated' in x and x['blacklisted'] == 0 and x['can_access_closed']:
        g.add_node(x['id'], fname=x['first_name'], lname=x['last_name'])
        g.add_edge(source_id, x['id'])
        data[x['id']] = {}
        if 'city' in x:
            data[x['id']]['city'] = x['city']['title']
        else:
            data[x['id']]['city'] = ''
        if 'career' in x:
            data[x['id']]['career'] = x['career']
        else:
            data[x['id']]['career'] = []
        if 'universities' in x:
            data[x['id']]['universities'] = x['universities']
        else:
            data[x['id']]['universities'] = []
        if 'schools' in x:
            data[x['id']]['schools'] = x['schools']
        else:
            data[x['id']]['schools'] = []

# add edges between friends
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

# remove lonely nodes
rm_nodes = set()
for v in g.nodes:
    if g.degree[v] == 1:
        rm_nodes.add(v)
for v in rm_nodes:
    g.remove_node(v)

# coloring saved to stat
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
for j in range(len(g.nodes)):
    if (stat[j] == 0):
        if col_for_draw[j] not in colors:
            colors_used += 1
            colors[col_for_draw[j]] = colors_used
        stat[j] = colors[col_for_draw[j]]
i = 0
stat_dict = {}
for v in g.nodes:
    stat_dict[v] = stat[i]
    i += 1

# form clusters
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

# get all groups
all_groups = dict()
i = 0
print('Getting groups info for following clusters:')
for cl in clusters:
    print('Cluster', i+1, 'of', len(clusters))
    for v in cl:
        tmp = requests.get(
            'https://api.vk.com/method/groups.get?user_id={}&extended=1&fields=name&access_token={}&v=5.124'.format(v, secret))
        sleep(0.3)
        if tmp.status_code != 200:
            tmp = requests.get(
                'https://api.vk.com/method/users.getSubscriptions?user_id={}&extended=1&fields=name&access_token={}&v=5.124'.format(v, secret))
            sleep(0.3)
        for item in tmp.json()['response']['items']:
            if 'name' in item:
                gr_name = item['name']
            else:
                gr_name = item['last_name'] + ' ' + item['first_name']
            if gr_name not in all_groups:
                all_groups[gr_name] = [0] * len(clusters)
            all_groups[gr_name][i] += 1
    i += 1
av_groups = [0] * len(all_groups)
j = 0
for gr in all_groups.keys():
    av_groups[j] = sum(all_groups[gr]) / len(g.nodes)
    for i in range(len(clusters)):
        all_groups[gr][i] = all_groups[gr][i]/len(clusters[i])
    j += 1
# find best fitting groups
best_groups = []
for i in range(len(clusters)):
    a = dict()
    best_groups.append(a)
i = 0
for gr in all_groups.keys():
    if max(all_groups[gr]) - av_groups[i] >= 0.15:
        m = max(all_groups[gr])
        mms = [k for k, j in enumerate(all_groups[gr]) if j == m]
        for mm in mms:
            if all_groups[gr][mm] * len(clusters[mm]) >= 3:
                best_groups[mm][gr] = round(m - av_groups[i], 4)
    i += 1
best_res = []
for cl in best_groups:
    best_res.append(dict(sorted(cl.items(), key=lambda item: -item[1])))

# find common
i = 1
for cl in clusters:
    city_dict = {}
    car_dict = {}
    uni_dict = {}
    fac_dict = {}
    sch_dict = {}
    for v in cl:
        a = data[v]['city']
        b = data[v]['career']
        c = data[v]['universities']
        d = data[v]['schools']
        if a != '':
            if a not in city_dict:
                city_dict[a] = 1
            else:
                city_dict[a] += 1
        for bb in b:
            if 'company' in bb:
                bbb = bb['company']
            elif 'group_id' in bb:
                tmp = requests.get(
                    'https://api.vk.com/method/groups.getById?group_id={}&fields=name&access_token={}&v=5.124'.format(bb['group_id'], secret))
                sleep(0.3)
                bbb = tmp.json()['response'][0]['name']
            if bbb not in car_dict:
                car_dict[bbb] = 1
            else:
                car_dict[bbb] += 1
        for cc in c:
            ccc = cc['name']
            if 'faculty_name' in cc:
                cccc = cc['name'] + ' ' + cc['faculty_name']
            else:
                cccc = 'None'
            if ccc not in uni_dict:
                uni_dict[ccc] = 1
            else:
                uni_dict[ccc] += 1
            if cccc != 'None' and cccc not in fac_dict:
                fac_dict[cccc] = 1
            elif cccc != 'None':
                fac_dict[cccc] += 1
        for dd in d:
            if dd['city'] not in city_base:
                tmp = requests.get(
                    'https://api.vk.com/method/database.getCitiesById?city_ids={}&fields=title&access_token={}&v=5.124'.format(dd['city'], secret))
                sleep(0.3)
                ddd = dd['name'] + ' ' + tmp.json()['response'][0]['title']
            else:
                ddd = dd['name'] + ' ' + city_base[dd['city']]
            if ddd not in sch_dict:
                sch_dict[ddd] = 1
            else:
                sch_dict[ddd] += 1
    sorted_city = sorted(city_dict.items(), key=lambda z: -z[1])
    sorted_car = sorted(car_dict.items(), key=lambda z: -z[1])
    sorted_uni = sorted(uni_dict.items(), key=lambda z: -z[1])
    sorted_fac = sorted(fac_dict.items(), key=lambda z: -z[1])
    sorted_sch = sorted(sch_dict.items(), key=lambda z: -z[1])
    if len(cl) > 5:  # big clusters
        print('Prediction for cluster ' + str(i) + ' (big):')
        print('___Cities:')
        for x in sorted_city:
            if x[1] >= 3 and round(x[1] / len(cl) * 100) >= 40:  # at least 3 and more than 40%
                print(x[0] + ' ' + str(round(x[1] / len(cl) * 100)) + '%')
            else:
                break
        print('___Career:')
        for x in sorted_car:
            if x[1] >= 2 and round(x[1] / len(cl) * 100) >= 2:  # at least 2 and more than 2%
                print(x[0] + ' ' + str(round(x[1] / len(cl) * 100)) + '%')
            else:
                break
        print('___University:')
        for x in sorted_uni:
            if x[1] >= 3 and round(x[1] / len(cl) * 100) >= 33:  # at least 3 and more than 33%
                print(x[0] + ' ' + str(round(x[1] / len(cl) * 100)) + '%')
            else:
                break
        for x in sorted_fac:
            if x[1] >= 3 and round(x[1] / len(cl) * 100) >= 2:  # at least 3 and more than 2%
                print(x[0] + ' ' + str(round(x[1] / len(cl) * 100)) + '%')
            else:
                break
        print('___School:')
        for x in sorted_sch:
            if x[1] >= 3 and round(x[1] / len(cl) * 100) >= 5:  # at least 3 and more than 5%
                print(x[0] + ' ' + str(round(x[1] / len(cl) * 100)) + '%')
            else:
                break
        print('___Interests:')
        for gr in best_res[i-1].keys():
            print(gr, f'{round(100 * best_res[i - 1][gr], 2)}% more than average')
        print('')
    else:  # small clusters (2-5 persons)
        print('Prediction for cluster ' + str(i) + ' (small):')
        print('___Cities:')
        for x in sorted_city:
            if x[1] >= 2:  # at least 2
                print(x[0] + ' ' + str(round(x[1] / len(cl) * 100)) + '%')
            else:
                break
        print('___Career:')
        for x in sorted_car:
            if x[1] >= 2:  # at least 2
                print(x[0] + ' ' + str(round(x[1] / len(cl) * 100)) + '%')
            else:
                break
        print('___University:')
        for x in sorted_uni:
            if x[1] >= 2:  # at least 2
                print(x[0] + ' ' + str(round(x[1] / len(cl) * 100)) + '%')
            else:
                break
        for x in sorted_fac:
            if x[1] >= 2:  # at least 2
                print(x[0] + ' ' + str(round(x[1] / len(cl) * 100)) + '%')
            else:
                break
        print('___School:')
        for x in sorted_sch:
            if x[1] >= 2:  # at least 2
                print(x[0] + ' ' + str(round(x[1] / len(cl) * 100)) + '%')
            else:
                break
        print('___Interests:')
        for gr in best_res[i - 1].keys():
            print(gr, f'{round(100 * best_res[i - 1][gr], 2)}% more than average')
        print('')
    i += 1

#count groups

# draw social graph
networkx.draw(g, with_labels=True, labels=stat_dict, font_size=6, font_color='black', width=0.5, node_size=50, node_color=stat, cmap='rainbow')
plt.show()
