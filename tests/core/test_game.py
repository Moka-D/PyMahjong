import pytest
import re
import time
import asyncio

import jongpy.core as majiang
from jongpy.core.exceptions import PaiFormatError


SCRIPT = 'script.json'
MSG = [{}] * 4
called = 0


def init_msg():
    global MSG
    MSG = [{}] * 4


@pytest.fixture(autouse=True)
def init_called():
    global called
    called = 0


def done():
    global called
    called = 1


def wrap_with_delay(sec, callback, *args):
    time.sleep(sec)
    callback(*args)


def set_timeout(timeout: int, callback, *args):
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_in_executor(None, wrap_with_delay, timeout / 1000, callback, *args)


class Player:
    def __init__(self, id, reply=None, delay=0):
        self._id = id
        self._reply = [] if reply is None else reply
        self._delay = delay

    def action(self, msg, callback=None):
        MSG[self._id] = msg
        if callback is not None:
            if self._delay:
                set_timeout(self._delay, callback, self._reply.pop(0))
            else:
                callback(self._reply.pop(0) if len(self._reply) else None)


class View:
    def kaiju(self, param=None):
        self._param = {'kaiju': param}

    def redraw(self, param=None):
        self._param = {'redraw': param}

    def update(self, param=None):
        self._param = {'update': param}

    def say(self, *param):
        self._say = param

    def summary(self, param):
        self._param = {'summary': param}


def init_game(param: dict = {}):

    init_msg()

    players = [Player(id) for id in range(4)]
    rule = param.get('rule') or majiang.rule()
    game = majiang.Game(players, param.get('callback'), rule)

    game.view = View()
    game._sync = True
    if param.get('qijia') is not None:
        game.kaiju(param['qijia'])
    else:
        game.kaiju()

    if 'lizhibang' in param:
        game.model['lizhibang'] = param['lizhibang']
    if 'changbang' in param:
        game.model['changbang'] = param['changbang']

    game.qipai()

    if 'shoupai' in param:
        for i in range(4):
            if not param['shoupai'][i]:
                continue
            paistr = param['shoupai'][i]
            if paistr == '_':
                paistr = '_' * 13
            game.model['shoupai'][i] = majiang.Shoupai.from_str(paistr)
    if 'zimo' in param:
        pai = game.model['shan']._pai
        for i in range(len(param['zimo'])):
            pai[-(i + 1)] = param['zimo'][i]
    if 'gangzimo' in param:
        pai = game.model['shan']._pai
        for i in range(len(param['gangzimo'])):
            pai[i] = param['gangzimo'][i]
    if 'baopai' in param:
        game.model['shan']._baopai = [param['baopai']]
    if 'defen' in param:
        for i in range(4):
            id = game.model['player_id'][i]
            game.model['defen'][id] = param['defen'][i]

    return game


def set_reply(game: majiang.Game, reply: list[dict]):
    for i in range(4):
        id = game.model['player_id'][i]
        game._players[id]._reply = [reply[i]]


def last_paipu(game: majiang.Game, i: int = 0) -> dict:
    return game._paipu['log'][-1 + i]


class TestGameInit:
    @pytest.fixture
    def setup(self):
        self._game = majiang.Game([], None)
        self._rule = majiang.rule()

    def test_instance(self, setup):
        assert self._game

    def test_title_ok(self, setup):
        assert self._game._model['title']

    def test_settable_title(self, setup):
        game = majiang.Game([], None, self._rule, 'タイトル')
        assert game._model['title'] == 'タイトル'

    def test_player_ok(self, setup):
        assert self._game._model['player'] == ['自家', '下家', '対面', '上家']

    def test_init_jushu(self, setup):
        assert self._game._model['zhuangfeng'] == 0
        assert self._game._model['jushu'] == 0

    def test_init_bang(self, setup):
        assert self._game._model['changbang'] == 0
        assert self._game._model['lizhibang'] == 0

    def test_init_defen(self, setup):
        assert self._game._model['defen'] == [25000, 25000, 25000, 25000]

    def test_changeable_defen(self):
        rule = majiang.rule({'origin_points': 30000})
        game = majiang.Game([], None, rule)
        assert game._model['defen'] == [30000, 30000, 30000, 30000]


class TestGameSpeed:
    def test_speed(self):
        game = majiang.Game([], None)
        game.speed = 5
        assert game.speed == 5


class TestGameDelay:
    @pytest.fixture
    def setup(self):
        self._game = majiang.Game([], None)

    def test_speed_0(self, setup):
        self._game.speed = 0
        self._game.delay(done)
        assert called == 1

    def test_speed_1(self, setup):
        self._game.speed = 1
        self._game.delay(done)
        time.sleep(0.2)
        assert called == 0
        time.sleep(0.5)
        assert called == 1

    def test_speed_3(self, setup):
        self._game.speed = 3
        self._game.delay(done)
        time.sleep(0.5)
        assert called == 0
        time.sleep(0.6)
        assert called == 1

    def test_speed_0_timeout_100(self, setup):
        self._game.speed = 0
        self._game.delay(done, 100)
        assert called == 1

    def test_speed_5_timeout_100(self, setup):
        self._game.speed = 5
        self._game.delay(done, 100)
        assert called == 0
        time.sleep(0.1)
        assert called == 1


class TestGameStop:
    @pytest.fixture
    def setup(self):
        self._game = majiang.Game([], None)

    def test_stop_ok(self, setup):
        self._game.stop()
        assert self._game._stop
        self._game._reply = [1, 1, 1, 1]
        self._game.next()

    def test_stop_callback(self, setup):
        self._game.stop(done)
        self._game._reply = [1, 1, 1, 1]
        self._game.next()
        assert called == 1


class TestGameStart:
    @pytest.fixture
    def setup(self):
        self._game = majiang.Game([], None)

    def test_restart(self, setup):
        self._game.stop()
        self._game.start()
        assert not self._game._stop
        assert self._game._loop

    def test_no_double_stand(self, setup):
        loop = asyncio.get_event_loop()
        self._game._loop = loop
        self._game.start()
        assert self._game._loop == loop


class TestGameNotifyPlayers:
    @pytest.fixture
    def setup(self):
        players = [Player(id) for id in range(4)]
        self._game = majiang.Game(players, None)
        self._msg = [{'a': None}, {'b': None}, {'c': None}, {'d': None}]

    def test_msg(self, setup):
        init_msg()
        self._game.notify_players('type', self._msg)
        assert MSG == self._msg


class TestGameCallPlayers:
    @pytest.fixture
    def setup(self):
        self._players = [Player(id) for id in range(4)]
        self._game = majiang.Game(self._players, None)
        self._game.speed = 1
        self._type = 'test'
        self._msg = [{'a': None}, {'b': None}, {'c': None}, {'d': None}]

    def test_msg(self, setup):
        self._game.stop()
        init_msg()
        self._game.call_players(self._type, self._msg)
        assert MSG == self._msg

    def test_reply(self, setup):
        self._game.stop(done)
        self._game.call_players(self._type, self._msg)
        assert called == 1

    def test_slow_player(self, setup):
        self._game.stop(done)
        for player in self._players:
            player._delay = 100
        self._game.call_players(self._type, self._msg, 0)
        time.sleep(1)


class TestGameKaiju:
    @pytest.fixture
    def setup(self):
        players = [Player(id) for id in range(4)]
        rule = majiang.rule()
        self._game = majiang.Game(players, None, rule)
        self._game.view = View()
        self._game.speed = 0
        self._game._sync = True
        self._game.stop()
        init_msg()
        self._game.kaiju(0)

    def test_init_qijia(self, setup):
        assert self._game._model['qijia'] == 0

    def test_init_paipu(self, setup):
        assert self._game._paipu['title'] == self._game._model['title']
        assert self._game._paipu['player'] == self._game._model['player']
        assert self._game._paipu['qijia'] == self._game._model['qijia']
        assert len(self._game._paipu['log']) == 0

    def test_init_view(self, setup):
        assert self._game.view._param == {'kaiju': None}

    def test_msg(self, setup):
        for id in range(4):
            msg = {
                'kaiju': {
                    'id': id,
                    'rule': self._game._rule,
                    'title': self._game._model['title'],
                    'player': self._game._model['player'],
                    'qijia': 0
                }
            }
            assert MSG[id] == msg

    def test_random_qijia(self, setup):
        self._game.stop()
        self._game.kaiju()
        assert (self._game._model['qijia'] == 0
                or self._game._model['qijia'] == 1
                or self._game._model['qijia'] == 2
                or self._game._model['qijia'] == 3)


class TestGameQipai:
    @pytest.fixture
    def setup(self):
        players = [Player(id) for id in range(4)]
        rule = majiang.rule()
        self._game = majiang.Game(players, None, rule)
        self._game.view = View()
        self._game.speed = 0
        self._game._sync = True
        init_msg()
        self._game.kaiju()
        self._game.qipai()

    def test_shan(self, setup):
        shan = self._game.model['shan']
        assert shan.paishu == 70
        assert len(shan.baopai) == 1
        assert shan.fubaopai is None

    def test_qipai(self, setup):
        for i in range(4):
            assert len(re.sub('[mpsz]', '', str(self._game.model['shoupai'][i]))) == 13

    def test_he(self, setup):
        for i in range(4):
            assert len(self._game.model['he'][i]._pai) == 0

    def test_diyizimo(self, setup):
        assert self._game._diyizimo

    def test_fengpai(self, setup):
        assert self._game._fengpai

    def test_paipu(self, setup):
        assert last_paipu(self._game).get('qipai')

    def test_msg(self, setup):
        for i in range(4):
            id = self._game.model['player_id'][i]
            assert MSG[id]['qipai']['defen'][i] == 25000
            assert MSG[id]['qipai']['shoupai'][i] is not None

    def test_selectable_shan(self):
        game = init_game()
        shan = majiang.Shan(game._rule)
        shoupai = majiang.Shoupai(list(shan._pai)[-13:])
        game.qipai(shan)
        assert str(game.model['shoupai'][0]) == str(shoupai)

    def test_no_interrupted_pingju(self):
        game = init_game({'rule': majiang.rule({'interrupted_pingju': False})})
        game.qipai()
        assert not game._fengpai


class TestGameZimo:
    @pytest.fixture
    def setup(self):
        self._game = init_game()
        self._game.zimo()

    def test_update_lunban(self, setup):
        assert self._game.model['lunban'] == 0

    def test_zimo_from_shan(self, setup):
        assert self._game.model['shan'].paishu == 69

    def test_add_to_shoupai(self, setup):
        assert self._game.model['shoupai'][0].get_dapai()

    def test_paipu(self, setup):
        assert last_paipu(self._game).get('zimo')

    def test_view(self, setup):
        assert self._game.view._param == {'update': last_paipu(self._game)}

    def test_msg(self, setup):
        for i in range(4):
            id = self._game.model['player_id'][i]
            assert MSG[id]['zimo']['l'] == self._game.model['lunban']
            if i == self._game.model['lunban']:
                assert MSG[id]['zimo']['p']
            else:
                assert not MSG[id]['zimo']['p']


