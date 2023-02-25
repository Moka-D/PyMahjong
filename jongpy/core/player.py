"""jongpy.core.player"""

import re
from abc import ABCMeta, abstractclassmethod
from typing import Callable, Any

from jongpy.core.shoupai import Shoupai
from jongpy.core.he import He
from jongpy.core.game import Game
from jongpy.core.board import Board, Shan
from jongpy.core.xiangting import xiangting, tingpai


class Player(metaclass=ABCMeta):
    """プレイヤー抽象クラス"""

    def __init__(self) -> None:
        self._model = Board()
        self._callback = None

    def action(self, msg: dict[str, dict], callback: Callable | None = None):
        """メッセージの処理"""

        self._callback = callback

        if 'kaiju' in msg:
            self.kaiju(msg['kaiju'])
        elif 'qipai' in msg:
            self.qipai(msg['qipai'])
        elif 'zimo' in msg:
            self.zimo(msg['zimo'])
        elif 'dapai' in msg:
            self.dapai(msg['dapai'])
        elif 'fulou' in msg:
            self.fulou(msg['fulou'])
        elif 'gang' in msg:
            self.gang(msg['gang'])
        elif 'gangzimo' in msg:
            self.zimo(msg['gangzimo'], True)
        elif 'kaigang' in msg:
            self.kaigang(msg['kaigang'])
        elif 'hule' in msg:
            self.hule(msg['hule'])
        elif 'pingju' in msg:
            self.pingju(msg['pingju'])
        elif 'jieju' in msg:
            self.jieju(msg['jieju'])

    @property
    def shoupai(self) -> Shoupai | None:
        """手牌"""
        return self._model.shoupai[self._menfeng]

    @property
    def he(self) -> He | None:
        """河"""
        return self._model.he[self._menfeng]

    @property
    def shan(self) -> Shan | None:
        """山"""
        return self._model.shan

    @property
    def hulepai(self):
        """和了牌の一覧"""
        return xiangting(self.shoupai) == 0 and tingpai(self.shoupai) or []

    def kaiju(self, kaiju: dict[str, Any]):
        """
        開局処理

        Parameters
        ----------
        kaiju : dict
            開局通知メッセージ
        """

        self._id = kaiju['id']
        self._rule = kaiju['rule']
        self._model.kaiju(kaiju)

        if self._callback is not None:
            self.action_kaiju(kaiju)

    def qipai(self, qipai: dict[str, Any]):
        """
        配牌処理

        Parameters
        ----------
        qipai : dict
            配牌通知メッセージ
        """

        self._model.qipai(qipai)
        self._menfeng = self._model.menfeng(self._id)
        self._diyizimo = True
        self._n_gang = 0
        self._neng_rong = True

        if self._callback is not None:
            self.action_qipai(qipai)

    def zimo(self, zimo: dict[str, int | str], gangzimo: bool = False):
        """
        ツモ処理

        Parameters
        ----------
        zimo : dict
            ツモ通知メッセージ
        gangzimo : bool, default False
            槓ツモかどうか
        """

        self._model.zimo(zimo)
        if gangzimo:
            self._n_gang += 1

        if self._callback is not None:
            self.action_zimo(zimo, gangzimo)

    def dapai(self, dapai: dict[str, int | str]):
        """
        打牌処理

        Parameters
        ----------
        dapai : dict
            打牌通知メッセージ
        """

        if dapai['l'] == self._menfeng:
            if not self.shoupai.lizhi:
                self._neng_rong = True

        self._model.dapai(dapai)

        if self._callback is not None:
            self.action_dapai(dapai)

        if dapai['l'] == self._menfeng:
            self._diyizimo = False
            if [p for p in self.hulepai if self.he.find(p)]:
                self._neng_rong = False
        else:
            s = dapai['p'][0]
            n = int(dapai['p'][1]) or 5
            if [p for p in self.hulepai if p == s + str(n)]:
                self._neng_rong = False

    def fulou(self, fulou: dict[str, int | str]):
        """
        副露処理

        Parameters
        ----------
        fulou : dict
            副露通知メッセージ
        """

        self._model.fulou(fulou)

        if self._callback is not None:
            self.action_fulou(fulou)

        self._diyizimo = False

    def gang(self, gang: dict[str, int | str]):
        """
        槓処理

        Parameters
        ----------
        gang : dict
            槓通知メッセージ
        """

        self._model.gang(gang)

        if self._callback is not None:
            self.action_gang(gang)

        self._diyizimo = False
        if gang['l'] != self._menfeng and re.search(r'^[mpsz]\d{4}$', gang['m']) is None:
            s = gang['m'][0]
            n = int(gang['m'][-1]) or 5
            if [p for p in self.hulepai if p == s + str(n)]:
                self._neng_rong = False

    def kaigang(self, kaigang: dict[str, str]):
        """
        開槓処理

        Parameters
        ----------
        kaigang : dict
            開槓通知メッセージ
        """
        self._model.kaigang(kaigang)

    def hule(self, hule: dict[str, Any]):
        """
        和了処理

        Parameters
        ----------
        hule : dict
            和了通知メッセージ
        """
        self._model.hule(hule)
        if self._callback is not None:
            self.action_hule(hule)

    def pingju(self, pingju: dict[str, Any]):
        """
        流局処理

        Parameters
        ----------
        pingju : dict
            流局通知メッセージ
        """
        self._model.pingju(pingju)
        if self._callback is not None:
            self.action_pingju(pingju)

    def jieju(self, paipu: dict):
        """
        終局処理

        Parameters
        ----------
        paipu : dict
            牌譜
        """
        self._model.jieju(paipu)
        self._paipu = paipu
        if self._callback is not None:
            self.action_jieju(paipu)

    def get_dapai(self, shoupai: Shoupai):
        """打牌候補の一覧"""
        return Game.get_dapai_(self._rule, shoupai)

    def get_chi_mianzi(self, shoupai: Shoupai, p: str):
        """チー候補面子の一覧"""
        return Game.get_chi_mianzi_(self._rule, shoupai, p, self.shan.paishu)

    def get_peng_mianzi(self, shoupai: Shoupai, p: str):
        """ポン候補面子の一覧"""
        return Game.get_peng_mianzi_(self._rule, shoupai, p, self.shan.paishu)

    def get_gang_mianzi(self, shoupai: Shoupai, p: str | None = None):
        """カン候補面子の一覧"""
        return Game.get_gang_mianzi_(self._rule, shoupai, p, self.shan.paishu, self._n_gang)

    def allow_lizhi(self, shoupai: Shoupai, p: str | None = None):
        """立直可能な牌の一覧"""
        return Game.allow_lizhi_(self._rule, shoupai, p, self.shan.paishu, self._model.defen[self._id])

    def allow_hule(self, shoupai: Shoupai, p: str, hupai: bool = False):
        """和了可能かどうか"""
        hupai = hupai or shoupai.lizhi or self.shan.paishu == 0
        return Game.allow_hule_(self._rule, shoupai, p, self._model.zhuangfeng, self._menfeng, hupai, self._neng_rong)

    def allow_pingju(self, shoupai: Shoupai):
        """九種九牌流局可能かどうか"""
        return Game.allow_pingju_(self._rule, shoupai, self._diyizimo)

    def allow_no_daopai(self, shoupai: Shoupai):
        """ノーテン宣言可能かどうか"""
        return Game.allow_no_daopai(self._rule, shoupai, self.shan.paishu)

    @ abstractclassmethod
    def action_kaiju(self, kaiju):
        pass

    @ abstractclassmethod
    def action_qipai(self, qipai):
        pass

    @ abstractclassmethod
    def action_zimo(self, zimo, gangzimo):
        pass

    @ abstractclassmethod
    def action_dapai(self, dapai):
        pass

    @ abstractclassmethod
    def action_fulou(self, fulou):
        pass

    @ abstractclassmethod
    def action_gang(self, gang):
        pass

    @ abstractclassmethod
    def action_hule(self, hule):
        pass

    @ abstractclassmethod
    def action_pingju(self, pingju):
        pass

    @ abstractclassmethod
    def action_jieju(self, paipu):
        pass
