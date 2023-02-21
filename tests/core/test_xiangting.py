import pytest   # noqa
import json

from jongpy.core import (Shoupai, xiangting_yiban,
                         xiangting_qidui,
                         xiangting_goushi,
                         xiangting,
                         tingpai)
from jongpy.core.xiangting import XIANGTING_INF


class TestXiangtingYiban:

    def test_empty(self):
        assert xiangting_yiban(Shoupai.from_str()) == 13

    def test_tingpai(self):
        assert xiangting_yiban(Shoupai.from_str('m123p406s789z1122')) == 0

    def test_hule(self):
        assert xiangting_yiban(Shoupai.from_str('m123p456s789z11222')) == -1

    def test_fulou(self):
        assert xiangting_yiban(Shoupai.from_str('m123p456s789z2,z111=')) == 0

    def test_no_jianpai(self):
        assert xiangting_yiban(Shoupai.from_str('m12389p456s12789z1')) == 1

    def test_over_dazi(self):
        assert xiangting_yiban(Shoupai.from_str('m12389p456s1289z11')) == 1

    def test_lack_dazi(self):
        assert xiangting_yiban(Shoupai.from_str('m133345568z23677')) == 2

    def test_shoupai_overflow(self):
        shoupai = Shoupai.from_str('m123,p123-,s456-,m789-')
        shoupai._fulou.append('z555=')
        assert xiangting_yiban(shoupai) == 0

    def test_shoupai_underflow(self):
        assert xiangting_yiban(Shoupai.from_str('p234s567,m222=,p0-67')) == 1

    def test_kezi_shunzi(self):
        assert xiangting_yiban(Shoupai.from_str('p222345z1234567')) == 4

    def test_shunzi_alone_pai_shunzi(self):
        assert xiangting_yiban(Shoupai.from_str('p2344456z123456')) == 4

    def test_duizi_kezi_shunzi(self):
        assert xiangting_yiban(Shoupai.from_str('p11222345z12345')) == 3

    def test_duizi_shunzi_shunzi_duizi(self):
        assert xiangting_yiban(Shoupai.from_str('p2234556788z123')) == 2

    def test_hule_after_fulou(self):
        assert xiangting_yiban(Shoupai.from_str('m11122,p123-,s12-3,z111=,')) == 0

    def test_nomarl_10000patterns(self, shared_datadir):
        with open(shared_datadir / 'xiangting_1.json', 'r') as f:
            data1 = json.load(f)
        for data in data1:
            shoupai = Shoupai(data['q'])
            assert xiangting_yiban(shoupai) == data['x'][0]

    def test_hunyise_10000patterns(self, shared_datadir):
        with open(shared_datadir / 'xiangting_2.json', 'r') as f:
            data2 = json.load(f)
        for data in data2:
            shoupai = Shoupai(data['q'])
            assert xiangting_yiban(shoupai) == data['x'][0]

    def test_qingyise_10000patterns(self, shared_datadir):
        with open(shared_datadir / 'xiangting_3.json', 'r') as f:
            data3 = json.load(f)
        for data in data3:
            shoupai = Shoupai(data['q'])
            assert xiangting_yiban(shoupai) == data['x'][0]

    def test_goushi_10000patterns(self, shared_datadir):
        with open(shared_datadir / 'xiangting_4.json', 'r') as f:
            data4 = json.load(f)
        for data in data4:
            shoupai = Shoupai(data['q'])
            assert xiangting_yiban(shoupai) == data['x'][0]


