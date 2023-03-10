"""jongpy.core.hule"""

import re
import math
from typing import Any
from jongpy.core.shoupai import Shoupai
from jongpy.core.shan import Shan
from jongpy.core.rule import rule
from jongpy.core.exceptions import InvalidOperationError


def _mianzi(s: str, bingpai: list[int], n: int = 1) -> list[list[str]]:
    """同色内の面子を全て求める"""

    if n > 9:
        return [[]]

    # 面子をすべて抜き取ったら次の位置に進む
    if bingpai[n] == 0:
        return _mianzi(s, bingpai, n + 1)

    # 順子を抜き取る
    shunzi = []
    if n <= 7 and bingpai[n] > 0 and bingpai[n + 1] > 0 and bingpai[n + 2] > 0:
        bingpai[n] -= 1
        bingpai[n + 1] -= 1
        bingpai[n + 2] -= 1
        shunzi = _mianzi(s, bingpai, n)  # 抜き取ったら同じ位置で再試行する
        bingpai[n] += 1
        bingpai[n + 1] += 1
        bingpai[n + 2] += 1
        for s_mianzi in shunzi:     # 試行結果のすべてに抜いた順子を加える
            s_mianzi.insert(0, s + str(n) + str(n + 1) + str(n + 2))

    # 刻子を抜き取る
    kezi = []
    if bingpai[n] == 3:
        bingpai[n] -= 3
        kezi = _mianzi(s, bingpai, n + 1)  # 抜き取ったら次の位置に進む
        bingpai[n] += 3
        for k_mianzi in kezi:   # 試行結果の全てに抜いた刻子を加える
            k_mianzi.insert(0, s + str(n) * 3)

    # 順子のパターンと刻子のパターンをマージして全て返す
    return shunzi + kezi


def mianzi_all(shoupai: Shoupai) -> list[list[str]]:
    """4面子となる組み合わせをすべて求める"""

    # 萬子・筒子・索子の副露していない牌から面子の組み合わせをすべて求める
    shupai_all = [[]]
    for s in ['m', 'p', 's']:
        new_mianzi = []
        for mm in shupai_all:
            # 同色内の面子をすべて求め、今までの結果すべてに追加する
            for nn in _mianzi(s, shoupai._bingpai[s]):
                new_mianzi.append(mm + nn)
        shupai_all = new_mianzi

    # 字牌の面子は刻子しかないので以下で取得する
    zipai = []
    for n in range(1, 8):
        if shoupai._bingpai['z'][n] == 0:
            continue
        if shoupai._bingpai['z'][n] != 3:   # 刻子以外がある場合は和了形ではない
            return []
        zipai.append('z' + str(n) * 3)

    # 副露面子内の 0 を 5 に正規化する
    fulou = list(map(lambda m: m.replace('0', '5'), shoupai._fulou))

    # 萬子・筒子・索子の副露していない和了形すべての後方に、
    # 字牌刻子と副露面子を追加する
    return list(map(lambda shupai: shupai + zipai + fulou, shupai_all))


def add_hulepai(mianzi: list[str], p: str) -> list[list[str]]:
    """和了牌のマークを付ける"""

    s = p[0]
    n = p[1]
    d = p[2] if len(p) == 3 else ''
    regexp = re.compile(f'^({s}.*{n})')     # 和了牌を探す正規表現
    replacer = f'\\1{d}!'   # マークを付ける置換文字列

    new_mianzi = []

    # 和了形の面子の中から和了牌を見つけマークする
    for i in range(0, len(mianzi)):
        if re.search(r'[\+\=\-]|\d{4}', mianzi[i]):     # 副露面子は対象外
            continue
        if i > 0 and mianzi[i] == mianzi[i - 1]:    # 重複して処理しない
            continue
        m = re.sub(regexp, replacer, mianzi[i])     # 置換を試みる
        if m == mianzi[i]:  # 出来なければ次へ
            continue
        tmp_mianzi = mianzi[:]  # 和了形を複製する
        tmp_mianzi[i] = m   # マークした面子と置き換える
        new_mianzi.append(tmp_mianzi)

    return new_mianzi


