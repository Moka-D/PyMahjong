import pytest

from jongpy.core import Board


def init_board():
    board = Board({
        'title': 'タイトル',
        'player': ['自家', '下家', '対面', '上家'],
        'qijia': 1
    })

    qipai = {
        'zhuangfeng': 1,
        'jushu': 2,
        'changbang': 3,
        'lizhibang': 4,
        'defen': [10000, 20000, 30000, 36000],
        'baopai': 'm1',
        'shoupai': ['', '', '', '']
    }
    board.qipai(qipai)

    return board


class TestBoardInit:
    @pytest.fixture
    def setup(self):
        self._board = Board({
            'title': 'タイトル',
            'player': ['自家', '下家', '対面', '上家'],
            'qijia': 1
        })

    def test_make_instance(self, setup):
        assert self._board

    def test_title(self, setup):
        assert self._board.title == 'タイトル'

    def test_players(self, setup):
        assert self._board.player == ['自家', '下家', '対面', '上家']

    def test_qijia(self, setup):
        assert self._board.qijia == 1

    def test_no_param(self):
        assert Board()


class TestBoardMenfeng:
    @pytest.fixture
    def setup(self):
        self._board = Board({})

    def test_qijia_ton_ton1(self, setup):
        self._board.qijia = 0
        self._board.jushu = 0
        assert self._board.menfeng(0) == 0
        assert self._board.menfeng(1) == 1
        assert self._board.menfeng(2) == 2
        assert self._board.menfeng(3) == 3

    def test_qijia_ton_ton2(self, setup):
        self._board.qijia = 0
        self._board.jushu = 1
        assert self._board.menfeng(0) == 3
        assert self._board.menfeng(1) == 0
        assert self._board.menfeng(2) == 1
        assert self._board.menfeng(3) == 2

    def test_qijia_nan_ton1(self, setup):
        self._board.qijia = 1
        self._board.jushu = 0
        assert self._board.menfeng(0) == 3
        assert self._board.menfeng(1) == 0
        assert self._board.menfeng(2) == 1
        assert self._board.menfeng(3) == 2


class TestBoardQipai:
    @pytest.fixture
    def setup(self):
        self._board = Board({
            'title': 'タイトル',
            'player': ['自家', '下家', '対面', '上家'],
            'qijia': 1
        })
        qipai = {
            'zhuangfeng': 1,
            'jushu': 2,
            'changbang': 3,
            'lizhibang': 4,
            'defen': [10000, 20000, 30000, 36000],
            'baopai': 'm1',
            'shoupai': ['', 'm123p456s789z1234', '', '']
        }
        self._board.qipai(qipai)

    def test_zhuangfeng(self, setup):
        assert self._board.zhuangfeng == 1

    def test_junshu(self, setup):
        assert self._board.jushu == 2

    def test_changbang(self, setup):
        assert self._board.changbang == 3

    def test_lizhibang(self, setup):
        assert self._board.lizhibang == 4

    def test_baopai(self, setup):
        assert self._board.shan.baopai[0] == 'm1'

    def test_defen(self, setup):
        assert self._board.defen[0] == 20000

    def test_shoupai(self, setup):
        assert str(self._board.shoupai[1]) == 'm123p456s789z1234'

    def test_he(self, setup):
        assert sum(map(lambda he: len(he._pai), self._board.he)) == 0

    def test_lunban(self, setup):
        assert self._board.lunban == -1


class TestBoardZimo:
    @pytest.fixture
    def setup(self):
        self._board = init_board()
        self._board.zimo({'l': 0, 'p': 'm1'})

    def test_linban(self, setup):
        assert self._board.lunban == 0

    def test_shan_paishu(self, setup):
        assert self._board.shan.paishu == 69

    def test_shoupai(self, setup):
        assert self._board.shoupai[0].get_dapai().pop() == 'm1_'

    def test_hidden_pai(self):
        board = init_board()
        board.zimo({'l': 0, 'p': ''})
        board.shoupai[0].get_dapai()

    def test_lizhi(self):
        board = init_board()
        board.zimo({'l': 0, 'p': 'm1'})
        board.dapai({'l': 0, 'p': 'm1_*'})
        board.zimo({'l': 1, 'p': 's9'})
        assert board.defen[board.player_id[0]] == 9000
        assert board.lizhibang == 5

    def test_shoupai_overflow(self):
        board = init_board()
        board.zimo({'l': 0, 'p': 'm1'})
        board.zimo({'l': 0, 'p': 'm2'})


class TestBoardDapai:
    @pytest.fixture
    def setup(self):
        self._board = init_board()
        self._board.zimo({'l': 0, 'p': 'm1'})
        self._board.dapai({'l': 0, 'p': 'm1_'})

    def test_dapai(self, setup):
        assert self._board.shoupai[0].get_dapai() is None

    def test_he(self, setup):
        assert self._board.he[0]._pai[0] == 'm1_'

    def test_shoupai_underflow(self):
        board = init_board()
        board.dapai({'l': 0, 'p': 'm1'})