class TestXiangTingGoushi:

    def test_empty(self):
        assert xiangting_goushi(Shoupai.from_str()) == 13

    def test_noexist_yao(self):
        assert xiangting_goushi(Shoupai.from_str('m23455p345s45678')) == 13

    def test_noexist_jiangpai(self):
        assert xiangting_goushi(Shoupai.from_str('m189p12s249z12345')) == 4

    def test_exist_jiangpai(self):
        assert xiangting_goushi(Shoupai.from_str('m119p12s299z12345')) == 3

    def test_tingpai(self):
        assert xiangting_goushi(Shoupai.from_str('m11p19s19z1234567')) == 0

    def test_tingpai_13men(self):
        assert xiangting_goushi(Shoupai.from_str('m19p19s19z1234567')) == 0

    def test_hule(self):
        assert xiangting_goushi(Shoupai.from_str('m119p19s19z1234567')) == -1

    def test_fulou(self):
        assert xiangting_goushi(Shoupai.from_str('m19p19s19z1234,z777=')) == XIANGTING_INF

    def test_shoupai_overflow(self):
        assert xiangting_goushi(Shoupai.from_str('m19p19s19z12345677').zimo('m1', False)) == -1

    def test_shoupai_underflow(self):
        assert xiangting_goushi(Shoupai.from_str('m119p19s19z12345')) == 1

    def test_nomarl_10000patterns(self, shared_datadir):
        with open(shared_datadir / 'xiangting_1.json', 'r') as f:
            data1 = json.load(f)
        for data in data1:
            shoupai = Shoupai(data['q'])
            assert xiangting_goushi(shoupai) == data['x'][1]

    def test_hunyise_10000patterns(self, shared_datadir):
        with open(shared_datadir / 'xiangting_2.json', 'r') as f:
            data2 = json.load(f)
        for data in data2:
            shoupai = Shoupai(data['q'])
            assert xiangting_goushi(shoupai) == data['x'][1]

    def test_qingyise_10000patterns(self, shared_datadir):
        with open(shared_datadir / 'xiangting_3.json', 'r') as f:
            data3 = json.load(f)
        for data in data3:
            shoupai = Shoupai(data['q'])
            assert xiangting_goushi(shoupai) == data['x'][1]

    def test_goushi_10000patterns(self, shared_datadir):
        with open(shared_datadir / 'xiangting_4.json', 'r') as f:
            data4 = json.load(f)
        for data in data4:
            shoupai = Shoupai(data['q'])
            assert xiangting_goushi(shoupai) == data['x'][1]


class TestXiangtingQidui:

    def test_empty(self):
        assert xiangting_qidui(Shoupai.from_str()) == 13

    def test_noexist_duizi(self):
        assert xiangting_qidui(Shoupai.from_str('m19p19s19z1234567')) == 6

    def test_exist_ganzi(self):
        assert xiangting_qidui(Shoupai.from_str('m1188p288s05z1111')) == 2

    def test_exist_ankezi(self):
        assert xiangting_qidui(Shoupai.from_str('m1188p2388s05z111')) == 1

    def test_tow_ankezi(self):
        assert xiangting_qidui(Shoupai.from_str('m1188p288s055z111')) == 2

    def test_tingpai(self):
        assert xiangting_qidui(Shoupai.from_str('m1188p288s05z1177')) == 0

    def test_hule(self):
        assert xiangting_qidui(Shoupai.from_str('m1188p288s05z1177p2')) == -1

    def test_fulou(self):
        assert xiangting_qidui(Shoupai.from_str('m1188p288s05z2,z111=')) == XIANGTING_INF

    def test_shoupai_overflow(self):
        assert xiangting_qidui(Shoupai.from_str('m1188p2288s05z1122').zimo('z7', False).zimo('z7', False)) == -1

    def test_shoupai_underflow(self):
        assert xiangting_qidui(Shoupai.from_str('m1188s05z1122')) == 3

    def test_nomarl_10000patterns(self, shared_datadir):
        with open(shared_datadir / 'xiangting_1.json', 'r') as f:
            data1 = json.load(f)
        for data in data1:
            shoupai = Shoupai(data['q'])
            assert xiangting_qidui(shoupai) == data['x'][2]

    def test_hunyise_10000patterns(self, shared_datadir):
        with open(shared_datadir / 'xiangting_2.json', 'r') as f:
            data2 = json.load(f)
        for data in data2:
            shoupai = Shoupai(data['q'])
            assert xiangting_qidui(shoupai) == data['x'][2]

    def test_qingyise_10000patterns(self, shared_datadir):
        with open(shared_datadir / 'xiangting_3.json', 'r') as f:
            data3 = json.load(f)
        for data in data3:
            shoupai = Shoupai(data['q'])
            assert xiangting_qidui(shoupai) == data['x'][2]

    def test_goushi_10000patterns(self, shared_datadir):
        with open(shared_datadir / 'xiangting_4.json', 'r') as f:
            data4 = json.load(f)
        for data in data4:
            shoupai = Shoupai(data['q'])
            assert xiangting_qidui(shoupai) == data['x'][2]


