"""jongpy.core.shan"""

import random
from collections import deque
from typing import Any

from jongpy.core.shoupai import Shoupai
from jongpy.core.exceptions import PaiFormatError, InvalidOperationError


class Shan:
    """
    牌山クラス

    Parameters
    ----------
    rule_ : dict
        ルール
    """

    @staticmethod
    def zhenbaopai(p: str) -> str:
        """
        ドラ表示牌``p``からドラ牌を取得

        Parameter
        ---------
        p : str
            ドラ表示牌の文字列表現

        Returns
        -------
        str
            ドラ牌の文字列表現
        """

        # 不正な牌の場合、例外を発生
        if Shoupai.valid_pai(p) is None:
            raise PaiFormatError(p)

        # p の次の牌を探す
        s = p[0]
        n = int(p[1]) or 5
        return (s + str(n % 4 + 1) if n < 5 else s + str((n - 4) % 3 + 5)) if s == 'z' else s + str(n % 9 + 1)

    def __init__(self, rule_: dict[str, Any] = {}) -> None:

        self._rule = rule_
        hongpai: dict[str, int] = rule_.get('hongpai')

        # 赤牌の枚数を考慮して136枚の牌を生成する
        pai = []
        for s in ['m', 'p', 's', 'z']:
            for n in range(1, (7 if s == 'z' else 9) + 1):
                for i in range(4):
                    if n == 5 and s in hongpai and i < hongpai[s]:
                        pai.append(s + '0')
                    else:
                        pai.append(s + str(n))

        # 生成した牌をランダムに並び変える
        self._pai = deque()
        while len(pai):
            self._pai.append(pai.pop(random.randrange(len(pai))))

        self._baopai = [self._pai[4]]   # ドラ表示牌を決定する
        # (裏ドラありなら)裏ドラ表示牌を決定する
        self._fubaopai = [self._pai[9]] if rule_.get('fubaopai') else None
        self._weikaigang = False
        self._closed = False

    def zimo(self) -> str:
        """
        山牌からのツモ

        Returns
        -------
        str
            牌の文字列表現
        """

        if self._closed:    # 牌山固定後は操作禁止
            raise InvalidOperationError(self)
        if self.paishu == 0:    # 王牌不足ならツモれない
            raise InvalidOperationError(self)
        if self._weikaigang:    # 開槓前はツモれない
            raise InvalidOperationError(self)

        return self._pai.pop()  # 牌山の末尾から1枚取得する

    def gangzimo(self) -> str:
        """
        嶺上牌のツモ

        Returns
        -------
        str
            牌の文字列表現
        """

        if self._closed:    # 牌山固定後は操作禁止
            raise InvalidOperationError(self)
        if self.paishu == 0:    # 王牌不足ならツモれない
            raise InvalidOperationError(self)
        if self._weikaigang:    # 開槓前はツモれない
            raise InvalidOperationError(self)
        if len(self._baopai) == 5:  # 5つ目のカンはできない
            raise InvalidOperationError(self)

        # カンドラありの場合、未開槓状態にする
        self._weikaigang = self._rule.get('gang_baopai')
        # カンドラなしの場合、カンドラに空文字列を追加する
        if not self._weikaigang:
            self._baopai.append('')
        return self._pai.popleft()  # 牌山の先頭から1枚取得する

    def kaigang(self):
        """開槓(槓ドラの追加)"""

        if self._closed:    # 牌山固定後は操作禁止
            raise InvalidOperationError(self)
        if not self._weikaigang:    # カンヅモ後に開槓可能となる
            raise InvalidOperationError(self)

        self._baopai.append(self._pai[4])   # カンドラを追加する
        # 裏ドラありかつカン裏ありなら、裏ドラも追加する
        if self._fubaopai is not None and self._rule.get('gang_fubaopai'):
            self._fubaopai.append(self._pai[9])
        self._weikaigang = False    # 未開槓状態を解除する
        return self

    def close(self):
        """牌山を固定する"""
        self._closed = True
        return self

    @property
    def paishu(self) -> int:
        """ツモ残り枚数"""
        return len(self._pai) - 14

    @property
    def baopai(self) -> list[str]:
        """ドラ表示牌"""
        return [x for x in self._baopai if x]

    @property
    def fubaopai(self) -> list[str] | None:
        """裏ドラ表示牌"""
        return (None if not self._closed
                else self._fubaopai[:] if self._fubaopai is not None
                else None)
