#!/usr/bin/env python
# -*- encoding: utf-8 -*-

# Copyright 2016 Tungee, Inc
# f**k slide challenge

import random
import json
import copy


with open('./doubanbook/libs/slide_db.json', 'r') as f:
    db = json.load(f)


def gen_random_a_array(pos):
    ret = []
    time = 0
    step = 0
    y = 0
    v = 0
    a = 0

    # 初始位置

    ret.append([
        random.randint(-29, -11),
        random.randint(-29, -11),
        0
    ])

    # 鼠标点击

    ret.append([
        step,
        y,
        time
    ])

    # 模拟初始阶段

    while step < pos:
        if random.random() > 0.5:
            y += random.randint(-1, 1)
        # 前半部分加速，后半部减速
        if step < pos / 2:
            a = random.random() * 0.0005 + 0.00001
        else:
            a = -random.random() * 0.0005 - 0.00001
        time_delta = random.randint(20, 150)
        time += time_delta
        v += a * time_delta
        step += int(max(1, round(v * time_delta)))
        # 添加噪声
        ret.append([
            step + random.randint(-1, 1),
            y,
            time
        ])

    # 模拟瞄准阶段

    max_aim = random.randint(3, 8)
    aim = 0
    shake = 0

    while aim < max_aim:
        shake = random.randint(0, 1)
        time_delta = random.randint(20, 150)
        time += time_delta
        aim += 1
        ret.append([
            pos + shake,
            y,
            time
        ])

    # 最终结果

    ret.append([
        pos,
        y,
        time
    ])

    return ret


def gen_random_p_array(pos):
    ret = []
    time = 0
    step = 0
    y = 0
    v = 0
    a = 0

    # 初始位置

    ret.append([
        random.randint(-29, -11),
        random.randint(-29, -11),
        0
    ])

    # 鼠标点击

    ret.append([
        step,
        y,
        time
    ])

    # 模拟初次无目的移动

    print ret

    target = random.randint(10, 200)
    move_max = random.randint(1, 3)
    v = random.random() * 0.04 + 0.01
    move = 0
    while step < target and move < move_max:
        s = random.randint(1, 5)
        step += s
        move += 1
        time += int(s / v)
        if random.random() > 0.8:
            y += random.randint(-1, 1)
        ret.append([
            step,
            y,
            time
        ])

    print ret

    # 模拟多次瞄准移动

    aim = 0
    aim_max = random.randint(1, 2)
    # v = random.random() * 0.0004 + 0.0001
    while aim < aim_max:
        if aim == aim_max - 1:
            target = pos
        else:
            target = pos + random.randint(-50, 50)
            target = min(200, target)
            target = max(0, target)
        while abs(target - step) > 0:
            a = (random.random() * 0.0005 + 0.0001) / (target - step)
            max_s = max(1, int(min(4, abs(target - step) / 5)))
            s = (target - step) / abs(target - step) * \
                max(1, random.randint(0, max_s))
            step += s
            time_delta = int((pow(v * v + 2 * a * s, 0.5) - v) / a)
            v += a * time_delta
            time_delta = random.randint(40, 80)
            time += time_delta
            if random.random() > 0.8:
                y += random.randint(-1, 1)
            print 'step=%d, s=%d a=%f v=%f time_delta=%f' % (step, s, a, v, time_delta)
            ret.append([
                step,
                y,
                time
            ])
        aim += 1

    # 最终结果

    time += random.randint(200, 500)
    ret.append([
        pos,
        y,
        time
    ])

    print ret

    return ret


