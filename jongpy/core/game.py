"""jongpy.core.game"""

from __future__ import annotations

import re
import datetime
import random
import json
import asyncio
import time
from decimal import Decimal, ROUND_HALF_UP
from typing import Callable, Any, TYPE_CHECKING

from jongpy.core.shoupai import Shoupai
from jongpy.core.shan import Shan
from jongpy.core.he import He
from jongpy.core.rule import rule
from jongpy.core.xiangting import tingpai, xiangting
from jongpy.core.hule import hule_mianzi, hule

if TYPE_CHECKING:
    from jongpy.core.player import Player


def wrap_with_delay(sec: float, callback: Callable, *args):
    time.sleep(sec)
    callback(*args)


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
            'jushu': 0,
            'changbang': 0,
            'lizhibang': 0,
            'defen': [self._rule['origin_points']] * 4,
            'shan': None,
            'shoupai': [None] * 4,
            'he': [None] * 4,
            'player_id': [0, 1, 2, 3]
        }

        self._view = None

        self._status = None
        self._reply = []

        self._sync = False
        self._stop = None
        self._speed = 3
        self._wait = 0
        self._loop = None
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
        self._paipu['log'][-1].append(paipu)

    def set_timeout(self, timeout: int, callback: Callable, *args):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_in_executor(None, wrap_with_delay, timeout / 1000, callback, *args)
        return loop

    def clear_timeout(self):
        if self._loop is not None:
            self._loop.stop()
            self._loop.close()
            self._loop = None

    def delay(self, callback: Callable, timeout: int | None = None, loop=None):

        if self._sync:
            return callback()

        timeout = (0 if self._speed == 0
                   else max(500, self._speed * 200) if timeout is None
                   else timeout)
        self.set_timeout(timeout, callback)

    def stop(self, callback: Callable | None = None):

        def f():
            return

        self._stop = f if callback is None else callback

    def start(self):
        if self._loop is not None:
            return
        self._stop = None
        self._loop = self.set_timeout(0, lambda: self.next())

    def notify_players(self, type: str, msg: list[dict]):
        """
        プレイヤーへメッセージの通知(callbackなし)

        Parameters
        ----------
        type : str
            通知メッセージの種別
        msg : list[dict]
            通知メッセージの配列
        """

        # 東家から順番に対局者にメッセージを送信する
        for i in range(4):
            id = self._model['player_id'][i]
            if self._sync:
                # 同期モードの場合は直接 action メソッドを呼び出す
                self._players[id].action(msg[i])
            else:
                self.set_timeout(0, self._players[id].action, msg[i])

    def call_players(self, type: str, msg: list[dict], timeout: int | None = None):
        """
        プレイヤーへメッセージの通知(callbackあり)

        Parameters
        ----------
        type : str
            通知メッセージの種別
        msg : list[dict]
            通知メッセージの配列
        timeout : int or None, default None
            next関数呼び出しまでの待ち時間
        """

        # timeoutの設定
        timeout = (0 if self._speed == 0
                   else self._speed * 200 if timeout is None
                   else timeout)

        # メッセージ種別を保存
        self._status = type

        # 応答を保存する配列を初期化
        self._reply = [None] * 4

        # 東家から順に対局者にメッセージを送信する
        for i in range(4):
            id = self._model['player_id'][i]
            if self._sync:
                # 同期モードの場合は直接 action メソッドを呼び出す
                self._players[id].action(msg[i], lambda reply: self.reply(id, reply))
            else:
                self.set_timeout(0, self._players[id].action, msg[i], lambda reply: self.reply(id, reply))

        if not self._sync:
            self._loop = self.set_timeout(timeout, self.next)

    def reply(self, id: int, reply: dict | None = None):
        """
        プレイヤーからの応答を処理

        Parameters
        ----------
        id : int
            対局者の席順
        reply : dict (or None)
            応答メッセージ
        """

        # 応答を格納
        self._reply[id] = reply or {}

        # 非同期モードですでに next() が呼ばれた後の場合、4人目の応答を契機に
        # 再度 next() を呼び出す
        if self._sync:
            return
        if len([x for x in self._reply if x is not None]) < 4:
            return
        if not self._loop:
            self._loop = self.set_timeout(0, self.next)

    def next(self):
        """対局者からの応答を読み出し、次のステップに遷移"""

        # 呼び出しタイマーのクリア
        self.clear_timeout()

        # 4人分の応答がそろっていない場合は以降の処理は行わない
        if len([x for x in self._reply if x is not None]) < 4:
            return

        # 外部から停止要求があった場合は停止する
        if self._stop is not None:
            return self._stop()

        # メッセージに対応した状態遷移メソッドを呼び出す
        if self._status == 'kaiju':
            self.reply_kaiju()  # 開局
        elif self._status == 'qipai':
            self.reply_qipai()  # 配牌
        elif self._status == 'zimo':
            self.reply_zimo()   # 自摸
        elif self._status == 'dapai':
            self.reply_dapai()  # 打牌
        elif self._status == 'fulou':
            self.reply_fulou()  # 副露
        elif self._status == 'gang':
            self.reply_gang()   # 槓
        elif self._status == 'gangzimo':
            self.reply_zimo()   # 槓自摸
        elif self._status == 'hule':
            self.reply_hule()   # 和了
        elif self._status == 'pingju':
            self.reply_pingju()     # 流局
        else:
            self._callback(self._paipu)

    def do_sync(self):
        """同期モードで実行"""

        self._sync = True

        self.kaiju()

        while True:
            if self._status == 'kaiju':
                self.reply_kaiju()
            elif self._status == 'qipai':
                self.reply_qipai()
            elif self._status == 'zimo':
                self.reply_zimo()
            elif self._status == 'dapai':
                self.reply_dapai()
            elif self._status == 'fulou':
                self.reply_fulou()
            elif self._status == 'gang':
                self.reply_gang()
            elif self._status == 'gangzimo':
                self.reply_zimo()
            elif self._status == 'hule':
                self.reply_hule()
            elif self._status == 'pingju':
                self.reply_pingju()
            else:
                break

        self._callback(self._paipu)

        return self

    def kaiju(self, qijia: int | None = None):
        """
        対局の開始

        Parameters
        ----------
        qijia : int (or None)
            起家の指定
        """

        # 1. 卓情報を更新
        self._model['qijia'] = qijia if qijia is not None else random.randrange(4)  # 起家を決定する
        # ルールに従い最大局数を決定する
        self._max_jushu = 0 if self._rule['n_zhuang'] == 0 else self._rule['n_zhuang'] * 4 - 1

        # 2. 牌譜を追加
        self._paipu = {     # 牌譜を初期状態にする
            'title': self._model['title'],
            'player': self._model['player'],
            'qijia': self._model['qijia'],
            'log': [],
            'defen': self._model['defen'][:],
            'point': [],
            'rank': []
        }

        # 3. 対局者に通知メッセージを送信する
        msg = [{}] * 4
        for id in range(4):
            msg[id] = json.loads(json.dumps({
                'kaiju': {
                    'id': id,   # 席順
                    'rule': self._rule,     # ルール
                    'title': self._paipu['title'],  # 牌譜のタイトル
                    'player': self._paipu['player'],    # 対局者情報
                    'qijia': self._paipu['qijia']   # 起家
                }
            }))
        self.call_players('kaiju', msg, 0)

        # 4. (必要であれば)描画を指示する
        if self._view is not None:
            self._view.kaiju()

    def qipai(self, shan: Shan | None = None):
        """
        配牌の局進行を行う

        Parameters
        ----------
        shan : jongpy.core.Shan (or None)
            牌山
        """

        # 1. 卓情報の更新
        model = self._model
        model['shan'] = shan or Shan(self._rule)    # 牌山を生成

        for i in range(4):  # 東家から順に処理
            qipai = []
            for _ in range(13):
                qipai.append(model['shan'].zimo())  # 牌山から13枚取り出し配牌とする

            model['shoupai'][i] = Shoupai(qipai)    # 配牌で手牌を初期化
            model['he'][i] = He()   # 捨て牌を初期化
            model['player_id'][i] = (model['qijia'] + model['jushu'] + i) % 4

        model['lunban'] = -1    # 手版を初期化

        # その他のインスタンス変数に初期値を設定する
        self._diyizimo = True
        self._fengpai = self._rule['interrupted_pingju']

        self._dapai = None
        self._gang = None

        self._lizhi = [0] * 4
        self._yifa = [False] * 4
        self._n_gang = [0] * 4
        self._neng_rong = [True] * 4

        self._hule = []
        self._hule_option = None
        self._no_game = False
        self._lianzhuang = False
        self._changbang = model['changbang']
        self._fenpei = None

        # 2. 牌譜を追加する
        self._paipu['defen'] = model['defen'][:]
        self._paipu['log'].append([])
        paipu = {
            'qipai': {
                'zhuangfeng': model['zhuangfeng'],  # 場風
                'jushu': model['jushu'],    # 局数
                'changbang': model['changbang'],    # 本場
                'lizhibang': model['lizhibang'],    # 供託リーチ棒の数
                'defen': list(map(lambda id: model['defen'][id], model['player_id'])),  # 持ち点
                'baopai': model['shan'].baopai[0],  # ドラ表示牌
                'shoupai': list(map(lambda shoupai: str(shoupai), model['shoupai']))    # 配牌
            }
        }
        self.add_paipu(paipu)

        # 3. 対局者に通知メッセージを送信する
        msg = [{}] * 4
        for i in range(4):
            msg[i] = json.loads(json.dumps(paipu))
            for j in range(4):
                if j != i:
                    msg[i]['qipai']['shoupai'][j] = ''  # 他の対局者はマスクする

        self.call_players('qipai', msg, 0)

        # 4. (必要であれば)描画を指示する
        if self._view is not None:
            self._view.redraw()

    def zimo(self):
        """ツモの局進行を行う"""

        # 1. 卓情報の更新
        model = self._model

        model['lunban'] = (model['lunban'] + 1) % 4

        zimo = model['shan'].zimo()     # 牌山から1枚取り出す
        model['shoupai'][model['lunban']].zimo(zimo)    # それを手に加える

        # 2. 牌譜を追加する
        paipu = {'zimo': {'l': model['lunban'], 'p': zimo}}
        self.add_paipu(paipu)

        # 3. 対局者に通知メッセージを送信する
        msg = [{}] * 4
        for i in range(4):
            msg[i] = json.loads(json.dumps(paipu))
            if i != model['lunban']:
                msg[i]['zimo']['p'] = ''    # 他者のツモ牌はマスクする

        self.call_players('zimo', msg)

        # 4. 必要であれば描画する
        if self._view is not None:
            self._view.update(paipu)

    def dapai(self, dapai: str):
        """
        牌``dapai``を打牌する

        Parameters
        ----------
        dapai : str
            牌の文字列表現
        """

        # 1. 卓情報の更新
        model = self._model
        self._yifa[model['lunban']] = False

        if not model['shoupai'][model['lunban']].lizhi:     # リーチ前なら
            self._neng_rong[model['lunban']] = True     # フリテンを解除

        model['shoupai'][model['lunban']].dapai(dapai)  # 手牌から dapai を取り出す
        model['he'][model['lunban']].dapai(dapai)   # dapai を河に捨てる

        if self._diyizimo:  # 第1ツモ巡なら、四風連打が継続中か判定
            if not re.search(r'^z[1234]', dapai):
                self._fengpai = False
            if self._dapai and self._dapai[0:2] != dapai[0:2]:
                self._fengpai = False
        else:
            self._fengpai = False

        if dapai[-1] == '*':    # リーチ宣言の場合
            self._lizhi[model['lunban']] = 2 if self._diyizimo else 1   # ダブルリーチか判定
            self._yifa[model['lunban']] = self._rule['yifa']    # 一発アリルールならフラグをONに

        if (xiangting(model['shoupai'][model['lunban']]) == 0
                and any(map(lambda p: model['he'][model['lunban']].find(p),
                            tingpai(model['shoupai'][model['lunban']])))):
            self._neng_rong[model['lunban']] = False    # フリテン判断する

        self._dapai = dapai     # 最後の打牌を保存

        # 2. 牌譜の追加
        paipu = {'dapai': {'l': model['lunban'], 'p': dapai}}
        self.add_paipu(paipu)

        # 開槓が必要なら行う
        if self._gang:
            self.kaigang()

        # 3. 対局者に通知メッセージを送信する
        msg = [{}] * 4
        for i in range(4):
            msg[i] = json.loads(json.dumps(paipu))
        self.call_players('dapai', msg)

        # 4. 必要であれば描画する
        if self._view is not None:
            self._view.update(paipu)

    def fulou(self, fulou: str):
        """
        面子``fulou``を副露する

        Parameters
        ----------
        fulou : str
            面子の文字列表現
        """

        # 1. 卓情報の更新
        model = self._model
        self._diyizimo = False  # 第1ツモ巡でなくなる
        self._yifa = [False] * 4    # 全員の一発フラグをOFFにする
        model['he'][model['lunban']].fulou(fulou)   # 現在の手番の河から副露牌を取り上げる

        d = re.search(r'[\+\=\-]', fulou)
        if d is None:
            d = '_'
        else:
            d = d.group()
        model['lunban'] = (model['lunban'] + '_-=+'.find(d)) % 4

        model['shoupai'][model['lunban']].fulou(fulou)  # 副露者の手牌に副露面子を加える

        if re.search(r'^[mpsz]\d{4}', fulou):   # 大明槓の場合
            self._gang = fulou  # 未開槓状態にする
            self._n_gang[model['lunban']] += 1  # 副露者のカン数を増やす

        # 2. 牌譜を追加
        paipu = {'fulou': {'l': model['lunban'], 'm': fulou}}
        self.add_paipu(paipu)

        # 3. 対局者に通知メッセージを送信する
        msg = [{}] * 4
        for i in range(4):
            msg[i] = json.loads(json.dumps(paipu))
        self.call_players('fulou', msg)

        # 4. 必要であれば描画する
        if self._view is not None:
            self._view.update(paipu)

    def gang(self, gang):
        """
        面子``gang``で、加槓あるいは暗槓を行う

        Parameters
        ----------
        gang : str
            面子の文字列表現
        """

        # 1. 卓情報の更新
        model = self._model
        model['shoupai'][model['lunban']].gang(gang)

        # 2. 牌譜の追加
        paipu = {'gang': {'l': model['lunban'], 'm': gang}}
        self.add_paipu(paipu)

        # 開槓が必要なら先に行う
        if self._gang:
            self.kaigang()

        self._gang = gang   # 未開槓状態にする
        self._n_gang[model['lunban']] += 1  # カン数を加算する

        # 3. 対局者に通知メッセージを送信する
        msg = [{}] * 4
        for i in range(4):
            msg[i] = json.loads(json.dumps(paipu))
        self.call_players('gang', msg)

        # 4. 必要であれば描画する
        if self._view is not None:
            self._view.update(paipu)

    def gangzimo(self):
        """嶺上牌のツモを行う"""

        # 1. 卓情報の更新
        model = self._model
        self._diyizimo = False  # 第1ツモ巡でなくなる
        self._yifa = [False] * 4    # 全対局者の一発フラグをOFFにする
        zimo = model['shan'].gangzimo()     # 嶺上牌から1枚取り出す
        model['shoupai'][model['lunban']].zimo(zimo)

        # 2. 牌譜を追加
        paipu = {'gangzimo': {'l': model['lunban'], 'p': zimo}}
        self.add_paipu(paipu)

        # カンドラ即乗せ、あるいは暗槓の場合、開槓を行う
        if not self._rule['gang_baopai_delay'] or re.search(r'^[mpsz]\d{4}$', self._gang):
            self.kaigang()

        # 3. 対局者に通知メッセージを送信する
        msg = [{}] * 4
        for i in range(4):
            msg[i] = json.loads(json.dumps(paipu))
            if i != model['lunban']:
                msg[i]['gangzimo']['p'] = ''    # 他者のツモ牌はマスクする
        self.call_players('gangzimo', msg)

        # 4. 必要であれば描画する
        if self._view is not None:
            self._view.update(paipu)

    def kaigang(self):
        """開槓を行う"""

        self._gang = None   # 開槓済みにする

        # カンドラなしのルールの場合は、開槓せずに終了
        if not self._rule['gang_baopai']:
            return

        # 1. 卓情報の更新
        model = self._model
        model['shan'].kaigang()     # 開槓する
        baopai = model['shan'].baopai.pop()     # カンドラ表示牌を取得する

        # 2. 牌譜を追加する
        paipu = {'kaigang': {'baopai': baopai}}
        self.add_paipu(paipu)

        # 3. 対局者に通知メッセージを送信する
        msg = [{}] * 4
        for i in range(4):
            msg[i] = json.loads(json.dumps(paipu))
        self.notify_players('kaigang', msg)

        # 4. 必要であれば描画する
        if self._view is not None:
            self._view.update(paipu)

    def hule(self):
        """和了を行う"""

        # 1. 卓情報の更新
        model = self._model

        # ダブロンの場合、この関数は2回呼び出される
        # 1回目の時だけ以下を行う
        if self._status != 'hule':
            model['shan'].close()   # 裏ドラを見れるようにする
            # 特殊な和了り方か確認する
            self._hule_option = ('qianggang' if self._status == 'gang'  # 槍槓
                                 else 'lingshang' if self._status == 'gangzimo'     # 嶺上開花
                                 else None)     # 通常

        # 和了者を決定する
        # self._hule はロン和了者の一覧なので、それがある場合にはそこから、
        # ない場合は現在の手番を和了者とする
        menfeng = self._hule.pop(0) if len(self._hule) else model['lunban']

        # ロン和了の和了牌を決定する
        # 現在の手番が和了者の倍はツモ和了なので None
        # 槍槓の場合は最後にカンした面子 _gang から、
        # その他の場合は最後に打牌した牌 _dapai から決定する
        rongpai = (None if menfeng == model['lunban']
                   else (self._gang[0] + self._gang[-1] if self._hule_option == 'qianggang'
                         else self._dapai[0:2]) + '_+=-'[(4 + model['lunban'] - menfeng) % 4])

        shoupai = model['shoupai'][menfeng].clone()     # 和了者の手牌を複製
        fubaopai = model['shan'].fubaopai if shoupai.lizhi else None    # リーチしている場合は裏ドラを取得

        # 和了点の計算に必要な手牌以外の情報(状況役など)を収集する
        param = {
            'rule': self._rule,     # ルール
            'zhuangfeng': model['zhuangfeng'],  # 場風
            'menfeng': menfeng,     # 自風(=和了者)
            'hupai': {
                'lizhi': self._lizhi[menfeng],  # 立直
                'yifa': self._yifa[menfeng],    # 一発
                'qianggang': self._hule_option == 'qianggang',  # 槍槓
                'lingshang': self._hule_option == 'lingshang',  # 嶺上開花
                'haidi': (0 if model['shan'].paishu > 0 or self._hule_option == 'lingshang'
                          else 1 if not rongpai     # 海底
                          else 2),  # 河底
                'tianhu': (0 if not (self._diyizimo and not rongpai)
                           else 1 if menfeng == 0   # 天和
                           else 2)      # 地和
            },
            'baopai': model['shan'].baopai,     # ドラ
            'fubaopai': fubaopai,   # 裏ドラ
            'jicun': {'changbang': model['changbang'],  # 積み棒
                      'lizhibang': model['lizhibang']}  # 供託リーチ棒
        }

        # 和了役を判定し、和了点を計算する
        hule_ = hule(shoupai, rongpai, param)

        # 連荘判断する
        if self._rule['continuous_zhuang'] > 0 and menfeng == 0:
            self._lianzhuang = True     # 連荘なし以外のルールで親の和了があれば連荘
        if self._rule['n_zhuang'] == 0:
            self._lianzhuang = False    # 一局戦の場合は連荘なし

        self._fenpei = hule_['fenpei']  # その局の点棒の移動を保存する

        # 2. 牌譜を追加する
        paipu = {
            'hule': {
                'l': menfeng,   # 和了者
                'shoupai': str(shoupai.zimo(rongpai)) if rongpai else str(shoupai),     # 手牌
                'baojia': model['lunban'] if rongpai else None,     # 手牌
                'fubaopai': fubaopai,   # 裏ドラ
                'fu': hule_['fu'],  # 符
                'fanshu': hule_['fanshu'],  # 翻数
                'damanguan': hule_['damanguan'],    # 役満複合数
                'defen': hule_['defen'],    # 和了打点
                'hupai': hule_['hupai'],    # 和了役
                'fenpei': hule_['fenpei']   # 収支
            }
        }
        for key in ['fu', 'fanshu', 'damanguan']:
            if not paipu['hule'][key]:
                del paipu['hule'][key]
        self.add_paipu(paipu)

        # 3. 対局者に通知メッセージを送信
        msg = [{}] * 4
        for i in range(4):
            msg[i] = json.loads(json.dumps(paipu))
        self.call_players('hule', msg, self._wait)

        # 4. 必要であれば描画する
        if self._view is not None:
            self._view.update(paipu)

    def pingju(self, name: str | None = None, shoupai: list[str] | None = None):
        """
        流局の処理を行う

        Parameters
        ----------
        name : str (or None)
            流局理由
        shoupai : list[str]
            牌姿の配列
        """

        if shoupai is None:
            shoupai = [''] * 4

        # 1. 卓情報を更新
        model = self._model
        fenpei = [0] * 4    # 流局による点棒の移動を初期化

        if not name:    # 通常の流局の場合

            # 手牌の公開・非公開を判定し、公開(=テンパイ)の人数をカウントする
            n_tingpai = 0
            for i in range(4):
                if self._rule['declare_no_tingpai'] and not shoupai[i] and not model['shoupai'][i].lizhi:
                    # ノーテン宣言ありの場合、リーチ者以外は対局者の
                    # 非公開の意思に従う
                    continue

                if (not self._rule['penalty_no_tingpai'] and (self._rule['continuous_zhuang'] != 2 or i != 0)
                        and not model['shoupai'][i].lizhi):
                    # ノーテン罰なしのルールの場合、リーチ以外で手牌公開の
                    # 意味があるのはテンパイ連荘のルールのときの親のみ
                    shoupai[i] = ''

                elif xiangting(model['shoupai'][i]) == 0 and len(tingpai(model['shoupai'][i])) > 0:
                    # それ以外でテンパイしている場合は手牌を公開する
                    n_tingpai += 1
                    shoupai[i] = str(model['shoupai'][i])

                    # テンパイ連荘のルールの場合は親がテンパイしていれば連荘が確定する
                    if self._rule['continuous_zhuang'] == 2 and i == 0:
                        self._lianzhuang = True
                else:
                    # ノーテンの場合は手牌は非公開
                    shoupai[i] = ''

            # 流し満貫ありのルールの場合、先に流し満貫の判定と清算を行う
            if self._rule['pingju_manguan']:
                for i in range(4):
                    # 流し満貫の判定を行う
                    # 鳴かれた牌がある場合、幺九牌を打牌している場合は、
                    # 流し満貫は成立しない
                    all_yaojiu = True
                    for p in model['he'][i]._pai:
                        if re.search(r'[\+\=\-]$', p):
                            all_yaojiu = False
                            break
                        if re.search(r'^z', p):
                            continue
                        if re.search(r'^[mps][19]', p):
                            continue
                        all_yaojiu = False
                        break
                    # 流し満貫が成立していれば清算する
                    if all_yaojiu:
                        name = '流し満貫'   # 流局理由を設定する
                        for j in range(4):
                            fenpei[j] += (12000 if i == 0 and j == i
                                          else -4000 if i == 0
                                          else 8000 if i != 0 and j == i
                                          else -4000 if i != 0 and j == 0
                                          else -2000)

            # 流し満貫がない場合、ノーテン罰符の清算を行う
            if not name:
                name = '荒牌平局'   # 流局理由を設定
                if self._rule['penalty_no_tingpai'] and 0 < n_tingpai < 4:
                    # ノーテン罰符ありのルールなら清算する
                    for i in range(4):
                        fenpei[i] = int(3000 / n_tingpai) if shoupai[i] else int(-3000 / (4 - n_tingpai))

            # ノーテン連荘の場合、流局は連荘とする
            if self._rule['continuous_zhuang'] == 3:
                self._lianzhuang = True

        else:   # 途中流局の場合
            self._no_game = True    # 途中流局フラグをONにする
            self._lianzhuang = True     # 途中流局は連荘とする

        # 一局戦の場合、流局は連荘とする
        if self._rule['n_zhuang'] == 0:
            self._lianzhuang = True

        self._fenpei = fenpei  # その局の点棒移動を保存

        # 2. 牌譜を追加する
        paipu = {
            'pingju': {'name': name, 'shoupai': shoupai, 'fenpei': fenpei}
        }
        self.add_paipu(paipu)

        # 3. 対局者に通知メッセージを送信する
        msg = [{}] * 4
        for i in range(4):
            msg[i] = json.loads(json.dumps(paipu))
        self.call_players('pingju', msg, self._wait)

        # 4. 必要であれば描画する
        if self._view is not None:
            self._view.update(paipu)

    def last(self):

        model = self._model

        # (必要であれば)描画を指示する
        model['lunban'] = -1
        if self._view is not None:
            self._view.update()

        # 連荘でなければ次の局に進む
        if not self._lianzhuang:
            model['jushu'] += 1
            model['zhuangfeng'] += int(model['jushu'] / 4) | 0
            model['jushu'] = model['jushu'] % 4

        # 持ち点30,000点以上で持ち点最大の対局者を guanjun に設定する
        # 持ち点同点の場合は起家に近い対局者を上位とする
        jieju = False
        guanjun = -1
        defen = model['defen']
        for i in range(4):
            id = (model['qijia'] + i) % 4
            if defen[id] < 0 and self._rule['minus_interruption']:
                jieju = True    # トビ終了
            if defen[id] >= 30000 and (guanjun < 0 or defen[id] > defen[guanjun]):
                guanjun = id

        sum_jushu = model['zhuangfeng'] * 4 + model['jushu']

        if 15 < sum_jushu:
            jieju = True    # 「返り東」には入らない
        elif (self._rule['n_zhuang'] + 1) * 4 - 1 < sum_jushu:
            jieju = True    # 4局を超えた延長戦は行わない
        elif self._max_jushu < sum_jushu:   # 最終局を超えた場合
            if self._rule['extra_game_method'] == 0:
                jieju = True    # 延長戦なしなら終局
            elif self._rule['n_zhuang'] == 0:
                jieju = True    # 一局戦なら終局
            elif guanjun >= 0:
                jieju = True    # 30,000点越えがいるなら終局
            else:   # さらに延長戦を続ける
                self._max_jushu += (4 if self._rule['extra_game_method'] == 3   # 4局固定延長の場合、最終局を4局先に延ばす
                                    else 1 if self._rule['extra_game_method'] == 2  # 連荘優先サドンデスの場合、1局先に延ばす
                                    else 0)     # その他の場合、延長しない
        elif self._max_jushu == sum_jushu:  # 最終局の場合
            if (self._rule['stop_last_game'] and guanjun == model['player_id'][0]
                    and self._lianzhuang and not self._no_game):
                jieju = True    # オーラス止めの条件を満たせば終局

        if jieju:
            self.delay(lambda: self.jieju(), 0)     # (終局の場合)終局処理を行う
        else:
            self.delay(lambda: self.qipai(), 0)     # (その他なら)配牌に遷移する

    def jieju(self):

        model = self._model

        # 持ち点により着順を決定する。同点の場合は起家に近い方を上位とする
        paiming = []
        defen = model['defen']
        for i in range(4):
            id = (model['qijia'] + i) % 4
            for j in range(4):
                if j == len(paiming) or defen[id] > defen[paiming[j]]:
                    paiming.insert(j, id)
                    break
        # 積み残しの供託リーチ棒はトップの点に加算する
        defen[paiming[0]] += model['lizhibang'] * 1000

        # 牌譜に終了時の持ち点を設定する
        self._paipu['defen'] = defen

        # 牌譜に着順を設定する
        rank = [0] * 4
        for i in range(4):
            rank[paiming[i]] = i + 1
        self._paipu['rank'] = rank

        # 順位点を加えたポイントを計算し、牌譜に設定する
        round_ = not any(map(lambda p: re.search(r'\.\d$', p), self._rule['rank_bounus']))
        point = [0.0] * 4
        for i in range(1, 4):
            id = paiming[i]
            point[id] = (defen[id] - 30000) / 1000 + float(self._rule['rank_bounus'][i])
            if round_:
                # point[id] = round(point[id])
                point[id] = float(Decimal(str(point[id])).quantize(Decimal('0'), rounding=ROUND_HALF_UP))
            point[paiming[0]] -= point[id]
        self._paipu['point'] = list(map(lambda p: ("{:.0f}" if round_ else "{:.1f}").format(p), point))

        # 対局者に通知メッセージを送信する
        paipu = {'jieju': self._paipu}
        msg = [{}] * 4
        for i in range(4):
            msg[i] = json.loads(json.dumps(paipu))
        self.call_players('jieju', msg, self._wait)

        # (必要であれば)描画を指示する
        if self._view is not None:
            self._view.summary(self._paipu)

        # 終局前のハンドラがある場合は、それを呼び出す
        if self._handler is not None:
            self._handler()

    def get_reply(self, i: int) -> dict | None:
        model = self._model
        return self._reply[model['player_id'][i]]

    def reply_kaiju(self):
        self.delay(lambda: self.qipai(), 0)     # 配牌に遷移

    def reply_qipai(self):
        self.delay(lambda: self.zimo(), 0)  # ツモに遷移

    def reply_zimo(self) -> None:

        model = self._model

        # 現在の応答を取得する
        reply = self.get_reply(model['lunban'])

        if 'daopai' in reply:     # 応答が倒牌の場合
            if self.allow_pingju():     # 九種九牌で流局が可能な場合
                shoupai = [''] * 4
                # 現在の手番の手牌を公開する
                shoupai[model['lunban']] = str(model['shoupai'][model['lunban']])
                # 九種九牌の流局に遷移する
                return self.delay(lambda: self.pingju('九種九牌', shoupai), 0)

        elif 'hule' in reply:     # 応答が和了の場合
            if self.allow_hule():   # 和了が可能な場合
                if self._view is not None:
                    self._view.say('zimo', model['lunban'])     # (必要なら)「ツモ」と発声する
                return self.delay(lambda: self.hule())  # 和了に遷移する

        elif 'gang' in reply:     # 応答が槓の場合
            if reply['gang'] in self.get_gang_mianzi():   # カンが可能な場合
                if self._view is not None:
                    self._view.say('gang', model['lunban'])     # (必要なら)「カン」と発声する
                return self.delay(lambda: self.gang(reply['gang']))     # 槓に遷移する

        elif 'dapai' in reply:    # 応答が打牌の場合
            dapai = re.sub(r'\*$', '', reply['dapai'])
            if dapai in self.get_dapai():     # 可能な打牌の場合
                if reply['dapai'][-1] == '*' and self.allow_lizhi(dapai):
                    # 打牌が'可能な)リーチ宣言の場合
                    if self._view is not None:
                        self._view.say('lizhi', model['lunban'])    # (必要なら)「リーチ」と発声する
                    return self.delay(lambda: self.dapai(reply['dapai']))   # 打牌に遷移
                return self.delay(lambda: self.dapai(dapai), 0)     # 打牌に遷移

        # 応答が不正な場合、手牌の一番右にある牌を打牌する
        p = self.get_dapai().pop()
        self.delay(lambda: self.dapai(p), 0)

    def reply_dapai(self) -> None:

        model = self._model

        # 下家→対面→上家の順に和了応答を処理する
        for i in range(1, 4):
            j = (model['lunban'] + i) % 4
            reply = self.get_reply(j)
            if 'hule' in reply and self.allow_hule(j):  # 応答が和了の場合
                if self._rule['n_max_simultaneous_hule'] == 1 and len(self._hule):
                    # ダブロンなしの場合、2人目以降の和了応答は処理しない
                    continue
                if self._view is not None:
                    self._view.say('rong', j)   # (必要なら)「ロン」と発声する
                self._hule.append(j)    # 和了者に追加する
            else:
                shoupai = model['shoupai'][j].clone().zimo(self._dapai)
                if xiangting(shoupai) == -1:
                    # 打牌で和了形となる場合はフリテンとする
                    self._neng_rong[j] = False

        # 和了応答があった場合の処理を行う
        # ダブロンありで3人和了の場合
        if len(self._hule) == 3 and self._rule['n_max_simultaneous_hule'] == 2:
            shoupai = [''] * 4
            for i in self._hule:    # 和了者の手牌を公開する
                shoupai[i] = str(model['shoupai'][i])
            # 三家和のと途中流局に遷移
            return self.delay(lambda: self.pingju('三家和', shoupai))
        elif len(self._hule):   # それ以外の場合
            return self.delay(lambda: self.hule())  # 和了に遷移

        # リーチ宣言後の場合、リーチ成立の処理をする
        if self._dapai[-1] == '*':
            model['defen'][model['player_id'][model['lunban']]] -= 1000     # 持ち点を1000点減らす
            model['lizhibang'] += 1     # 供託リーチ棒を追加する

            # 途中流局ありで4人目リーチの場合
            if len([x for x in self._lizhi if x]) == 4 and self._rule['interrupted_pingju']:
                shoupai = list(map(lambda s: str(s), model['shoupai']))     # 全員の手牌を公開
                # 4人立直の途中流局に遷移
                return self.delay(lambda: self.pingju('四家立直', shoupai))

        # 北家の打牌で第1ツモ巡は終了する
        if self._diyizimo and model['lunban'] == 3:
            self._diyizimo = False  # 第1ツモ巡を終了
            if self._fengpai:   # 四風連打が継続していた場合
                # 四風連打の途中流局に遷移
                return self.delay(lambda: self.pingju('四風連打'), 0)

        # 4つ目のカンの場合の処理を行う
        if sum(self._n_gang) == 4:
            # 途中流局ありで1人が4つカンしていない場合
            if max(self._n_gang) < 4 and self._rule['interrupted_pingju']:
                # 四開槓の途中流局に遷移
                return self.delay(lambda: self.pingju('四開槓'), 0)

        # 牌山が尽きた場合の処理
        if not model['shan'].paishu:
            shoupai = [''] * 4
            for i in range(4):
                reply = self.get_reply(i)
                if 'daopai' in reply:
                    shoupai[i] = reply['daopai']    # 応答が倒牌の手牌を公開する
            return self.delay(lambda: self.pingju('', shoupai), 0)  # 流局に遷移

        # 下家→対面→上家の順にカン応答・ポン応答を処理する
        for i in range(1, 4):
            j = (model['lunban'] + i) % 4
            reply = self.get_reply(j)
            if 'fulou' in reply:
                m = reply['fulou'].replace('0', '5')
                if re.search(r'^[mpsz](\d)\1\1\1', m):  # カン応答の場合
                    if reply['fulou'] in self.get_gang_mianzi(j):   # カンが可能な場合
                        if self._view is not None:
                            self._view.say('gang', j)   # (必要なら)「カン」と発声する
                        return self.delay(lambda: self.fulou(reply['fulou']))   # 副露に遷移
                elif re.search(r'^[mpsz](\d)\1\1', m):  # ポン応答の場合
                    if reply['fulou'] in self.get_peng_mianzi(j):   # ポンが可能な場合
                        if self._view is not None:
                            self._view.say('peng', j)   # (必要なら)「ポン」と発声する
                        return self.delay(lambda: self.fulou(reply['fulou']))   # 副露に遷移

        # 下家のチー応答を処理する
        i = (model['lunban'] + 1) % 4
        reply = self.get_reply(i)
        if 'fulou' in reply:    # チー応答の場合
            if reply['fulou'] in self.get_chi_mianzi(i):    # チーが可能な場合
                if self._view is not None:
                    self._view.say('chi', i)    # (必要なら)「チー」と発声する
                return self.delay(lambda: self.fulou(reply['fulou']))

        # それ以外の場合、自摸に遷移する
        self.delay(lambda: self.zimo(), 0)

    def reply_fulou(self) -> None:

        model = self._model

        # 副露がカンの場合は打牌せず槓自摸に遷移する
        if self._gang:
            return self.delay(lambda: self.gangzimo(), 0)

        # 副露がポン・チーの場合は打牌する
        reply = self.get_reply(model['lunban'])
        if 'dapai' in reply:    # 応答が打牌の場合
            if reply['dapai'] in self.get_dapai():  # 可能な打牌の場合
                return self.delay(lambda: self.dapai(reply['dapai']), 0)    # 打牌に遷移

        # 応答が不正な場合、手牌の一番右にある牌を打牌する
        p = self.get_dapai().pop()
        self.delay(lambda: self.dapai(p), 0)

    def reply_gang(self) -> None:

        model = self._model

        # 明槓は槍槓できないので、即座に槓自摸に遷移する
        if re.search(r'^[mpsz]\d{4}$', self._gang):
            return self.delay(lambda: self.gangzimo(), 0)

        # 加槓は槍槓可能なので、下家→対面→上家の順に和了応答を処理する
        for i in range(1, 4):
            j = (model['lunban'] + i) % 4
            reply = self.get_reply(j)
            if 'hule' in reply and self.allow_hule(j):  # 応答が和了の場合
                if self._rule['n_max_simultaneous_hule'] == 1 and len(self._hule):
                    # ダブロンなしの場合、2人目以降の和了応答は処理しない
                    continue
                if self._view is not None:
                    self._view.say('rong', j)   # (必要なら)「ロン」と発声する
                self._hule.append(j)    # 和了者に追加する
            else:   # 応答が和了でない場合
                p = self._gang[0] + self._gang[-1]
                shoupai = model['shoupai'][j].clone().zimo(p)
                if xiangting(shoupai) == -1:
                    # カンの牌で和了形となる場合はフリテンとする
                    self._neng_rong[j] = False

        # 和了応答があった場合の処理を行う
        if len(self._hule):
            return self.delay(lambda: self.hule())  # 和了に遷移する

        # それ以外の場合、槓自摸に遷移する
        self.delay(lambda: self.gangzimo(), 0)

    def reply_hule(self) -> None:

        model = self._model

        # 和了者の収支を持ち点に反映する
        for i in range(4):
            model['defen'][model['player_id'][i]] += self._fenpei[i]
        # 供託をクリアする
        model['changbang'] = 0
        model['lizhibang'] = 0

        if len(self._hule):     # 続く和了がある場合
            return self.delay(lambda: self.hule())  # 和了に遷移する
        else:   # 和了がない場合
            if self._lianzhuang:    # 連荘の場合
                # 局開始時の状態の積み棒に1加算する
                model['changbang'] = self._changbang + 1
            return self.delay(lambda: self.last(), 0)   # 終局判断する

    def reply_pingju(self) -> None:

        model = self._model

        # 流局時の収支を持ち点に反映する
        for i in range(4):
            model['defen'][model['player_id'][i]] += self._fenpei[i]
        # 積み棒を加算する
        model['changbang'] += 1

        # 終局判断する
        self.delay(lambda: self.last(), 0)

    def get_dapai(self):
        """
        打牌可能な牌の一覧

        Returns
        -------
        list[str] (or None)
            牌の配列
        """
        model = self._model
        return Game.get_dapai_(self._rule, model['shoupai'][model['lunban']])

    def get_chi_mianzi(self, i: int):
        """
        チー可能な面子の一覧

        Parameters
        ----------
        i : int
            手番

        Returns
        -------
        list[str] (or None)
            面子の配列
        """
        model = self._model
        d = '_+=-'[(4 + model['lunban'] - i) % 4]
        return Game.get_chi_mianzi_(self._rule, model['shoupai'][i],
                                    self._dapai + d, model['shan'].paishu)

    def get_peng_mianzi(self, i: int):
        """
        ポン可能な面子の一覧

        Parameters
        ----------
        i : int
            手番

        Returns
        -------
        list[str] (or None)
            面子の配列
        """
        model = self._model
        d = '_+=-'[(4 + model['lunban'] - i) % 4]
        return Game.get_peng_mianzi_(self._rule, model['shoupai'][i],
                                     self._dapai + d, model['shan'].paishu)

    def get_gang_mianzi(self, i: int | None = None):
        """
        カン可能な面子の一覧

        Parameters
        ----------
        i : int (or None, default None)
            手番
            指定しない場合は暗槓・加槓を対象に、指定する場合は大明槓を対象とする

        Returns
        -------
        list[str] (or None)
            面子の配列
        """
        model = self._model
        if i is None:   # 暗槓・加槓の場合
            return Game.get_gang_mianzi_(self._rule, model['shoupai'][model['lunban']],
                                         None, model['shan'].paishu,
                                         sum(self._n_gang))
        else:   # 大明槓の場合
            d = '_+=-'[(4 + model['lunban'] - i) % 4]
            return Game.get_gang_mianzi_(self._rule, model['shoupai'][i],
                                         self._dapai + d, model['shan'].paishu,
                                         sum(self._n_gang))

    def allow_lizhi(self, p: str | None = None):
        """
        リーチ可能かどうか判定する

        Parameters
        ----------
        p : str (or None)
            牌

        Returns
        -------
        list[str] or bool
            ``p``が指定されていない場合、リーチ可能な牌の一覧を返す
            リーチできる牌がない場合、または``p``が指定されている場合、リーチ可能かどうかを返す
        """
        model = self._model
        return Game.allow_lizhi_(self._rule, model['shoupai'][model['lunban']],
                                 p, model['shan'].paishu,
                                 model['defen'][model['player_id'][model['lunban']]])

    def allow_hule(self, i: int | None = None):
        """
        和了可能かどうか判定する

        Parameters
        ----------
        i : int (or None)
            手番
            `None`の場合は現在手番のツモ和了について評価する

        Returns
        -------
        bool
            和了可能かどうか
        """
        model = self._model
        if i is None:   # 現在の手番がツモ和了可能か判定する
            # 状況役の有無を判定する
            hupai = (model['shoupai'][model['lunban']].lizhi    # 立直
                     or self._status == 'gangzimo'  # 嶺上開花
                     or model['shan'].paishu == 0)  # 海底自摸
            # ツモ和了可能か判定する
            return Game.allow_hule_(self._rule,
                                    model['shoupai'][model['lunban']], None,
                                    model['zhuangfeng'], model['lunban'], hupai)
        else:   # 手番 i がロン和了可能か判定する
            # 和了牌を決定する
            # 槍槓の場合は最後にカンした面子 _gang から、
            # その他の場合は最後に打牌した牌 _dapai から決定する
            p = (self._gang[0] + self._gang[-1] if self._status == 'gang'
                 else self._dapai) + '_+=-'[(4 + model['lunban'] - i) % 4]
            # 状況役の有無を判定する
            hupai = (model['shoupai'][i].lizhi      # 立直
                     or self._status == 'gang'  # 槍槓
                     or model['shan'].paishu == 0)  # 海底自摸
            # ロン和了可能か判定する
            return Game.allow_hule_(self._rule,
                                    model['shoupai'][i], p,
                                    model['zhuangfeng'], i, hupai,
                                    self._neng_rong[i])

    def allow_pingju(self):
        """
        現在の手番が九種九牌流局可能か判定する

        Returns
        -------
        bool
            現在の手番が九牌流局可能かどうか
        """
        model = self._model
        return Game.allow_pingju_(self._rule, model['shoupai'][model['lunban']],
                                  self._diyizimo)

    @staticmethod
    def get_dapai_(rule_: dict[str, Any], shoupai: Shoupai):
        """
        打牌可能な牌の一覧

        Parameters
        ----------
        rule_ : dict
            ルール
        shoupai : jongpy.core.Shoupai
            手牌

        Returns
        -------
        list[str] (or None)
            牌の配列
        """

        # 喰い替えなしの場合は Shoupai に処理を任せる
        if rule_['allow_fulou_slide'] == 0:
            return shoupai.get_dapai(True)

        # 現物喰い替えなしの場合はここで喰い替えをチェックする
        if rule_['allow_fulou_slide'] == 1 and shoupai._zimo and len(shoupai._zimo) > 2:
            deny = shoupai._zimo[0] + str(int(re.search(r'\d(?=[\+\=\-])', shoupai._zimo).group()) or 5)
            return [p for p in shoupai.get_dapai(False) if p.replace('0', '5') != deny]

        # 食い替えありの場合は Shoupai でチェックしない
        return shoupai.get_dapai(False)

    @staticmethod
    def get_chi_mianzi_(rule_: dict[str, Any], shoupai: Shoupai, p: str, paishu: int) -> list[str] | None:
        """
        チー可能な面子の一覧

        Parameters
        ----------
        rule_ : dict
            ルール
        shoupai : jongpy.core.Shoupai
            手牌
        p : str
            牌
        paishu : int
            残り牌数

        Returns
        -------
        list[str] (or None)
            面子の配列
        """

        # 喰い替えなしの場合は Shoupai に任せる
        mianzi = shoupai.get_chi_mianzi(p, rule_['allow_fulou_slide'] == 0)
        if not mianzi:
            return mianzi
        # 現物喰い替えなしの場合は、すでに3副露していて残り2枚が現物となる場合だけ鳴けない
        if rule_['allow_fulou_slide'] == 1 and len(shoupai._fulou) == 3 and shoupai._bingpai[p[0]][int(p[1])] == 2:
            mianzi = []
        return [] if paishu == 0 else mianzi    # 河底牌は鳴けない

    @staticmethod
    def get_peng_mianzi_(rule_: dict[str, Any], shoupai: Shoupai, p: str, paishu: int) -> list[str] | None:
        """
        ポン可能な面子の一覧

        Parameters
        ----------
        rule_ : dict
            ルール
        shoupai : jongpy.core.Shoupai
            手牌
        p : str
            牌
        paishu : int
            残り牌数

        Returns
        -------
        list[str] (or None)
            面子の配列
        """

        mianzi = shoupai.get_peng_mianzi(p)     # Shoupai に任せる
        if not mianzi:
            return mianzi
        return [] if paishu == 0 else mianzi    # 河底牌は鳴けない

    @staticmethod
    def get_gang_mianzi_(
        rule_: dict[str, Any],
        shoupai: Shoupai,
        p: str | None,
        paishu: int,
        n_gang: int = 0
    ) -> list[str] | None:
        """
        カン可能な面子の一覧

        Parameters
        ----------
        rule_ : dict
            ルール
        shoupai : jongpy.core.Shoupai
            手牌
        p : str (or None)
            牌
            None の場合は暗槓・加槓と対象とする
        paishu : int
            残り牌数
        n_gang : int
            局のカン数

        Returns
        -------
        list[str] (or None)
            面子の一覧
        """

        mianzi = shoupai.get_gang_mianzi(p)     # Shoupai に任せる
        if not mianzi:
            return mianzi   # カンできない場合はそう応答する

        if shoupai.lizhi:   # リーチ後の暗槓可否を確認する
            if rule_['allow_angang_after_lizhi'] == 0:  # すべての暗槓が不可の場合
                return []
            elif rule_['allow_angang_after_lizhi'] == 1:    # 牌姿の変わる暗槓が不可の場合
                new_shoupai = shoupai.clone().dapai(shoupai._zimo)
                n_hule1 = 0
                n_hule2 = 0
                # 暗槓前の牌姿から可能な和了形をすべて求める
                for p in tingpai(new_shoupai):
                    n_hule1 += len(hule_mianzi(new_shoupai, p))
                new_shoupai = shoupai.clone().gang(mianzi[0])
                for p in tingpai(new_shoupai):
                    n_hule2 += len(hule_mianzi(new_shoupai, p))
                if n_hule1 > n_hule2:   # 両者が一致しない場合暗槓不可
                    return []
            else:   # 待ちの変わる暗槓が不可の場合
                # 暗槓前の牌姿での和了牌一覧を求める
                new_shoupai = shoupai.clone().dapai(shoupai._zimo)
                n_tingpai1 = len(tingpai(new_shoupai))
                # 暗槓後の牌姿での和了牌一覧を求める
                new_shoupai = shoupai.clone().gang(mianzi[0])
                if xiangting(new_shoupai) > 0:  # テンパイが崩れるカンは不可
                    return []
                n_tingpai2 = len(tingpai(new_shoupai))
                if n_tingpai1 > n_tingpai2:     # 両者が一致しない場合暗槓不可
                    return []

        # 海底(河底)牌はカンできない
        # 5つ目となるカンもできない
        return [] if paishu == 0 or n_gang == 4 else mianzi

    @staticmethod
    def allow_lizhi_(
        rule_: dict[str, Any],
        shoupai: Shoupai,
        p: str | None = None,
        paishu: int = 4,
        defen: int = 1000
    ) -> list[str] | bool:
        """
        リーチ可能かどうか判定する

        Parameters
        ----------
        rule_ : dict
            ルール
        shoupai : jongpy.core.Shoupai
            手牌
        p : str (or None)
            牌
        paishu : int
            残り牌数
        defen : int
            持ち点

        Returns
        -------
        list[str] or bool
            ``p``が指定されていない場合、リーチ可能な牌の一覧を返す
            リーチできる牌がない場合、または``p``が指定されている場合、リーチ可能かどうかを返す
        """

        if shoupai._zimo is None:
            return False    # 打牌できないときはリーチも不可
        if shoupai.lizhi:
            return False    # リーチ後はリーチ不可
        if not shoupai.menqian:
            return False    # 副露後はリーチ不可

        # ツモ番なしリーチ不可の場合、残り牌数4枚以下ではリーチ不可
        if not rule_['lizhi_no_zimo'] and paishu < 4:
            return False

        # トビ終了ありの場合、持ち点1000点未満ではリーチ不可
        if rule_['minus_interruption'] and defen < 1000:
            return False

        # テンパイしていない場合はリーチ不可
        if xiangting(shoupai) > 0:
            return False

        if p:   # 牌 p の指定あり
            new_shoupai = shoupai.clone().dapai(p)
            # p を打牌した牌姿がテンパイしていればリーチ可
            return xiangting(new_shoupai) == 0 and len(tingpai(new_shoupai)) > 0
        else:   # 牌 p の指定なし
            dapai = []
            # 打牌可能な牌について以下を行う
            for p in Game.get_dapai_(rule_, shoupai):
                new_shoupai = shoupai.clone().dapai(p)
                if xiangting(new_shoupai) == 0 and len(tingpai(new_shoupai)) > 0:
                    dapai.append(p)     # 打牌後の牌姿がテンパイしていればリーチ可
            # リーチ可能な牌がない場合は False を返す
            return dapai if len(dapai) else False

    @staticmethod
    def allow_hule_(
        rule_: dict[str, Any],
        shoupai: Shoupai,
        p: str | None,
        zhuangfeng: int,
        menfeng: int,
        hupai: bool,
        neng_rong: bool = False
    ) -> bool:
        """
        和了可能か判定する

        Parameters
        ----------
        rule_ : dict
            ルール
        shoupai : jongpy.core.Shoupai
            手牌
        p : str (or None)
            ロン牌
            `None`の場合はツモ和了として扱う
        zhuangfeng : int
            場風牌の指定
        menfeng : int
            自風牌の指定
        hupai : bool
            状況役があるかどうか
        neng_rong : bool
            フリテンの場合は`False`

        Returns
        -------
        bool
            和了可能かどうか
        """

        # フリテンはロン和了できない
        if p and not neng_rong:
            return False

        # ロン牌を含めて和了形(シャン点数 = -1)となっていない場合は和了できない
        new_shoupai = shoupai.clone()
        if p:
            new_shoupai.zimo(p)
        if xiangting(new_shoupai) != -1:
            return False

        # 和了形となっていて状況役があれば和了できる
        if hupai:
            return True

        # 和了点計算ルーチンを呼び出して和了可能か判定する
        param = {
            'rule': rule_,  # ルール
            'zhuangfeng': zhuangfeng,   # 場風
            'menfeng': menfeng,     # 自風
            'hupai': {},
            'baopai': [],
            'jicun': {'changbang': 0, 'lizhibang': 0}
        }
        h = hule(shoupai, p, param)

        return h['hupai'] is not None

    @staticmethod
    def allow_pingju_(rule_: dict[str, Any], shoupai: Shoupai, diyizimo: bool) -> bool:
        """
        九種九牌流局可能か判定する

        Parameters
        ----------
        rule_ : dict
            ルール
        shoupai : jongpy.core.Shoupai
            手牌
        diyizimo : bool
            第一ツモ巡かどうか

        Returns
        -------
        bool
            九種九牌流局可能かどうか
        """

        # 第一ツモでなければ成立しない
        if not (diyizimo and shoupai._zimo):
            return False

        # 途中流局なしの場合は成立しない
        if not rule_['interrupted_pingju']:
            return False

        # 手牌中の幺九牌の種類数を数える
        n_yaojiu = 0
        for s in ['m', 'p', 's', 'z']:
            bingpai = shoupai._bingpai[s]
            nn = [1, 2, 3, 4, 5, 6, 7] if s == 'z' else [1, 9]
            for n in nn:
                if bingpai[n] > 0:
                    n_yaojiu += 1
        # 9種類以上あれば成立する
        return n_yaojiu >= 9

    @staticmethod
    def allow_no_daopai(rule_: dict[str, Any], shoupai: Shoupai, paishu: int) -> bool:
        """
        「ノーテン宣言」可能か判定する

        Parameters
        ----------
        rule_ : dict
            ルール
        shoupai : jongpy.core.Shoupai
            手牌
        paishu : int
            残り牌数

        Returns
        -------
        bool
            ノーテン宣言可能かどうか
        """

        # 最終打牌以外はノーテン宣言できない
        if paishu > 0 or shoupai._zimo:
            return False

        # ノーテン宣言なしの場合はノーテン宣言できない
        if not rule_['declare_no_tingpai']:
            return False

        # リーチ後はノーテン宣言できない
        if shoupai.lizhi:
            return False

        # テンパイしていない場合、テンパイしていても和了牌が存在しない場合はノーテン宣言できない
        return xiangting(shoupai) == 0 and len(tingpai(shoupai)) > 0