def hule_mianzi_yiban(shoupai: Shoupai, hulepai: str):
    """一般形の和了形を取得"""

    mianzi = []

    for s in ['m', 'p', 's', 'z']:
        bingpai = shoupai._bingpai[s]
        for n in range(1, len(bingpai)):
            if bingpai[n] < 2:
                continue
            bingpai[n] -= 2     # 2枚ある牌を雀頭候補として抜き取る
            jiangpai = s + str(n) * 2
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
    d = hulepai[2] if len(hulepai) == 3 else ''

    # 全ての牌について対子があるかチェックする
    for s in ['m', 'p', 's', 'z']:
        bingpai = shoupai._bingpai[s]
        for n in range(1, len(bingpai)):
            if bingpai[n] == 0:     # 0枚の場合は継続
                continue
            if bingpai[n] == 2:     # 2枚(対子)の場合
                m = s + str(n) * 2 + d + '!' if s + str(n) == hulepai[0:2] else s + str(n) * 2
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
    d = hulepai[2] if len(hulepai) == 3 else ''

    # すべての幺九牌の存在と枚数をチェックする
    for s in ['m', 'p', 's', 'z']:
        bingpai = shoupai._bingpai[s]
        nn = [1, 2, 3, 4, 5, 6, 7] if s == 'z' else [1, 9]
        for n in nn:
            if bingpai[n] == 2:     # 2舞の場合
                m = s + str(n) * 2 + d + '!' if s + str(n) == hulepai[0:2] else s + str(n) * 2
                mianzi.insert(0, m)     # 雀頭は先頭にする
                n_duizi += 1
            elif bingpai[n] == 1:   # 1枚の場合
                m = s + str(n) + d + '!' if s + str(n) == hulepai[0:2] else s + str(n)
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
        if (n == 1 or n == 9) and bingpai[n] < 3:   # 1と9は3枚必要
            return []
        n_pai = bingpai[n] - 1 if n == int(hulepai[1]) else bingpai[n]
        for i in range(0, n_pai):
            mianzi += str(n)

    if len(mianzi) != 14:   # 手牌が14枚でない場合は九蓮宝燈ではない
        return []
    mianzi += hulepai[1:] + '!'

    return [[mianzi]]


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

    new_shoupai = shoupai.clone()   # 手牌をコピー
    if rongpai:
        new_shoupai.zimo(rongpai)   # ロン牌はツモとして手牌に加える

    # 14枚の手牌でない場合や副露直後の手牌は和了形でない
    if not new_shoupai._zimo or len(new_shoupai._zimo) > 2:
        return []

    # ツモ和了の場合は和了牌に '_' のマークを加え、0 は 5 に正規化する
    hulepai = (rongpai or new_shoupai._zimo + '_').replace('0', '5')

    return (hule_mianzi_yiban(new_shoupai, hulepai)     # 一般形
            + hule_mianzi_qidui(new_shoupai, hulepai)   # 七対子形
            + hule_mianzi_goushi(new_shoupai, hulepai)  # 国士無双形
            + hule_mianzi_jiulian(new_shoupai, hulepai))    # 九蓮宝燈形


def get_hudi(mianzi: list[str], zhuangfeng: int, menfeng: int) -> dict[str, int | bool | dict[str, list[int]]]:
    """和了形の符を計算する"""

    # パターンマッチ用の正規表現
    zhuangfengpai = re.compile(f'^z{zhuangfeng+1}.*$')  # 場風
    menfengpai = re.compile(f'^z{menfeng+1}.*$')    # 自風
    sanyuanpai = re.compile(r'^z[567].*$')  # 三元牌

    yaojiu = re.compile(r'^.*[z19].*$')     # 幺九牌
    zipai = re.compile(r'^z.*$')    # 字牌

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
        'n_yaojiu': 0,  # 幺九牌を含むブロックの数
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

        if len(mianzi) == 1:    # 九蓮宝燈の場合、以下は処理しない
            continue

        if re.search(danqi, m):
            hudi['danqi'] = True    # 単騎待ちの場合 True

        if len(mianzi) == 13:   # 国士無双の場合、以下は処理しない
            continue

        if re.search(yaojiu, m):
            hudi['n_yaojiu'] += 1   # 幺九牌を含むブロック数を加算
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
                fu *= 2     # 幺九牌の場合、符を2倍にする
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


