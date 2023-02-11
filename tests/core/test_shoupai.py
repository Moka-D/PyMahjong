import pytest
from jongpy.core.shoupai import Shoupai


class TestShoupai:

    def test_valid_pai(self):
        assert Shoupai.valid_pai('m1') == 'm1'
        assert Shoupai.valid_pai('p0-') == 'p0-'
        assert not Shoupai.valid_pai('z')
        assert not Shoupai.valid_pai('_')

    def test_valid_mianzi(self):
        assert Shoupai.valid_mianzi('m055=') == 'm505='
        assert Shoupai.valid_mianzi('p0555') == 'p5550'
        assert Shoupai.valid_mianzi('p0555=') == 'p5505='
        assert Shoupai.valid_mianzi('s6-45') == 's456-'
        assert not Shoupai.valid_mianzi('z678')

    def test_from_string(self):
        shoupai = Shoupai.from_string('m055z77,m78-9,z5555,z666=,')
        assert shoupai._zimo == 'z666='
        assert shoupai._fulou == ['m78-9', 'z5555', 'z666=']
        assert not shoupai._lizhi

    def test_zimo(self):
        shoupai = Shoupai.from_string('m55z77,m78-9,z5555,z666=')
        shoupai.zimo('m0')
        assert shoupai._zimo == 'm0'
        assert shoupai._fulou == ['m78-9', 'z5555', 'z666=']
        assert not shoupai._lizhi

    def test_get_dapai(self):
        shoupai1 = Shoupai.from_string('m1550m1,s888-,p2-34,z111=')
        assert shoupai1.get_dapai() == ['m1', 'm0', 'm5', 'm1_']
        shoupai2 = Shoupai.from_string('m1550z1,s888=,p2-34,m234-,')
        assert shoupai2.get_dapai() == ['m0', 'm5', 'z1']

    def test_get_chi_mianzi(self):
        shoupai1 = Shoupai.from_string('m123p345067s789z1')
        assert shoupai1.get_chi_mianzi('p4-') == ['p34-0', 'p34-5', 'p4-06', 'p4-56']
        shoupai2 = Shoupai.from_string('p1112344,z111+,s40-6')
        assert shoupai2.get_chi_mianzi('p4-') == []

    def test_get_peng_mianzi(self):
        shoupai = Shoupai.from_string('m123p500s789z1234')
        assert shoupai.get_peng_mianzi('p5=') == ['p005=', 'p505=']

    def test_get_gang_mianzi(self):
        shoupai1 = Shoupai.from_string('m550p456s789z1,m111')
        assert shoupai1.get_gang_mianzi('m0+') == ['m5500+']
        shoupai2 = Shoupai.from_string('m1p456s789z1111,m111+')
        assert shoupai2.get_gang_mianzi() == ['m111+1', 'z1111']
