"""jongpy.core.hule"""

import re
import copy
import math
from jongpy.core.shoupai import Shoupai
from jongpy.core.shan import Shan


def hule(shoupai: Shoupai, rongpai: str, param: dict):

    if rongpai:
        if not re.search(r'[\+\=\-]$', rongpai):
            raise Exception(rongpai)
        rongpai = rongpai[0:2] + rongpai[-1]

    h_max = None

    # 状況役の一覧を作成
    pre_hupai = get_pre_hupai(param['hupai'])

    # 懸賞役の一覧を作成
    post_hupai = get_post_hupai(shoupai, rongpai,
                                param['baopai'], param['fubaopai'])

    # 和了形を求め、すべての和了形について以下を実行する
    for mianzi in hule_mianzi(shoupai, rongpai):

        # 符を計算する
        hudi = get_hudi(mianzi, param['zhuangfeng'], param['mengfeng'])

        # 和了形を判定する
        hupaio = get_hupai(mianzi, hudi, pre_hupai, post_hupai, param['rule'])

        # 和了点を計算する
        rv = get_defen(mianzi, hudi, rongpai, param)

        # 最も和了点の高い和了形を選択する。
        # 和了点が同じ場合は、より翻数の多い方を(役満があればそれを)
        # 翻数も同じ場合はより符の高い方を選択する
        if (not max or (rv['defen'] > h_max['defen']) or (rv['defen'] == h_max['defen']) and
                (not rv['defen'] or (rv['fanshu'] > h_max['fanshu']) or (rv['fanshu'] == h_max['fanshu']) and (rv['fu'] > h_max['fu']))):
            max = rv

    return h_max


def hule_mianzi(shoupai: Shoupai, rongpai: str | None = None) -> list[list[str]]:
    """
    和了形の候補をすべて求める

    Parameters
    ----------
    shoupai : Shoupai
        手牌
    rongpai : str or None, default None
        ロン牌

    Returns
    -------
    list[list[str]]
        和了形の候補一覧
    """

    new_shoupai = copy.copy(shoupai)    # 手牌をコピー
    if rongpai:
        new_shoupai.zimo(rongpai)   # ロン牌はツモとして手牌に加える

    # 14枚の手牌でない場合や副露直後の手牌は和了形でない
    if not new_shoupai._zimo or (len(new_shoupai._zimo) > 2):
        return []

    # ツモ和了の場合は和了牌に '_' のマークを加え、0 は 5 に正規化する
    hulepai = (rongpai or new_shoupai._zimo + '_').replace('0', '5')

    return (hule_mianzi_yiban(new_shoupai, hulepai) +   # 一般形
            hule_mianzi_qidui(new_shoupai, hulepai) +   # 七対子形
            hule_mianzi_goushi(new_shoupai, hulepai) +  # 国士無双形
            hule_mianzi_jiulian(new_shoupai, hulepai))  # 九蓮宝燈形


def hule_mianzi_yiban(shoupai: Shoupai, hulepai: str):
    """一般形の和了形を取得"""

    mianzi = []

    for s in ['m', 'p', 's', 'z']:
        bingpai = shoupai._bingpai[s]
        for n in range(1, len(bingpai)):
            if bingpai[n] < 2:
                continue
            bingpai[n] -= 2     # 2枚ある牌を雀頭候補として抜き取る
            jiangpai = s+str(n)*2
            # 残りの手牌から4面子となる組み合わせをすべて求める
            for mm in mianzi_all(shoupai):
                mm.insert(0, jiangpai)  # 雀頭を先頭に差し込む
                if len(mm) != 5:    # 5ブロック以外は和了形でない
                    continue
                # 和了牌のマークをつける
                mianzi.extend(add_hulepai(mm, hulepai))
            bingpai[n] += 2

    return mianzi