class TestGameDapai:
    @pytest.fixture
    def setup(self):
        self._game = init_game()
        self._game.zimo()
        self._dapai = self._game.model['shoupai'][0].get_dapai()[0]
        self._game.dapai(self._dapai)

    def test_from_shoupai(self, setup):
        assert not self._game.model['shoupai'][0].get_dapai()

    def test_to_shan(self, setup):
        assert self._game.model['he'][0]._pai[0] == self._dapai

    def test_paipu(self, setup):
        assert last_paipu(self._game).get('dapai')

    def test_view(self, setup):
        assert self._game.view._param == {'update': last_paipu(self._game)}

    def test_msg(self, setup):
        for i in range(4):
            id = self._game.model['player_id'][i]
            assert MSG[id]['dapai']['l'] == self._game.model['lunban']
            assert MSG[id]['dapai']['p'] == self._dapai

    def test_without_fengpai(self):
        game = init_game({'shoupai': ['_', '', '', '']})
        game.zimo()
        game.dapai('m1')
        assert not game._fengpai

    def test_other_fengpai(self):
        game = init_game({'shoupai': ['_', '_', '', '']})
        game.zimo()
        game.dapai('z1')
        game.zimo()
        game.dapai('z2')
        assert not game._fengpai

    def test_fengpai_diyizimo_end(self):
        game = init_game({'shoupai': ['_', '_', '', '']})
        game.zimo()
        game.dapai('z1')
        game.zimo()
        game._diyizimo = False
        game.dapai('z1')
        assert not game._fengpai

    def test_double_lizhi(self):
        game = init_game({'shoupai': ['_', '', '', '']})
        game.zimo()
        game.dapai('m1*')
        assert game._lizhi[game.model['lunban']] == 2
        assert game._yifa[game.model['lunban']]

    def test_lizhi(self):
        game = init_game({'shoupai': ['_', '', '', '']})
        game._diyizimo = False
        game.zimo()
        game.dapai('m1_*')
        assert game._lizhi[game.model['lunban']] == 1
        assert game._yifa[game.model['lunban']]

    def test_not_yifa(self):
        game = init_game({'rule': majiang.rule({'yifa': False}),
                          'shoupai': ['_', '', '', '']})
        game._diyizimo = False
        game.zimo()
        game.dapai('m1*')
        assert game._lizhi[game.model['lunban']] == 1
        assert not game._yifa[game.model['lunban']]

    def test_dissapear_yifa(self):
        game = init_game({'shoupai': ['_', '', '', '']})
        game._yifa[0] = True
        game.zimo()
        game.dapai('m1')
        assert not game._yifa[game.model['lunban']]

    def test_neng_rong_he(self):
        game = init_game({'shoupai': ['m123p456s789z11122', '', '', '']})
        game.model['lunban'] = 0
        game.dapai('m1')
        assert not game._neng_rong[game.model['lunban']]

    def test_lift_neng_rong(self):
        game = init_game({'shoupai': ['_', '', '', '']})
        game._neng_rong[0] = False
        game.zimo()
        game.dapai('m1')
        assert game._neng_rong[game.model['lunban']]

    def test_neng_rong_after_lizhi(self):
        game = init_game({'shoupai': ['_____________*', '', '', '']})
        game._neng_rong[0] = False
        game.zimo()
        dapai = game.model['shoupai'][0]._zimo
        game.dapai(dapai)
        assert not game._neng_rong[game.model['lunban']]

    def test_kaigang(self):
        game = init_game({'shoupai': ['__________,s333=', '', '', '']})
        game.zimo()
        game.gang('s333=3')
        game.gangzimo()
        game.dapai('p1')
        assert len(game.model['shan'].baopai) == 2


class TestGameFulou:
    @pytest.fixture
    def setup(self):
        self._game = init_game({'shoupai': ['_', '_', '', '']})
        self._game.zimo()
        self._game.dapai('m2_')
        self._game.fulou('m12-3')

    def test_from_he(self, setup):
        assert self._game.model['he'][0]._pai[0] == 'm2_-'

    def test_lunban(self, setup):
        assert self._game.model['lunban'] == 1

    def test_shoupai_fulou(self, setup):
        assert self._game.model['shoupai'][1]._fulou[0] == 'm12-3'

    def test_paipu(self, setup):
        assert last_paipu(self._game).get('fulou')

    def test_view(self, setup):
        assert self._game.view._param == {'update': last_paipu(self._game)}

    def test_msg(self, setup):
        for i in range(4):
            id = self._game.model['player_id'][i]
            assert MSG[id]['fulou']['l'] == self._game.model['lunban']
            assert MSG[id]['fulou']['m'] == 'm12-3'

    def test_daimingang(self):
        game = init_game({'shoupai': ['_', '', '', '_']})
        game.zimo()
        game.dapai('m2')
        game.fulou('m2222+')
        assert game.model['shoupai'][3]._fulou[0] == 'm2222+'

    def test_diyizimo(self):
        game = init_game({'shoupai': ['_', '_', '', '_']})
        game.zimo()
        game.dapai('m3')
        game.fulou('m123-')
        assert not game._diyizimo

    def test_yifa(self):
        game = init_game({'shoupai': ['_', '_', '', '_']})
        game.zimo()
        game.dapai('m3*')
        game.fulou('m123-')
        assert not [x for x in game._yifa if x]


class TestGameGang:
    @pytest.fixture
    def setup(self):
        self._game = init_game({'shoupai': ['__________,s555+', '', '', '']})
        self._game.zimo()
        self._game.gang('s555+0')

    def test_fulou(self, setup):
        assert self._game.model['shoupai'][0]._fulou[0] == 's555+0'

    def test_paipu(self, setup):
        assert last_paipu(self._game).get('gang')

    def test_view(self, setup):
        assert self._game.view._param == {'update': last_paipu(self._game)}

    def test_msg(self, setup):
        for i in range(4):
            id = self._game.model['player_id'][i]
            assert MSG[id]['gang']['l'] == self._game.model['lunban']
            assert MSG[id]['gang']['m'] == 's555+0'

    def test_angang(self):
        game = init_game({'shoupai': ['_', '', '', '']})
        game.zimo()
        game.gang('s5550')
        assert game.model['shoupai'][0]._fulou[0] == 's5550'

    def test_kaigang_after(self):
        game = init_game({'shoupai': ['_______,s222+,z111=', '', '', '']})
        game.zimo()
        game.gang('z111=1')
        game.gangzimo()
        game.gang('s222+2')
        assert len(game.model['shan'].baopai) == 2


class TestGameGangzimo:
    @pytest.fixture
    def setup(self):
        self._game = init_game({'shoupai': ['_', '', '', '']})
        self._game.zimo()
        self._game.gang('m5550')
        self._game.gangzimo()

    def test_shan(self, setup):
        assert self._game.model['shan'].paishu == 68

    def test_shoupai(self, setup):
        assert self._game.model['shoupai'][0].get_dapai()

    def test_paipu(self, setup):
        assert last_paipu(self._game, -1).get('gangzimo')

    def test_view(self, setup):
        assert self._game.view._param == {'update': last_paipu(self._game, -1)}

    def test_msg(self, setup):
        for i in range(4):
            id = self._game.model['player_id'][i]
            assert MSG[id]['gangzimo']['l'] == self._game.model['lunban']
            if i == self._game.model['lunban']:
                assert MSG[id]['gangzimo']['p']
            else:
                assert not MSG[id]['gangzimo']['p']

    def test_diyizimo(self):
        game = init_game({'shoupai': ['_', '', '', '_']})
        game.zimo()
        game.gang('m3333')
        game.gangzimo()
        assert not game._diyizimo

    def test_yifa(self):
        game = init_game({'shoupai': ['_', '_', '', '_']})
        game.zimo()
        game.dapai('m3*')
        game.zimo()
        game.gang('m4444')
        game.gangzimo()
        assert not [x for x in game._yifa if x]

    def test_kagang_after(self):
        game = init_game({'shoupai': ['__________,s333=', '', '', '']})
        game.zimo()
        game.gang('s333=3')
        game.gangzimo()
        assert len(game.model['shan'].baopai) == 1

    def test_kagang_soon(self):
        game = init_game({'rule': majiang.rule({'gang_baopai_delay': False}),
                          'shoupai': ['__________,s333=', '', '', '']})
        game.zimo()
        game.gang('s333=3')
        game.gangzimo()
        assert len(game.model['shan'].baopai) == 2

    def test_daimingang_after(self):
        game = init_game({'shoupai': ['_', '', '_', '']})
        game.zimo()
        game.dapai('s3')
        game.fulou('s3333=')
        game.gangzimo()
        assert len(game.model['shan'].baopai) == 1

    def test_daimingang_soon(self):
        game = init_game({'rule': majiang.rule({'gang_baopai_delay': False}),
                          'shoupai': ['_', '', '_', '']})
        game.zimo()
        game.dapai('s3')
        game.fulou('s3333=')
        game.gangzimo()
        assert len(game.model['shan'].baopai) == 2


class TestGameKaigang:
    @pytest.fixture
    def setup(self):
        self._game = init_game({'shoupai': ['__________,s555+', '', '', '']})
        self._game.zimo()
        self._game.gang('s555+0')
        self._game.gangzimo()
        self._game.kaigang()

    def test_gang_baopai(self, setup):
        assert len(self._game.model['shan'].baopai) == 2
        assert not self._game._gang

    def test_paipu(self, setup):
        assert last_paipu(self._game).get('kaigang')

    def test_view(self, setup):
        assert self._game.view._param == {'update': last_paipu(self._game)}

    def test_msg(self, setup):
        for i in range(4):
            id = self._game.model['player_id'][i]
            assert MSG[id]['kaigang']['baopai'] == self._game.model['shan'].baopai.pop()

    def test_no_gang_baopai(self):
        rule = majiang.rule({'gang_baopai': False})
        game = init_game({'rule': rule, 'shoupai': ['_', '', '', '']})
        game.zimo()
        game.gang('m1111')
        game.gangzimo()
        assert len(game.model['shan'].baopai) == 1
        assert not game._gang


