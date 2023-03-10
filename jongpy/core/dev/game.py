"""jongpy.core.dev.game"""

import re
from typing import Callable

import jongpy.core as majiang


def make_shan(rule: dict, log: list[dict]):

    def set_qipai(paistr: str):
        nonlocal shan
        nonlocal zimo_idx
        for suitstr in re.findall(r'[mpsz]\d+', paistr):
            s = suitstr[0]
            for n in re.findall(r'\d', suitstr):
                zimo_idx -= 1
                shan._pai[zimo_idx] = s + n

    shan = majiang.Shan(rule)
    for i in range(len(shan._pai)):
        shan._pai[i] = '_'

    zimo_idx = len(shan._pai)
    gang_idx = 0
    baopai = []
    fubaopai = []

    for data in log:
        if 'qipai' in data:
            for i in range(4):
                set_qipai(data['qipai']['shoupai'][i])
            if data['qipai'].get('baopai'):
                baopai.append(data['qipai']['baopai'])
        elif 'zimo' in data:
            zimo_idx -= 1
            shan._pai[zimo_idx] = data['zimo']['p']
        elif 'gangzimo' in data:
            shan._pai[gang_idx] = data['gangzimo']['p']
            gang_idx += 1
        elif 'kaigang' in data:
            baopai.append(data['kaigang']['baopai'])
        elif 'hule' in data and data['hule'].get('fubaopai'):
            fubaopai = data['hule']['fubaopai']

    for i in range(len(baopai)):
        shan._pai[4 + i] = baopai[i]
    for i in range(len(fubaopai)):
        shan._pai[9 + i] = fubaopai[i]

    shan._baopai = [shan._pai[4]]
    shan._fubaopai = [shan._pai[9]]

    return shan


def make_reply(i: int, log: list[dict]):

    reply = []

    for data in log:
        if 'zimo' in data or 'gangzimo' in data:
            reply.append({})
        elif 'dapai' in data:
            reply.append({'dapai': data['dapai']['p']} if i == data['dapai']['l'] else {})
        elif 'fulou' in data:
            reply.append({'fulou': data['fulou']['m']} if i == data['fulou']['l'] else {})
        elif 'gang' in data:
            reply.append({'gang': data['gang']['m']} if i == data['gang']['l'] else {})
        elif 'pingju' in data:
            if data['pingju']['shoupai'][i]:
                if re.search(r'^三家和', data['pingju']['name']):
                    reply.append({'hule': '-'})
                else:
                    reply.append({'daopai': '-'})
        elif 'hule' in data:
            if i == data['hule']['l']:
                reply.append({'hule': '-'})

    return reply


class Player:
    def __init__(self):
        self._reply = []

    def action(self, msg: dict, callback: Callable | None = None):
        if callback is not None:
            callback(self._reply.pop(0) if self._reply else None)


class Game(majiang.Game):
    def __init__(self, script: dict, rule: dict):

        def f(paipu):
            pass

        super().__init__([Player() for _ in range(4)], f, rule)
        self._model['title'] = script['title']
        self._model['player'] = script['player']
        self._script = script

    def kaiju(self):
        super().kaiju(self._script.get('qijia'))

    def qipai(self):
        log = self._script['log'].pop(0)
        for i in range(4):
            id = (self._model['qijia'] + self._model['jushu'] + i) % 4
            self._players[id]._reply = make_reply(i, log)
        super().qipai(make_shan(self._rule, log))
