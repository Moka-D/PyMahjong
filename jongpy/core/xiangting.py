"""jongpy.core.xiangting"""

from jongpy.core.shoupai import Shoupai


XIANGTING_INF = 999


def xiangting_goushi(shoupai: Shoupai):
    """
    国士無双のシャンテン数

    Parameters
    ----------
    shoupai : Shoupai
        手牌

    Returns
    -------
    int
        シャンテン数
    """

    if len(shoupai._fulou):     # 副露ありは国士無双にならない
        return XIANGTING_INF

    n_yaojiu = 0    # ヤオ九牌の種類数
    n_duizi = 0     # ヤオ九牌の対子数

    # すべてのヤオ九牌について種類数と対子数をカウントする
    for s in ['m', 'p', 's', 'z']:
        bingpai = shoupai._bingpai[s]
        nn = [1, 2, 3, 4, 5, 6, 7] if s == 'z' else [1, 9]
        for n in nn:
            if bingpai[n] >= 1:
                n_yaojiu += 1   # 種類数を増やす
            if bingpai[n] >= 2:
                n_duizi += 1    # 対子数を増やす

    # 公式に当てはめてシャンテン数を計算する
    return 12 - n_yaojiu if n_duizi else 13 - n_yaojiu


def xiangting_qidui(shoupai: Shoupai):
    """
    七対子のシャンテン数

    Parameters
    ----------
    shoupai : Shoupai
        手牌

    Returns
    -------
    int
        シャンテン数
    """

    if len(shoupai._fulou):     # 副露ありは七対子にならない
        return XIANGTING_INF

    n_duizi = 0     # 対子の種類数
    n_guli = 0      # 孤立牌の種類数

    # 全ての牌について対子と孤立牌の種類数をカウントする
    for s in ['m', 'p', 's', 'z']:
        bingpai = shoupai._bingpai[s]
        for n in range(1, len(bingpai)):
            if bingpai[n] >= 2:
                n_duizi += 1    # 対子の種類数を増やす
            elif bingpai[n] == 1:
                n_guli += 1     # 孤立牌の種類数を増やす

    if n_duizi > 7:
        n_duizi = 7     # 対子の種類数を補正
    if (n_duizi + n_guli) > 7:
        n_guli = 7 - n_duizi    # 孤立牌の種類数を補正

    # 公式に当てはめてシャンテン数を計算する
    return 13 - n_duizi * 2 - n_guli


def _xiangting(m: int, d: int, g: int, j: bool):
    """
    面子数、搭子数、孤立牌数からシャンテン数を計算する

    Parameters
    ----------
    m : int
        面子数
    d : int
        搭子数
    g : int
        孤立牌数
    j : bool
        雀頭があるとき True

    Returns
    -------
    int
        シャンテン数
    """

    n = 4 if j else 5   # 必要なブロック数
    if m > 4:
        # 面子数を補正
        d += m - 4
        m = 4
    if (m + d) > 4:
        # 搭子数を補正
        g += m + d - 4
        d = 4 - m
    if (m + d + g) > 4:
        g = n - m - d   # 孤立牌数を補正
    if j:
        d += 1  # 雀頭ありの場合、雀頭は搭子として数える

    # 公式に当てはめてシャンテン数を計算する
    return 13 - m * 3 - d * 2 - g


def mianzi(bingpai: list[int], n: int = 1) -> dict[str, list[int]]:
    """
    同色内の面子数、搭子数、孤立牌数をカウントする

    Parameters
    ----------
    bingpai : list[int]
        各牌の枚数
    n : int
        牌の数字

    Returns
    -------
    r_max : dict
        パターンA,Bの面子数、搭子数、孤立牌数を格納
        { 'a': [0,0,0], 'b': [0,0,0] } の形式
        配列は左から順に面子数、搭子数、孤立牌数
    """

    # 面子抜き取り後に搭子数、孤立牌数をカウントする
    if n > 9:
        return dazi(bingpai)

    # 1. 面子を(あえて)取らない
    r_max = mianzi(bingpai, n+1)  # 次の位置に進む

    # 2. 順子として面子をとる
    if (n <= 7) and (bingpai[n] > 0) and (bingpai[n+1] > 0) and (bingpai[n+2] > 0):
        bingpai[n] -= 1
        bingpai[n+1] -= 1
        bingpai[n+2] -= 1
        r = mianzi(bingpai, n)  # 抜き取ったら同じ位置で再試行する
        bingpai[n] += 1
        bingpai[n+1] += 1
        bingpai[n+2] += 1
        # パターンA・Bの面子数を1増やす
        r['a'][0] += 1
        r['b'][0] += 1
        # A・Bともに最良の組み合わせを r_max とする
        if (r['a'][2] < r_max['a'][2]) or (r['a'][2] == r_max['a'][2]) and (r['a'][1] < r_max['a'][1]):
            r_max['a'] = r['a']
        if (r['b'][0] > r_max['b'][0]) or (r['b'][0] == r_max['b'][0]) and (r['b'][1] > r_max['b'][1]):
            r_max['b'] = r['b']

    # 3. 刻子として面子を取る
    if bingpai[n] >= 3:
        bingpai[n] -= 3
        r = mianzi(bingpai, n)  # 抜き取ったら同じ位置で再試行する
        bingpai[n] += 3
        # パターンA・Bの面子数を1増やす
        r['a'][0] += 1
        r['b'][0] += 1
        # A・Bともに最良の組み合わせを r_max とする
        if (r['a'][2] < r_max['a'][2]) or (r['a'][2] == r_max['a'][2]) and (r['a'][1] < r_max['a'][1]):
            r_max['a'] = r['a']
        if (r['b'][0] > r_max['b'][0]) or (r['b'][0] == r_max['b'][0]) and (r['b'][1] > r_max['b'][1]):
            r_max['b'] = r['b']

    return r_max


