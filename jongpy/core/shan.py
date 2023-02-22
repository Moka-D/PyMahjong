"""jongpy.core.shan"""

import random
import copy
from collections import deque
from typing import Any

from jongpy.core.shoupai import Shoupai
from jongpy.core.exceptions import PaiFormatError, InvalidOperationError


class Shan:
    """山牌クラス"""

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

        if Shoupai.valid_pai(p) is None:
            raise PaiFormatError(p)
        s = p[0]
        n = int(p[1]) or 5
        return (s + str(n % 4 + 1) if n < 5 else s + str((n - 4) % 3 + 5)) if s == 'z' else s + str(n % 9 + 1)

    def __init__(self, rule_: dict[str, Any] = {}) -> None:

        self._rule = rule_
        hongpai: dict[str, int] = rule_.get('hongpai')

        pai = []
        for s in ['m', 'p', 's', 'z']:
            for n in range(1, (7 if s == 'z' else 9) + 1):
                for i in range(4):
                    if n == 5 and s in hongpai and i < hongpai[s]:
                        pai.append(s + '0')
                    else:
                        pai.append(s + str(n))

        self._pai = deque()
        while len(pai):
            self._pai.append(pai.pop(random.randrange(len(pai))))

        self._baopai = [self._pai[4]]
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

        if self._closed:
            raise InvalidOperationError(self)
        if self.paishu == 0:
            raise InvalidOperationError(self)
        if self._weikaigang:
            raise InvalidOperationError(self)

        return self._pai.pop()

    def gangzimo(self) -> str:
        """
        嶺上牌のツモ

        Returns
        -------
        str
            牌の文字列表現
        """

        if self._closed:
            raise InvalidOperationError(self)
        if self.paishu == 0:
            raise InvalidOperationError(self)
        if self._weikaigang:
            raise InvalidOperationError(self)
        if len(self._baopai) == 5:
            raise InvalidOperationError(self)

        self._weikaigang = self._rule.get('gang_baopai')
        if not self._weikaigang:
            self._baopai.append('')
        return self._pai.popleft()

    def kaigang(self):
        """開槓(槓ドラの追加)"""

        if self._closed:
            raise InvalidOperationError(self)
        if not self._weikaigang:
            raise InvalidOperationError(self)

        self._baopai.append(self._pai[4])
        if self._fubaopai is not None and self._rule.get('gang_fubaopai'):
            self._fubaopai.append(self._pai[9])
        self._weikaigang = False
        return self

    def close(self):
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
        return None if not self._closed else copy.copy(self._fubaopai)
