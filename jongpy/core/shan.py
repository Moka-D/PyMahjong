"""jongpy.core.shan"""

from jongpy.core.shoupai import Shoupai
from jongpy.core.exceptions import PaiFormatError


class Shan:

    @staticmethod
    def zhenbaopai(p: str) -> str:
        """
        ドラ牌の取得

        Parameter
        ---------
        p : str
            ドラ表示牌の文字列表現

        Returns
        -------
        str
            ドラ表示牌
        """

        if Shoupai.valid_pai(p) is None:
            raise PaiFormatError(p)
        s = p[0]
        n = int(p[1]) or 5
        return (s + str(n % 4 + 1) if n < 5 else s + str((n - 4) % 3 + 5)) if s == 'z' else s + str(n % 9 + 1)