def dazi(bingpai: list[int]):

    n_pai = 0   # 現在の搭子グループの牌数
    n_dazi = 0  # 総搭子数
    n_guli = 0  # 総孤立牌数

    for n in range(1, 10):
        n_pai += bingpai[n]
        # 現在の搭子グループが終わった場合、搭子数と孤立牌数を計算する
        if (n <= 7) and (bingpai[n+1] == 0) and (bingpai[n+2] == 0):
            n_dazi += n_pai >> 1
            n_guli += n_pai % 2
            n_pai = 0

    # 最後の搭子グループの搭子数と孤立牌数を計算する
    n_dazi += n_pai >> 1
    n_guli += n_pai % 2

    # パターンA,Bの初期値を設定して返す
    return {'a': [0, n_dazi, n_guli], 'b': [0, n_dazi, n_guli]}


def xiangting_yiban(shoupai: Shoupai):
    """
    一般形のシャンテン数計算

    Parameters
    ----------
    shoupai : Shoupai
        手牌

    Returns
    -------
    int
        シャンテン数
    """

    # 雀頭なしとした場合のシャンテン数を計算する
    x_min = mianzi_all(shoupai)

    # 可能な雀頭を抜き取り、雀頭ありの場合のシャンテン数を計算する
    for s in ['m', 'p', 's', 'z']:
        bingpai = shoupai._bingpai[s]
        for n in range(1, len(bingpai)):
            if bingpai[n] >= 2:
                bingpai[n] -= 2
                n_xiangting = mianzi_all(shoupai, True)
                bingpai[n] += 2
                if n_xiangting < x_min:
                    x_min = n_xiangting

    # 副露直後の牌姿が和了形の場合、テンパイとして扱う
    if (x_min == -1) and shoupai._zimo and (len(shoupai._zimo) > 2):
        return 0

    return x_min


def mianzi_all(shoupai: Shoupai, jiangpai: bool = False):

    # 各色ごとの面子・搭子・孤立牌数をカウントする
    r = {
        'm': mianzi(shoupai._bingpai['m']),     # 萬子
        'p': mianzi(shoupai._bingpai['p']),     # 筒子
        's': mianzi(shoupai._bingpai['s'])      # 索子
    }

    # 字牌の面子・搭子・孤立牌数をカウントする
    z = [0, 0, 0]
    for n in range(1, 8):
        if shoupai._bingpai['z'][n] >= 3:
            z[0] += 1   # 面子
        elif shoupai._bingpai['z'][n] == 2:
            z[1] += 1   # 搭子
        elif shoupai._bingpai['z'][n] == 1:
            z[2] += 1   # 孤立牌

    # 副露面子は面子数にカウントする
    n_fulou = len(shoupai._fulou)

    x_min = 13  # シャンテン数を仮に 13 とする

    # 萬子・筒子・索子・字牌それぞれの面子・搭子・孤立牌数を使用して
    # パターンA・Bの全ての組み合わせでシャンテン数を計算する
    for m in [r['m']['a'], r['m']['b']]:
        for p in [r['p']['a'], r['p']['b']]:
            for s in [r['s']['a'], r['s']['b']]:
                x = [n_fulou, 0, 0]
                # 面子・搭子・孤立牌、それぞれについて全色の総和を取る
                for i in range(3):
                    x[i] += m[i] + p[i] + s[i] + z[i]
                    n_xiangting = _xiangting(x[0], x[1], x[2], jiangpai)
                    if n_xiangting < x_min:
                        x_min = n_xiangting

    return x_min


def xiangting(shoupai: Shoupai):
    """
    一般形・国士無双形・七対子形のシャンテン数から最小の値を取得

    Parameters
    ----------
    shoupai : Shoupai
        手牌

    Returns
    -------
    int
        手牌のシャンテン数
    """
    return min([
        xiangting_yiban(shoupai),   # 一般形
        xiangting_goushi(shoupai),  # 国士無双形
        xiangting_qidui(shoupai)    # 七対子形
    ])
