"""jongpy.core.he"""

import re

from jongpy.core.shoupai import Shoupai
from jongpy.core.exceptions import (PaiFormatError,
                                    MianziFormatError,
                                    InvalidOperationError)


class He:
    """捨て牌クラス"""

    def __init__(self) -> None:
        self._pai = []
        self._find = set()

    def dapai(self, p: str):
        """
        牌``p``を捨て牌に追加

        Parameters
        ----------
        p : str
            牌
        """
        # 不正な牌の場合、例外を発生
        if Shoupai.valid_pai(p) is None:
            raise PaiFormatError(p)
        self._pai.append(re.sub(r'[\+\=\-]$', '', p))   # 捨て牌に追加
        self._find.add(p[0] + str(int(p[1]) or 5))  # キャッシュに追加
        return self

    def fulou(self, m: str):
        """
        面子``m``で副露された状態にする

        Parameters
        ----------
        m : str
            面子
        """
        # 不正な面子の場合、例外を発生する
        if Shoupai.valid_mianzi(m) is None:
            raise MianziFormatError(m)
        # 面子から鳴いた牌を取得する
        m_matched = re.search(r'\d(?=[\+\=\-])', m)
        p = m[0] + (m_matched.group() if m_matched is not None else '')
        d = re.search(r'[\+\=\-]', m)
        # 鳴いていない場合、例外を発生する
        if d is None:
            raise InvalidOperationError(m)
        # 鳴いた牌が河の牌と一致しない場合、例外を発生する
        if self._pai[-1][0:2] != p:
            raise InvalidOperationError(m)
        # 河の牌に鳴かれたマークを追加する
        self._pai[-1] += d.group()
        return self

    def find(self, p: str) -> bool:
        """
        牌``p``が捨て牌にあるかどうか判定する

        Parameters
        ----------
        p : str
            牌

        Returns
        -------
        bool
            牌``p``が捨て牌にあるかどうか
        """
        return p[0] + str(int(p[1]) or 5) in self._find