class TestGameHule:
    @pytest.fixture
    def setup(self):
        self._game = init_game({'shoupai': ['_', '', 'm123p456s789z1122', '']})
        self._game.zimo()
        self._game.dapai('z1')
        self._game._hule = [2]
        self._game.hule()

    def test_paipu(self, setup):
        assert last_paipu(self._game).get('hule')

    def test_view(self, setup):
        assert self._game.view._param == {'update': last_paipu(self._game)}

    def test_msg(self, setup):
        for i in range(4):
            id = self._game.model['player_id'][i]
            assert MSG[id]['hule']['l'] == 2

    def test_delay_notify(self):
        game = init_game({'shoupai': ['m123p456s789z1122', '', '', ''],
                          'zimo': ['z2']})
        game.wait = 20
        game.zimo()
        init_msg()
        game._sync = False
        game.stop(done)
        game.hule()
        assert [x for x in MSG if x]
        assert called == 1

    def test_lizhi_yifa(self):
        game = init_game({'shoupai': ['m123p456s789z1122', '_', '', '']})
        game._diyizimo = False
        game.zimo()
        game.dapai(game.model['shoupai'][0]._zimo + '_*')
        game.zimo()
        game.dapai('z1')
        game._hule = [0]
        game.hule()
        assert [h for h in last_paipu(game)['hule']['hupai'] if h['name'] == '立直']
        assert [h for h in last_paipu(game)['hule']['hupai'] if h['name'] == '一発']

    def test_double_lizhi(self):
        game = init_game({'shoupai': ['m123p456s789z1122', '_', '', '']})
        game.zimo()
        game.dapai(game.model['shoupai'][0]._zimo + '_*')
        game.zimo()
        game.dapai('z1')
        game._hule = [0]
        game.hule()
        assert [h for h in last_paipu(game)['hule']['hupai'] if h['name'] == 'ダブル立直']

    def test_qianggang(self):
        game = init_game({'shoupai': ['_________m1,m111=', '_', 'm23p456s789z11222', '']})
        game.zimo()
        game.gang('m111=1')
        game._hule = [2]
        game.hule()
        assert [h for h in last_paipu(game)['hule']['hupai'] if h['name'] == '槍槓']

    def test_lingshang(self):
        game = init_game({'shoupai': ['m123p456s78z11,m111=', '', '', ''],
                          'zimo': ['m4'], 'gangzimo': ['s9']})
        game.zimo()
        game.gang('m111=1')
        game.gangzimo()
        game.hule()
        assert [h for h in last_paipu(game)['hule']['hupai'] if h['name'] == '嶺上開花']

    def test_lingshang_last(self):
        game = init_game({'shoupai': ['m123p456s78z11,m111=', '', '', ''],
                          'zimo': ['m4'], 'gangzimo': ['s9']})
        game._diyizimo = False
        game.zimo()
        game.gang('m111=1')
        while game.model['shan'].paishu > 1:
            game.model['shan'].zimo()
        game.gangzimo()
        game.hule()
        assert not [h for h in last_paipu(game)['hule']['hupai'] if h['name'] == '海底摸月']

    def test_haidi_zimo(self):
        game = init_game({'shoupai': ['m123p456s789z1122', '', '', ''],
                          'zimo': ['z2']})
        game._diyizimo = False
        game.zimo()
        while game.model['shan'].paishu > 0:
            game.model['shan'].zimo()
        game.hule()
        assert [h for h in last_paipu(game)['hule']['hupai'] if h['name'] == '海底摸月']

    def test_haidi_rong(self):
        game = init_game({'shoupai': ['_', '', 'm123p456s789z1122', '']})
        game._diyizimo = False
        game.zimo()
        while game.model['shan'].paishu > 0:
            game.model['shan'].zimo()
        game.dapai('z2')
        game._hule = [2]
        game.hule()
        assert [h for h in last_paipu(game)['hule']['hupai'] if h['name'] == '河底撈魚']

    def test_tianhu(self):
        game = init_game({'shoupai': ['m123p456s789z1122', '', '', ''],
                          'zimo': ['z2']})
        game.zimo()
        game.hule()
        assert [h for h in last_paipu(game)['hule']['hupai'] if h['name'] == '天和']

    def test_chihu(self):
        game = init_game({'shoupai': ['', 'm123p456s789z1122', '', ''],
                          'zimo': ['m1', 'z2']})
        game.zimo()
        game.dapai('m1_')
        game.zimo()
        game.hule()
        assert [h for h in last_paipu(game)['hule']['hupai'] if h['name'] == '地和']

    def test_qianggang_double_rong(self):
        game = init_game({'shoupai': ['__________,m111=', 'm23p456s789z11122', 'm23p789s456z33344', '']})
        game.zimo()
        game.gang('m111=1')
        game._hule = [1, 2]
        game.hule()
        game.hule()
        assert [h for h in last_paipu(game)['hule']['hupai'] if h['name'] == '槍槓']

    def test_lianzhuang_child(self):
        game = init_game({'shoupai': ['_', 'm123p456s789z1122', '', '']})
        game.zimo()
        game.dapai('z1')
        game._hule = [1]
        game.hule()
        assert not game._lianzhuang

    def test_lianzhuang_parent(self):
        game = init_game({'shoupai': ['m123p456s789z1122', '', '', ''],
                          'zimo': ['z1']})
        game.zimo()
        game.hule()
        assert game._lianzhuang

    def test_lianzhuang_double_rong(self):
        game = init_game({'shoupai': ['m23p456s789z11122', '_', 'm23p789s546z33344', ''],
                          'zimo': ['m2', 'm1']})
        game.zimo()
        game.dapai('m2')
        game.zimo()
        game.dapai('m1')
        game._hule = [2, 0]
        game.hule()
        game.hule()
        assert game._lianzhuang

    def test_no_lianzhuang(self):
        game = init_game({'rule': majiang.rule({'continuous_zhuang': 0}),
                          'shoupai': ['m123p456s789z1122', '', '', ''],
                          'zimo': ['z1']})
        game.zimo()
        game.hule()
        assert not game._lianzhuang

    def test_lianzhuang_one_game(self):
        game = init_game({'rule': majiang.rule({'n_zhuang': 0}),
                          'shoupai': ['m123p456s789z1122', '', '', ''],
                          'zimo': ['z1']})
        game.zimo()
        game.hule()
        assert not game._lianzhuang


class TestGamePingju:
    @pytest.fixture
    def setup(self):
        self._game = init_game()
        self._game.pingju('九種九牌')

    def test_interrupted_pingju(self, setup):
        assert self._game._no_game
        assert self._game._lianzhuang

    def test_paipu(self, setup):
        assert last_paipu(self._game).get('pingju')

    def test_view(self, setup):
        assert self._game.view._param == {'update': last_paipu(self._game)}

    def test_msg(self, setup):
        for i in range(4):
            id = self._game.model['player_id'][i]
            assert MSG[id]['pingju']['name'] == '九種九牌'

    def test_delay_notify(self):
        game = init_game()
        game.wait = 20
        game.zimo()
        init_msg()
        game._sync = False
        game.stop(done)
        game.pingju('九種九牌')
        assert [x for x in MSG if x]
        assert called == 1

    def test_all_tingpai(self):
        game = init_game({'rule': majiang.rule({'pingju_manguan': False}),
                          'shoupai': ['m22p12366s406789',
                                      'm55p40s123,z111-,p678-',
                                      'm67p678s22,s56-7,p444-',
                                      'm12345p33s333,m406-']})
        game.pingju()
        assert last_paipu(game)['pingju']['name'] == '荒牌平局'
        assert len([s for s in last_paipu(game)['pingju']['shoupai'] if s]) == 4
        assert game._fenpei == [0, 0, 0, 0]

    def test_all_no_tingpai(self):
        game = init_game({'rule': majiang.rule({'pingju_manguan': False}),
                          'shoupai': ['m40789p4667s8z577',
                                      'm99p12306z277,m345-',
                                      'm3p1234689z55,s7-89',
                                      'm2233467p234555']})
        game.pingju()
        assert last_paipu(game)['pingju']['name'] == '荒牌平局'
        assert len([s for s in last_paipu(game)['pingju']['shoupai'] if s]) == 0
        assert game._fenpei == [0, 0, 0, 0]

    def test_two_tingpai(self):
        game = init_game({'rule': majiang.rule({'pingju_manguan': False}),
                          'shoupai': ['m22p12366s406789',
                                      'm99p12306z277,m345-',
                                      'm3p1234689z55,s7-89',
                                      'm12345p33s333,m406-']})
        game.pingju()
        assert last_paipu(game)['pingju']['name'] == '荒牌平局'
        assert len([s for s in last_paipu(game)['pingju']['shoupai'] if s]) == 2
        assert game._fenpei == [1500, -1500, -1500, 1500]

    def test_no_format_tingpai(self):
        game = init_game({'rule': majiang.rule({'pingju_manguan': False}),
                          'shoupai': ['m123p456s789z1111',
                                      'm99p12306z277,m345-',
                                      'm3p1234689z55,s7-89',
                                      'm12345p33s333,m406-']})
        game.pingju()
        assert last_paipu(game)['pingju']['name'] == '荒牌平局'
        assert len([s for s in last_paipu(game)['pingju']['shoupai'] if s]) == 1
        assert game._fenpei == [-1000, -1000, -1000, 3000]

    def test_declare_no_tingpai(self):
        game = init_game({'rule': majiang.rule({'pingju_manguan': False,
                                                'declare_no_tingpai': True}),
                          'shoupai': ['m22p12366s406789',
                                      'm55p40s123,z111-,p678-',
                                      'm67p678s22,s56-7,p444-',
                                      'm12345p33s333,m406-']})
        game.pingju('', ['', '_', '_', '_'])
        assert last_paipu(game)['pingju']['name'] == '荒牌平局'
        assert len([s for s in last_paipu(game)['pingju']['shoupai'] if s]) == 3
        assert game._fenpei == [-3000, 1000, 1000, 1000]

    def test_declare_no_tingpai_open_lizhied(self):
        game = init_game({'rule': majiang.rule({'pingju_manguan': False,
                                                'declare_no_tingpai': True}),
                          'shoupai': ['m22p12366s406789*', '', '', '']})
        game.pingju()
        assert last_paipu(game)['pingju']['name'] == '荒牌平局'
        assert last_paipu(game)['pingju']['shoupai'][0]

    def test_no_penalty_no_tingpai(self):
        game = init_game({'rule': majiang.rule({'pingju_manguan': False,
                                                'penalty_no_tingpai': False}),
                          'shoupai': ['m22p12366s406789',
                                      'm99p12306z277,m345-',
                                      'm3p1234689z55,s7-89',
                                      'm12345p33s333,m406-']})
        game.pingju()
        assert last_paipu(game)['pingju']['name'] == '荒牌平局'
        assert len([s for s in last_paipu(game)['pingju']['shoupai'] if s]) == 1
        assert game._fenpei == [0, 0, 0, 0]

    def test_tingpai_lianzhuang(self):
        game = init_game({'rule': majiang.rule({'pingju_manguan': False}),
                          'shoupai': ['m22p12366s406789',
                                      'm99p12306z277,m345-',
                                      'm3p1234689z55,s7-89',
                                      'm2233467p234555']})
        game.pingju()
        assert game._lianzhuang

    def test_no_tingpai_no_lianzhuang(self):
        game = init_game({'rule': majiang.rule({'pingju_manguan': False}),
                          'shoupai': ['m40789p4667s8z577',
                                      'm99p12306z277,m345-',
                                      'm3p1234689z55,s7-89',
                                      'm2233467p234555']})
        game.pingju()
        assert not game._lianzhuang

    def test_no_tingpai_lianzhuang(self):
        game = init_game({'rule': majiang.rule({'pingju_manguan': False,
                                                'continuous_zhuang': 3}),
                          'shoupai': ['m40789p4667s8z577',
                                      'm99p12306z277,m345-',
                                      'm3p1234689z55,s7-89',
                                      'm2233467p234555']})
        game.pingju()
        assert game._lianzhuang

    def test_one_game(self):
        game = init_game({'rule': majiang.rule({'pingju_manguan': False,
                                                'n_zhuang': 0}),
                          'shoupai': ['m40789p4667s8z577',
                                      'm99p12306z277,m345-',
                                      'm3p1234689z55,s7-89',
                                      'm2233467p234555']})
        game.pingju()
        assert game._lianzhuang

    def test_pingju_manguan(self):
        game = init_game({'shoupai': ['_', '_', '_', '_']})
        game.zimo()
        game.dapai('z1')
        game.zimo()
        game.dapai('m2')
        game.zimo()
        game.dapai('p2')
        game.zimo()
        game.dapai('s2')
        game.pingju()
        assert last_paipu(game)['pingju']['name'] == '流し満貫'
        assert game._fenpei == [12000, -4000, -4000, -4000]

    def test_pingju_manguan_fuloued(self):
        game = init_game({'shoupai': ['_', '_', '_', '_']})
        game.zimo()
        game.dapai('z1')
        game.fulou('z111-')
        game.dapai('m2')
        game.zimo()
        game.dapai('p2')
        game.zimo()
        game.dapai('s2')
        game.pingju()
        assert last_paipu(game)['pingju']['name'] == '荒牌平局'

    def test_two_pingju_manguan(self):
        game = init_game({'shoupai': ['_', '_', '_', '_']})
        game.zimo()
        game.dapai('z1')
        game.zimo()
        game.dapai('m1')
        game.zimo()
        game.dapai('p2')
        game.zimo()
        game.dapai('s2')
        game.pingju()
        assert last_paipu(game)['pingju']['name'] == '流し満貫'
        assert game._fenpei == [8000, 4000, -6000, -6000]

    def test_no_penalty_no_tingpai_open_shoupai(self):
        game = init_game({'rule': majiang.rule({'pingju_manguan': False,
                                                'penalty_no_tingpai': False}),
                          'shoupai': ['m567999s4466777',
                                      'm05p123s56z333*,s8888',
                                      'm11p789s06,z555-,p406-',
                                      '']})
        game.pingju()
        assert last_paipu(game)['pingju']['shoupai'] == ['m567999s4466777', 'm05p123s56z333*,s8888', '', '']

    def test_no_penalty_no_tingpai_and_hule_lianzhuang_open_shoupai(self):
        game = init_game({'rule': majiang.rule({'pingju_manguan': False,
                                                'penalty_no_tingpai': False,
                                                'continuous_zhuang': 1}),
                          'shoupai': ['m567999s4466777',
                                      'm05p123s56z333*,s8888',
                                      'm11p789s06,z555-,p406-',
                                      '']})
        game.pingju()
        assert last_paipu(game)['pingju']['shoupai'] == ['', 'm05p123s56z333*,s8888', '', '']


