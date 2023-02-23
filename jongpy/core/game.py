"""jongpy.core.game"""

from __future__ import annotations

import re
import datetime
import copy
import random
import json
from typing import Callable, Any, TYPE_CHECKING

from jongpy.core.shoupai import Shoupai
from jongpy.core.shan import Shan
from jongpy.core.he import He
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
                pass

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
                pass

        if not self._sync:
            pass

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
        if len([x for x in self._reply if x]) < 4:
            return
        if not self._timeout_id:
            pass

    def next(self):
        """対局者からの応答を読み出し、次のステップに遷移"""

        # 呼び出しタイマーのクリア
        # self._timeout_id = clearTimeout(self._timeout_id)

        # 4人分の応答がそろっていない場合は以降の処理は行わない
        if len([x for x in self._reply if x]) > 4:
            return

        # 外部から停止要求があった場合は停止する
        if self._stop is not None:
            self._stop()

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
            model['player_id'][i] = (model['qijia'] + model['jushu'] + 1) % 4

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
                    msg[i]['qipai']['shoupai'][i] = ''  # 他の対局者はマスクする

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
                and (p for p in tingpai(model['shoupai'][model['lunban']]) if model['he'][model['lunban']].find(p))):
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

        shoupai = copy.copy(model['shoupai'][menfeng])  # 和了者の手牌を複製
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

    def pingju(self, name: str | None, shoupai: list[str] = ['', '', '', '']):
        """
        流局の処理を行う

        Parameters
        ----------
        name : str (or None)
            流局理由
        shoupai : list[str]
            牌姿の配列
        """

        # 1. 卓情報を更新
        model = self._model
        fenpei = [0] * 4    # 流局による点棒の移動を初期化

        if not name:    # 通常の流局の場合

            # 手牌の公開・非公開を判定し、公開(=テンパイ)の人数をカウントする
            n_tingpai = 0
            for i in range(4):
                if (self._rule['declare_no_tingpai'] and not shoupai[i]
                        and not model['shoupai'][i].lizhi):
                    # ノーテン宣言ありの場合、リーチ者以外は対局者の
                    # 非公開の意思に従う
                    continue

                if (not self._rule['penalty_no_tingpai']
                    and (self._rule['continuous_zhuang'] != 2 or i != 0)
                        and not model['shoupai'][i].lizhi):
                    # ノーテン罰なしのルールの場合、リーチ以外で手牌公開の
                    # 意味があるのはテンパイ連荘のルールのときの親のみ
                    shoupai[i] = ''
                elif xiangting(model['shoupai'][i]) == 0 and len(tingpai(model['shoupai'][i])) > 0:
                    # それ以外でテンパイしている場合は手牌を公開する
                    n_tingpai += 1
                    shoupai[i] = str(model['shoupai'])

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
                    # 鳴かれた牌がある場合、ヤオ九牌を打牌している場合は、
                    # 流し満貫は成立しない
                    all_yaojiu = True
                    for p in model['he'][i]._pai:
                        if re.search(r'[\+\=\-]$', p):
                            all_yaojiu = False
                            break
                        if re.search(r'^z', p):
                            continue
                        if re.search(r'^[mps][19]'):
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
                name = '荒牌流局'   # 流局理由を設定
                if self._rule['penalty_no_tingpai'] and 0 < n_tingpai < 4:
                    # ノーテン罰符ありのルールなら清算する
                    for i in range(4):
                        fenpei[i] = 3000 / n_tingpai if shoupai[i] else -3000 / (4 - n_tingpai)

            # ノーテン連荘の場合、流局は連荘とする
            if self._rule['continuous_zhuang'] == 3:
                self._lianzhuang = True

        else:   # 途中流局の場合
            self._no_game = True    # 途中流局フラグをONにする
            self._lianzhuang = True     # 途中流局は連荘とする

        # 一局戦の場合、流局は連荘とする
        if self._rule['n_zhuang'] == 0:
            self._lianzhuang = True

        self._fengpai = fenpei  # その局の点棒移動を保存

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