def get_pre_hupai(hupai: dict[str, int | bool]) -> list[dict[str, str | int]]:
    """状況役一覧の作成"""

    pre_hupai = []

    if hupai.get('lizhi') == 1:
        pre_hupai.append({'name': '立直', 'fanshu': 1})
    if hupai.get('lizhi') == 2:
        pre_hupai.append({'name': 'ダブル立直', 'fanshu': 2})
    if hupai.get('yifa'):
        pre_hupai.append({'name': '一発', 'fanshu': 1})
    if hupai.get('haidi') == 1:
        pre_hupai.append({'name': '海底摸月', 'fanshu': 1})
    if hupai.get('haidi') == 2:
        pre_hupai.append({'name': '河底撈魚', 'fanshu': 1})
    if hupai.get('lingshang'):
        pre_hupai.append({'name': '嶺上開花', 'fanshu': 1})
    if hupai.get('qianggang'):
        pre_hupai.append({'name': '槍槓', 'fanshu': 1})
    if hupai.get('tianhu') == 1:
        pre_hupai.append({'name': '天和', 'fanshu': '*'})
    if hupai.get('tianhu') == 2:
        pre_hupai.append({'name': '地和', 'fanshu': '*'})

    return pre_hupai


class HupaiSolver:
    """役の判定処理をまとめたクラス"""

    def __init__(self, mianzi: list[str], hudi: dict[str, int | bool | dict[str, list[int]]], rule: dict[str, Any]):
        self._mianzi = mianzi
        self._hudi = hudi
        self._rule = rule

    def menqianging(self):
        """面前ツモ"""
        if self._hudi['menqian'] and self._hudi['zimo']:
            return [{'name': '門前清自摸和', 'fanshu': 1}]
        return []

    def fanpai(self):
        """翻牌"""
        feng_hanzi = ['東', '南', '西', '北']
        fanpai_all = []
        if self._hudi['kezi']['z'][self._hudi['zhuangfeng'] + 1]:
            fanpai_all.append({'name': '場風 ' + feng_hanzi[self._hudi['zhuangfeng']], 'fanshu': 1})
        if self._hudi['kezi']['z'][self._hudi['menfeng'] + 1]:
            fanpai_all.append({'name': '自風 ' + feng_hanzi[self._hudi['menfeng']], 'fanshu': 1})
        if self._hudi['kezi']['z'][5]:
            fanpai_all.append({'name': '翻牌 白', 'fanshu': 1})
        if self._hudi['kezi']['z'][6]:
            fanpai_all.append({'name': '翻牌 發', 'fanshu': 1})
        if self._hudi['kezi']['z'][7]:
            fanpai_all.append({'name': '翻牌 中', 'fanshu': 1})
        return fanpai_all

    def pinghu(self):
        """平和"""
        if self._hudi['pinghu']:
            return [{'name': '平和', 'fanshu': 1}]
        return []

    def duanyaojiu(self):
        """タンヤオ"""
        if self._hudi['n_yaojiu'] > 0:
            return []
        # 喰いタンありの場合、副露していても成立
        if self._rule['fulou_duanyaojiu'] or self._hudi['menqian']:
            return [{'name': '断幺九', 'fanshu': 1}]
        return []

    def yibeikou(self):
        """一盃口"""
        if not self._hudi['menqian']:
            return []
        shunzi = self._hudi['shunzi']
        beiko = sum(map(lambda x: x >> 1, shunzi['m'] + shunzi['p'] + shunzi['s']))
        if beiko == 1:
            return [{'name': '一盃口', 'fanshu': 1}]
        return []

    def sansetongshun(self):
        """三色同順"""
        shunzi = self._hudi['shunzi']
        for n in range(1, 8):
            if shunzi['m'][n] and shunzi['p'][n] and shunzi['s'][n]:
                return [{'name': '三色同順', 'fanshu': (2 if self._hudi['menqian'] else 1)}]
        return []

    def yiqitongguan(self):
        """一気通貫"""
        shunzi = self._hudi['shunzi']
        for s in ['m', 'p', 's']:
            if shunzi[s][1] and shunzi[s][4] and shunzi[s][7]:
                return [{'name': '一気通貫', 'fanshu': (2 if self._hudi['menqian'] else 1)}]
        return []

    def hunquandaiyaojiu(self):
        """チャンタ"""
        if self._hudi['n_yaojiu'] == 5 and self._hudi['n_shunzi'] > 0 and self._hudi['n_zipai'] > 0:
            return [{'name': '混全帯幺九', 'fanshu': (2 if self._hudi['menqian'] else 1)}]
        return []

    def qiduizi(self):
        """七対子"""
        if len(self._mianzi) == 7:
            return [{'name': '七対子', 'fanshu': 2}]
        return []

    def duiduihu(self):
        """対々和"""
        if self._hudi['n_kezi'] == 4:
            return [{'name': '対々和', 'fanshu': 2}]
        return []

    def sananke(self):
        """三暗刻"""
        if self._hudi['n_ankezi'] == 3:
            return [{'name': '三暗刻', 'fanshu': 2}]
        return []

    def sangangzi(self):
        """三槓子"""
        if self._hudi['n_gangzi'] == 3:
            return [{'name': '三槓子', 'fanshu': 2}]
        return []

    def sansetongke(self):
        """三色同刻"""
        kezi = self._hudi['kezi']
        for n in range(1, 10):
            if kezi['m'][n] and kezi['p'][n] and kezi['s'][n]:
                return [{'name': '三色同刻', 'fanshu': 2}]
        return []

    def hunlaotou(self):
        """混老頭"""
        if self._hudi['n_yaojiu'] == len(self._mianzi) and self._hudi['n_shunzi'] == 0 and self._hudi['n_zipai'] > 0:
            return [{'name': '混老頭', 'fanshu': 2}]
        return []

    def xiaosanyuan(self):
        """小三元"""
        kezi = self._hudi['kezi']
        if ((kezi['z'][5] + kezi['z'][6] + kezi['z'][7]) == 2) and re.match(r'z[567]', self._mianzi[0]):
            return [{'name': '小三元', 'fanshu': 2}]
        return []

    def hunyise(self):
        """混一色"""
        for s in ['m', 'p', 's']:
            yise = re.compile(f'^[z{s}]')
            if len([m for m in self._mianzi if re.search(yise, m)]) == len(self._mianzi) and self._hudi['n_zipai'] > 0:
                return [{'name': '混一色', 'fanshu': (3 if self._hudi['menqian'] else 2)}]
        return []

    def chunquandaiyaojiu(self):
        """純チャン"""
        if self._hudi['n_yaojiu'] == 5 and self._hudi['n_shunzi'] > 0 and self._hudi['n_zipai'] == 0:
            return [{'name': '純全帯幺九', 'fanshu': (3 if self._hudi['menqian'] else 2)}]
        return []

    def erbeikou(self):
        """二盃口"""
        if not self._hudi['menqian']:
            return []
        shunzi = self._hudi['shunzi']
        beiko = sum(map(lambda x: x >> 1, shunzi['m'] + shunzi['p'] + shunzi['s']))
        if beiko == 2:
            return [{'name': '二盃口', 'fanshu': 3}]
        return []

    def qingyise(self):
        """清一色"""
        for s in ['m', 'p', 's']:
            yise = re.compile(f'^[{s}]')
            if len([m for m in self._mianzi if re.search(yise, m)]) == len(self._mianzi):
                return [{'name': '清一色', 'fanshu': (6 if self._hudi['menqian'] else 5)}]
        return []

    def goushiwushuang(self):
        """国士無双"""
        if len(self._mianzi) != 13:
            return []
        if self._hudi['danqi']:
            return [{'name': '国士無双十三面', 'fanshu': '**'}]
        else:
            return [{'name': '国士無双', 'fanshu': '*'}]

    def sianke(self):
        """四暗刻"""
        if self._hudi['n_ankezi'] != 4:
            return []
        if self._hudi['danqi']:
            return [{'name': '四暗刻単騎', 'fanshu': '**'}]
        else:
            return [{'name': '四暗刻', 'fanshu': '*'}]

    def dasanyuan(self):
        """大三元"""
        kezi = self._hudi['kezi']
        if kezi['z'][5] + kezi['z'][6] + kezi['z'][7] == 3:
            bao_mianzi = [m for m in self._mianzi if re.match(r'z([567])\1\1(?:[\+\=\-]|\1)(?!\!)', m)]
            baojia = len(bao_mianzi) == 3 and re.search(r'[\+\=\-]', bao_mianzi[2])
            if baojia:
                return [{'name': '大三元', 'fanshu': '*', 'baojia': baojia.group()}]
            else:
                return [{'name': '大三元', 'fanshu': '*'}]
        return []

    def sixihu(self):
        """四喜和"""
        kezi = self._hudi['kezi']
        if kezi['z'][1] + kezi['z'][2] + kezi['z'][3] + kezi['z'][4] == 4:
            bao_mianzi = [m for m in self._mianzi if re.match(r'z([1234])\1\1(?:[\+\=\-]|\1)(?!\!)', m)]
            baojia = len(bao_mianzi) == 4 and re.search(r'[\+\=\-]', bao_mianzi[3])
            if baojia:
                return [{'name': '大四喜', 'fanshu': '**', 'baojia': baojia.group()}]
            else:
                return [{'name': '大四喜', 'fanshu': '**'}]
        if kezi['z'][1] + kezi['z'][2] + kezi['z'][3] + kezi['z'][4] == 3 and re.match(r'z[1234]', self._mianzi[0]):
            return [{'name': '小四喜', 'fanshu': '*'}]
        return []

    def ziyise(self):
        """字一色"""
        if self._hudi['n_zipai'] == len(self._mianzi):
            return [{'name': '字一色', 'fanshu': '*'}]
        return []

    def lvyise(self):
        """緑一色"""
        if len([m for m in self._mianzi if re.match(r'[mp]', m)]) > 0:
            return []
        if len([m for m in self._mianzi if re.match(r'z[^6]', m)]) > 0:
            return []
        if len([m for m in self._mianzi if re.match(r's.*[1579]', m)]) > 0:
            return []
        return [{'name': '緑一色', 'fanshu': '*'}]

    def qinglaotou(self):
        """清老頭"""
        if self._hudi['n_yaojiu'] == 5 and self._hudi['n_kezi'] == 4 and self._hudi['n_zipai'] == 0:
            return [{'name': '清老頭', 'fanshu': '*'}]
        return []

    def sigangzi(self):
        """四槓子"""
        if self._hudi['n_gangzi'] == 4:
            return [{'name': '四槓子', 'fanshu': '*'}]
        return []

    def jiulianbaodeng(self):
        """九蓮宝燈"""
        if len(self._mianzi) != 1:
            return []
        if re.search(r'^[mpsz]1112345678999', self._mianzi[0]):
            return [{'name': '純正九蓮宝燈', 'fanshu': '**'}]
        else:
            return [{'name': '九蓮宝燈', 'fanshu': '*'}]