class TestGameLast:
    def test_lianzhuang(self):
        game = init_game()
        game._lianzhuang = True
        game.last()
        assert game.model['zhuangfeng'] == 0
        assert game.model['jushu'] == 0

    def test_not_lianzhuang(self):
        game = init_game()
        game.model['zhunagfeng'] = 0
        game.model['jushu'] = 3
        game.last()
        assert game.model['zhuangfeng'] == 1
        assert game.model['jushu'] == 0

    def test_ton_4(self):
        game = init_game({'rule': majiang.rule({'n_zhuang': 1}),
                          'defen': [10000, 20000, 30000, 40000]})
        game.model['zhuangfeng'] = 0
        game.model['jushu'] = 3
        game.last()
        assert game._status == 'jieju'

    def test_tonnan_8(self):
        game = init_game({'rule': majiang.rule({'n_zhuang': 2}),
                          'defen': [10000, 20000, 30000, 40000]})
        game.model['zhuangfeng'] = 1
        game.model['jushu'] = 3
        game.last()
        assert game._status == 'jieju'

    def test_full_game_12(self):
        game = init_game({'rule': majiang.rule({'n_zhuang': 3}),
                          'defen': [10000, 20000, 30000, 40000]})
        game.model['zhuangfeng'] = 3
        game.model['jushu'] = 3
        game.last()
        assert game._status == 'jieju'

    def test_minus_end(self):
        game = init_game({'defen': [50100, 30000, 20000, -100]})
        game._lianzhuang = True
        game.last()
        assert game._status == 'jieju'

    def test_no_minus_end(self):
        game = init_game({'rule': majiang.rule({'minus_interruption': False}),
                          'defen': [50100, 30000, 20000, -100]})
        game.last()
        assert game._status == 'qipai'

    def test_stop_last_game_ton(self):
        game = init_game({'rule': majiang.rule({'n_zhuang': 1}),
                          'defen': [40000, 30000, 20000, 10000]})
        game.model['zhuangfeng'] = 0
        game.model['jushu'] = 3
        game._lianzhuang = True
        game.last()
        assert game._status == 'jieju'

    def test_stop_last_game_tonnan(self):
        game = init_game({'defen': [40000, 30000, 20000, 10000]})
        game.model['zhuangfeng'] = 1
        game.model['jushu'] = 3
        game._lianzhuang = True
        game.last()
        assert game._status == 'jieju'

    def test_stop_last_game_pingju(self):
        game = init_game({'defen': [40000, 30000, 20000, 10000]})
        game.model['zhuangfeng'] = 1
        game.model['jushu'] = 3
        game._lianzhuang = True
        game._no_game = True
        game.last()
        assert game._status == 'qipai'

    def test_no_stop_last_game(self):
        game = init_game({'rule': majiang.rule({'stop_last_game': False}),
                          'defen': [40000, 30000, 20000, 10000]})
        game.model['zhuangfeng'] = 1
        game.model['jushu'] = 3
        game._lianzhuang = True
        game.last()
        assert game._status == 'qipai'

    def test_no_extra_full_game(self):
        game = init_game({'rule': majiang.rule({'extra_game_method': 0})})
        game.model['zhuangfeng'] = 1
        game.model['jushu'] = 3
        game.last()
        assert game._status == 'jieju'

    def test_extra_game(self):
        game = init_game()
        game.model['zhuangfeng'] = 1
        game.model['jushu'] = 3
        game.last()
        assert game._status == 'qipai'

    def test_extra_sudden_death(self):
        game = init_game({'defen': [10000, 20000, 30000, 40000]})
        game.model['zhuangfeng'] = 2
        game.model['jushu'] = 0
        game.last()
        assert game._max_jushu == 7
        assert game._status == 'jieju'

    def test_extra_sudden_death_prior_lianzhuang(self):
        game = init_game({'rule': majiang.rule({'extra_game_method': 2})})
        game.model['zhuangfeng'] = 1
        game.model['jushu'] = 3
        game.last()
        assert game._max_jushu == 8
        assert game._status == 'qipai'

    def test_extra_4game_only(self):
        game = init_game({'rule': majiang.rule({'extra_game_method': 2})})
        game.model['zhuangfeng'] = 1
        game.model['jushu'] = 3
        game.last()
        assert game._max_jushu == 8
        assert game._status == 'qipai'

    def test_extra_max_4game(self):
        game = init_game()
        game.model['zhuangfeng'] = 2
        game.model['jushu'] = 3
        game.last()
        assert game._status == 'jieju'

    def test_no_extra_one_game(self):
        game = init_game({'rule': majiang.rule({'n_zhuang': 0})})
        game.model['zhuangfeng'] = 0
        game.model['jushu'] = 0
        game.last()
        assert game._status == 'jieju'


class TestGameJieju:
    @pytest.fixture
    def setup(self):
        self._game = init_game({'qijia': 1, 'defen': [20400, 28500, 20500, 30600]})
        self._game.jieju()

    def test_paipu(self, setup):
        assert self._game._paipu['defen'] == [30600, 20400, 28500, 20500]
        assert self._game._paipu['rank'] == [1, 4, 2, 3]
        assert self._game._paipu['point'] == ['40.6', '-29.6', '8.5', '-19.5']

    def test_view(self, setup):
        assert self._game.view._param.get('summary')

    def test_msg(self, setup):
        for i in range(4):
            id = self._game.model['player_id'][i]
            assert MSG[id]['jieju']

    def test_delay_notify(self):
        game = init_game()
        game.wait = 20
        init_msg()
        game._sync = False
        game.stop(done)
        game.jieju()
        assert len([x for x in MSG if x]) == 4
        assert called == 1

    def test_same_defen(self):
        game = init_game({'qijia': 2})
        game.jieju()
        assert game._paipu['rank'] == [3, 4, 1, 2]
        assert game._paipu['point'] == ['-15.0', '-25.0', '35.0', '5.0']

    def test_lizhibang(self):
        game = init_game({'qijia': 3, 'defen': [9000, 19000, 29000, 40000],
                          'lizhibang': 3})
        game.jieju()
        assert game._paipu['defen'] == [19000, 29000, 43000, 9000]

    def test_round_under_1000(self):
        game = init_game({'qijia': 0, 'defen': [20400, 28500, 20500, 30600],
                          'rule': majiang.rule({'rank_bounus': ['20', '10', '-10', '-20']})})
        game.jieju()
        assert game._paipu['point'] == ['-30', '9', '-20', '41']

    def test_round_under_1000_minus(self):
        game = init_game({'qijia': 0, 'defen': [-1500, 83800, 6000, 11700],
                          'rule': majiang.rule({'rank_bounus': ['20', '10', '-10', '-20']})})
        game.jieju()
        assert game._paipu['point'] == ['-52', '94', '-34', '-8']

    def test_rank_bounus(self):
        game = init_game({'rule': majiang.rule({'rank_bounus': ['30', '10', '-10', '-30']}),
                          'qijia': 2})
        game.jieju()
        assert game._paipu['rank'] == [3, 4, 1, 2]
        assert game._paipu['point'] == ['-15', '-35', '45', '5']

    def test_handler(self):
        game = init_game()
        game.handler = done
        game.jieju()
        assert called == 1


class TestGameReplyKaiju:
    def test_to_qipai(self):
        players = [Player(id) for id in range(4)]
        rule = majiang.rule()
        game = majiang.Game(players, None, rule)
        game.view = View()
        game._sync = True
        game.kaiju()
        game.next()
        assert last_paipu(game).get('qipai')


class TestGameReplyQipai:
    def test_to_zimo(self):
        game = init_game()
        game.qipai()
        game.next()
        assert last_paipu(game).get('zimo')