def hule_mianzi_qidui(shoupai: Shoupai, hulepai: str) -> list[list[str]]:
    """七対子の和了形を取得"""

    if len(shoupai._fulou) > 0:     # 副露ありは七対子にならない
        return []

    mianzi = []

    # 全ての牌について対子があるかチェックする
    for s in ['m', 'p', 's', 'z']:
        bingpai = shoupai._bingpai[s]
        for n in range(1, len(bingpai)):
            if bingpai[n] == 0:     # 0枚の場合は継続
                continue
            if bingpai[n] == 2:     # 2枚(対子)の場合
                m = s+str(n)*2 + hulepai[2] + '!' if (s+str(n)) == hulepai[0:2] else s+str(n)*2
                mianzi.append(m)
            else:   # それ以外は七対子にならない
                return []

    return [mianzi] if len(mianzi) == 7 else []


def hule_mianzi_goushi(shoupai: Shoupai, hulepai: str) -> list[list[str]]:
    """国士無双の和了形を取得"""

    if len(shoupai._fulou) > 0:     # 副露ありは国士無双にならない
        return []

    mianzi = []
    n_duizi = 0

    # すべてのヤオ九牌の存在と枚数をチェックする
    for s in ['m', 'p', 's', 'z']:
        bingpai = shoupai._bingpai[s]
        nn = [1, 2, 3, 4, 5, 6, 7] if s == 'z' else [1, 9]
        for n in nn:
            if bingpai[n] == 2:     # 2舞の場合
                m = s+str(n)*2 + hulepai[2] + '!' if (s+str(n)) == hulepai[0:2] else s+str(n)*2
                mianzi.insert(0, m)     # 雀頭は先頭にする
                n_duizi += 1
            elif bingpai[n] == 1:   # 1枚の場合
                m = s+str(n) + hulepai[2] + '!' if (s+str(n)) == hulepai[0:2] else s+str(n)
                mianzi.append(m)
            else:   # それ以外は国士無双にならない
                return []

    return [mianzi] if n_duizi == 1 else []


def hule_mianzi_jiulian(shoupai: Shoupai, hulepai: str) -> list[list[str]]:
    """九蓮宝燈の和了形を取得"""

    if len(shoupai._fulou) > 0:     # 副露ありは九蓮宝燈にならない
        return []

    s = hulepai[0]  # 和了牌の色をチェック対象にする
    if s == 'z':    # 字牌は九蓮宝燈にならない
        return []

    mianzi = s
    bingpai = shoupai._bingpai[s]
    # 対象の色の 1~9 がそろっているかチェックする
    for n in range(1, 10):
        if bingpai[n] == 0:     # そろっていない場合は九蓮宝燈ではない
            return []
        if ((n == 1) or (n == 9)) and (bingpai[n] < 3):     # 1と9は3枚必要
            return []
        n_pai = bingpai[n] - 1 if n == int(hulepai[1]) else bingpai[n]
        for i in range(0, n_pai):
            mianzi += str(n)

    if len(mianzi) != 14:   # 手牌が14枚でない場合は九蓮宝燈ではない
        return []
    mianzi += hulepai[1:] + '!'

    return [[mianzi]]


def get_pre_hupai(hupai: dict[str, int | bool]) -> list[dict[str, str | int]]:
    """状況役一覧の作成"""

    pre_hupai = []

    if hupai['lizhi'] == 1:
        pre_hupai.append({'name': '立直', 'fanshu': 1})
    if hupai['lizhi'] == 2:
        pre_hupai.append({'name': 'ダブル立直', 'fanshu': 2})
    if hupai['yifa']:
        pre_hupai.append({'name': '一発', 'fanshu': 1})
    if hupai['haidi'] == 1:
        pre_hupai.append({'name': '海底摸月', 'fanshu': 1})
    if hupai['haidi'] == 2:
        pre_hupai.append({'name': '河底撈魚', 'fanshu': 1})
    if hupai['lingshang']:
        pre_hupai.append({'name': '嶺上開花', 'fanshu': 1})
    if hupai['qianggang']:
        pre_hupai.append({'name': '槍槓', 'fanshu': 1})
    if hupai['tianhu'] == 1:
        pre_hupai.append({'name': '天和', 'fanshu': '*'})
    if hupai['tianhu'] == 2:
        pre_hupai.append({'name': '地和', 'fanshu': '*'})

    return pre_hupai


