import pytest

import jongpy.core as jongpy


class Player(jongpy.Player):
    def __init__(self) -> None:
        super().__init__()

    def action_kaiju(self, kaiju):
        self._callback()

    def action_qipai(self, qipai):
        self._callback()

    def action_zimo(self, zimo):
        self._callback()

    def action_dapai(self, dapai):
        self._callback()

    def action_fulou(self, fulou):
        self._callback()

    def action_gang(self, gang):
        self._callback()

    def action_hule(self, hule):
        self._callback()

    def action_pingju(self, pingju):
        self._callback()

    def action_jieju(self, paipu):
        self._callback()


def init_player(param: dict = {}):

    player = Player()

    kaiju = {
        'id': 1,
        'rule': jongpy.rule(),
        'title': 'タイトル',
        'player': ['自家', '下家', '対面', '上家'],
        'qijia': 1
    }

    qipai = {
        'zhuangfeng': 0,
        'jushu': 0,
        'changbang': 0,
        'lizhibang': 0,
        'defen': [25000, 25000, 25000, 25000],
        'baopai': 'm1',
        'shoupai': ['', '', '', '']
    }

    if 'rule' in param:
        kaiju['rule'] = param['rule']
    if param.get('jushu') is not None:
        qipai['jushu'] = param['jushu']

    menfeng = (kaiju['id'] + 4 - kaiju['qijia'] + 4 - qipai['jushu']) % 4
    qipai['shoupai'][menfeng] = param.get('shoupai') or 'm123p456s789z1234'

    player.kaiju(kaiju)
    player.qipai(qipai)

    return player


class TestPlayerInit:
    @pytest.fixture
    def setup(self):
        self._player = Player()

    def test_error_abstract_class(self):
        with pytest.raises(TypeError):
            jongpy.Player()

    def test_instance(self, setup):
        assert self._player

    def test_initial_value(self, setup):
        assert self._player._model


class TestPlayerKaiju:
    def test_initial_value(self):
        player = Player()
        kaiju = {'id': 1, 'rule': jongpy.rule(), 'title': 'タイトル',
                 'player': ['自家', '下家', '対面', '上家']}
        player.kaiju(kaiju)

        assert player._id == 1
        assert player._rule == jongpy.rule()
        assert player._model.title == 'タイトル'


class TestPlayerQipai:
    def test_initial_value(self):
        player = Player()
        kaiju = {'id': 1, 'rule': jongpy.rule(), 'title': 'タイトル',
                 'player': ['自家', '下家', '対面', '上家'], 'qijia': 2}
        player.kaiju(kaiju)

        qipai = {'zhuangfeng': 1, 'jushu': 2, 'changbang': 3, 'lizhibang': 4,
                 'defen': [25000, 25000, 25000, 25000], 'baopai': 's5',
                 'shoupai': ['', 'm123p456s789z1234', '', '']}
        player.qipai(qipai)

        assert player._menfeng == 1
        assert player._diyizimo
        assert player._n_gang == 0
        assert player._neng_rong
        assert str(player.shoupai) == 'm123p456s789z1234'
        assert len(player.he._pai) == 0


class TestPlayerZimo:
    @pytest.fixture
    def setup(self):
        self._player = init_player()

    def test_update_board(self, setup):
        self._player.zimo({'l': 0, 'p': 'z5'})
        assert str(self._player.shoupai) == 'm123p456s789z1234z5'

    def test_n_gang(self, setup):
        self._player.zimo({'l': 0, 'p': 'z5'}, True)
        assert self._player._n_gang == 1