class TestGameReplyZimo:
    def test_dapai(self):
        game = init_game({'zimo': ['m1']})
        set_reply(game, [{'dapai': 'm1_'}, {}, {}, {}])
        game.zimo()
        game.next()
        assert last_paipu(game)['dapai']['p'] == 'm1_'

    def test_lizhi(self):
        game = init_game({'shoupai': ['m123p456s789z1122', '', '', ''],
                          'zimo': ['m1']})
        set_reply(game, [{'dapai': 'm1_*'}, {}, {}, {}])
        game.zimo()
        game.next()
        assert last_paipu(game)['dapai']['p'] == 'm1_*'

    def test_dapai_invalid_reply(self):
        game = init_game({'zimo': ['m1']})
        set_reply(game, [{'dapai': 'm2_'}, {}, {}, {}])
        game.zimo()
        game.next()
        assert last_paipu(game).get('dapai')

    def test_pingju(self):
        game = init_game({'shoupai': ['m123459z1234567', '', '', '']})
        set_reply(game, [{'daopai': '-'}, {}, {}, {}])
        game.zimo()
        game.next()
        assert last_paipu(game)['pingju']['name'] == '九種九牌'

    def test_pingju_invalid_reply(self):
        game = init_game({'shoupai': ['m234567z1234567', '', '', '']})
        set_reply(game, [{'daopai': '-'}, {}, {}, {}])
        game.zimo()
        game.next()
        assert last_paipu(game).get('dapai')

    def test_no_pingju(self):
        game = init_game({'rule': majiang.rule({'interrupted_pingju': False}),
                          'shoupai': ['m123459z1234567', '', '', '']})
        set_reply(game, [{'daopai': '-'}, {}, {}, {}])
        game.zimo()
        game.next()
        assert last_paipu(game).get('dapai')

    def test_hule_zimo(self):
        game = init_game({'shoupai': ['m123p456s789z1122', '', '', ''],
                          'zimo': ['z1']})
        set_reply(game, [{'hule': '-'}, {}, {}, {}])
        game.zimo()
        game.next()
        assert game.view._say == ('zimo', 0)
        assert last_paipu(game).get('hule')

    def test_gang(self):
        game = init_game({'shoupai': ['m123p456z1122,s888+', '', '', ''],
                          'zimo': ['s8']})
        set_reply(game, [{'gang': 's888+8'}, {}, {}, {}])
        game.zimo()
        game.next()
        assert last_paipu(game)['gang']['m'] == 's888+8'

    def test_gang_invalid_reply(self):
        game = init_game({'shoupai': ['m123p456z1122,s888+', '', '', ''],
                          'zimo': ['s7']})
        set_reply(game, [{'gang': 's888+8'}, {}, {}, {}])
        game.zimo()
        game.next()
        assert last_paipu(game).get('dapai')

    def test_ng_5th_gang(self):
        game = init_game({'shoupai': ['m123p456z1122,s888+', '', '', ''],
                          'zimo': ['s8']})
        game._n_gang = [0, 0, 0, 4]
        set_reply(game, [{'gang': 's888+8'}, {}, {}, {}])
        game.zimo()
        game.next()
        assert last_paipu(game).get('dapai')

    def test_no_reply(self):
        game = init_game({'zimo': ['m1']})
        game.zimo()
        game.next()
        assert last_paipu(game)['dapai']['p'] == 'm1_'

    def test_gangzimo(self):
        game = init_game({'shoupai': ['_', '', '', '']})
        game.zimo()
        game.gang('m1111')
        game.gangzimo()
        game.next()
        assert last_paipu(game).get('dapai')


class TestGameReplyDapai:
    def test_no_reply(self):
        game = init_game({'shoupai': ['_', '', '', '']})
        game.zimo()
        game.dapai('m1')
        game.next()
        assert last_paipu(game).get('zimo')

    def test_hule_rong(self):
        game = init_game({'shoupai': ['_', 'm123p456s789z1122', '', '']})
        game.zimo()
        set_reply(game, [{}, {'hule': '-'}, {}, {}])
        game.dapai('z1')
        game.next()
        assert game.view._say == ('rong', 1)
        assert last_paipu(game)['hule']['l'] == 1

    def test_miss_hule(self):
        game = init_game({'shoupai': ['_', 'm123p456s789z1122', '', '']})
        game.zimo()
        game.dapai('z1')
        game.next()
        assert not game._neng_rong[1]

    def test_double_rong(self):
        game = init_game({'shoupai': ['_', 'm23446p45688s345', 'm34s33,s444-,s666+,p406-', '']})
        game.zimo()
        set_reply(game, [{}, {'hule': '-'}, {'hule': '-'}, {}])
        game.dapai('m5*')
        game.next()
        assert game.view._say == ('rong', 2)
        assert last_paipu(game)['hule']['l'] == 1
        assert game._hule == [2]

    def test_no_double_rong(self):
        game = init_game({'rule': majiang.rule({'n_max_simultaneous_hule': 1}),
                          'shoupai': ['_', 'm23446p45688s345', 'm34s33,s444-,s666+,p406-', '']})
        game.zimo()
        set_reply(game, [{}, {'hule': '-'}, {'hule': '-'}, {}])
        game.dapai('m5*')
        game.next()
        assert game.view._say == ('rong', 1)
        assert last_paipu(game)['hule']['l'] == 1
        assert game._hule == []

    def test_triple_rong_pingju(self):
        game = init_game({'shoupai': ['_', 'm23446p45688s345',
                                      'm34s33,s444-,s666+,p406-',
                                      'm23467s88,s222+,z666=']})
        game.zimo()
        set_reply(game, [{}, {'hule': '-'}, {'hule': '-'}, {'hule': '-'}])
        game.dapai('m5*')
        game.next()
        assert game.view._say == ('rong', 3)
        assert last_paipu(game)['pingju']['name'] == '三家和'
        assert last_paipu(game)['pingju']['shoupai'] == ['', 'm23446p45688s345',
                                                         'm34s33,s444-,s666+,p406-',
                                                         'm23467s88,s222+,z666=']

    def test_ok_triple_rong(self):
        game = init_game({'rule': majiang.rule({'n_max_simultaneous_hule': 3}),
                          'shoupai': ['_', 'm23446p45688s345',
                                      'm34s33,s444-,s666+,p406-',
                                      'm23467s88,s222+,z666=']})
        game.zimo()
        set_reply(game, [{}, {'hule': '-'}, {'hule': '-'}, {'hule': '-'}])
        game.dapai('m5*')
        game.next()
        assert game.view._say == ('rong', 3)
        assert last_paipu(game)['hule']['l'] == 1
        assert game._hule == [2, 3]

    def test_enable_lizhi(self):
        game = init_game({'shoupai': ['m55688p234567s06', '', '', ''],
                          'qijia': 0, 'zimo': ['s7']})
        game.zimo()
        game.dapai('m5*')
        game.next()
        assert game.model['defen'][0] == 24000
        assert game.model['lizhibang'] == 1
        assert last_paipu(game).get('zimo')

    def test_disable_lizhi(self):
        game = init_game({'shoupai': ['m55688p234567s06', 'm23446p45688s345', '', ''],
                          'qijia': 0, 'zimo': ['s7']})
        game.zimo()
        set_reply(game, [{}, {'hule': '-'}, {}, {}])
        game.dapai('m5*')
        game.next()
        assert game.model['defen'][0] == 25000
        assert game.model['lizhibang'] == 0
        assert last_paipu(game).get('hule')

    def test_4cha_lizhi_pingju(self):
        game = init_game({'shoupai': ['m11156p5688s2346',
                                      'm2227p11340s2356',
                                      'm2346789p345699',
                                      'm34056p4678s3456'],
                          'qijia': 0, 'zimo': ['p4', 's1', 'm7', 's6']})
        for p in ['s6*', 'm7*', 'p6*', 'p4*']:
            game.zimo()
            game.dapai(p)
        game.next()
        assert last_paipu(game)['pingju']['name'] == '四家立直'
        assert last_paipu(game)['pingju']['shoupai'] == ['m11156p45688s234*',
                                                         'm222p11340s12356*',
                                                         'm23467789p34599*',
                                                         'm34056p678s34566*']

    def test_enable_4cha_lizhi(self):
        game = init_game({'rule': majiang.rule({'interrupted_pingju': False}),
                          'shoupai': ['m11156p5688s2346',
                                      'm2227p11340s2356',
                                      'm2346789p345699',
                                      'm34056p4678s3456'],
                          'qijia': 0, 'zimo': ['p4', 's1', 'm7', 's6']})
        for p in ['s6*', 'm7*', 'p6*', 'p4*']:
            game.zimo()
            game.dapai(p)
        game.next()
        assert last_paipu(game).get('zimo')

    def test_4feng_pingju(self):
        game = init_game({'shoupai': ['_', '_', '_', '_']})
        for _ in range(4):
            game.zimo()
            game.dapai('z1')
        game.next()
        assert last_paipu(game)['pingju']['name'] == '四風連打'
        assert last_paipu(game)['pingju']['shoupai'] == ['', '', '', '']

    def test_disable_4feng_pingju(self):
        game = init_game({'rule': majiang.rule({'interrupted_pingju': False}),
                          'shoupai': ['_', '_', '_', '_']})
        for _ in range(4):
            game.zimo()
            game.dapai('z1')
        game.next()
        assert not game._diyizimo
        assert last_paipu(game).get('zimo')

    def test_4gang_pingju(self):
        game = init_game({'shoupai': ['_', 'm111p22279s57,s333=', 'm123p456s222789z2', ''],
                          'zimo': ['m1'],
                          'gangzimo': ['p2', 's3', 's2', 'z7']})
        game.zimo()
        game.dapai('m1_')
        game.fulou('m1111-')
        game.gangzimo()
        game.gang('p2222')
        game.gangzimo()
        game.gang('s333=3')
        game.gangzimo()
        game.dapai('s2')
        game.fulou('s2222-')
        game.gangzimo()
        game.dapai('s7_')
        game.next()
        assert last_paipu(game)['pingju']['name'] == '四開槓'
        assert last_paipu(game)['pingju']['shoupai'] == ['', '', '', '']

    def test_4gang_only(self):
        game = init_game({'shoupai': ['m1112,p111+,s111=,z111-', '', '', ''],
                          'zimo': ['m1'], 'gangzimo': ['p1', 's1', 'z1', 'z7']})
        game.zimo()
        game.gang('m1111')
        game.gangzimo()
        game.gang('p111+1')
        game.gangzimo()
        game.gang('s111=1')
        game.gangzimo()
        game.gang('z111-1')
        game.gangzimo()
        game.dapai('z7')
        game.next()
        assert last_paipu(game).get('zimo')

    def test_disable_4gang_pingju(self):
        game = init_game({'rule': majiang.rule({'interrupted_pingju': False}),
                          'shoupai': ['_', 'm111p22279s57,s333=', 'm123p456s222789z2', ''],
                          'zimo': ['m1'],
                          'gangzimo': ['p2', 's3', 's2', 'z7']})
        game.zimo()
        game.dapai('m1_')
        game.fulou('m1111-')
        game.gangzimo()
        game.gang('p2222')
        game.gangzimo()
        game.gang('s333=3')
        game.gangzimo()
        game.dapai('s2')
        game.fulou('s2222-')
        game.gangzimo()
        game.dapai('z7_')
        game.next()
        assert last_paipu(game).get('zimo')

    def test_pingju(self):
        game = init_game({'rule': majiang.rule({'pingju_manguan': False, 'declare_no_tingpai': True}),
                          'shoupai': ['_', 'm222p11340s12356', 'm23467789p34599', '_']})
        game.zimo()
        while game.model['shan'].paishu:
            game.model['shan'].zimo()
        set_reply(game, [{}, {'daopai': '-'}, {'daopai': '-'}, {}])
        game.dapai(game.model['shoupai'][0].get_dapai()[0])
        game.next()
        assert last_paipu(game)['pingju']['name'] == '荒牌平局'
        assert last_paipu(game)['pingju']['shoupai'] == ['', 'm222p11340s12356',
                                                         'm23467789p34599', '']

    def test_gang(self):
        game = init_game({'shoupai': ['_', '', '', 'm111234p567s3378']})
        game.zimo()
        set_reply(game, [{}, {}, {}, {'fulou': 'm1111+'}])
        game.dapai('m1')
        game.next()
        assert game.view._say == ('gang', 3)
        assert last_paipu(game)['fulou']['m'] == 'm1111+'

    def test_gang_invalid_reply(self):
        game = init_game({'shoupai': ['_', '', '', 'm111234p567s3378']})
        game.zimo()
        set_reply(game, [{}, {}, {}, {'fulou': 'm1111+'}])
        game.dapai('m2')
        game.next()
        assert last_paipu(game).get('zimo')

    def test_ng_5th_gang(self):
        game = init_game({'shoupai': ['_', '', '', 'm111234p567s3378']})
        game._n_gang = [4, 0, 0, 0]
        game.zimo()
        set_reply(game, [{}, {}, {}, {'fulou': 'm1111+'}])
        game.dapai('m1')
        game.next()
        assert last_paipu(game).get('zimo')

    def test_peng(self):
        game = init_game({'shoupai': ['_', '', 'm112345p567s3378', '']})
        game.zimo()
        set_reply(game, [{}, {}, {'fulou': 'm111='}, {}])
        game.dapai('m1')
        game.next()
        assert game.view._say == ('peng', 2)
        assert last_paipu(game)['fulou']['m'] == 'm111='

    def test_peng_invalid_reply(self):
        game = init_game({'shoupai': ['_', '', 'm112345p567s3378', '']})
        game.zimo()
        set_reply(game, [{}, {}, {'fulou': 'm111='}, {}])
        game.dapai('m2')
        game.next()
        assert last_paipu(game).get('zimo')

    def test_chi(self):
        game = init_game({'shoupai': ['_', 'm112345p567s3378', '', '']})
        game.zimo()
        set_reply(game, [{}, {'fulou': 'm456-'}, {}, {}])
        game.dapai('m6')
        game.next()
        assert game.view._say == ('chi', 1)
        assert last_paipu(game)['fulou']['m'] == 'm456-'

    def test_chi_invalid_reply(self):
        game = init_game({'shoupai': ['_', 'm112345p567s3378', '', '']})
        game.zimo()
        set_reply(game, [{}, {'fulou': 'm456-'}, {}, {}])
        game.dapai('m5')
        game.next()
        assert last_paipu(game).get('zimo')

    def test_peng_and_chi(self):
        game = init_game({'shoupai': ['_', 'm23567p456s889z11', 'm11789p123s11289', '']})
        game.zimo()
        set_reply(game, [{}, {'fulou': 'm1-23'}, {'fulou': 'm111='}, {}])
        game.dapai('m1')
        game.next()
        assert game.view._say == ('peng', 2)
        assert last_paipu(game)['fulou']['m'] == 'm111='