class TestBoardFulou:
    @pytest.fixture
    def setup(self):
        self._board = init_board()
        self._board.zimo({'l': 0, 'p': 'm1'})
        self._board.dapai({'l': 0, 'p': 'm1_'})
        self._board.fulou({'l': 2, 'm': 'm111='})

    def test_he(self, setup):
        assert self._board.he[0]._pai[0] == 'm1_='

    def test_lunbun(self, setup):
        assert self._board.lunban == 2

    def test_fulou(self, setup):
        assert self._board.shoupai[2]._fulou[0] == 'm111='

    def test_after_lizhi(self):
        board = init_board()
        board.zimo({'l': 0, 'p': 'm1'})
        board.dapai({'l': 0, 'p': 'm1_*'})
        board.fulou({'l': 2, 'm': 'm111='})
        assert board.defen[board.player_id[0]] == 9000
        assert board.lizhibang == 5

    def test_shoupai_overflow(self):
        board = init_board()
        board.zimo({'l': 0, 'p': 'm1'})
        board.dapai({'l': 2, 'p': 'm1'})
        board.fulou({'l': 0, 'm': 'm111='})


class TestBoardGang:
    @pytest.fixture
    def setup(self):
        self._board = init_board()

    def test_fulou(self, setup):
        self._board.zimo({'l': 0, 'p': 'm1'})
        self._board.gang({'l': 0, 'm': 'm1111'})
        assert self._board.shoupai[0]._fulou[0] == 'm1111'

    def test_shoupai_underflow(self, setup):
        self._board.gang({'l': 0, 'm': 'm1111'})


class TestBoardKaigang:
    def test_baopai(self):
        board = init_board()
        board.zimo({'l': 0, 'p': 'm1'})
        board.gang({'l': 0, 'm': 'm1111'})
        board.kaigang({'baopai': 's9'})
        assert board.shan.baopai[1] == 's9'


class TestBoardHule:
    @pytest.fixture
    def setup(self):
        self._board = init_board()
        self._board.zimo({'l': 0, 'p': 'm1'})
        self._board.hule({'l': 0, 'shoupai': 'm123p456s789z1122z2*', 'fubaopai': ['s9']})

    def test_shoupai(self, setup):
        assert str(self._board.shoupai[0]) == 'm123p456s789z1122z2*'

    def test_fubaopai(self, setup):
        assert self._board.shan.fubaopai[0] == 's9'

    def test_double_rong(self):
        board = init_board()
        board.zimo({'l': 1, 'p': ''})
        board.dapai({'l': 1, 'p': 'p4_'})
        board.hule({'l': 2, 'shoupai': 'm444678p44s33p4,s505=', 'baojia': 1,
                    'fubaopai': None, 'fu': 30, 'fanshu': 2, 'defen': 2000,
                    'hupai': [{'name': '断ヤオ九', 'fanshu': 1},
                              {'name': '赤ドラ', 'fanshu': 1}],
                    'fenpei': [0, -2900, 6900, 0]})
        board.hule({'l': 0, 'shoupai': 'p06s12344p4,z777-,p333+', 'baojia': 1,
                    'fubaopai': None, 'fu': 30, 'fanshu': 2, 'defen': 2900,
                    'hupai': [{'name': '役牌 中', 'fanshu': 1},
                              {'name': '赤ドラ', 'fanshu': 1}],
                    'fenpei': [0, -2900, 2900, 0]})
        assert board.changbang == 0
        assert board.lizhibang == 0
        assert board.defen == [17100, 36900, 36000, 10000]


class TestBoardPingju:
    @pytest.fixture
    def setup(self):
        self._board = init_board()

    def test_shoupai(self, setup):
        self._board.pingju({'name': '', 'shoupai': ['', 'm123p456s789z1122', '', '']})
        assert str(self._board.shoupai[1]) == 'm123p456s789z1122'

    def test_lizhi(self, setup):
        self._board.zimo({'l': 0, 'p': 'm1'})
        self._board.dapai({'l': 0, 'p': 'm1_*'})
        self._board.pingju({'name': '荒牌平局', 'shoupai': ['', '', '', '']})
        assert self._board.defen[self._board.player_id[0]] == 9000
        assert self._board.lizhibang == 5

    def test_triple_rong(self, setup):
        self._board.zimo({'l': 0, 'p': 'm1'})
        self._board.dapai({'l': 0, 'p': 'm1_*'})
        self._board.pingju({'name': '三家和', 'shoupai': ['', '', '', '']})
        assert self._board.defen[self._board.player_id[0]] == 10000
        assert self._board.lizhibang == 4


class TestBoardJieju:
    @pytest.fixture
    def setup(self):
        self._board = init_board()
        self._board.lunban = 0
        paipu = {'defen': [17100, 36900, 36000, 10000]}
        self._board.jieju(paipu)

    def test_defen(self, setup):
        assert self._board.defen == [17100, 36900, 36000, 10000]

    def test_lunban(self, setup):
        assert self._board.lunban == -1
