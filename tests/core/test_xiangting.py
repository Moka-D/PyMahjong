import pytest
from jongpy.core.xiangting import xiangting
from jongpy.core.shoupai import Shoupai


class TestXiangting:

    def test_xiangting_normal(self):
        shoupai1 = Shoupai.from_string('m12389p456s12789z1')
        assert xiangting(shoupai1) == 1
        shoupai2 = Shoupai.from_string('s1223444556889s1')
        assert xiangting(shoupai2) == 1

    def test_xiangting_goushi(self):
        shoupai = Shoupai.from_string('m11259p19z123456z3')
        assert xiangting(shoupai) == 2

    def test_xiangting_qidui(self):
        shoupai1 = Shoupai.from_string('m1144p3366s89z4567')
        assert xiangting(shoupai1) == 2
        shoupai2 = Shoupai.from_string('m11144p33366s8899')
        assert xiangting(shoupai2) == 1