class TestGameReplyFulou:
    def test_daimingang(self):
        game = init_game({'shoupai': ['_', 'm1112356p456s889', '', '']})
        game.zimo()
        game.dapai('m1')
        game.fulou('m1111-')
        game.next()
        assert last_paipu(game)['gangzimo']

    def test_dapai(self):
        game = init_game({'shoupai': ['_', 'm23567p456s889z11', '', '']})
        game.zimo()
        game.dapai('m1')
        set_reply(game, [{}, {'dapai': 's9'}, {}, {}])
        game.fulou('m1-23')
        game.next()
        assert last_paipu(game)['dapai']['p'] == 's9'

    def test_dapai_invalid_reply(self):
        game = init_game({'shoupai': ['_', 'm23456p456s889z11', '', '']})
        game.zimo()
        game.dapai('m1')
        set_reply(game, [{}, {'dapai': 'm4'}, {}, {}])
        game.fulou('m1-23')
        game.next()
        assert last_paipu(game)['dapai']['p'] == 'z1'

    def test_no_reply(self):
        game = init_game({'shoupai': ['_', 'm23567p456s889z11', '', '']})
        game.zimo()
        game.dapai('m1')
        game.fulou('m1-23')
        game.next()
        assert last_paipu(game)['dapai']['p'] == 'z1'


class TestGameReplyGang:
    def test_no_reply(self):
        game = init_game({'shoupai': ['m45p456s11789,m111+', '', '', ''],
                          'zimo': ['m1']})
        game.zimo()
        game.gang('m111+1')
        game.next()
        assert last_paipu(game).get('gangzimo')

    def test_rong_changgang(self):
        game = init_game({'shoupai': ['m45p456s11789,m111+', '', '', 'm23456p123s67899'],
                          'zimo': ['m1']})
        game.zimo()
        set_reply(game, [{}, {}, {}, {'hule': '-'}])
        game.gang('m111+1')
        game.next()
        assert game.view._say == ('rong', 3)
        assert last_paipu(game)['hule']['l'] == 3

    def test_rong_invalid_reply(self):
        game = init_game({'shoupai': ['m45p456s11789,m111+', '', '', 'm33456p123s67899'],
                          'zimo': ['m1']})
        game.zimo()
        set_reply(game, [{}, {}, {}, {'hule': '-'}])
        game.gang('m111+1')
        game.next()
        assert last_paipu(game).get('gangzimo')

    def test_ng_angang(self):
        game = init_game({'shoupai': ['m11145p456s11789', '',
                                      '', 'm23456p123s67899'],
                          'zimo': ['m1']})
        game.zimo()
        set_reply(game, [{}, {}, {}, {'hule': '-'}])
        game.gang('m1111')
        game.next()
        assert last_paipu(game, -1).get('gangzimo')
        assert last_paipu(game).get('kaigang')

    def test_miss_hule(self):
        game = init_game({'shoupai': ['m45p456s11789,m111+', '', '', 'm23456p123s67899'],
                          'zimo': ['m1']})
        game.zimo()
        game.gang('m111+1')
        game.next()
        assert not game._neng_rong[3]

    def test_double_rong(self):
        game = init_game({'shoupai': ['m11p222s88,z666=,m505-',
                                      'm23446p45688s345',
                                      'm34s33,s444-,s666+,p406-', ''],
                          'zimo': ['m5']})
        game.zimo()
        set_reply(game, [{}, {'hule': '-'}, {'hule': '-'}, {}])
        game.gang('m505-5')
        game.next()
        assert game.view._say == ('rong', 2)
        assert last_paipu(game)['hule']['l'] == 1
        assert game._hule == [2]

    def test_no_double_rong(self):
        game = init_game({'rule': majiang.rule({'n_max_simultaneous_hule': 1}),
                          'shoupai': ['m11p222s88,z666=,m505-',
                                      'm23446p45688s345',
                                      'm34s33,s444-,s666+,p406-', ''],
                          'zimo': ['m5']})
        game.zimo()
        set_reply(game, [{}, {'hule': '-'}, {'hule': '-'}, {}])
        game.gang('m505-5')
        game.next()
        assert game.view._say == ('rong', 1)
        assert last_paipu(game)['hule']['l'] == 1
        assert game._hule == []


class TestGameReplyHule:
    def test_parent_zimo(self):
        game = init_game({'shoupai': ['m345567p111s3368', '', '', ''],
                          'qijia': 0, 'changbang': 1, 'lizhibang': 1,
                          'defen': [25000, 25000, 25000, 24000],
                          'baopai': 'p2', 'zimo': ['s7']})
        game._diyizimo = False
        game.zimo()
        game._hule = [0]
        game.hule()
        game.next()
        assert game.model['defen'] == [28400, 24200, 24200, 23200]
        assert game.model['changbang'] == 2
        assert game.model['lizhibang'] == 0
        assert last_paipu(game).get('qipai')

    def test_child_rong(self):
        game = init_game({'shoupai': ['_', 'm345567p111s66z11', '', ''],
                          'qijia': 0, 'changbang': 1, 'lizhibang': 1,
                          'defen': [25000, 25000, 25000, 24000],
                          'baopai': 'p2', 'zimo': ['s7']})
        game.zimo()
        game.dapai('z1')
        game._hule = [1]
        game.hule()
        game.next()
        assert game.model['defen'] == [23100, 27900, 25000, 24000]
        assert game.model['changbang'] == 0
        assert game.model['lizhibang'] == 0
        assert last_paipu(game).get('qipai')

    def test_double_rong(self):
        game = init_game({'shoupai': ['m23p456s789z11122', '_',
                                      'm23p789s546z33344', ''],
                          'qijia': 0, 'changbang': 1, 'lizhibang': 1,
                          'defen': [25000, 25000, 25000, 24000],
                          'baopai': 's9', 'zimo': ['m2', 'm1']})
        game.zimo()
        game.dapai('m2')
        game.zimo()
        game.dapai('m1')
        game._hule = [2, 0]
        game.hule()
        game.next()
        assert game.model['defen'] == [25000, 23400, 27600, 24000]
        assert game.model['changbang'] == 0
        assert game.model['lizhibang'] == 0
        assert last_paipu(game).get('hule')
        game.next()
        assert game.model['defen'] == [28900, 19500, 27600, 24000]
        assert game.model['changbang'] == 2
        assert game.model['lizhibang'] == 0
        assert last_paipu(game).get('qipai')


class TestGameReplyPingju:
    def test_pingju(self):
        game = init_game({'shoupai': ['m123p456s789z1122', '_', '_', '_'],
                          'qijia': 0, 'changbang': 1, 'lizhibang': 1,
                          'defen': [25000, 25000, 25000, 24000],
                          'zimo': ['m2', 'm3', 'm4', 'm5']})
        for p in ['m2', 'm3', 'm4', 'm5']:
            game.zimo()
            game.dapai(p)
        game.pingju()
        game.next()
        assert game.model['defen'] == [28000, 24000, 24000, 23000]
        assert game.model['changbang'] == 2
        assert game.model['lizhibang'] == 1
        assert last_paipu(game).get('qipai')


class TestGameCallback:
    def test_callback(self):

        def callback(paipu):
            assert paipu == game._paipu
            done()

        game = init_game({'rule': majiang.rule({'n_zhuang': 0}),
                          'shoupai': ['m123p456s789z1122', '', '', ''],
                          'zimo': ['z2'], 'callback': callback})
        game.zimo()
        game.hule()
        game.next()
        game.next()
        assert called == 1


class TestGameGetDapai:
    def test_get_dapai(self):
        game = init_game({'shoupai': ['m123,z111+,z222=,z333-', '', '', ''],
                          'zimo': ['m1']})
        game.zimo()
        assert game.get_dapai() == ['m1', 'm2', 'm3', 'm1_']

    def test_allow_fulou_slide(self):
        game = init_game({'rule': majiang.rule({'allow_fulou_slide': 2}),
                          'shoupai': ['_', 'm1234p567,z111=,s789-', '', '']})
        game.zimo()
        game.dapai('m1')
        game.fulou('m1-23')
        assert game.get_dapai() == ['m1', 'm4', 'p5', 'p6', 'p7']


class TestGameGetChiMianzi:
    def test_chi_mianzi(self):
        game = init_game({'shoupai': ['', '_', 'm1234p456s789z111', '']})
        game.zimo()
        game.dapai(game.get_dapai()[0])
        game.zimo()
        game.dapai('m2')
        assert game.get_chi_mianzi(2) == ['m12-3', 'm2-34']

    def test_ng_self(self):
        game = init_game({'shoupai': ['m1234p456s789z111', '', '', '']})
        game.zimo()
        game.dapai(game.get_dapai().pop())
        with pytest.raises(PaiFormatError):
            game.get_chi_mianzi(0)

    def test_ng_from_toimen(self):
        game = init_game({'shoupai': ['_', '', 'm1234p456s789z111', '']})
        game.zimo()
        game.dapai('m2')
        assert game.get_chi_mianzi(2) == []

    def test_ng_haidi(self):
        game = init_game({'shoupai': ['_', 'm1234p456s789z111', '', '']})
        game.zimo()
        while game.model['shan'].paishu:
            game.model['shan'].zimo()
        game.dapai('m2')
        assert game.get_chi_mianzi(1) == []

    def test_allow_slide(self):
        game = init_game({'rule': majiang.rule({'allow_fulou_slide': 2}),
                          'shoupai': ['_', 'm1123,p456-,z111=,s789-', '', '']})
        game.zimo()
        game.dapai('m1')
        assert game.get_chi_mianzi(1) == ['m1-23']