class TestPlayerDapai:
    def test_update_board(self):
        player = init_player({'shoupai': 'm123p456s789z1234z5'})
        player.dapai({'l': 0, 'p': 'z5'})
        assert str(player.shoupai) == 'm123p456s789z1234'

    def test_diyizimo(self):
        player = init_player({'jushu': 3})
        player.dapai({'l': 0, 'p': 'z5'})
        assert player._diyizimo
        player.dapai({'l': 1, 'p': 'z1'})
        assert not player._diyizimo

    def test_neng_rong(self):
        player = init_player({'shoupai': 'm123p406s789z11222'})
        player.dapai({'l': 0, 'p': 'p0'})
        assert not player._neng_rong

    def test_neng_rong_lifted(self):
        player = init_player({'shoupai': 'm123p456s789z11223'})
        player._neng_rong = False
        player.dapai({'l': 0, 'p': 'z3_'})
        assert player._neng_rong

    def test_neng_rong_before_lizhi(self):
        player = init_player({'shoupai': 'm123p456s789z11232'})
        player._neng_rong = False
        player.dapai({'l': 0, 'p': 'z3*'})
        assert player._neng_rong

    def test_neng_rong_after_lizhi(self):
        player = init_player({'shoupai': 'm123p456s789z11223*'})
        player._neng_rong = False
        player.dapai({'l': 0, 'p': 'z3_'})
        assert not player._neng_rong

    def test_neng_rong_overlooked(self):
        player = init_player({'shoupai': 'm123p46s789z11122'})
        player.dapai({'l': 1, 'p': 'p0'})
        assert not player._neng_rong


class TestPlayerFulou:
    def test_update_board(self):
        player = init_player({'shoupai': 'm123p456s789z1134'})
        player.dapai({'l': 2, 'p': 'z1'})
        player.fulou({'l': 0, 'm': 'z111='})
        assert str(player.shoupai) == 'm123p456s789z34,z111=,'

    def test_diyizimo(self):
        player = init_player({'jushu': 1})
        player.dapai({'l': 0, 'p': 'z3'})
        assert player._diyizimo
        player.fulou({'l': 1, 'm': 'z333='})
        assert not player._diyizimo


class TestPlayerGang:
    def test_update_board(self):
        player = init_player({'shoupai': 'm123p456s788z12,z111='})
        player.gang({'l': 0, 'm': 'z111=1'})
        assert str(player.shoupai) == 'm123p456s788z2,z111=1'

    def test_diyizimo(self):
        player = init_player({'jushu': 1})
        player.gang({'l': 0, 'm': 'm9999'})
        assert not player._diyizimo

    def test_neng_rong(self):
        player = init_player({'shoupai': 'm34p456s788z11222'})
        player.dapai({'l': 2, 'p': 'm5'})
        player.fulou({'l': 3, 'm': 'm555-'})
        player.dapai({'l': 2, 'p': 's4'})
        player.fulou({'l': 3, 'm': 's444-'})
        player.zimo({'l': 0, 'p': 's9'})
        player.dapai({'l': 0, 'p': 's8'})
        player.gang({'l': 3, 'm': 's444-4'})
        assert player._neng_rong
        player.gang({'l': 3, 'm': 'm555-0'})
        assert not player._neng_rong


class TestPlayerKaigang:
    def test_update_board(self):
        player = init_player()
        player.kaigang({'baopai': 'p1'})
        assert player.shan.baopai.pop() == 'p1'


class TestPlayerHule:
    def test_update_board(self):
        player = init_player()
        player.hule({'l': 1, 'shoupai': 'm123p456s789z1122z1*',
                     'fubaopai': ['s1']})
        assert str(player._model.shoupai[1]) == 'm123p456s789z1122z1*'
        assert player.shan.fubaopai[0] == 's1'


class TestPlayerPingju:
    def test_update_board(self):
        player = init_player()
        player.dapai({'l': 1, 'p': 'm3*'})
        player.pingju({'name': '', 'shoupai': ['', '', '', 'm123p456s789z1122*']})
        assert str(player._model.shoupai[3]) == 'm123p456s789z1122*'
        assert player._model.lizhibang == 1