def get_hupai(
    mianzi: list[str],
    hudi: dict[str, int | bool | dict[str, list[int]]],
    pre_hupai: list[dict[str, str | int]],
    post_hupai: list[dict[str, str | int]],
    rule: dict[str, Any]
) -> list[dict[str, str | int]]:
    """和了役を判定する"""

    # 役満の初期値を設定する。状況役に役満(天和、地和)が含まれている場合は
    # それを設定、ない場合は空配列で初期化する
    damanguan = pre_hupai if len(pre_hupai) > 0 and isinstance(pre_hupai[0]['fanshu'], str) else []

    # 役判定クラス
    hs = HupaiSolver(mianzi, hudi, rule)

    # 判定できた役満を追加していく
    damanguan = (damanguan  # 天和・地和
                 + hs.goushiwushuang()  # 国士無双
                 + hs.sianke()  # 四暗刻
                 + hs.dasanyuan()   # 大三元
                 + hs.sixihu()  # 四喜和
                 + hs.ziyise()  # 字一色
                 + hs.lvyise()  # 緑一色
                 + hs.qinglaotou()  # 清老頭
                 + hs.sigangzi()    # 四槓子
                 + hs.jiulianbaodeng())     # 九蓮宝燈

    for hupai in damanguan:
        # 「ダブル役満なし」のルールの場合、判定済みダブル役満を通常の役満にダウングレードする
        if not rule['double_damanguan']:
            hupai['fanshu'] = '*'

        # 「役満パオなし」のルールの場合、判定済みのパオ情報を削除する
        if not rule['damanguan_baojia']:
            del hupai['baojia']

    # 役満がある場合は通常役の判定はせず、役満のみを返す
    if len(damanguan) > 0:
        return damanguan

    # 通常役を判定する。判定済みの状況役に判定できた役を追加していく
    hupai = (pre_hupai  # 状況役
             + hs.menqianging()     # 面前清自摸和
             + hs.fanpai()  # 翻牌
             + hs.pinghu()  # 平和
             + hs.duanyaojiu()  # タンヤオ
             + hs.yibeikou()    # 一盃口
             + hs.sansetongshun()   # 三色同順
             + hs.yiqitongguan()    # 一気通貫
             + hs.hunquandaiyaojiu()    # チャンタ
             + hs.qiduizi()     # 七対子
             + hs.duiduihu()    # 対々和
             + hs.sananke()     # 三暗刻
             + hs.sangangzi()   # 三槓子
             + hs.sansetongke()     # 三色同刻
             + hs.hunlaotou()   # 混老頭
             + hs.xiaosanyuan()     # 小三元
             + hs.hunyise()     # 混一色
             + hs.chunquandaiyaojiu()   # 純チャン
             + hs.erbeikou()    # 二盃口
             + hs.qingyise())   # 清一色

    # 和了役がある場合は、さらに懸賞役を追加する
    if len(hupai) > 0:
        hupai.extend(post_hupai)

    return hupai