class TestGameGetPengMianzi:
    def test_peng_mianzi(self):
        game = init_game({'shoupai': ['', '_', '', 'm1123p456s789z111']})
        game.zimo()
        game.dapai(game.get_dapai()[0])
        game.zimo()
        game.dapai('m1')
        assert game.get_peng_mianzi(3) == ['m111=']

    def test_ng_self(self):
        game = init_game({'shoupai': ['m1123p456s789z111', '', '', '']})
        game.zimo()
        game.dapai(game.get_dapai().pop())
        with pytest.raises(PaiFormatError):
            game.get_peng_mianzi(0)

    def test_ng_haidi(self):
        game = init_game({'shoupai': ['_', '', 'm1123p456s789z111', '']})
        game.zimo()
        while game.model['shan'].paishu:
            game.model['shan'].zimo()
        game.dapai('m1')
        assert game.get_peng_mianzi(2) == []


class TestGameGetGangMianzi:
    def test_gang_mianzi(self):
        game = init_game({'shoupai': ['', '_', '', 'm1112p456s789z111']})
        game.zimo()
        game.dapai(game.get_dapai()[0])
        game.zimo()
        game.dapai('m1')
        assert game.get_gang_mianzi(3) == ['m1111=']

    def test_ng_self(self):
        game = init_game({'shoupai': ['m1112p456s789z111', '', '', '']})
        game.zimo()
        game.dapai(game.get_dapai().pop())
        with pytest.raises(PaiFormatError):
            game.get_gang_mianzi(0)

    def test_ng_haidi(self):
        game = init_game({'shoupai': ['_', '', 'm1112p456s789z111', '']})
        game.zimo()
        while game.model['shan'].paishu:
            game.model['shan'].zimo()
        game.dapai('m1')
        assert game.get_gang_mianzi(2) == []

    def test_angang_or_kagang(self):
        game = init_game({'shoupai': ['m1111p4569s78,z111=', '', '', ''],
                          'zimo': ['z1']})
        game.zimo()
        assert game.get_gang_mianzi() == ['m1111', 'z111=1']

    def test_ng_after_haidi(self):
        game = init_game({'shoupai': ['m1111p4567s78,z111=', '', '', ''],
                          'zimo': ['z1']})
        game.zimo()
        while game.model['shan'].paishu:
            game.model['shan'].zimo()
        assert game.get_gang_mianzi() == []

    def test_ng_after_lizhi(self):
        game = init_game({'rule': majiang.rule({'allow_angang_after_lizhi': 0}),
                          'shoupai': ['m111p456s789z1122*', '', '', ''],
                          'zimo': ['m1']})
        game.zimo()
        assert game.get_gang_mianzi() == []


class TestGameAllowLizhi:
    def test_assert_true(self):
        game = init_game({'shoupai': ['m123p456s789z1123', '', '', ''],
                          'zimo': ['z2']})
        game.zimo()
        assert game.allow_lizhi('z3*')

    def test_ng_no_zimo(self):
        game = init_game({'shoupai': ['m123p456s789z1123', '', '', ''],
                          'zimo': ['z2']})
        game.zimo()
        while game.model['shan'].paishu >= 4:
            game.model['shan'].zimo()
        assert not game.allow_lizhi('z3*')

    def test_ng_under_1000(self):
        game = init_game({'shoupai': ['m123p456s789z1123', '', '', ''],
                          'zimo': ['z2'], 'defen': [900, 19100, 45000, 35000]})
        game.zimo()
        assert not game.allow_lizhi('z3*')

    def test_ok_no_zimo(self):
        game = init_game({'rule': majiang.rule({'lizhi_no_zimo': True}),
                          'shoupai': ['m123p456s789z1123', '', '', ''],
                          'zimo': ['z2']})
        game.zimo()
        while game.model['shan'].paishu >= 4:
            game.model['shan'].zimo()
        assert game.allow_lizhi('z3*')

    def test_ok_under_1000(self):
        game = init_game({'rule': majiang.rule({'minus_interruption': False}),
                          'shoupai': ['m123p456s789z1123', '', '', ''],
                          'zimo': ['z2'], 'defen': [900, 19100, 45000, 35000]})
        game.zimo()
        assert game.allow_lizhi('z3*')


class TestGameAllowHule:
    def test_zimo_hule(self):
        game = init_game({'shoupai': ['m123p456s789z3344', '', '', ''],
                          'zimo': ['z4']})
        game.zimo()
        assert game.allow_hule()

    def test_lizhi_zimo(self):
        game = init_game({'shoupai': ['m123p456s789z4*,z333=', '', '', ''],
                          'zimo': ['z4']})
        game.zimo()
        assert game.allow_hule()

    def test_lingshang(self):
        game = init_game({'shoupai': ['_', '', 'm123p456s789z3334', ''],
                          'gangzimo': ['z4']})
        game.zimo()
        game.dapai('z3')
        game.fulou('z3333=')
        game.gangzimo()
        assert game.allow_hule()

    def test_haidi_zimo(self):
        game = init_game({'shoupai': ['m123p456s789z4,z333=', '', '', ''],
                          'zimo': ['z4']})
        game.zimo()
        while game.model['shan'].paishu:
            game.model['shan'].zimo()
        assert game.allow_hule()

    def test_zhuangfeng_zimo(self):
        game = init_game({'shoupai': ['_', 'm123p456s789z4,z111=', '', ''],
                          'zimo': ['m1', 'z4']})
        game.zimo()
        game.dapai('m1')
        game.zimo()
        assert game.allow_hule()

    def test_menfeng_zimo(self):
        game = init_game({'shoupai': ['_', 'm123p456s789z4,z222=', '', ''],
                          'zimo': ['m1', 'z4']})
        game.zimo()
        game.dapai('m1')
        game.zimo()
        assert game.allow_hule()

    def test_lizhi_rong(self):
        game = init_game({'shoupai': ['_', 'm123p456s789z3334*', '', '']})
        game.zimo()
        game.dapai('z4')
        assert game.allow_hule(1)

    def test_changkang(self):
        game = init_game({'shoupai': ['m1234p567s789,m111=', '', 'm23p123567s12377', '']})
        game.zimo()
        game.gang('m111=1')
        assert game.allow_hule(2)

    def test_haidi_rong(self):
        game = init_game({'shoupai': ['_', '', '', 'm123p456s789z4,z333=']})
        game.zimo()
        while game.model['shan'].paishu:
            game.model['shan'].zimo()
        game.dapai('z4')
        assert game.allow_hule(3)

    def test_zhuangfeng_rong(self):
        game = init_game({'shoupai': ['_', 'm123p456s789z4,z111=', '', '']})
        game.zimo()
        game.dapai('z4')
        assert game.allow_hule(1)

    def test_menfeng_rong(self):
        game = init_game({'shoupai': ['_', 'm123p456s789z4,z222=', '', '']})
        game.zimo()
        game.dapai('z4')
        assert game.allow_hule(1)

    def test_neng_rong(self):
        game = init_game({'shoupai': ['m123p456s789z3344', '', '', ''],
                          'zimo': ['z4', 'z3']})
        game.zimo()
        game.dapai('z4')
        game.zimo()
        game.dapai('z3')
        assert not game.allow_hule(0)

    def test_no_fulou_danyaojiu(self):
        game = init_game({'rule': majiang.rule({'fulou_duanyaojiu': False}),
                          'shoupai': ['_', 'm234p567s2244,m888-', '', '']})
        game.zimo()
        game.dapai('s4')
        assert not game.allow_hule(1)


class TestGameAllowPingju:
    def test_9shu9pai(self):
        game = init_game({'shoupai': ['m123459z1234567', '', '', '']})
        game.zimo()
        assert game.allow_pingju()

    def test_not_diyizimo(self):
        game = init_game({'shoupai': ['_', '_', 'm123459z1234567', '']})
        game.zimo()
        game.dapai('s2')
        game.fulou('s2-34')
        game.dapai('z3')
        game.zimo()
        assert not game.allow_pingju()

    def test_no_9shu9pai(self):
        game = init_game({'rule': majiang.rule({'interrupted_pingju': False}),
                          'shoupai': ['m123459z1234567', '', '', '']})
        game.zimo()
        assert not game.allow_pingju()


class TestStaticGetDapai:
    @pytest.fixture
    def setup(self):
        self._shoupai = majiang.Shoupai.from_str('m5678p567,z111=,s789-').fulou('m0-67')

    def test_no_fulou_slide(self, setup):
        rule = majiang.rule({'allow_fulou_slide': 0})
        assert majiang.Game.get_dapai_(rule, self._shoupai) == ['p5', 'p6', 'p7']

    def test_allow_exclude_just_pai(self, setup):
        rule = majiang.rule({'allow_fulou_slide': 1})
        assert majiang.Game.get_dapai_(rule, self._shoupai) == ['m8', 'p5', 'p6', 'p7']

    def test_allow_just_pai(self, setup):
        rule = majiang.rule({'allow_fulou_slide': 2})
        assert majiang.Game.get_dapai_(rule, self._shoupai) == ['m5', 'm8', 'p5', 'p6', 'p7']


class TestStaticGetChiMianzi:
    @pytest.fixture
    def setup(self):
        self._shoupai1 = majiang.Shoupai.from_str('m1234,p456-,z111=,s789-')
        self._shoupai2 = majiang.Shoupai.from_str('m1123,p456-,z111=,s789-')

    def test_no_fulou_slide(self, setup):
        rule = majiang.rule({'allow_fulou_slide': 0})
        assert majiang.Game.get_chi_mianzi_(rule, self._shoupai1, 'm1-', 1) == []
        assert majiang.Game.get_chi_mianzi_(rule, self._shoupai2, 'm1-', 1) == []

    def test_allow_exclude_just_pai(self, setup):
        rule = majiang.rule({'allow_fulou_slide': 1})
        assert majiang.Game.get_chi_mianzi_(rule, self._shoupai1, 'm1-', 1) == ['m1-23']
        assert majiang.Game.get_chi_mianzi_(rule, self._shoupai2, 'm1-', 1) == []

    def test_allow_just_pai(self, setup):
        rule = majiang.rule({'allow_fulou_slide': 2})
        assert majiang.Game.get_chi_mianzi_(rule, self._shoupai1, 'm1-', 1) == ['m1-23']
        assert majiang.Game.get_chi_mianzi_(rule, self._shoupai2, 'm1-', 1) == ['m1-23']

    def test_no_haidi(self, setup):
        rule = majiang.rule({'allow_fulou_slide': 2})
        assert majiang.Game.get_chi_mianzi_(rule, self._shoupai1, 'm1-', 0) == []

    def test_ng_with_zimo(self):
        assert majiang.Game.get_chi_mianzi_(majiang.rule(),
                                            majiang.Shoupai.from_str('m123p456s12789z123'),
                                            's3-', 1) is None