class TestPlayerJieju:
    @pytest.fixture
    def setup(self):
        self._player = init_player()

    def test_update_board(self, setup):
        paipu = {'defen': [10000, 20000, 30000, 40000]}
        self._player.jieju(paipu)
        assert self._player._model.defen == paipu['defen']

    def test_get_paipu(self, setup):
        self._player.jieju({'defen': [None, None, None, None]})
        assert self._player._paipu


class TestPlayerGetDapai:
    def test_no_change(self):
        player = init_player()
        shoupai = jongpy.Shoupai.from_str('m14p45677s6788,m234-,')
        assert player.get_dapai(shoupai) == ['p4', 'p5', 'p6', 'p7', 's6', 's7', 's8']

    def test_ok_change(self):
        player = init_player({'rule': jongpy.rule({'allow_fulou_slide': 1})})
        shoupai = jongpy.Shoupai.from_str('m14p45677s6788,m234-,')
        assert player.get_dapai(shoupai) == ['m1', 'p4', 'p5', 'p6', 'p7', 's6', 's7', 's8']


class TestPlayerGetChiMianzi:
    def test_no_change(self):
        player = init_player()
        shoupai = jongpy.Shoupai.from_str('p1112344,z111=,z222+')
        assert player.get_chi_mianzi(shoupai, 'p4-') == []

    def test_ok_change(self):
        player = init_player({'rule': jongpy.rule({'allow_fulou_slide': 1})})
        shoupai = jongpy.Shoupai.from_str('p1112344,z111=,z222+')
        assert player.get_chi_mianzi(shoupai, 'p4-') == ['p234-']

    def test_ng_haidi(self):
        player = init_player()
        while player.shan.paishu:
            player.shan.zimo()
        shoupai = jongpy.Shoupai.from_str('m23p456s789z11123')
        assert player.get_chi_mianzi(shoupai, 'm1-') == []


class TestPlayerGetPengMianzi:
    @pytest.fixture
    def setup(self):
        self._player = init_player()

    def test_ok(self, setup):
        shoupai = jongpy.Shoupai.from_str('m123p456s789z1123')
        assert self._player.get_peng_mianzi(shoupai, 'z1+') == ['z111+']

    def test_ng_haidi(self, setup):
        while self._player.shan.paishu:
            self._player.shan.zimo()
        shoupai = jongpy.Shoupai.from_str('m123p456s789z1123')
        assert self._player.get_chi_mianzi(shoupai, 'z1+') == []


class TestPlayerGetGangMianzi:
    @pytest.fixture
    def setup(self):
        self._player = init_player()

    def test_angang(self, setup):
        shoupai = jongpy.Shoupai.from_str('m123p456s789z11112')
        assert self._player.get_gang_mianzi(shoupai) == ['z1111']

    def test_daimingang(self, setup):
        shoupai = jongpy.Shoupai.from_str('m123p456s789z1112')
        assert self._player.get_gang_mianzi(shoupai, 'z1=') == ['z1111=']

    def test_ng_haidi(self, setup):
        while self._player.shan.paishu:
            self._player.shan.zimo()
        shoupai = jongpy.Shoupai.from_str('m123p456s789z11112')
        assert self._player.get_gang_mianzi(shoupai) == []

    def test_ng_5th_gang(self, setup):
        self._player._n_gang = 4
        shoupai = jongpy.Shoupai.from_str('m123p456s789z11112')
        assert self._player.get_gang_mianzi(shoupai) == []

    def test_ok_angang_after_lizhi(self, setup):
        shoupai = jongpy.Shoupai.from_str('m123p456s789z1112z1*')
        assert self._player.get_gang_mianzi(shoupai) == ['z1111']

    def test_ng_angang_after_lizhi(self):
        player = init_player({'rule': jongpy.rule({'allow_angang_after_lizhi': 0})})
        shoupai = jongpy.Shoupai.from_str('m123p456s789z1112z1*')
        assert player.get_gang_mianzi(shoupai) == []


