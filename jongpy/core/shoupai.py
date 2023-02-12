"""jongpy.core.shoupai"""

import re
import copy


class Shoupai:
    """手牌クラス"""

    _bingpai: dict[str, int | list[int]]
    _fulou: list[str]
    _zimo: str | None
    _lizhi: bool

    def __init__(self, qipai: list[str] = []):
        self._bingpai = {   # 副露牌を含まない手牌の枚数
            '_': 0,     # 伏せ牌
            'm': [0, 0, 0, 0, 0, 0, 0, 0, 0, 0],    # 萬子
            'p': [0, 0, 0, 0, 0, 0, 0, 0, 0, 0],    # 筒子
            's': [0, 0, 0, 0, 0, 0, 0, 0, 0, 0],    # 索子
            'z': [0, 0, 0, 0, 0, 0, 0, 0]   # 字牌
        }
        self._fulou = []    # 副露面子
        self._zimo = None   # ツモ牌
        self._lizhi = False     # リーチ有無

        for p in qipai:
            if p == '_':    # 伏せ牌の場合
                self._bingpai['_'] += 1     # 伏せ牌の枚数を加算
                continue

            # 伏せ牌以外の場合
            p = Shoupai.valid_pai(p)
            if not p:
                raise Exception(p)  # 牌の形式が不正なら例外を発生

            s = p[0]
            n = int(p[1])
            if self._bingpai[s][n] == 4:
                # 5枚目の牌なら例外を発生
                raise Exception([self, p])

            self._bingpai[s][n] += 1    # 手牌の枚数を加算
            if (s != 'z') and (n == 0):
                # 赤牌なら、黒牌の枚数も加算する
                self._bingpai[s][5] += 1

    @classmethod
    def from_string(cls, paistr: str = ''):
        """
        牌姿文字列から`Shoupai`インスタンスを生成

        Parameters
        ----------
        paistr : str
            牌姿の文字列表現

        Returns
        -------
        jongpy.Shoupai
        """
        fulou = paistr.split(',')   # 牌姿を , 区切りで分割
        bingpai = fulou.pop(0)  # 1つ目を手牌、残りを副露面子とする

        # 手牌を牌の配列に分解し、それを配列とみなす
        qipai = re.findall(r'_', bingpai)    # 伏せ牌を配牌に追加する

        # 手牌を萬子・筒子・索子ごとに分解し、それぞれについて配牌に追加
        for suitstr in re.findall(r'[mpsz]\d+', bingpai):
            s = suitstr[0]  # 色部分(m,p,s,z)を取得
            for n in re.findall(r'\d', suitstr):    # 数字部分を順に取得
                if (s == 'z') and (int(n) < 1 or int(n) > 7):
                    continue    # 字牌に0,8,9はない
                qipai.append(s + n)

        # 14枚を超える場合、配牌から取り除く
        qipai = qipai[0: 14 - len([m for m in fulou if m]) * 3]
        # 14枚の場合、配牌の最後をツモとみなす
        zimo = qipai[-1] if (len(qipai) - 2) % 3 == 0 else None

        # 配牌からインスタンスを生成する
        shoupai = cls(qipai)

        # 副露面子を順に加えるが、空文字列がある場合は最後に加えた面子を副露した直後とみなす
        last = None
        for m in fulou:     # 副露面子を順に処理する

            # 空文字列の場合、最後に加えた面子を副露した直後とし、処理を終える
            if not m:
                shoupai._zimo = last
                break

            m = Shoupai.valid_mianzi(m)     # 面子の正規化
            if m:
                shoupai._fulou.append(m)
                last = m

        # 副露直後でない場合は、ツモ牌を加える
        shoupai._zimo = shoupai._zimo or zimo or None

        # 牌姿の手牌部分が * で終端する場合はリーチ直後とみなす
        shoupai._lizhi = bingpai[-1] == '*'

        return shoupai

    @staticmethod
    def valid_pai(p: str):
        """
        牌の文字列表現判定

        '_'(伏せ牌の表現)は正しいとみなさない

        Parameters
        ----------
        p : str
            牌の文字列表現

        Returns
        -------
        str or None
            引数``p``が牌の文字表現として正しければそのまま返す
            正しくなければ None を返す
        """
        return p if re.fullmatch(r'(?:[mps]\d|z[1-7])_?\*?[\+\=\-]?', p) else None

    @staticmethod
    def valid_mianzi(m: str):
        """
        面子の文字列表現判定

        Parameters
        ----------
        m : str
            面子の文字列表現

        Returns
        -------
        str or None
            引数``m``が面子の文字表現として正しければそのまま返す
            正しくなければ None を返す
        """
        if re.match(r'z.*[089]', m):   # 字牌に0, 8, 9があればエラー
            return None

        h = m.replace('0', '5')     # 赤牌(0)を黒牌(5)に正規化

        if re.fullmatch(r'[mpsz](\d)\1\1[\+\=\-]\1?', h):     # 刻子か槓子の場合
            # 先頭の'05'を'50'に
            return re.sub(r'([mps])05', lambda x: x.group(1) + '50', m)

        elif re.fullmatch(r'[mpsz](\d)\1\1\1[\+\=\-]?', h):   # 暗槓か大明槓の場合
            # 鳴いた牌以外の順序を0が後ろになるように並び変える
            m_tail = re.search(r'\d[\+\=\-]$', m)
            return m[0] + ''.join(sorted(re.findall(r'\d(?![\+\=\-])', m), reverse=True)) + (m_tail.group() if m_tail else '')

        elif re.fullmatch(r'[mps]\d+\-\d*', h):     # それ以外は順子とみなす
            # まず順子として正しいかチェック
            hongpai = '0' in m      # 赤牌が含まれているかチェック
            nn = sorted(re.findall(r'\d', h))   # 数字部分だけを取り出し並び替える

            if len(nn) != 3:    # 数字が3つでなければエラー
                return None

            # 数字が順番に並んでなければエラー
            if (int(nn[0]) + 1 != int(nn[1])) or (int(nn[1]) + 1 != int(nn[2])):
                return None

            # 順子として正しいので順番を正しく入れ替える
            h = h[0] + ''.join(sorted(re.findall(r'\d[\+\=\-]?', h)))

            # 赤牌を復元
            return h.replace('5', '0') if hongpai else h

        return None

    def __str__(self) -> str:
        paistr = '_' * (self._bingpai['_'] + (-1 if self._zimo == '_' else 0))

        # 萬子・筒子・索子・字牌のそれぞれについて以下を行う
        for s in ['m', 'p', 's', 'z']:
            suitstr = s     # 種類を表す文字(m,p,s,z)を追加
            bingpai = self._bingpai[s]
            n_hongpai = 0 if s == 'z' else bingpai[0]   # 赤牌の枚数

            # 1~9(字牌の場合は1~7)について以下を行う
            for n in range(1, len(bingpai)):
                n_pai = bingpai[n]  # 牌の枚数
                # 処理中の牌がツモ牌の場合は後で追加する
                if self._zimo:
                    if (s+str(n)) == self._zimo:
                        n_pai -= 1
                    if (n == 5) and ((s+'0') == self._zimo):
                        n_pai -= 1
                        n_hongpai -= 1
                # 赤牌を考慮して牌を追加する
                for i in range(n_pai):
                    if (n == 5) and (n_hongpai > 0):
                        suitstr += '0'
                        n_hongpai -= 1
                    else:
                        suitstr += str(n)

            # その種類の牌がある場合には牌姿に追加する
            if len(suitstr) > 1:
                paistr += suitstr

        # ツモ牌がある場合は最後に追加する
        if self._zimo and (len(self._zimo) <= 2):
            paistr += self._zimo
        # リーチ後は牌姿に * を追加する
        if self._lizhi:
            paistr += '*'

        # 副露牌を , 区切りで追加する
        for m in self._fulou:
            paistr += ',' + m
        # 副露した直後の場合は末尾に , を追加する
        if self._zimo and (len(self._zimo) > 2):
            paistr += ','

        return paistr

    def __copy__(self):
        # 空のインスタンスを生成
        shoupai = Shoupai()

        # インスタンス変数をコピーする
        shoupai._bingpai = {
            '_': self._bingpai['_'],
            'm': copy.deepcopy(self._bingpai['m']),
            'p': copy.deepcopy(self._bingpai['p']),
            's': copy.deepcopy(self._bingpai['s']),
            'z': copy.deepcopy(self._bingpai['z'])
        }
        shoupai._fulou = copy.deepcopy(self._fulou)
        shoupai._zimo = self._zimo
        shoupai._lizhi = self._lizhi

        return shoupai

    def update_from_string(self, paistr: str):
        """
        手牌情報を``paistr``で置き換える

        Parameters
        ----------
        paistr : str
            手牌の文字列表現
        """
        # paistr からインスタンスを生成
        shoupai = Shoupai.from_string(paistr)

        # 生成したインスタンスからインスタンス変数をコピーする
        self._bingpai = {
            '_': shoupai._bingpai['_'],
            'm': copy.deepcopy(shoupai._bingpai['m']),
            'p': copy.deepcopy(shoupai._bingpai['p']),
            's': copy.deepcopy(shoupai._bingpai['s']),
            'z': copy.deepcopy(shoupai._bingpai['z'])
        }
        self._fulou = copy.deepcopy(shoupai._fulou)
        self._zimo = shoupai._zimo
        self._lizhi = shoupai._lizhi

    def zimo(self, p: str, check: bool = True):
        """
        牌``p``をツモる

        Parameters
        ----------
        p : str
            ツモ牌の文字列表現
        check : bool, default True
            多牌のチェックを行うかどうか

        Exceptions
        ----------
        Exception
            ``check``が真のときかつ多牌となる場合と、ツモ牌``p``が5枚目の牌の場合
        """
        # ツモ直後の場合は多牌となるので例外を発生する
        if check and self._zimo:
            raise Exception([self, p])

        if p == '_':    # 伏せ牌の場合
            self._bingpai['_'] += 1     # 伏せ牌の枚数を加算
            self._zimo = p  # ツモ牌を伏せ牌とする
        else:   # 通常牌の場合
            # 不正な牌の場合、例外を発生する
            if not Shoupai.valid_pai(p):
                raise Exception(p)
            s = p[0]
            n = int(p[1])
            bingpai = self._bingpai[s]
            # 5枚目の牌の場合、例外を発生する
            if bingpai[n] == 4:
                raise Exception([self, p])
            bingpai[n] += 1    # 枚数を加算する
            # 赤牌の場合は対応する「黒牌」の枚数も加算する
            if n == 0:
                if bingpai[5] == 4:
                    raise Exception([self, p])
                bingpai[5] += 1
            self._zimo = s + str(n)     # ツモ牌を設定する

    def dapai(self, p: str, check: bool = True):
        """
        手牌から牌``p``を打牌する

        Parameters
        ----------
        p : str
            牌の文字列表現
        check : True, default True
            少牌のチェックを行うかどうか

        Exceptions
        ----------
        Exception
            ``check``が真のときかつ打牌後に少牌となる場合
        """
        # ツモあるいは副露直後以外の打牌は少牌となるので例外を発生する
        if check and not self._zimo:
            raise Exception([self, p])

        # 不正な牌の場合、例外を発生する
        if not Shoupai.valid_pai(p):
            raise Exception(p)

        s = p[0]
        n = int(p[1])
        self._decrease(s, n)    # 牌の枚数を減算する
        self._zimo = None   # ツモしていない状態にする
        # 打牌がリーチ宣言の場合はリーチ後に状態を変更する
        if p[-1] == '*':
            self._lizhi = True

    def fulou(self, m: str, check: bool = True):
        """
        面子``m``を副露する

        Parameters
        ----------
        m : str
            面子の文字列表現
        check : bool, default True
            多牌のチェックを行うかどうか

        Exceptions
        ----------
        Exception
            ``check``が真のときかつ多牌となる場合
        """
        # ツモ直後の場合は多牌となるので例外を発生
        if check and self._zimo:
            raise Exception([self, m])

        # 不正な面子の場合、例外を発生
        if m != Shoupai.valid_mianzi(m):
            raise Exception(m)

        # 暗槓の場合、例外を発生
        if re.search(r'\d{4}$', m):
            raise Exception([self, m])

        # 加槓の場合、例外を発生
        if re.search(r'\d{3}[\+\=\-]\d$', m):
            raise Exception([self, m])

        # 副露に使う牌の枚数を減算する
        s = m[0]
        for n in re.findall(r'\d(?![\+\=\-])', m):
            self._decrease(s, int(n))
        # 副露面子に加える
        self._fulou.append(m)

        # 大明槓以外の場合は副露直後の状態にする
        if not re.search(r'\d{4}', m):
            self._zimo = m

    def gang(self, m: str, check: bool = True):
        """
        面子``m``で、暗槓もしくは加槓を行う

        Parameters
        ----------
        m : str
            面子の文字列表現
        check : bool, default True
            少牌のチェックを行うかどうか

        Exceptions
        ----------
        Exception
            ``check``が真のときかつ槓後に少牌となる場合
        """
        # ツモの直後は槓できないので、例外を発生
        if check and not self._zimo:
            raise Exception([self, m])
        if check and (len(self._zimo) > 2):
            raise Exception([self, m])

        # 不正な面子の場合、例外を発生
        if m != Shoupai.valid_mianzi(m):
            raise Exception([self, m])

        s = m[0]
        if re.search(r'\d{4}$', m):     # 暗槓の場合
            # 槓に使う牌の枚数を減算する
            for n in re.findall(r'\d', m):
                self._decrease(s, int(n))
            self._fulou.append(m)   # 副露面子に加える

        elif re.search(r'\d{3}[\+\=\-]\d$', m):     # 加槓の場合
            # 加槓前の刻子と一致する面子が副露されているかチェックし、
            # 副露されていない場合は例外を発生する
            m1 = m[0:5]
            try:
                i = self._fulou.index(m1)
            except ValueError:
                raise Exception([self, m])
            self._fulou[i] = m  # 元の刻子を槓子置き換える
            self._decrease(s, int(m[-1]))   # 加槓した牌の枚数を減算する

        else:   # 暗槓でも加槓でもない場合は例外を発生
            raise Exception([self, m])

        self._zimo = None   # ツモしていない状態にする

    def _decrease(self, s: str, n: int):
        bingpai = self._bingpai[s]
        if (bingpai[n] == 0) or (n == 5) and (bingpai[0] == bingpai[5]):
            # 存在しない牌を打牌しようとしている場合、伏せ牌があるなら
            # 伏せ牌からの打牌と解釈する。伏せ牌がない場合は例外を発生する
            if self._bingpai['_'] == 0:
                raise Exception([self, s+str(n)])
            self._bingpai['_'] -= 1
        else:
            bingpai[n] -= 1     # 牌の枚数を減算する
            if n == 0:  # 赤牌の場合は対応する「黒牌」の枚数も減算する
                bingpai[5] -= 1

    @property
    def menqian(self):
        """メンゼンかどうか"""
        return len([m for m in self._fulou if re.search(r'[\+\=\-]', m)]) == 0

    @property
    def lizhi(self) -> bool:
        """リーチしているかどうか"""
        return self._lizhi

    def get_dapai(self, check: bool = True) -> list[str] | None:
        """
        打牌可能な牌の一覧を返す

        Parameters
        ----------
        check : bool, default True
            True の場合、喰い替えとなる打牌を含まない

        Returns
        -------
        list[str] (or None)
            打牌可能な牌の配列
            打牌すると少牌になる場合は None を返す
        """
        # ツモあるいは副露直後以外は少牌となるので None を返す
        if not self._zimo:
            return None

        # 喰い替えとなる牌を deny に格納する
        deny = []
        if check and (len(self._zimo) > 2):     # 副露直後の場合
            m = self._zimo
            s = m[0]
            n = int(re.search(r'\d(?=[\+\=\-])', m).group()) or 5
            deny.append(s+str(n))   # 現物の喰い替えを禁止する
            # 順子の場合はスジ喰い替えも禁止する
            if not re.match(r'[mpsz](\d)\1\1', m.replace('0', '5')):
                if (n < 7) and re.fullmatch(r'[mps]\d\-\d\d', m):
                    deny.append(s+str(n+3))
                if (n > 3) and re.fullmatch(r'[mps]\d\d\d\-', m):
                    deny.append(s+str(n-3))

        # dapai に打牌可能な牌を追加していく。副露面子以外から重複しないよう追加
        # するが、赤牌とツモ牌は別の牌として扱う
        dapai = []
        if not self._lizhi:     # リーチしていない場合
            # すべての牌を順に検討していく
            for s in ['m', 'p', 's', 'z']:
                bingpai = self._bingpai[s]
                for n in range(1, len(bingpai)):
                    p = s + str(n)
                    if bingpai[n] == 0:     # 0枚の牌は打牌できない
                        continue
                    if p in deny:   # 喰い替えとなる牌は対象外
                        continue
                    if (p == self._zimo) and (bingpai[n] == 1):     # ツモ牌は最後に加える
                        continue

                    if (s == 'z') or (n != 5):
                        dapai.append(p)     # 赤牌以外はそのまま加える
                    else:   # 赤牌を考慮する場合
                        if (bingpai[0] > 0) and ((s+'0') != self._zimo) or (bingpai[0] > 1):
                            dapai.append(s+'0')     # 赤牌として加える
                        if bingpai[0] < bingpai[5]:
                            dapai.append(p)     # 赤牌以外として加える

        if len(self._zimo) == 2:
            dapai.append(self._zimo + '_')  # 最後にツモ牌を加える

        return dapai

    def get_chi_mianzi(self, p: str, check: bool = True) -> list[str] | None:
        """
        牌``p``でチー可能な牌の一覧を返す

        Parameters
        ----------
        p : str
            牌の文字列
        check : bool, default True
            True の場合、喰い替えが発生する面子は含まない

        Returns
        -------
        list[str] (or None)
            牌``p``でチー可能な面子のリスト
            リーチ後は空配列を返す
            チーすると少牌になる場合は None を返す
        """
        # ツモ直後の場合は多牌となるので None を返す
        if self._zimo:
            return None

        # 不正な牌の場合、例外を発生する
        if not Shoupai.valid_pai(p):
            raise Exception(p)

        mianzi = []
        s = p[0]
        n = int(p[1]) or 5
        d = re.search(r'[\+\=\-]$', p)
        # 方向(下家: +, 対面: =, 上家: -)が指定されていない場合は例外を発生する
        if not d:
            raise Exception(p)
        d = d.group()
        if (s == 'z') or d != '-':  # 上家からの数牌以外はチー不可
            return mianzi
        if self._lizhi:     # リーチ後はチー不可
            return mianzi

        bingpai = self._bingpai[s]

        # 喰い替えと赤牌を考慮して mianzi にチー可能な面子を追加していく

        # 鳴く牌が右に当たる場合
        if (n >= 3) and (bingpai[n-2] > 0) and (bingpai[n-1] > 0):
            if (not check) or (((bingpai[n-3] if n > 3 else 0) + bingpai[n]) < (14 - (len(self._fulou) + 1) * 3)):
                if ((n-2) == 5) and (bingpai[0] > 0):
                    mianzi.append(s + '067-')
                if ((n-1) == 5) and (bingpai[0] > 0):
                    mianzi.append(s + '406-')
                if ((n-2) != 5) and ((n-1) != 5) or bingpai[0] < bingpai[5]:
                    mianzi.append(s + str(n-2) + str(n-1) + (p[1]+d))

        # 鳴く牌が中央に当たる場合
        if (n >= 2) and (n <= 8) and (bingpai[n-1] > 0) and (bingpai[n+1] > 0):
            if (not check) or (bingpai[n] < (14 - (len(self._fulou) + 1) * 3)):
                if ((n-1) == 5) and (bingpai[0] > 0):
                    mianzi.append(s + '06-7')
                if ((n+1) == 5) and (bingpai[0] > 0):
                    mianzi.append(s + '34-0')
                if ((n-1) != 5) and ((n+1) != 5) or (bingpai[0] < bingpai[5]):
                    mianzi.append(s + str(n-1) + (p[1]+d) + str(n+1))

        # 鳴く牌が左に当たる場合
        if (n <= 7) and (bingpai[n+1] > 0) and bingpai[n+2] > 0:
            if (not check) or ((bingpai[n] + (bingpai[n+3] if n < 7 else 0)) < (14 - (len(self._fulou) + 1) * 3)):
                if ((n+1) == 5) and (bingpai[0] > 0):
                    mianzi.append(s + '4-06')
                if ((n+2) == 5) and (bingpai[0] > 0):
                    mianzi.append(s + '3-40')
                if ((n+1) != 5) and ((n+2) != 5) or (bingpai[0] < bingpai[5]):
                    mianzi.append(s + (p[1]+d) + str(n+1) + str(n+2))

        return mianzi

    def get_peng_mianzi(self, p: str) -> list[str] | None:
        """
        牌``p``でポン可能な面子の一覧を返す

        Parameters
        ----------
        p : str
            牌の文字列表現

        Returns
        -------
        list[str] (or None)
            牌``p``でポン可能な面子のリスト
            リーチ後は空配列を返す
            ポンすると多牌になる場合は None を返す
        """
        # ツモ直後の場合は多牌となるので None を返す
        if self._zimo:
            return None

        # 不正な牌の場合、例外を発生する
        if not Shoupai.valid_pai(p):
            raise Exception(p)

        mianzi = []
        s = p[0]
        n = int(p[1]) or 5
        d = re.search(r'[\+\=\-]$', p)
        # 方向(下家: +, 対面: =, 上家: -)が指定されていない場合は例外を発生する
        if not d:
            raise Exception(p)
        d = d.group()
        if self._lizhi:     # リーチ後はポンできない
            return mianzi

        bingpai = self._bingpai[s]

        # 赤牌を考慮して mianzi にポン可能な面子を追加していく
        if bingpai[n] >= 2:
            if (n == 5) and (bingpai[0] >= 2):
                mianzi.append(s + '00' + p[1] + d)
            if (n == 5) and (bingpai[0] >= 1):
                mianzi.append(s + '50' + p[1] + d)
            if (n != 5) or ((bingpai[5] - bingpai[0]) >= 2):
                mianzi.append(s + str(n)*2 + p[1] + d)

        return mianzi

    def get_gang_mianzi(self, p: str | None = None) -> list[str] | None:
        """
        牌``p``で大明槓可能な面子の一覧を返す

        ``p``が指定されていない場合は、加槓あるいは暗槓可能な面子の一覧を返す
        リーチ後は送り槓は含まない

        Parameters
        ----------
        p : str or None
            牌の文字列表現

        Returns
        -------
        list[str] (or None)
            牌``p``で大明槓可能な面子のリスト
            もしくは、加槓、暗槓が可能な面子のリスト
            カンすると少牌あるいは多牌になる場合は None を返す
            """

        mianzi = []
        if p:   # 大明槓の場合
            # ツモ直後の場合は多牌となるので None を返す
            if self._zimo:
                return None

            # 不正な牌の場合、例外を発生する
            if not Shoupai.valid_pai(p):
                raise Exception(p)

            s = p[0]
            n = int(p[1]) or 5
            d = re.search(r'[\+\=\-]$', p)
            # 方向(下家: +, 対面: =, 上家: -)が指定されていない場合は例外を発生する
            if not d:
                raise Exception(p)
            d = d.group()
            if self._lizhi:     # リーチ後は大明槓できない
                return mianzi

            bingpai = self._bingpai[s]

            # 赤牌を考慮して mianzi に大明槓可能な面子を追加する
            if bingpai[n] == 3:
                if n == 5:
                    mianzi = [s + '5'*(3-bingpai[0]) + '0'*bingpai[0] + p[1] + d]
                else:
                    mianzi = [s + str(n)*4 + d]

        else:   # 暗槓・加槓の場合
            # ツモの直後以外は暗槓・加槓できないので None を返す
            if not self._zimo:
                return None
            if len(self._zimo) > 2:
                return None

            p = self._zimo.replace('0', '5')

            # 副露面子以外の手牌の全ての牌について以下の処理を行う
            for s in ['m', 'p', 's', 'z']:
                bingpai = self._bingpai[s]
                for n in range(1, len(bingpai)):
                    if bingpai[n] == 0:     # 0枚の牌は槓できない
                        continue

                    if bingpai[n] == 4:     # 暗槓可能な場合
                        if self._lizhi and ((s+str(n)) != p):   # リーチ後に送り槓はできない
                            continue
                        # 赤牌を考慮して mianzi に暗槓を加える
                        if n == 5:
                            mianzi.append(s + '5'*(4-bingpai[0]) + '0'*bingpai[0])
                        else:
                            mianzi.append(s + str(n)*4)

                    else:   # その他の場合
                        if self._lizhi:     # リーチ後は槓できない
                            continue
                        # 副露面子に当該の牌で加槓できる刻子があれば mianzi に槓子として追加する
                        for m in self._fulou:
                            if m.replace('0', '5')[0:4] == (s+str(n)*3):
                                if (n == 5) and (bingpai[0] > 0):
                                    mianzi.append(m+'0')
                                else:
                                    mianzi.append(m+str(n))

        return mianzi