class TestXiangting:

    def test_normal_tingpai(self):
        assert xiangting(Shoupai.from_str('m123p406s789z1122')) == 0

    def test_goushi_tingpai(self):
        assert xiangting(Shoupai.from_str('m19p19s19z1234567')) == 0

    def test_qidui_tingpai(self):
        assert xiangting(Shoupai.from_str('m1188p288s05z1177')) == 0

    def test_nomarl_10000patterns(self, shared_datadir):
        with open(shared_datadir / 'xiangting_1.json', 'r') as f:
            data1 = json.load(f)
        for data in data1:
            shoupai = Shoupai(data['q'])
            assert xiangting(shoupai) == min(data['x'])

    def test_hunyise_10000patterns(self, shared_datadir):
        with open(shared_datadir / 'xiangting_2.json', 'r') as f:
            data2 = json.load(f)
        for data in data2:
            shoupai = Shoupai(data['q'])
            assert xiangting(shoupai) == min(data['x'])

    def test_qingyise_10000patterns(self, shared_datadir):
        with open(shared_datadir / 'xiangting_3.json', 'r') as f:
            data3 = json.load(f)
        for data in data3:
            shoupai = Shoupai(data['q'])
            assert xiangting(shoupai) == min(data['x'])

    def test_goushi_10000patterns(self, shared_datadir):
        with open(shared_datadir / 'xiangting_4.json', 'r') as f:
            data4 = json.load(f)
        for data in data4:
            shoupai = Shoupai(data['q'])
            assert xiangting(shoupai) == min(data['x'])


class TestTingpai:

    def test_error_can_dapai(self):
        assert tingpai(Shoupai.from_str('m123p456s789z12345')) is None
        assert tingpai(Shoupai.from_str('m123p456z12345,s789-,')) is None

    def test_without_fulou(self):
        assert tingpai(Shoupai.from_str('m123p456s789z1234')) == ['z1', 'z2', 'z3', 'z4']

    def test_with_fulou(self):
        assert tingpai(Shoupai.from_str('m123p456z1234,s789-')) == ['z1', 'z2', 'z3', 'z4']

    def test_goushi_13men(self):
        assert tingpai(Shoupai.from_str('m19p19s19z1234567')) == ['m1', 'm9', 'p1', 'p9', 's1', 's9',
                                                                  'z1', 'z2', 'z3', 'z4', 'z5', 'z6', 'z7']

    def test_not_include_four_pai(self):
        assert tingpai(Shoupai.from_str('m1234444p456s789')) == ['m1']

    def test_include_ankezi(self):
        assert tingpai(Shoupai.from_str('m13p456s789z11,m2222')) == ['m2']

    def test_qidui_and_yiban(self):
        assert tingpai(Shoupai.from_str('m11155p2278s66z17')) == ['m5', 'p2', 'p6', 'p7', 'p8', 'p9', 's6', 'z1', 'z7']

    def test_f_xiangting(self):
        assert tingpai(Shoupai.from_str('m11155p2278s66z17'), xiangting_qidui) == ['p7', 'p8', 'z1', 'z7']