class TestPlayerAllowLizhi:
    @pytest.fixture
    def setup(self):
        self._player = init_player()
        self._shoupai = jongpy.Shoupai.from_str('m223p456s789z11122')

    def test_get_ok_list(self, setup):
        assert self._player.allow_lizhi(self._shoupai) == ['m2', 'm3']

    def test_judge_ok(self, setup):
        assert self._player.allow_lizhi(self._shoupai, 'm2')

    def test_ng_no_lizhi(self, setup):
        while self._player.shan.paishu >= 4:
            self._player.shan.zimo()
        assert not self._player.allow_lizhi(self._shoupai)

    def test_ok_no_lizhi(self, setup):
        player = init_player({'rule': jongpy.rule({'lizhi_no_zimo': True})})
        while player.shan.paishu >= 4:
            player.shan.zimo()
        assert self._player.allow_lizhi(self._shoupai)

    def test_enable_minus_interruption(self, setup):
        self._player._model.defen[self._player._id] = 900
        assert not self._player.allow_lizhi(self._shoupai)

    def test_disable_minus_interruption(self, setup):
        player = init_player({'rule': jongpy.rule({'minus_interruption': False})})
        player._model.defen[player._id] = 900
        assert player.allow_lizhi(self._shoupai)


class TestPlayerAllowHule:
    @pytest.fixture
    def setup(self):
        self._player = init_player()
        self._shoupai = jongpy.Shoupai.from_str('m123p456s789z1122')

    def test_no_hule(self, setup):
        assert not self._player.allow_hule(self._shoupai, 'z2=')

    def test_lizhi(self, setup):
        shoupai = jongpy.Shoupai.from_str('m123p456s789z1122*')
        assert self._player.allow_hule(shoupai, 'z2=')

    def test_haidi(self, setup):
        while self._player.shan.paishu:
            self._player.shan.zimo()
        assert self._player.allow_hule(self._shoupai, 'z2=')

    def test_qianggang(self, setup):
        assert self._player.allow_hule(self._shoupai, 'z2=', True)

    def test_neng_rong(self, setup):
        self._player._neng_rong = False
        assert not self._player.allow_hule(self._shoupai, 'z1=')


class TestPlayerAllowPingju:
    def test_9shu_9pai(self):
        player = init_player()
        shouapi = jongpy.Shoupai.from_str('m1234569z1234567')
        assert player.allow_pingju(shouapi)

    def test_ng_after_diyizimo(self):
        player = init_player()
        player._diyizimo = False
        shouapi = jongpy.Shoupai.from_str('m123459z1234567')
        assert not player.allow_pingju(shouapi)

    def test_disable_interrupted_pingju(self):
        player = init_player({'rule': jongpy.rule({'interrupted_pingju': False})})
        shoupai = jongpy.Shoupai.from_str('m123459z1234567')
        assert not player.allow_pingju(shoupai)


class TestPlayerAllowNoDaopai:
    def test_ok_declare_no_tingpai(self):
        player = init_player({'rule': jongpy.rule({'declare_no_tingpai': True})})
        shoupai = jongpy.Shoupai.from_str('m123p456s789z1122')
        while player.shan.paishu:
            player.shan.zimo()
        assert player.allow_no_daopai(shoupai)

    def test_diable_declare_no_tingpai(self):
        player = init_player()
        shoupai = jongpy.Shoupai.from_str('m123p456s789z1122')
        while player.shan.paishu:
            player.shan.zimo()
        assert not player.allow_no_daopai(shoupai)

    def test_no_tingpai(self):
        player = init_player({'rule': jongpy.rule({'declare_no_tingpai': True})})
        shoupai = jongpy.Shoupai.from_str('m123p456s789z1123')
        while player.shan.paishu:
            player.shan.zimo()
        assert not player.allow_no_daopai(shoupai)

    def test_no_pingju(self):
        player = init_player({'rule': jongpy.rule({'declare_no_tingpai': True})})
        shoupai = jongpy.Shoupai.from_str('m123p456s789z1122')
        assert not player.allow_no_daopai(shoupai)
