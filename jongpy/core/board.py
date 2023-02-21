"""jongpy.core.board"""

import re
from typing import Any

from jongpy.core.shoupai import Shoupai
from jongpy.core.he import He


class Shan:
    def __init__(self, baopai: str):
        self.paishu = 136 - 13 * 4 - 14
        self.baopai = [baopai]
        self.fubaopai = None

    def zimo(self, p: str | None):
        self.paishu -= 1
        return p or '_'

    def kaigang(self, baopai: str):
        self.baopai.append(baopai)


class Board:
    """卓定義クラス"""

    title: str
    player: list[str]
    qijia: int
    zhuangfeng: int
    jushu: int
    changbang: int
    lizhibang: int
    defen: list[int | None]
    shan: Shan | None
    shoupai: list[Shoupai | None]
    he: list[He | None]
    player_id: list[int]
    lunban: int
    _lizhi: bool | None
    _fenpei: list[int] | None

    def __init__(self, kaiju: dict[str, Any] | None = None):
        if kaiju is not None:
            self.kaiju(kaiju)

    def kaiju(self, kaiju: dict[str, Any]):

        self.title = kaiju.get('title')
        self.player = kaiju.get('player')
        self.qijia = kaiju.get('qijia')

        self.zhuangfeng = 0
        self.jushu = 0
        self.changbang = 0
        self.lizhibang = 0
        self.defen = [None, None, None, None]
        self.shan = None
        self.shoupai = [None, None, None, None]
        self.he = [None, None, None, None]
        self.player_id = [0, 1, 2, 3]
        self.lunban = -1

        self._lizhi = None
        self._fenpei = None

    def menfeng(self, id: int) -> int:
        return (id + 4 - self.qijia + 4 - self.jushu) % 4

    def qipai(self, qipai: dict[str, Any]):
        self.zhuangfeng = qipai['zhuangfeng']
        self.jushu = qipai['jushu']
        self.changbang = qipai['changbang']
        self.lizhibang = qipai['lizhibang']
        self.shan = Shan(qipai['baopai'])
        for i in range(4):
            paistr = qipai['shoupai'][i] or '_' * 13
            self.shoupai[i] = Shoupai.from_str(paistr)
            self.he[i] = He()
            self.player_id[i] = (self.qijia + self.jushu + i) % 4
            self.defen[self.player_id[i]] = qipai['defen'][i]
        self.lunban = -1

        self._lizhi = False
        self._fenpei = None

    def lizhi(self):
        if self._lizhi:
            self.defen[self.player_id[self.lunban]] -= 1000
            self.lizhibang += 1
            self._lizhi = False

    def zimo(self, zimo: dict[str, int | str]):
        self.lizhi()
        self.lunban = zimo['l']
        self.shoupai[zimo['l']].zimo(self.shan.zimo(zimo['p']), False)

    def dapai(self, dapai: dict[str, int | str]):
        self.lunban = dapai['l']
        self.shoupai[dapai['l']].dapai(dapai['p'], False)
        self.he[dapai['l']].dapai(dapai['p'])
        self._lizhi = dapai['p'][-1] == '*'

    def fulou(self, fulou: dict[str, int | str]):
        self.lizhi()
        self.he[self.lunban].fulou(fulou['m'])
        self.lunban = fulou['l']
        self.shoupai[fulou['l']].fulou(fulou['m'], False)

    def gang(self, gang: dict[str, int | str]):
        self.lunban = gang['l']
        self.shoupai[gang['l']].gang(gang['m'], False)

    def kaigang(self, kaigang: dict[str, str]):
        self.shan.kaigang(kaigang['baopai'])

    def hule(self, hule: dict[str, Any]):
        shoupai = self.shoupai[hule['l']]
        shoupai.update(hule['shoupai'])
        if hule.get('baojia') is not None:
            shoupai.dapai(shoupai.get_dapai().pop())
        if self._fenpei is not None:
            self.changbang = 0
            self.lizhibang = 0
            for i in range(4):
                self.defen[self.player_id[i]] += self._fenpei[i]
        self.shan.fubaopai = hule['fubaopai']
        self._fenpei = hule.get('fenpei')

    def pingju(self, pingju: dict[str, Any]):
        if re.search(r'^三家和', pingju['name']) is None:
            self.lizhi()
        for i in range(4):
            if pingju['shoupai'][i]:
                self.shoupai[i].update(pingju['shoupai'][i])

    def jieju(self, paipu: dict):
        for id in range(4):
            self.defen[id] = paipu['defen'][id]
        self.lunban -= 1