def get_post_hupai(
    shoupai: Shoupai,
    rongpai: str | None,
    baopai: list[str],
    fubaopai: list[str] | None
) -> list[dict[str, str | int]]:
    """懸賞役一覧の作成"""

    # 手牌に和了牌を加え、文字列系に変換する
    new_shoupai = shoupai.clone()
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


def get_defen(
    fu: int,
    hupai: list[dict[str, str | int]],
    rongpai: str | None,
    param: dict[str, Any]
) -> dict[str, Any]:
    """和了点の計算"""

    if len(hupai) == 0:     # 役なしの場合
        return {
            'hupai': None,
            'fu': fu,
            'fanshu': 0,
            'damanguan': 0,
            'defen': 0,
            'fenpei': []
        }

    menfeng = param['menfeng']
    fanshu = None
    damanguan = None
    defen = None
    base = None
    baojia = None
    defen2 = None
    base2 = None
    baojia2 = None

    # 基本点を計算する
    if isinstance(hupai[0]['fanshu'], str):     # 役満の場合
        fu = None   # 符はない
        # 役満複合数を決定する。役満の複合なしの場合は、1固定とする。
        damanguan = 1 if not param['rule']['compound_damanguan'] else sum(map(lambda h: len(h['fanshu']), hupai))
        base = 8000 * damanguan

        # パオ責任者がいる場合は責任対象の基本点を算出する
        # 大三元と大四喜は同時に成立しないので対象の役満は1つ
        h = next(filter(lambda h: 'baojia' in h, hupai), None)
        if h:
            baojia2 = (menfeng + {'+': 1, '=': 2, '-': 3}[h['baojia']]) % 4
            base2 = 8000 * min(len(h['fanshu']), damanguan)

    else:   # 通常役の場合
        # 役ごとの翻数の総和を和了の翻数とする
        fanshu = sum(map(lambda h: h['fanshu'], hupai))

        # 基本点を計算する
        base = (8000 if fanshu >= 13 and param['rule']['counting_damanguan']    # 数え役満
                else 6000 if fanshu >= 11   # 三倍満
                else 4000 if fanshu >= 8    # 倍満
                else 3000 if fanshu >= 6    # 跳満
                # 切り上げ満貫
                else 2000 if param['rule']['ceiled_manguan'] and fu << (2 + fanshu) == 1920
                else min(fu << (2 + fanshu), 2000))     # それ以外は2,000点を上限とする

    fenpei = [0, 0, 0, 0]
    chang = param['jicun']['changbang']
    lizhi = param['jicun']['lizhibang']

    # パオ責任者がいる場合、パオ分について精算する
    if baojia2 is not None:
        if rongpai:
            base2 = base2 / 2   # ロン和了は放銃者と折半
        base = base - base2     # 放銃者の負担する基本点を決定する
        defen2 = base2 * (6 if menfeng == 0 else 4)     # パオ責任者の負担額を決定する
        fenpei[menfeng] += defen2   # 和了者の収支 = + 負担額
        fenpei[baojia2] -= defen2   # パオ責任者の収支 = - 負担額
    else:
        defen2 = 0

    # パオ分以外について和了点を精算する
    if rongpai or base == 0:    # ロン和了、もしくはパオ責任者一人払いの場合
        # 支払者を決定する(パオ責任者か放銃者か)
        baojia = baojia2 if base == 0 else (menfeng + {'+': 1, '=': 2, '-': 3}[rongpai[2]]) % 4

        defen = math.ceil(base * (6 if menfeng == 0 else 4) / 100) * 100    # 負担者の支払額を決定

        # 供託・積み棒も含め精算する
        # 和了者の収支 = + 負担額 + 積み棒x300 + リーチ棒
        fenpei[menfeng] += defen + chang * 300 + lizhi * 1000
        # 支払者の収支 = - 負担額 - 積み棒x300
        fenpei[baojia] -= defen + chang * 300

    else:   # ツモ和了の場合
        zhuangjia = math.ceil(base * 2 / 100) * 100     # 親の負担額
        sanjia = math.ceil(base / 100) * 100    # 子の負担額
        if menfeng == 0:    # 親の和了
            defen = zhuangjia * 3   # 和了点 = 親の負担額 x3
            for i in range(0, 4):
                if i == menfeng:
                    # 和了者の収支 = + 和了点 + 積み棒 x300 + リーチ棒
                    fenpei[i] += defen + chang * 300 + lizhi * 1000
                else:
                    # 支払者の負担 = - 子の負担額 - 積み棒 x100
                    fenpei[i] -= zhuangjia + chang * 100
        else:   # 子の和了
            defen = zhuangjia + sanjia * 2  # 和了点 = 親の負担額 + 子の負担額 x2
            for i in range(0, 4):
                if i == menfeng:
                    # 和了者の収支 = + 和了点 + 積み棒 x300 + リーチ棒
                    fenpei[i] += defen + chang * 300 + lizhi * 1000
                elif i == 0:
                    # 支払者(親)の収支 = - 親の負担額 - 積み棒 x100
                    fenpei[i] -= zhuangjia + chang * 100
                else:
                    # 支払者(子)の収支 = - 子の負担額 - 積み棒 x100
                    fenpei[i] -= sanjia + chang * 100

    return {
        'hupai': hupai,     # 和了役一覧
        'fu': fu,   # 符
        'fanshu': fanshu,   # 翻数
        'damanguan': damanguan,     # 役満複合数
        'defen': defen + defen2,    # 和了点
        'fenpei': fenpei    # 局収支
    }


