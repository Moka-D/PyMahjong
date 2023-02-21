"""jongpy.core.game"""

from __future__ import annotations

import re
import datetime
import copy
from typing import Callable, Any, TYPE_CHECKING

from jongpy.core.shoupai import Shoupai
from jongpy.core.rule import rule
from jongpy.core.xiangting import tingpai, xiangting
from jongpy.core.hule import hule_mianzi, hule

if TYPE_CHECKING:
    from jongpy.core.player import Player


class Game:
    """ゲーム管理クラス"""

    def __init__(
        self,
        players: list[Player],
        callback: Callable,
        rule_: dict | None = None,
        title: str | None = None
    ) -> None:

        # 指定されたパラメータをインスタンス変数に設定
        self._players = players
        self._callback = callback
        self._rule = rule_ or rule()    # 省略時はデフォルトのルールを使用

        self._model = {
            'title': title or 'PyMahjong' + datetime.datetime.now().strftime('%Y/%m/%d %H:%M%S'),
            'player': ['自家', '下家', '対面', '上家'],
            'qijia': 0,
            'zhuangfeng': 0,
            'jishu': 0,
            'changbang': 0,
            'lizhibang': 0,
            'defen': [self._rule['origin_points']] * 4,
            'shan': None,
            'shoupai': [],
            'he': [],
            'player_id': [0, 1, 2, 3]
        }

        self._view = None

        self._status = None
        self._reply = []

        self._sync = False
        self._stop = None
        self._speed = 3
        self._wait = 0
        self._timeout_id = None

        self._handler = None

    @property
    def model(self):
        return self._model

    @property
    def view(self):
        return self._view

    @view.setter
    def view(self, view):
        self._view = view

    @property
    def speed(self):
        return self._speed

    @speed.setter
    def speed(self, speed: int):
        self._speed = speed

    @property
    def wait(self):
        return self._wait

    @wait.setter
    def wait(self, wait):
        self._wait = wait

    @property
    def handler(self):
        return self._handler

    @handler.setter
    def handler(self, callback: Callable):
        self._handler = callback

    def add_paipu(self, paipu: dict):
        pass

    def delay(self, callback: Callable, timeout: int | None):
        pass

    def stop(self, callback: Callable):
        self._stop = callback

    def start(self):
        pass

    def notify_players(self, type, msg):
        pass

    def call_players(self, type, msg, timeout):
        pass

    def reply(self, id, reply):
        pass

    def next(self):
        pass

    def do_sync(self):
        pass

    def kaiju(self, qijia):
        pass

    def qipai(self, shan):
        pass

    def zimo(self):
        pass

    def dapai(self, dapai):
        pass

    def fulou(self, fulou):
        pass

    def gang(self, gang):
        pass

    def gangzimo(self):
        pass

    def kaigang(self):
        pass

    def hule(self):
        pass

    def pingju(self, name, shoupai=['', '', '', '']):
        pass

    def last(self):
        pass

    def jieju(self):
        pass

    def get_reply(self, i):
        pass

    def reply_kaiju(self):
        pass

    def reply_qipai(self):
        pass

    def reply_zimo(self):
        pass

    def reply_dapai(self):
        pass

    def reply_fulou(self):
        pass

    def reply_gang(self):
        pass

    def reply_hule(self):
        pass

    def reply_pingju(self):
        pass

    def get_dapai(self):
        pass

    def get_chi_mianzi(self, i):
        pass

    def get_peng_mianzi(self, i):
        pass

    def get_gang_mianzi(self, i):
        pass

    def allow_lizhi(self, p):
        pass

    def allow_hule(self, i):
        pass

    def allow_pingju(self):
        pass

    @staticmethod
    def get_dapai_(rule_: dict[str, Any], shoupai: Shoupai):

        if rule_['allow_fulou_slide'] == 0:
            return shoupai.get_dapai(True)
        if rule_['allow_fulou_slide'] == 1 and shoupai._zimo and len(shoupai._zimo) > 2:
            deny = shoupai._zimo[0] + str(int(re.search(r'\d(?=[\+\=\-])', shoupai._zimo).group()) or 5)
            return [p for p in shoupai.get_dapai(False) if p.replace('0', '5') != deny]
        return shoupai.get_dapai(False)

    @staticmethod
    def get_chi_mianzi_(rule_: dict[str, Any], shoupai: Shoupai, p: str, paishu: int):

        mianzi = shoupai.get_chi_mianzi(p, rule_['allow_fulou_slide'] == 0)
        if not mianzi:
            return mianzi
        if rule_['allow_fulou_slide'] == 1 and len(shoupai._fulou) == 3 and shoupai._bingpai[p[0]][int(p[1])] == 2:
            mianzi = []
        return [] if paishu == 0 else mianzi

    @staticmethod
    def get_peng_mianzi_(rule_: dict[str, Any], shoupai: Shoupai, p: str, paishu: int):

        mianzi = shoupai.get_peng_mianzi(p)
        if not mianzi:
            return mianzi
        return [] if paishu == 0 else mianzi

    @staticmethod
    def get_gang_mianzi_(rule_: dict[str, Any], shoupai: Shoupai, p: str | None, paishu: int, n_gang: int):

        mianzi = shoupai.get_gang_mianzi(p)
        if not mianzi:
            return mianzi

        if shoupai.lizhi:
            if rule_['allow_angang_after_lizhi'] == 0:
                return []
            elif rule_['allow_angang_after_lizhi'] == 1:
                new_shoupai = copy.copy(shoupai).dapai(shoupai._zimo)
                n_hule1 = 0
                n_hule2 = 0
                for p in tingpai(new_shoupai):
                    n_hule1 += len(hule_mianzi(new_shoupai, p))
                new_shoupai = copy.copy(shoupai).gang(mianzi[0])
                for p in tingpai(new_shoupai):
                    n_hule2 += len(hule_mianzi(new_shoupai, p))
                if n_hule1 > n_hule2:
                    return []
            else:
                new_shoupai = copy.copy(shoupai).dapai(shoupai._zimo)
                n_tingpai1 = len(tingpai(new_shoupai))
                new_shoupai = copy.copy(shoupai).gang(mianzi[0])
                if xiangting(new_shoupai) > 0:
                    return []
                n_tingpai2 = len(tingpai(new_shoupai))
                if n_tingpai1 > n_tingpai2:
                    return []

        return [] if paishu == 0 or n_gang == 4 else mianzi

    @staticmethod
    def allow_lizhi_(rule_: dict[str, Any], shoupai: Shoupai, p: str | None, paishu: int, defen: int):

        if shoupai._zimo is None:
            return False
        if shoupai.lizhi:
            return False
        if not Shoupai.menqian:
            return False

        if not rule_['lizhi_no_zimo'] and paishu < 4:
            return False
        if rule_['minus_interruption'] and defen < 1000:
            return False

        if xiangting(shoupai) > 0:
            return False

        if p:
            new_shoupai = copy.copy(shoupai).dapai(p)
            return xiangting(new_shoupai) == 0 and len(tingpai(new_shoupai)) > 0
        else:
            dapai = []
            for p in Game.get_dapai_(rule_, shoupai):
                new_shoupai = copy.copy(shoupai).dapai(p)
                if xiangting(new_shoupai) == 0 and len(tingpai(new_shoupai)) > 0:
                    dapai.append(p)
            return dapai if len(dapai) else False

    @staticmethod
    def allow_hule_(
        rule_: dict[str, Any],
        shoupai: Shoupai,
        p: str | None,
        zhuangfeng: int,
        menfeng: int,
        hupai: bool,
        neng_rong: bool
    ) -> bool:

        if p and not neng_rong:
            return False

        new_shoupai = copy.copy(shoupai)
        if p:
            new_shoupai.zimo(p)
        if xiangting(new_shoupai) != -1:
            return False

        if hupai:
            return True

        param = {
            'rule': rule_,
            'zhuangfeng': zhuangfeng,
            'menfeng': menfeng,
            'hupai': {},
            'baopai': [],
            'jicun': {'changbang': 0, 'lizhibang': 0}
        }
        h = hule(shoupai, p, param)

        return h['hupai'] is not None

    @staticmethod
    def allow_pingju_(rule_: dict[str, Any], shoupai: Shoupai, diyizimo: str) -> bool:

        if not (diyizimo and shoupai._zimo):
            return False
        if not rule_['interrupted_pingju']:
            return False

        n_yaojiu = 0
        for s in ['m', 'p', 's', 'z']:
            bingpai = shoupai._bingpai[s]
            nn = [1, 2, 3, 4, 5, 6, 7] if s == 'z' else [1, 9]
            for n in nn:
                if bingpai[n] > 0:
                    n_yaojiu += 1
        return n_yaojiu >= 9

    @staticmethod
    def allow_no_daopai(rule_: dict[str, Any], shoupai: Shoupai, paishu: int) -> bool:

        if paishu > 0 or shoupai._zimo:
            return False
        if not rule_['declare_no_tingpai']:
            return False
        if shoupai.lizhi:
            return False

        return xiangting(shoupai) == 0 and len(tingpai(shoupai)) > 0