def get_post_hupai(shoupai: Shoupai, rongpai: str, baopai, fubaopai) -> list[dict[str, str | int]]:
    """懸賞役一覧の作成"""

    # 手牌に和了牌を加え、文字列系に変換する
    new_shoupai = copy.copy(shoupai)
    if rongpai:
        new_shoupai.zimo(rongpai)
    paistr = str(new_shoupai)

    post_hupai = []

    suitstr = re.findall(r'[mpsz][^mpsz,]*', paistr)

    # パターンマッチで保有するドラの枚数を取得する
    n_baopai = 0
    for p in baopai:
        p = Shan.zhenbaopai(p)
        regexp = re.compile(p[1])
        for m in suitstr:
            if m[0] != p[0]:
                continue
            m = m.replace('0', '5')
            nn = re.findall(regexp, m)
            if nn:
                n_baopai += len(nn)
    if n_baopai:
        post_hupai.append({'name': 'ドラ', 'fanshu': n_baopai})

    # パターンマッチで保有する赤ドラの枚数を取得する
    n_hongpai = 0
    nn = re.findall(r'0', paistr)
    if nn:
        n_hongpai = len(nn)
    if n_hongpai:
        post_hupai.append({'name': '赤ドラ', 'fanshu': n_hongpai})

    # パターンマッチで保有する裏ドラの枚数を取得する
    n_fubaopai = 0
    for p in (fubaopai or []):
        p = Shan.zhenbaopai(p)
        regexp = re.compile(p[1])
        for m in suitstr:
            if m[0] != p[0]:
                continue
            m = m.replace('0', '5')
            nn = re.findall(regexp, m)
            if nn:
                n_fubaopai += len(nn)
    if n_fubaopai:
        post_hupai.append({'name': '裏ドラ', 'fanshu': n_fubaopai})

    return post_hupai


