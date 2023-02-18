"""jongpy.core.he"""

import re

from jongpy.core.shoupai import Shoupai
from jongpy.core.exceptions import (PaiFormatError,
                                    MianziFormatError,
                                    InvalidOperationError)


class He:
    """河クラス"""

    def __init__(self):
        self._pai = []
        self._find = {}

    def dapai(self, p: str):
        if Shoupai.valid_pai(p) is None:
            raise PaiFormatError(p)
        self._pai.append(re.sub(r'[\+\=\-]$', '', p))
        self._find[p[0] + str(int(p[1]) or 5)] = True
        return self

    def fulou(self, m: str):
        if Shoupai.valid_mianzi(m) is None:
            raise MianziFormatError(m)
        m_matched = re.search(r'\d(?=[\+\=\-])', m)
        p = m[0] + (m_matched.group() if m_matched is not None else '')
        d = re.search(r'[\+\=\-]', m)
        if d is None:
            raise InvalidOperationError(m)
        if self._pai[len(self._pai) - 1][0:2] != p:
            raise InvalidOperationError(m)
        self._pai[len(self._pai) - 1] += d.group()
        return self

    def find(self, p: str):
        return self._find.get(p[0] + str(int(p[1]) or 5))