def hule(shoupai: Shoupai, rongpai: str | None, param: dict) -> dict[str, Any] | None:
    """
    和了情報の計算

    Parameters
    ----------
    shoupai : Shoupai
        手牌
    rongpai : str or None
        ロン牌の文字列表現
    param : dict
        点数計算に関する各種パラメータ

    Returns
    -------
    h_max : dict (or None)
        和了情報
    """

    if rongpai:
        if not re.search(r'[\+\=\-]$', rongpai):
            raise InvalidOperationError(rongpai)
        rongpai = rongpai[0:2] + rongpai[-1]

    h_max = None

    # 状況役の一覧を作成
    pre_hupai = get_pre_hupai(param['hupai'])

    # 懸賞役の一覧を作成
    post_hupai = get_post_hupai(shoupai, rongpai, param['baopai'], param.get('fubaopai'))

    # 和了形を求め、すべての和了形について以下を実行する
    for mianzi in hule_mianzi(shoupai, rongpai):

        # 符を計算する
        hudi = get_hudi(mianzi, param['zhuangfeng'], param['menfeng'])

        # 和了形を判定する
        hupai = get_hupai(mianzi, hudi, pre_hupai, post_hupai, param['rule'])

        # 和了点を計算する
        rv = get_defen(hudi['fu'], hupai, rongpai, param)

        # 最も和了点の高い和了形を選択する。
        # 和了点が同じ場合は、より翻数の多い方を(役満があればそれを)
        # 翻数も同じ場合はより符の高い方を選択する
        if (not h_max or rv['defen'] > h_max['defen'] or rv['defen'] == h_max['defen']
                and (not rv['fanshu'] or rv['fanshu'] > h_max['fanshu']
                     or rv['fanshu'] == h_max['fanshu'] and rv['fu'] > h_max['fu'])):
            h_max = rv

    return h_max


def hule_param(param: dict[str, Any] = {}):
    """点数計算に関する各種パラメータを取得"""

    rv = {
        'rule': param.get('rule') or rule(),
        'zhuangfeng': param.get('zhuangfeng') or 0,
        'menfeng': param['menfeng'] if 'menfeng' in param else 1,
        'hupai': {
            'lizhi': param.get('lizhi') or 0,
            'yifa': param.get('yifa') or False,
            'qianggang': param.get('qianggang') or False,
            'lingshang': param.get('lingshang') or False,
            'haidi': param.get('haidi') or 0,
            'tianhu': param.get('tianhu') or 0
        },
        'baopai': param['baopai'][:] if 'baopai' in param else [],
        'fubaopai': param['fubaopai'][:] if 'fubaopai' in param else [],
        'jicun': {
            'changbang': param.get('changbang') or 0,
            'lizhibang': param.get('lizhibang') or 0
        }
    }

    return rv