class TestStaticGetPengMianzi:
    @pytest.fixture
    def setup(self):
        self._shoupai = majiang.Shoupai.from_str('m1112,p456-,z111=,s789-')

    def test_allow_fulou_slide(self, setup):
        rule = majiang.rule({'allow_fulou_slide': 0})
        assert majiang.Game.get_peng_mianzi_(rule, self._shoupai, 'm1+', 1) == ['m111+']

    def test_no_haidi(self, setup):
        rule = majiang.rule({'allow_fulou_slide': 0})
        assert majiang.Game.get_peng_mianzi_(rule, self._shoupai, 'm1+', 0) == []

    def test_ng_with_zimo(self):
        assert majiang.Game.get_peng_mianzi_(majiang.rule(),
                                             majiang.Shoupai.from_str('m123p456s12789z123'),
                                             's1-', 1) is None


class TestStaticGetGangMianzi:
    @pytest.fixture
    def setup(self):
        self._shoupai1 = majiang.Shoupai.from_str('m1112p456s789z111z1*')
        self._shoupai2 = majiang.Shoupai.from_str('m1112p456s789z111m1*')
        self._shoupai3 = majiang.Shoupai.from_str('m23p567s33345666s3*')
        self._shoupai4 = majiang.Shoupai.from_str('s1113445678999s1*')
        self._shoupai5 = majiang.Shoupai.from_str('m23s77789s7*,s5550,z6666')

    def test_no_after_lizhi(self, setup):
        rule = majiang.rule({'allow_angang_after_lizhi': 0})
        assert majiang.Game.get_gang_mianzi_(rule, self._shoupai1, None, 1) == []
        assert majiang.Game.get_gang_mianzi_(rule, self._shoupai2, None, 1) == []
        assert majiang.Game.get_gang_mianzi_(rule, self._shoupai3, None, 1) == []
        assert majiang.Game.get_gang_mianzi_(rule, self._shoupai4, None, 1) == []
        assert majiang.Game.get_gang_mianzi_(rule, self._shoupai5, None, 1) == []

    def test_no_after_lizhi_change_shoupai(self, setup):
        rule = majiang.rule({'allow_angang_after_lizhi': 1})
        assert majiang.Game.get_gang_mianzi_(rule, self._shoupai1, None, 1) == ['z1111']
        assert majiang.Game.get_gang_mianzi_(rule, self._shoupai2, None, 1) == []
        assert majiang.Game.get_gang_mianzi_(rule, self._shoupai3, None, 1) == []
        assert majiang.Game.get_gang_mianzi_(rule, self._shoupai4, None, 1) == []
        assert majiang.Game.get_gang_mianzi_(rule, self._shoupai5, None, 1) == []

    def test_no_after_lizhi_change_tingpai(self, setup):
        rule = majiang.rule({'allow_angang_after_lizhi': 2})
        assert majiang.Game.get_gang_mianzi_(rule, self._shoupai1, None, 1) == ['z1111']
        assert majiang.Game.get_gang_mianzi_(rule, self._shoupai2, None, 1) == []
        assert majiang.Game.get_gang_mianzi_(rule, self._shoupai3, None, 1) == ['s3333']
        assert majiang.Game.get_gang_mianzi_(rule, self._shoupai4, None, 1) == ['s1111']
        assert majiang.Game.get_gang_mianzi_(rule, self._shoupai5, None, 1) == []

    def test_ng_haidi(self):
        rule = majiang.rule()
        assert majiang.Game.get_gang_mianzi_(rule,
                                             majiang.Shoupai.from_str('m1112p456s789z111z1'),
                                             None, 0) == []
        assert majiang.Game.get_gang_mianzi_(rule,
                                             majiang.Shoupai.from_str('m1112p456s789z111'),
                                             'z1=', 0) == []


class TestStatiAllowLizhi:
    def test_false_cannot_dapai(self):
        shoupai = majiang.Shoupai.from_str('m123p456s789z1122')
        assert not majiang.Game.allow_lizhi_(majiang.rule(), shoupai)

    def test_false_after_lizhi(self):
        shoupai = majiang.Shoupai.from_str('m123p456s789z11223*')
        assert not majiang.Game.allow_lizhi_(majiang.rule(), shoupai)

    def test_false_not_menqian(self):
        shoupai = majiang.Shoupai.from_str('m123p456s789z23,z111=')
        assert not majiang.Game.allow_lizhi_(majiang.rule(), shoupai)

    def test_false_no_zimo(self):
        shoupai = majiang.Shoupai.from_str('m123p456s789z11223')
        assert not majiang.Game.allow_lizhi_(majiang.rule(), shoupai, 'z3', 3)

    def test_allow_no_zimo(self):
        shoupai = majiang.Shoupai.from_str('m123p456s789z11223')
        assert majiang.Game.allow_lizhi_(majiang.rule({'lizhi_no_zimo': True}), shoupai, 'z3', 3)

    def test_false_defen(self):
        shoupai = majiang.Shoupai.from_str('m123p456s789z11223')
        assert not majiang.Game.allow_lizhi_(majiang.rule(), shoupai, 'z3', defen=900)

    def test_allow_defen(self):
        shoupai = majiang.Shoupai.from_str('m123p456s789z11223')
        assert majiang.Game.allow_lizhi_(majiang.rule({'minus_interruption': False}), shoupai, 'z3', defen=900)

    def test_false_no_tingpai(self):
        shoupai = majiang.Shoupai.from_str('m123p456s789z11234')
        assert not majiang.Game.allow_lizhi_(majiang.rule(), shoupai)

    def test_false_invalid_tingpai(self):
        shoupai = majiang.Shoupai.from_str('m123p456s789z11112')
        assert not majiang.Game.allow_lizhi_(majiang.rule(), shoupai, 'z2')

    def test_true_specified_pai(self):
        shoupai = majiang.Shoupai.from_str('m123p456s789z11112')
        assert majiang.Game.allow_lizhi_(majiang.rule(), shoupai, 'z1')

    def test_false_specified_pai(self):
        shoupai = majiang.Shoupai.from_str('m123p456s789z11112')
        assert not majiang.Game.allow_lizhi_(majiang.rule(), shoupai, 'z2')

    def test_list_unspecified_pai(self):
        shoupai = majiang.Shoupai.from_str('m123p456s788z11122')
        assert majiang.Game.allow_lizhi_(majiang.rule(), shoupai) == ['s7', 's8']
        shoupai = majiang.Shoupai.from_str('m123p456s789z11223')
        assert majiang.Game.allow_lizhi_(majiang.rule(), shoupai) == ['z3_']

    def test_false_unspecified_pai(self):
        shoupai = majiang.Shoupai.from_str('m11112344449999')
        assert not majiang.Game.allow_lizhi_(majiang.rule(), shoupai)


class TestStaticAllowHule:
    def test_neng_rong(self):
        shoupai = majiang.Shoupai.from_str('m123p456z1122,s789-')
        assert not majiang.Game.allow_hule_(majiang.rule(), shoupai, 'z1=', 0, 1, False, False)

    def test_not_hule(self):
        shoupai = majiang.Shoupai.from_str('m123p456z11223,s789-')
        assert not majiang.Game.allow_hule_(majiang.rule(), shoupai, None, 0, 1, False, True)

    def test_with_hupai(self):
        shoupai = majiang.Shoupai.from_str('m123p456s789z3377')
        assert majiang.Game.allow_hule_(majiang.rule(), shoupai, 'z3+', 0, 1, True, True)

    def test_without_hupai(self):
        shoupai = majiang.Shoupai.from_str('m123p456s789z3377')
        assert not majiang.Game.allow_hule_(majiang.rule(), shoupai, 'z3+', 0, 1, False, True)

    def test_no_fulou_danyaojiu(self):
        shoupai = majiang.Shoupai.from_str('m22555p234s78,p777-')
        rule = majiang.rule({'fulou_duanyaojiu': False})
        assert not majiang.Game.allow_hule_(rule, shoupai, 's6=', 0, 1, False, True)

    def test_zimo(self):
        shoupai = majiang.Shoupai.from_str('m123p456s789z33377')
        assert majiang.Game.allow_hule_(majiang.rule(), shoupai, None, 0, 1, False, False)

    def test_rong(self):
        shoupai = majiang.Shoupai.from_str('m123p456z1122,s789-')
        assert majiang.Game.allow_hule_(majiang.rule(), shoupai, 'z1=', 0, 1, False, True)


class TestStaticPingju:
    def test_after_diyizimo(self):
        shoupai = majiang.Shoupai.from_str('m1234569z1234567')
        assert not majiang.Game.allow_pingju_(majiang.rule(), shoupai, False)

    def test_not_after_zimo(self):
        shoupai = majiang.Shoupai.from_str('m123459z1234567')
        assert not majiang.Game.allow_pingju_(majiang.rule(), shoupai, True)

    def test_no_pingju(self):
        shoupai = majiang.Shoupai.from_str('m1234569z1234567')
        assert not majiang.Game.allow_pingju_(majiang.rule({'interrupted_pingju': False}), shoupai, True)

    def test_false_8shu(self):
        shoupai = majiang.Shoupai.from_str('m1234567z1234567')
        assert not majiang.Game.allow_pingju_(majiang.rule(), shoupai, True)

    def test_true(self):
        shoupai = majiang.Shoupai.from_str('m1234569z1234567')
        assert majiang.Game.allow_pingju_(majiang.rule(), shoupai, True)


class TestStaticAllowNoDaopai:
    @pytest.fixture
    def setup(self):
        self._rule = majiang.rule({'declare_no_tingpai': True})

    def test_false_exclude_last_dapai(self, setup):
        shoupai = majiang.Shoupai.from_str('m123p456z1122,s789-')
        assert not majiang.Game.allow_no_daopai(self._rule, shoupai, 1)
        assert not majiang.Game.allow_no_daopai(self._rule, shoupai.zimo('z3'), 0)

    def test_not_allow_diclare_no_tingpai(self):
        shoupai = majiang.Shoupai.from_str('m123p456z1122,s789-')
        assert not majiang.Game.allow_no_daopai(majiang.rule(), shoupai, 0)

    def test_false_lizhi(self, setup):
        shoupai = majiang.Shoupai.from_str('m123p456p789z1122*')
        assert not majiang.Game.allow_no_daopai(self._rule, shoupai, 0)

    def test_no_tingpai(self, setup):
        shoupai = majiang.Shoupai.from_str('m123p456p789z1123')
        assert not majiang.Game.allow_no_daopai(self._rule, shoupai, 0)

    def test_no_tinpai_paishi(self, setup):
        shoupai = majiang.Shoupai.from_str('m123p456p789z1111')
        assert not majiang.Game.allow_no_daopai(self._rule, shoupai, 0)

    def test_declare_no_tingpai(self, setup):
        shoupai = majiang.Shoupai.from_str('m123p456z1122,s789-')
        assert majiang.Game.allow_no_daopai(self._rule, shoupai, 0)