def get_hudi(mianzi: list[str], zhuangfeng: int, menfeng: int) -> dict[str, int | bool | dict[str, list[int]]]:
    """和了形の符を計算する"""

    # パターンマッチ用の正規表現
    zhuangfengpai = re.compile(f'^z{zhuangfeng+1}.*$')  # 場風
    menfengpai = re.compile(f'^z{menfeng+1}.*$')    # 自風
    sanyuanpai = re.compile('^z[567].*$')   # 三元牌

    yaojiu = re.compile('^.*[z19].*$')  # ヤオ九牌
    zipai = re.compile('^z.*$')     # 字牌

    kezi = re.compile(r'^[mpsz](\d)\1\1.*$')    # 刻子
    ankezi = re.compile(r'^[mpsz](\d)\1\1(?:\1|_\!)?$')     # 暗刻
    gangzi = re.compile(r'^[mpsz](\d)\1\1.*\1.*$')  # 槓子

    danqi = re.compile(r'^[mpsz](\d)\1[\+\=\-\_]\!$')   # 単騎待ち
    kanzhang = re.compile(r'^[mps]\d\d[\+\=\-\_]\!\d$')     # 嵌張待ち
    bianzhang = re.compile(r'^[mps](123[\+\=\-\_]\!|7[\+\=\-\_]\!89)$')     # 辺張待ち

    # 面子構成情報の初期値
    hudi = {
        'fu': 20,   # 符
        'menqian': True,    # 面前のとき True
        'zimo': True,   # ツモ和了のとき True
        'shunzi': {     # 順子の構成情報
            'm': [0, 0, 0, 0, 0, 0, 0, 0],
            'p': [0, 0, 0, 0, 0, 0, 0, 0],
            's': [0, 0, 0, 0, 0, 0, 0, 0]
        },
        'kezi': {   # 刻子の構成情報
            'm': [0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
            'p': [0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
            's': [0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
            'z': [0, 0, 0, 0, 0, 0, 0, 0]
        },
        'n_shunzi': 0,  # 順子の数
        'n_kezi': 0,    # 刻子の数
        'n_ankezi': 0,  # 暗刻の数
        'n_gangzi': 0,  # 槓子の数
        'n_yaojiu': 0,  # ヤオ九牌を含むブロックの数
        'n_zipai': 0,   # 字牌を含むブロックの数
        'danqi': False,     # 単騎待ちのとき True
        'pinghu': False,    # 平和のとき True
        'zhuangfeng': zhuangfeng,   # 場風 (0:東, 1:南, 2:西, 3:北)
        'menfeng': menfeng  # 自風 (0:東, 1:南, 2:西, 3:北)
    }

    # 和了形の各ブロックについて処理を行う
    for m in mianzi:

        if re.search(r'[\+\=\-](?!\!)', m):
            hudi['menqian'] = False     # 副露している場合 False に変更
        if re.search(r'[\+\=\-]\!', m):
            hudi['zimo'] = False    # ロン和了の場合 False に変更

        if len(mianzi) == 1:    # 九牌宝燈の場合、以下は処理しない
            continue

        if re.search(danqi, m):
            hudi['danqi'] = True    # 単騎待ちの場合 True

        if len(mianzi) == 13:   # 国士無双の場合、以下は処理しない
            continue

        if re.search(yaojiu, m):
            hudi['n_yaojiu'] += 1   # ヤオ九牌を含むブロック数を加算
        if re.search(zipai, m):
            hudi['n_zipai'] += 1    # 字牌を含むブロック数を加算

        if len(mianzi) != 5:    # 七対子の場合、以下は処理しない
            continue

        if m == mianzi[0]:  # 雀頭の処理
            fu = 0  # 雀頭の符を 0 で初期化
            if re.search(zhuangfengpai, m):
                fu += 2     # 場風の場合、2符加算
            if re.search(menfengpai, m):
                fu += 2     # 自風の場合、2符加算
            if re.search(sanyuanpai, m):
                fu += 2     # 三元牌の場合、2符加算
            hudi['fu'] += fu    # 雀頭の符を加算
            if hudi['danqi']:
                hudi['fu'] += 2     # 単騎待ちの場合、2符加算

        elif re.search(kezi, m):    # 刻子の処理
            hudi['n_kezi'] += 1     # 刻子の数を加算
            fu = 2  # 刻子の符を 2 で初期化
            if re.search(yaojiu, m):
                fu *= 2     # ヤオ九牌の場合、符を2倍にする
            if re.search(ankezi, m):
                fu *= 2     # 暗刻の場合、符を2倍にする
                hudi['n_ankezi'] += 1
            if re.search(gangzi, m):
                fu *= 4     # 槓子の場合、符を4倍にする
                hudi['n_gangzi'] += 1
            hudi['fu'] += fu    # 刻子の符を加算
            hudi['kezi'][m[0]][int(m[1])] += 1   # 刻子の構成情報に追加

        else:   # 順子の処理
            hudi['n_shunzi'] += 1   # 順子の数を加算
            if re.search(kanzhang, m):
                hudi['fu'] += 2     # 辺張待ちの場合、2符加算
            if re.search(bianzhang, m):
                hudi['fu'] += 2     # 嵌張待ちの場合、2符加算
            hudi['shunzi'][m[0]][int(m[1])] += 1     # 順子の構成情報に追加

    # 和了全体に関する加符を行う
    if len(mianzi) == 7:    # 七対子の場合
        hudi['fu'] = 25     # 副底は25符固定
    elif len(mianzi) == 5:  # 一般形の場合
        hudi['pinghu'] = hudi['menqian'] and (hudi['fu'] == 20)     # 符のない面前手は平和
        if hudi['zimo']:    # ツモ和了
            if not hudi['pinghu']:
                hudi['fu'] += 2     # 平和でなければ、2符加算
        else:   # ロン和了
            if hudi['menqian']:
                hudi['fu'] += 10    # 面前なら、10符加算
            elif hudi['fu'] == 20:
                hudi['fu'] = 30     # 符のない副露手は、30符固定
        hudi['fu'] = math.ceil(hudi['fu'] / 10) * 10    # 10符未満を切り上げる

    return hudi


def get_hupai():
    pass


def get_defen():
    pass


def mianzi_all(shoupai: Shoupai) -> list[list[str]]:
    """4面子となる組み合わせをすべて求める"""

    # 萬子・筒子・索子の副露していない牌から面子の組み合わせをすべて求める
    shupai_all = [[]]
    for s in ['m', 'p', 's']:
        new_mianzi = []
        for mm in shupai_all:
            # 同色内の面子をすべて求め、今までの結果すべてに追加する
            for nn in mianzi(s, shoupai._bingpai[s]):
                new_mianzi.append(mm + nn)
        shupai_all = new_mianzi

    # 字牌の面子は刻子しかないので以下で取得する
    zipai = []
    for n in range(1, 8):
        if shoupai._bingpai['z'][n] == 0:
            continue
        if shoupai._bingpai['z'][n] != 3:   # 刻子以外がある場合は和了形ではない
            return []
        zipai.append('z'+str(n)*3)

    # 副露面子内の 0 を 5 に正規化する
    fulou = list(map(lambda m: m.replace('0', '5'), shoupai._fulou))

    # 萬子・筒子・索子の副露していない和了形すべての後方に、
    # 字牌刻子と副露面子を追加する
    return list(map(lambda shupai: shupai + zipai + fulou, shupai_all))


def mianzi(s: str, bingpai: list[int], n: int = 1) -> list[list[str]]:
    """同色内の面子を全て求める"""

    if n > 9:
        return [[]]

    # 面子をすべて抜き取ったら次の位置に進む
    if bingpai[n] == 0:
        return mianzi(s, bingpai, n+1)

    # 順子を抜き取る
    shunzi = []
    if (n <= 7) and (bingpai[n] > 0) and (bingpai[n+1] > 0) and (bingpai[n+2] > 0):
        bingpai[n] -= 1
        bingpai[n+1] -= 1
        bingpai[n+2] -= 1
        shunzi = mianzi(s, bingpai, n)  # 抜き取ったら同じ位置で再試行する
        bingpai[n] += 1
        bingpai[n+1] += 1
        bingpai[n+2] += 1
        for s_mianzi in shunzi:     # 試行結果のすべてに抜いた順子を加える
            s_mianzi.insert(0, s+str(n)+str(n+1)+str(n+2))

    # 刻子を抜き取る
    kezi = []
    if bingpai[n] == 3:
        bingpai[n] -= 3
        kezi = mianzi(s, bingpai, n+1)  # 抜き取ったら次の位置に進む
        bingpai[n] += 3
        for k_mianzi in kezi:   # 試行結果の全てに抜いた刻子を加える
            k_mianzi.insert(0, s+str(n)*3)

    # 順子のパターンと刻子のパターンをマージして全て返す
    return shunzi + kezi


def add_hulepai(mianzi: list[str], p: str) -> list[list[str]]:
    """和了牌のマークを付ける"""

    s, n, d = p[:]
    regexp = re.compile(f'^({s}.*{n})')     # 和了牌を探す正規表現
    replacer = f'\\1{d}!'   # マークを付ける置換文字列

    new_mianzi = []

    # 和了形の面子の中から和了牌を見つけマークする
    for i in range(0, len(mianzi)):
        if re.search(r'[\+\=\-]|\d{4}', mianzi[i]):     # 副露面子は対象外
            continue
        if (i > 0) and (mianzi[i] == mianzi[i-1]):  # 重複して処理しない
            continue
        m = re.sub(regexp, replacer, mianzi[i])     # 置換を試みる
        if m == mianzi[i]:  # 出来なければ次へ
            continue
        tmp_mianzi = copy.deepcopy(mianzi)  # 和了形を複製する
        tmp_mianzi[i] = m   # マークした面子と置き換える
        new_mianzi.append(tmp_mianzi)

    return new_mianzi