def gen_pos_i_array(pos):
    arr_a = None
    arr_b = None
    arr_c = []
    print pos

    while not arr_a:
        random_a = pos + random.randint(-50, 50)
        arr_a = db.get(str(random_a), None)
    while not arr_b:
        random_b = pos + random.randint(-50, 50)
        arr_b = db.get(str(random_b), None)
    time_a = arr_a[-1][2]
    time_b = arr_b[-1][2]
    time_c = max(500, (time_a + time_b) / 2 + random.randint(-1000, 1000))
    child_progress = 0.0
    print arr_a
    print arr_b
    while child_progress < 1:
        delta = random.random() * 0.20
        if random.random() < 0.5:
            parent = arr_a
        else:
            parent = arr_b
        parent_progress = 0.0
        parent_time = parent[-1][2]
        parent_pos = parent[-1][0]

        # 基因突变之倒序
        invert = False
        if random.random() < 0.05 and child_progress + delta < 1:
            invert = True

        # 基因突变之整体偏移
        offset = 0
        if random.random() < 0.05 and child_progress + delta < 1:
            offset = random.randint(-20, 20)

        for i in xrange(0, len(parent)):
            parent_progress = float(parent[i][2]) / parent_time
            if parent_progress > child_progress + delta:
                break
            elif parent_progress >= child_progress:
                j = i
                if invert:
                    j = -i - 1
                x = int(float(parent[j][0]) / parent_pos * pos)
                # 基因突变之单体突变
                shake = 0
                if random.random() < 0.01 and parent_progress < 1:
                    shake = random.randint(-10, 10)
                arr_c.append([
                    x + offset + shake,
                    parent[j][1],
                    int(float(parent[i][2]) / parent_time * time_c)
                ])
        child_progress += delta

    print arr_c

    return arr_c


def report_true(pos, arr):
    db[str(pos)] = arr


def gen_pos_array(pos):
    # if str(pos) in db:
    #     ret = copy.deepcopy(db[str(pos)])
    #     for i in range(2, len(ret) - 3):
    #         ret[i][0] += random.randint(-2, 2)
    #         ret[i][2] += random.randint(-5, 5)
    #     return ret

    # return gen_random_a_array(pos)
    # return gen_random_p_array(pos)
    return gen_pos_i_array(pos)


def encode_pos(a, b):
    c = b[32:]
    d = []
    e = 0
    while e < len(c):
        f = ord(c[e])
        d.append(f - 87 if f > 57 else f - 48)
        e += 1
    c = 36 * d[0] + d[1]
    g = int(round(a) + c)
    b = b[0:32]
    h = None
    i = [[], [], [], [], []]
    j = {}
    k = 0
    e = 0
    l = len(b)
    while e < l:
        h = b[e]
        if h not in j:
            j[h] = 1
            i[k].append(h)
            k += 1
            k = 0 if 5 == k else k
        e += 1
    m = None
    n = g
    o = 4
    p = ''
    q = [1, 2, 5, 10, 50]
    while n > 0:
        if n - q[o] >= 0:
            m = int(random.random() * len(i[o]))
            p += i[o][m]
            n -= q[o]
        else:
            i = i[0:o] + i[o + 1:-1]
            q = q[0:o] + q[o + 1:-1]
            o -= 1
    return p


def c(a):
    b = None
    c = None
    d = None
    e = []
    f = 0
    g = []
    h = 0
    i = len(a) - 1
    while h < i:
        b = round(a[h + 1][0] - a[h][0])
        c = round(a[h + 1][1] - a[h][1])
        d = round(a[h + 1][2] - a[h][2])
        g.append([b, c, d])
        if 0 == b and 0 == c and 0 == d:
            pass
        elif 0 == b and 0 == c:
            f += d
        else:
            e.append([b, c, d + f])
            f = 0
        h += 1
    if (0 != f):
        e.append([b, c, f])
    return e


def d(a):
    b = '()*,-./0123456789:?@ABCDEFGHIJKLMNOPQRSTUVWXYZ_abcdefghijklmnopqr'
    c = len(b)
    d = ''
    e = abs(a)
    f = int(e / c)
    if f >= c:
        f = c - 1
    if f:
        d = b[f]
    e %= c
    g = ""
    if a < 0:
        g += "!"
    if d:
        g += "$"
    return g + d + b[int(e)]


def e(a):
    b = [[1, 0], [2, 0], [1, -1], [1, 1], [0, 1], [0, -1], [3, 0], [2, -1],
         [2, 1]]
    c = "stuvwxyz~"
    d = 0
    e = len(b)
    while d < e:
        if a[0] == b[d][0] and a[1] == b[d][1]:
            return c[d]
        d += 1
    return 0


def encode_pos_arr(arr):
    b = None
    f = c(arr)
    g = []
    h = []
    i = []
    j = 0
    k = len(f)
    while j < k:
        b = e(f[j])
        if b:
            h.append(b)
        else:
            g.append(d(f[j][0]))
            h.append(d(f[j][1]))
        i.append(d(f[j][2]))
        j += 1
    return "".join(g) + "!!" + "".join(h) + "!!" + "".join(i)
