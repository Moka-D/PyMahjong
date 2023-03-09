import pytest   # noqa
import json

from jongpy.core import Shoupai, hule_mianzi, hule, rule
from jongpy.core import hule_param as param
from jongpy.core.exceptions import InvalidOperationError


class TestHuleMianzi:

    def test_normal_zimo(self):
        assert (hule_mianzi(Shoupai.from_str('m123p055s789z11122'), None)
                == [['z22_!', 'm123', 'p555', 's789', 'z111']])

    def test_normal_rong(self):
        assert (hule_mianzi(Shoupai.from_str('m123p055s789z1112'), 'z2+')
                == [['z22+!', 'm123', 'p555', 's789', 'z111']])

    def test_normal_fulou(self):
        assert (hule_mianzi(Shoupai.from_str('m123p055z1112,s7-89'), 'z2=')
                == [['z22=!', 'm123', 'p555', 'z111', 's7-89']])

    def test_goushi_zimo(self):
        assert (hule_mianzi(Shoupai.from_str('m9p19s19z12345677m1'), None)
                == [['z77', 'm1_!', 'm9', 'p1', 'p9', 's1', 's9', 'z1', 'z2', 'z3', 'z4', 'z5', 'z6']])

    def test_goushi_13men_rong(self):
        assert (hule_mianzi(Shoupai.from_str('m19p19s19z1234567'), 'm9+')
                == [['m99+!', 'm1', 'p1', 'p9', 's1', 's9', 'z1', 'z2', 'z3', 'z4', 'z5', 'z6', 'z7']])

    def test_jiulian(self):
        assert (hule_mianzi(Shoupai.from_str('m1112345678999'), 'm0=')
                == [['m55=!', 'm111', 'm234', 'm678', 'm999'],
                    ['m11123456789995=!']])

    def test_no_hule_shoupai_underflow(self):
        assert hule_mianzi(Shoupai.from_str('m123p055s789z1122')) == []

    def test_no_hule_three_mianzi(self):
        assert hule_mianzi(Shoupai.from_str('___m123p055z2,s7-89'), 'z2=') == []

    def test_no_hule_one_duizi(self):
        assert hule_mianzi(Shoupai.from_str('m22')) == []

    def test_no_hule_goushi_tingpai(self):
        assert hule_mianzi(Shoupai.from_str('m19p19s19z123456'), 'z7=') == []

    def test_no_hule_jiulian_tingpai(self):
        assert hule_mianzi(Shoupai.from_str('m111234567899'), 'm9=') == []

    def test_single_hule(self):
        assert (hule_mianzi(Shoupai.from_str('m111123p789999z1z1'), None)
                == [['z11_!', 'm123', 'm111', 'p789', 'p999']])

    def test_multi_hule_erbeiko_or_qidui(self):
        assert (hule_mianzi(Shoupai.from_str('m223344p556677s88'))
                == [['s88_!', 'm234', 'm234', 'p567', 'p567'],
                    ['m22', 'm33', 'm44', 'p55', 'p66', 'p77', 's88_!']])

    def test_multi_hule_shunzi_or_kezi(self):
        assert (hule_mianzi(Shoupai.from_str('m111222333p89997'))
                == [['p99', 'm123', 'm123', 'm123', 'p7_!89'],
                    ['p99', 'm111', 'm222', 'm333', 'p7_!89']])

    def test_multi_hule_pinghu_or_sansetongshun(self):
        assert (hule_mianzi(Shoupai.from_str('m2234455p234s234m3'))
                == [['m22', 'm3_!45', 'm345', 'p234', 's234'],
                    ['m55', 'm23_!4', 'm234', 'p234', 's234']])

    def test_multi_hule_include_ankezi(self):
        assert (hule_mianzi(Shoupai.from_str('m23p567s33345666m1'))
                == [['s33', 'm1_!23', 'p567', 's345', 's666'],
                    ['s66', 'm1_!23', 'p567', 's333', 's456']])

    def test_multi_hule_jiulian(self):
        assert (hule_mianzi(Shoupai.from_str('s1113445678999s2'))
                == [['s99', 's111', 's2_!34', 's456', 's789'],
                    ['s11134456789992_!']])

    def test_bug_anganged_5th_pai(self):
        assert (hule_mianzi(Shoupai.from_str('s4067999z444s8,s8888'))
                == [['s99', 's456', 's78_!9', 'z444', 's8888']])


class TestHuleFu:

    def test_invalid_param(self):
        with pytest.raises(InvalidOperationError):
            hule(Shoupai.from_str(), 'm1', param())

    def test_not_hule(self):
        h = hule(Shoupai.from_str(), None, param())
        assert h is None

    def test_fu_pinghu_zimo(self):
        h = hule(Shoupai.from_str('m345567p234s33789'), None, param())
        assert h['fu'] == 20

    def test_fu_pinghu_rong(self):
        h = hule(Shoupai.from_str('m345567p234s3378'), 's9=', param())
        assert h['fu'] == 30

    def test_fu_otafeng_jiangpai(self):
        h = hule(Shoupai.from_str('m112233p456z33s78'), 's9=', param())
        assert h['fu'] == 30

    def test_fu_zhuanfeng_jiangpai(self):
        h = hule(Shoupai.from_str('m112233p456z11s78'), 's9=', param())
        assert h['fu'] == 40

    def test_fu_menfeng_jiangpai(self):
        h = hule(Shoupai.from_str('m112233p456z22s78'), 's9=', param())
        assert h['fu'] == 40

    def test_fu_sanyuan_jiangpai(self):
        h = hule(Shoupai.from_str('m112233p456z55s78'), 's9=', param())
        assert h['fu'] == 40

    def test_fu_zhuanfeng_and_menfeng_jiangpai(self):
        h = hule(Shoupai.from_str('m112233z444z11s78'), 's9=', param({'menfeng': 0}))
        assert h['fu'] == 50

    def test_fu_zhungzhang_minkezi(self):
        h = hule(Shoupai.from_str('m123z11m88,p888+,s888-'), 'm8=', param({'menfeng': 0}))
        assert h['fu'] == 30

    def test_fu_yaojiu_minkezi(self):
        h = hule(Shoupai.from_str('m123p22s99,z222+,p111-'), 's9=', param())
        assert h['fu'] == 40

    def test_fu_zhungzhang_ankezi(self):
        h = hule(Shoupai.from_str('z33p222777s888m23'), 'm4=', param())
        assert h['fu'] == 50

    def test_fu_yaojiu_ankezi(self):
        h = hule(Shoupai.from_str('s33p111999z555m23'), 'm4=', param())
        assert h['fu'] == 60

    def test_fu_zhungzhang_mingang(self):
        h = hule(Shoupai.from_str('p33m22245667,s444+4'), 'm8=', param())
        assert h['fu'] == 40

    def test_fu_yaojiu_mingang(self):
        h = hule(Shoupai.from_str('p33m23445667,z6666-'), 'm8=', param())
        assert h['fu'] == 40

    def test_fu_zhungzhang_angang(self):
        h = hule(Shoupai.from_str('p33m23445667,s4444'), 'm8=', param())
        assert h['fu'] == 50

    def test_fu_yaojiu_angang(self):
        h = hule(Shoupai.from_str('p33m23445667,z7777'), 'm8=', param())
        assert h['fu'] == 70

    def test_fu_zimo(self):
        h = hule(Shoupai.from_str('p33m222s222345,s888-'), None, param())
        assert h['fu'] == 40

    def test_fu_danqi(self):
        h = hule(Shoupai.from_str('m222s222345p3,s888-'), 'p3=', param())
        assert h['fu'] == 40

    def test_fu_kanzhang(self):
        h = hule(Shoupai.from_str('p33m222s22235,s888-'), 's4=', param())
        assert h['fu'] == 40

    def test_fu_bianzhang(self):
        h = hule(Shoupai.from_str('p33z111m12389,s222-'), 'm7=', param())
        assert h['fu'] == 40

    def test_fu_fulou_pinghu(self):
        h = hule(Shoupai.from_str('m22p345678s34,s67-8'), 's5=', param())
        assert h['fu'] == 30

    def test_fu_qidui(self):
        h = hule(Shoupai.from_str('m2255p88s1166z1155'), None, param())
        assert h['fu'] == 25

    def test_fu_goushi(self):
        h = hule(Shoupai.from_str('m19p19s1z12345677s9'), None, param())
        assert h['fu'] is None

    def test_fu_jiulian(self):
        h = hule(Shoupai.from_str('m11123456789995'), None, param())
        assert h['fu'] is None


class TestHuleHupai:

    def test_no_hupai(self):
        h = hule(Shoupai.from_str('m344556s24678z66'), 's3=', param())
        assert h['hupai'] is None

    def test_hupai_lizhi(self):
        h = hule(Shoupai.from_str('m344556s24678z66*'), 's3=', param({'lizhi': 1}))
        assert h['hupai'] == [{'name': '立直', 'fanshu': 1}]

    def test_hupai_double_lizhi(self):
        h = hule(Shoupai.from_str('m344556s24678z66*'), 's3=', param({'lizhi': 2}))
        assert h['hupai'] == [{'name': 'ダブル立直', 'fanshu': 2}]

    def test_hupai_lizhi_yifa(self):
        h = hule(Shoupai.from_str('m344556s24678z66*'), 's3=', param({'lizhi': 1, 'yifa': True}))
        assert h['hupai'] == [{'name': '立直', 'fanshu': 1},
                              {'name': '一発', 'fanshu': 1}]

    def test_hupai_haidi_zimo(self):
        h = hule(Shoupai.from_str('m344556s24z66s3,s6-78'), None, param({'haidi': 1}))
        assert h['hupai'] == [{'name': '海底摸月', 'fanshu': 1}]

    def test_hupai_haidi_rong(self):
        h = hule(Shoupai.from_str('m344556s24678z66'), 's3=', param({'haidi': 2}))
        assert h['hupai'] == [{'name': '河底撈魚', 'fanshu': 1}]

    def test_hupai_lingshang(self):
        h = hule(Shoupai.from_str('m344556s24z66s3,s777+7'), None, param({'lingshang': True}))
        assert h['hupai'] == [{'name': '嶺上開花', 'fanshu': 1}]

    def test_hupai_qianggang(self):
        h = hule(Shoupai.from_str('m344556s24678z66'), 's3=', param({'qianggang': True}))
        assert h['hupai'] == [{'name': '槍槓', 'fanshu': 1}]

    def test_hupai_tianhu(self):
        h = hule(Shoupai.from_str('m344556s24678z66s3'), None, param({'tianhu': 1}))
        assert h['hupai'] == [{'name': '天和', 'fanshu': '*'}]

    def test_hupai_zhihu(self):
        h = hule(Shoupai.from_str('m344556s24678z66s3'), None, param({'tianhu': 2}))
        assert h['hupai'] == [{'name': '地和', 'fanshu': '*'}]

    def test_hupai_menqianging(self):
        h = hule(Shoupai.from_str('m344556s24678z66s3'), None, param())
        assert h['hupai'] == [{'name': '門前清自摸和', 'fanshu': 1}]

    def test_hupai_zhuangfeng_dong(self):
        h = hule(Shoupai.from_str('m345567s3378z111'), 's9=', param())
        assert h['hupai'] == [{'name': '場風 東', 'fanshu': 1}]

    def test_hupai_menfeng_xi(self):
        h = hule(Shoupai.from_str('m345567s33789,z333+'), None, param({'menfeng': 2}))
        assert h['hupai'] == [{'name': '自風 西', 'fanshu': 1}]

    def test_hupai_zhuangfeng_and_menfeng_nan(self):
        h = hule(Shoupai.from_str('m345567s33z22,s789-'), 'z2=', param({'zhuangfeng': 1}))
        assert h['hupai'] == [{'name': '場風 南', 'fanshu': 1},
                              {'name': '自風 南', 'fanshu': 1}]

    def test_hupai_fanpai_hak(self):
        h = hule(Shoupai.from_str('m345567s33789,z555+5'), None, param())
        assert h['hupai'] == [{'name': '翻牌 白', 'fanshu': 1}]

    def test_hupai_fanpai_fa_chun(self):
        h = hule(Shoupai.from_str('m345567s33,z6666+,z7777'), None, param())
        assert h['hupai'] == [{'name': '翻牌 發', 'fanshu': 1},
                              {'name': '翻牌 中', 'fanshu': 1}]

    def test_hupai_pinghu(self):
        h = hule(Shoupai.from_str('z33m234456p78s123'), 'p9=', param())
        assert h['hupai'] == [{'name': '平和', 'fanshu': 1}]

    def test_hupai_pinghu_zimo(self):
        h = hule(Shoupai.from_str('z33m234456p78s123p9'), None, param())
        assert h['hupai'] == [{'name': '門前清自摸和', 'fanshu': 1},
                              {'name': '平和', 'fanshu': 1}]

    def test_hupai_fulou_pinghu(self):
        h = hule(Shoupai.from_str('z33m234456p78,s1-23'), 'p9=', param())
        assert h['hupai'] is None

    def test_hupai_danyaojiu(self):
        h = hule(Shoupai.from_str('m22555p234s78,p777-'), 's6=', param())
        assert h['hupai'] == [{'name': '断幺九', 'fanshu': 1}]

    def test_hupai_danyaojiu_qiduizi(self):
        h = hule(Shoupai.from_str('m2255p4488s33667'), 's7=', param())
        assert h['hupai'] == [{'name': '断幺九', 'fanshu': 1},
                              {'name': '七対子', 'fanshu': 2}]

    def test_hupai_yibeikou(self):
        h = hule(Shoupai.from_str('m33455p111s33789'), 'm4=', param())
        assert h['hupai'] == [{'name': '一盃口', 'fanshu': 1}]

    def test_hupai_fulou_yibeikou(self):
        h = hule(Shoupai.from_str('m33455p111s33,s78-9'), 'm4=', param())
        assert h['hupai'] is None

    def test_hupai_sansetongshun(self):
        h = hule(Shoupai.from_str('m567p567s2256799'), 's9=', param())
        assert h['hupai'] == [{'name': '三色同順', 'fanshu': 2}]

    def test_hupai_fulou_sansetongshun(self):
        h = hule(Shoupai.from_str('m567s2256799,p56-7'), 's9=', param())
        assert h['hupai'] == [{'name': '三色同順', 'fanshu': 1}]

    def test_hupai_yiqitongguan(self):
        h = hule(Shoupai.from_str('m12456789s33789'), 'm3=', param())
        assert h['hupai'] == [{'name': '一気通貫', 'fanshu': 2}]

    def test_hupai_fulou_yiqitongguan(self):
        h = hule(Shoupai.from_str('m12789s33789,m4-56'), 'm3=', param())
        assert h['hupai'] == [{'name': '一気通貫', 'fanshu': 1}]

    def test_hupai_hunquandaiyaojiu(self):
        h = hule(Shoupai.from_str('m123999p789z33s12'), 's3=', param())
        assert h['hupai'] == [{'name': '混全帯幺九', 'fanshu': 2}]

    def test_hupai_fulou_hunquandaiyaojiu(self):
        h = hule(Shoupai.from_str('m123p789z33s12,m999+'), 's3=', param())
        assert h['hupai'] == [{'name': '混全帯幺九', 'fanshu': 1}]

    def test_hupai_qiduizi(self):
        h = hule(Shoupai.from_str('m115599p2233s8z22'), 's8=', param())
        assert h['hupai'] == [{'name': '七対子', 'fanshu': 2}]

    def test_hupai_duiduihu(self):
        h = hule(Shoupai.from_str('m55888z333s22,p111='), 's2=', param())
        assert h['hupai'] == [{'name': '対々和', 'fanshu': 2}]

    def test_hupai_sananke(self):
        h = hule(Shoupai.from_str('p99s111m555,p345-,s3333'), None, param())
        assert h['hupai'] == [{'name': '三暗刻', 'fanshu': 2}]

    def test_hupai_sangangzi(self):
        h = hule(Shoupai.from_str('p11m45,s2222+,m888=8,z4444'), 'm3=', param())
        assert h['hupai'] == [{'name': '三槓子', 'fanshu': 2}]

    def test_hupai_sansetongke(self):
        h = hule(Shoupai.from_str('s12377m22,p222-,s222-'), 'm2=', param())
        assert h['hupai'] == [{'name': '三色同刻', 'fanshu': 2}]

    def test_hupai_hunlaotou_duiduihu(self):
        h = hule(Shoupai.from_str('z11p11199,m111=,z333+'), 'p9=', param())
        assert h['hupai'] == [{'name': '対々和', 'fanshu': 2},
                              {'name': '混老頭', 'fanshu': 2}]

    def test_hupai_hunlaotou_qiduizi(self):
        h = hule(Shoupai.from_str('m1199p11s99z11335'), 'z5=', param())
        assert h['hupai'] == [{'name': '七対子', 'fanshu': 2},
                              {'name': '混老頭', 'fanshu': 2}]

    def test_hupai_xiaosanyuan(self):
        h = hule(Shoupai.from_str('z55577m567p22,z666-'), 'p2=', param())
        assert h['hupai'] == [{'name': '翻牌 白', 'fanshu': 1},
                              {'name': '翻牌 發', 'fanshu': 1},
                              {'name': '小三元', 'fanshu': 2}]

    def test_hupai_hunyise(self):
        h = hule(Shoupai.from_str('m111234789z1133'), 'z3=', param())
        assert h['hupai'] == [{'name': '混一色', 'fanshu': 3}]

    def test_hupai_fulou_hunyise(self):
        h = hule(Shoupai.from_str('z11333p23478,p111+'), 'p9=', param())
        assert h['hupai'] == [{'name': '混一色', 'fanshu': 2}]

    def test_hupai_hunyise_qiduizi(self):
        h = hule(Shoupai.from_str('s11224488z22557'), 'z7=', param())
        assert h['hupai'] == [{'name': '七対子', 'fanshu': 2},
                              {'name': '混一色', 'fanshu': 3}]

    def test_hupai_chunquandaiyaojiu(self):
        h = hule(Shoupai.from_str('m11s123p789s789m99'), 'm9=', param())
        assert h['hupai'] == [{'name': '純全帯幺九', 'fanshu': 3}]

    def test_hupai_fulou_chunquandaiyaojiu(self):
        h = hule(Shoupai.from_str('m11s123p789s78,m999='), 's9=', param())
        assert h['hupai'] == [{'name': '純全帯幺九', 'fanshu': 2}]

    def test_hupai_erbeiko(self):
        h = hule(Shoupai.from_str('m223344p667788s9'), 's9=', param())
        assert h['hupai'] == [{'name': '二盃口', 'fanshu': 3}]

    def test_hupai_erbeiko_4pais(salf):
        h = hule(Shoupai.from_str('m222233334444s9'), 's9=', param())
        assert h['hupai'] == [{'name': '二盃口', 'fanshu': 3}]

    def test_hupai_fulou_erbeiko(self):
        h = hule(Shoupai.from_str('m223344p678s9,p678-'), 's9=', param())
        assert h['hupai'] is None

    def test_hupai_qingyise(self):
        h = hule(Shoupai.from_str('m1113456677778'), 'm9=', param())
        assert h['hupai'] == [{'name': '清一色', 'fanshu': 6}]

    def test_hupai_fulou_qingyise(self):
        h = hule(Shoupai.from_str('p2344555,p12-3,p7-89'), 'p1=', param())
        assert h['hupai'] == [{'name': '清一色', 'fanshu': 5}]

    def test_hupai_qingyise_qiduizi(self):
        h = hule(Shoupai.from_str('s1122445577889'), 's9=', param())
        assert h['hupai'] == [{'name': '七対子', 'fanshu': 2},
                              {'name': '清一色', 'fanshu': 6}]

    def test_hupai_goushiwushuang(self):
        h = hule(Shoupai.from_str('m119p19s19z1234567'), None, param())
        assert h['hupai'] == [{'name': '国士無双', 'fanshu': '*'}]

    def test_hupai_goushiwushuang_13men(self):
        h = hule(Shoupai.from_str('m19p19s19z1234567m1'), None, param())
        assert h['hupai'] == [{'name': '国士無双十三面', 'fanshu': '**'}]

    def test_hupai_sianke(self):
        h = hule(Shoupai.from_str('m33m111p333s777z111'), None, param())
        assert h['hupai'] == [{'name': '四暗刻', 'fanshu': '*'}]

    def test_hupai_sianke_danqi(self):
        h = hule(Shoupai.from_str('m111p333s777z111m3'), 'm3=', param())
        assert h['hupai'] == [{'name': '四暗刻単騎', 'fanshu': '**'}]

    def test_hupai_dasanyuan(self):
        h = hule(Shoupai.from_str('z555m456p22z66,z777+'), 'z6=', param())
        assert h['hupai'] == [{'name': '大三元', 'fanshu': '*'}]

    def test_hupai_dasanyuan_baojia(self):
        h = hule(Shoupai.from_str('m2234,z555-5,z6666,z777+'), 'm5=', param())
        assert h['hupai'] == [{'name': '大三元', 'fanshu': '*', 'baojia': '+'}]

    def test_hupai_shosixi(self):
        h = hule(Shoupai.from_str('m234z2244,z333+,z111-'), 'z4=', param())
        assert h['hupai'] == [{'name': '小四喜', 'fanshu': '*'}]

    def test_hupai_daisixi(self):
        h = hule(Shoupai.from_str('m22z22244,z333+,z111-'), 'z4=', param())
        assert h['hupai'] == [{'name': '大四喜', 'fanshu': '**'}]

    def test_hupai_daisixi_baojia(self):
        h = hule(Shoupai.from_str('m2,z222+,z4444,z333+,z111-'), 'm2=', param())
        assert h['hupai'] == [{'name': '大四喜', 'fanshu': '**', 'baojia': '-'}]

    def test_hupai_ziyise(self):
        h = hule(Shoupai.from_str('z1112277,z555=,z444+'), 'z7=', param())
        assert h['hupai'] == [{'name': '字一色', 'fanshu': '*'}]

    def test_hupai_ziyise_qiduizi(self):
        h = hule(Shoupai.from_str('z1122334455667'), 'z7=', param())
        assert h['hupai'] == [{'name': '字一色', 'fanshu': '*'}]

    def test_hupai_lvyise(self):
        h = hule(Shoupai.from_str('s22334466z66,s888+'), 'z6=', param())
        assert h['hupai'] == [{'name': '緑一色', 'fanshu': '*'}]

    def test_hupai_lvyise_without_fa(self):
        h = hule(Shoupai.from_str('s4466,s222=,s333+,s888-'), 's6=', param())
        assert h['hupai'] == [{'name': '緑一色', 'fanshu': '*'}]

    def test_hupai_qinglaotou(self):
        h = hule(Shoupai.from_str('s11p111m11,s999-,m999='), 'm1=', param())
        assert h['hupai'] == [{'name': '清老頭', 'fanshu': '*'}]

    def test_hupai_sigangzi(self):
        h = hule(Shoupai.from_str('m1,z5555,p222+2,p777-7,s1111-'), 'm1=', param())
        assert h['hupai'] == [{'name': '四槓子', 'fanshu': '*'}]

    def test_hupai_jiulianbaodeng(self):
        h = hule(Shoupai.from_str('m1112235678999'), 'm4=', param())
        assert h['hupai'] == [{'name': '九蓮宝燈', 'fanshu': '*'}]

    def test_hupai_pure_jiulianbaodeng(self):
        h = hule(Shoupai.from_str('m1112345678999'), 'm2=', param())
        assert h['hupai'] == [{'name': '純正九蓮宝燈', 'fanshu': '**'}]


class TestHuleBaopai:

    def test_baopai_none(self):
        h = hule(Shoupai.from_str('p55m234s78,m4-56,z111+'), 's9=', param({'baopai': ['s1']}))
        assert h['hupai'] == [{'name': '場風 東', 'fanshu': 1}]

    def test_baopai_shoupai_one(self):
        h = hule(Shoupai.from_str('p55m234s78,m4-56,z111+'), 's9=', param({'baopai': ['m2']}))
        assert h['hupai'] == [{'name': '場風 東', 'fanshu': 1},
                              {'name': 'ドラ', 'fanshu': 1}]

    def test_baopai_shoupai_two(self):
        h = hule(Shoupai.from_str('p55m234s78,m4-56,z111+'), 's9=', param({'baopai': ['p4']}))
        assert h['hupai'] == [{'name': '場風 東', 'fanshu': 1},
                              {'name': 'ドラ', 'fanshu': 2}]

    def test_baopai_shoupai_one_fulou_one(self):
        h = hule(Shoupai.from_str('p55m23s789,m4-56,z111+'), 'm4=', param({'baopai': ['m3']}))
        assert h['hupai'] == [{'name': '場風 東', 'fanshu': 1},
                              {'name': 'ドラ', 'fanshu': 2}]

    def test_baopai_gang_one(self):
        h = hule(Shoupai.from_str('p55m234s78,m4-56,z111+'), 's9=', param({'baopai': ['s1', 'm2']}))
        assert h['hupai'] == [{'name': '場風 東', 'fanshu': 1},
                              {'name': 'ドラ', 'fanshu': 1}]

    def test_baopai_hongpai_two(self):
        h = hule(Shoupai.from_str('p50m234s78,m4-06,z111+'), 's9=', param({'baopai': ['s1']}))
        assert h['hupai'] == [{'name': '場風 東', 'fanshu': 1},
                              {'name': '赤ドラ', 'fanshu': 2}]

    def test_baopai_hongpai_double(self):
        h = hule(Shoupai.from_str('p55m234s78,m4-06,z111+'), 's9=', param({'baopai': ['m4']}))
        assert h['hupai'] == [{'name': '場風 東', 'fanshu': 1},
                              {'name': 'ドラ', 'fanshu': 1},
                              {'name': '赤ドラ', 'fanshu': 1}]

    def test_baopai_indicator_hongpai(self):
        h = hule(Shoupai.from_str('p55m234s78,m4-56,z111+'), 's9=', param({'baopai': ['m0']}))
        assert h['hupai'] == [{'name': '場風 東', 'fanshu': 1},
                              {'name': 'ドラ', 'fanshu': 1}]

    def test_baopai_fubaopai_none(self):
        h = hule(Shoupai.from_str('m344556s24678z66*'), 's3=', param({'lizhi': 1, 'baopai': ['s9'],
                                                                      'fubaopai': ['s9']}))
        assert h['hupai'] == [{'name': '立直', 'fanshu': 1}]

    def test_baopai_fubaopai_one(self):
        h = hule(Shoupai.from_str('m344556s24678z66*'), 's3=', param({'lizhi': 1, 'baopai': ['s9'],
                                                                      'fubaopai': ['m2']}))
        assert h['hupai'] == [{'name': '立直', 'fanshu': 1},
                              {'name': '裏ドラ', 'fanshu': 1}]

    def test_baopai_one_fubaopai_one(self):
        h = hule(Shoupai.from_str('m344556s24678z66*'), 's3=', param({'lizhi': 1, 'baopai': ['m2'],
                                                                      'fubaopai': ['m2']}))
        assert h['hupai'] == [{'name': '立直', 'fanshu': 1},
                              {'name': 'ドラ', 'fanshu': 1},
                              {'name': '裏ドラ', 'fanshu': 1}]

    def test_baopai_only(self):
        h = hule(Shoupai.from_str('m344556s24678z66'), 's3=', param({'baopai': ['m2']}))
        assert h['hupai'] is None

    def test_baopai_damanguan(self):
        h = hule(Shoupai.from_str('m119p19s19z1234567'), None, param({'baopai': ['m9']}))
        assert h['hupai'] == [{'name': '国士無双', 'fanshu': '*'}]


class TestHuleDefen:

    def test_20fu_2fan_child_zimo(self):
        h = hule(Shoupai.from_str('z33m123p456s789m234'), None, param())
        assert h == {'hupai': [{'name': '門前清自摸和', 'fanshu': 1},
                               {'name': '平和', 'fanshu': 1}],
                     'fu': 20, 'fanshu': 2, 'damanguan': None, 'defen': 1500,
                     'fenpei': [-700, 1500, -400, -400]}

    def test_20fu_3fan_parent_zimo(self):
        h = hule(Shoupai.from_str('z33m123p456s789m231'), None, param({'menfeng': 0}))
        assert h == {'hupai': [{'name': '門前清自摸和', 'fanshu': 1},
                               {'name': '平和', 'fanshu': 1},
                               {'name': '一盃口', 'fanshu': 1}],
                     'fu': 20, 'fanshu': 3, 'damanguan': None, 'defen': 3900,
                     'fenpei': [3900, -1300, -1300, -1300]}

    def test_20f_4fan_child_zimo(self):
        h = hule(Shoupai.from_str('z33m123p234s234m234'), None, param())
        assert h == {'hupai': [{'name': '門前清自摸和', 'fanshu': 1},
                               {'name': '平和', 'fanshu': 1},
                               {'name': '三色同順', 'fanshu': 2}],
                     'fu': 20, 'fanshu': 4, 'damanguan': None, 'defen': 5200,
                     'fenpei': [-2600, 5200, -1300, -1300]}

    def test_25fu_2fan_child_rong(self):
        h = hule(Shoupai.from_str('m1122p3344s5566z7'), 'z7-', param({'lizhibang': 1, 'changbang': 1}))
        assert h == {'hupai': [{'name': '七対子', 'fanshu': 2}],
                     'fu': 25, 'fanshu': 2, 'damanguan': None, 'defen': 1600,
                     'fenpei': [-1900, 2900, 0, 0]}

    def test_25fu_3fan_parent_zimo(self):
        h = hule(Shoupai.from_str('m1122p3344s5566z77'), None, param({'menfeng': 0, 'lizhibang': 1, 'changbang': 1}))
        assert h == {'hupai': [{'name': '門前清自摸和', 'fanshu': 1},
                               {'name': '七対子', 'fanshu': 2}],
                     'fu': 25, 'fanshu': 3, 'damanguan': None, 'defen': 4800,
                     'fenpei': [6100, -1700, -1700, -1700]}

    def test_25fu_4fan_child_zimo(self):
        h = hule(Shoupai.from_str('m2277p3344s556688'), None, param({'lizhibang': 1, 'changbang': 1}))
        assert h == {'hupai': [{'name': '門前清自摸和', 'fanshu': 1},
                               {'name': '断幺九', 'fanshu': 1},
                               {'name': '七対子', 'fanshu': 2}],
                     'fu': 25, 'fanshu': 4, 'damanguan': None, 'defen': 6400,
                     'fenpei': [-3300, 7700, -1700, -1700]}

    def test_30fu_1fan_parent_rong(self):
        h = hule(Shoupai.from_str('m77234p456s67,m34-5'), 's8=', param({'menfeng': 0}))
        assert h == {'hupai': [{'name': '断幺九', 'fanshu': 1}],
                     'fu': 30, 'fanshu': 1, 'damanguan': None, 'defen': 1500,
                     'fenpei': [1500, 0, -1500, 0]}

    def test_30fu_2fan_child_rong(self):
        h = hule(Shoupai.from_str('m77234p345s34,m34-5'), 's5-', param())
        assert h == {'hupai': [{'name': '断幺九', 'fanshu': 1},
                               {'name': '三色同順', 'fanshu': 1}],
                     'fu': 30, 'fanshu': 2, 'damanguan': None, 'defen': 2000,
                     'fenpei': [-2000, 2000, 0, 0]}

    def test_30fu_3fan_parent_zimo(self):
        h = hule(Shoupai.from_str('m22z111p445566s789'), None, param({'zhuangfeng': 1, 'menfeng': 0}))
        assert h == {'hupai': [{'name': '門前清自摸和', 'fanshu': 1},
                               {'name': '自風 東', 'fanshu': 1},
                               {'name': '一盃口', 'fanshu': 1}],
                     'fu': 30, 'fanshu': 3, 'damanguan': None, 'defen': 6000,
                     'fenpei': [6000, -2000, -2000, -2000]}

    def test_30fu_4fan_child_zimo(self):
        h = hule(Shoupai.from_str('m11z111p123789s789'), None, param())
        assert h == {'hupai': [{'name': '門前清自摸和', 'fanshu': 1},
                               {'name': '場風 東', 'fanshu': 1},
                               {'name': '混全帯幺九', 'fanshu': 2}],
                     'fu': 30, 'fanshu': 4, 'damanguan': None, 'defen': 7900,
                     'fenpei': [-3900, 7900, -2000, -2000]}

    def test_40fu_1fan_parent_rong(self):
        h = hule(Shoupai.from_str('m11234234p456s89'), 's7=', param({'menfeng': 0}))
        assert h == {'hupai': [{'name': '一盃口', 'fanshu': 1}],
                     'fu': 40, 'fanshu': 1, 'damanguan': None, 'defen': 2000,
                     'fenpei': [2000, 0, -2000, 0]}

    def test_40fu_2fan_child_rong(self):
        h = hule(Shoupai.from_str('m22334455p456s68'), 's7-', param())
        assert h == {'hupai': [{'name': '断幺九', 'fanshu': 1},
                               {'name': '一盃口', 'fanshu': 1}],
                     'fu': 40, 'fanshu': 2, 'damanguan': None, 'defen': 2600,
                     'fenpei': [-2600, 2600, 0, 0]}

    def test_40fu_3fan_parent_zimo(self):
        h = hule(Shoupai.from_str('z33222m222,s222=,p999+'), None, param({'zhuangfeng': 1, 'menfeng': 0}))
        assert h == {'hupai': [{'name': '場風 南', 'fanshu': 1},
                               {'name': '対々和', 'fanshu': 2}],
                     'fu': 40, 'fanshu': 3, 'damanguan': None, 'defen': 7800,
                     'fenpei': [7800, -2600, -2600, -2600]}

    def test_40fu_4fan_child_zimo(self):
        h = hule(Shoupai.from_str('z33222m222,s222=,p999+'), None, param({'zhuangfeng': 1}))
        assert h == {'hupai': [{'name': '場風 南', 'fanshu': 1},
                               {'name': '自風 南', 'fanshu': 1},
                               {'name': '対々和', 'fanshu': 2}],
                     'fu': 40, 'fanshu': 4, 'damanguan': None, 'defen': 8000,
                     'fenpei': [-4000, 8000, -2000, -2000]}

    def test_50fu_1fan_parent_rong(self):
        h = hule(Shoupai.from_str('m123p456s789z2227'), 'z7=', param({'zhuangfeng': 1, 'menfeng': 0}))
        assert h == {'hupai': [{'name': '場風 南', 'fanshu': 1}],
                     'fu': 50, 'fanshu': 1, 'damanguan': None, 'defen': 2400,
                     'fenpei': [2400, 0, -2400, 0]}

    def test_50fu_2fan_child_rong(self):
        h = hule(Shoupai.from_str('m123p456s789z2227'), 'z7-', param({'zhuangfeng': 1}))
        assert h == {'hupai': [{'name': '場風 南', 'fanshu': 1},
                               {'name': '自風 南', 'fanshu': 1}],
                     'fu': 50, 'fanshu': 2, 'damanguan': None, 'defen': 3200,
                     'fenpei': [-3200, 3200, 0, 0]}

    def test_50fu_3fan_parent_zimo(self):
        h = hule(Shoupai.from_str('z33m222z222,p8888,s789-'), None, param({'zhuangfeng': 1, 'menfeng': 0}))
        assert h == {'hupai': [{'name': '場風 南', 'fanshu': 1},
                               {'name': '三暗刻', 'fanshu': 2}],
                     'fu': 50, 'fanshu': 3, 'damanguan': None, 'defen': 9600,
                     'fenpei': [9600, -3200, -3200, -3200]}

    def test_50fu_4fan_child_zimo(self):
        h = hule(Shoupai.from_str('z33m222z222,p8888,s789-'), None, param({'zhuangfeng': 1}))
        assert h == {'hupai': [{'name': '場風 南', 'fanshu': 1},
                               {'name': '自風 南', 'fanshu': 1},
                               {'name': '三暗刻', 'fanshu': 2}],
                     'fu': 50, 'fanshu': 4, 'damanguan': None, 'defen': 8000,
                     'fenpei': [-4000, 8000, -2000, -2000]}

    def test_60fu_1fan_parent_rong(self):
        h = hule(Shoupai.from_str('s789z2227,m2222,p111='), 'z7=', param({'zhuangfeng': 1, 'menfeng': 0}))
        assert h == {'hupai': [{'name': '場風 南', 'fanshu': 1}],
                     'fu': 60, 'fanshu': 1, 'damanguan': None, 'defen': 2900,
                     'fenpei': [2900, 0, -2900, 0]}

    def test_60fu_2fan_child_rong(self):
        h = hule(Shoupai.from_str('s789z2227,m2222,p111='), 'z7-', param({'zhuangfeng': 1}))
        assert h == {'hupai': [{'name': '場風 南', 'fanshu': 1},
                               {'name': '自風 南', 'fanshu': 1}],
                     'fu': 60, 'fanshu': 2, 'damanguan': None, 'defen': 3900,
                     'fenpei': [-3900, 3900, 0, 0]}

    def test_60fu_3fan_parent_zimo(self):
        h = hule(Shoupai.from_str('m11222789,z2222,m444='), None, param({'zhuangfeng': 1, 'menfeng': 0}))
        assert h == {'hupai': [{'name': '場風 南', 'fanshu': 1},
                               {'name': '混一色', 'fanshu': 2}],
                     'fu': 60, 'fanshu': 3, 'damanguan': None, 'defen': 11700,
                     'fenpei': [11700, -3900, -3900, -3900]}

    def test_60fu_4fan_child_zimo(self):
        h = hule(Shoupai.from_str('m11222789,z2222,m444='), None, param({'zhuangfeng': 1}))
        assert h == {'hupai': [{'name': '場風 南', 'fanshu': 1},
                               {'name': '自風 南', 'fanshu': 1},
                               {'name': '混一色', 'fanshu': 2}],
                     'fu': 60, 'fanshu': 4, 'damanguan': None, 'defen': 8000,
                     'fenpei': [-4000, 8000, -2000, -2000]}

    def test_70fu_1fan_parent_rong(self):
        h = hule(Shoupai.from_str('m12377p456s78,z2222'), 's9=', param({'zhuangfeng': 1, 'menfeng': 0}))
        assert h == {'hupai': [{'name': '場風 南', 'fanshu': 1}],
                     'fu': 70, 'fanshu': 1, 'damanguan': None, 'defen': 3400,
                     'fenpei': [3400, 0, -3400, 0]}

    def test_70fu_2fan_child_rong(self):
        h = hule(Shoupai.from_str('m12377p456s78,z2222'), 's9-', param({'zhuangfeng': 1}))
        assert h == {'hupai': [{'name': '場風 南', 'fanshu': 1},
                               {'name': '自風 南', 'fanshu': 1}],
                     'fu': 70, 'fanshu': 2, 'damanguan': None, 'defen': 4500,
                     'fenpei': [-4500, 4500, 0, 0]}

    def test_70fu_3fan_parent_zimo(self):
        h = hule(Shoupai.from_str('p77s223344,z2222,m2222'), None, param({'zhuangfeng': 1, 'menfeng': 0}))
        assert h == {'hupai': [{'name': '門前清自摸和', 'fanshu': 1},
                               {'name': '場風 南', 'fanshu': 1},
                               {'name': '一盃口', 'fanshu': 1}],
                     'fu': 70, 'fanshu': 3, 'damanguan': None, 'defen': 12000,
                     'fenpei': [12000, -4000, -4000, -4000]}

    def test_80fu_1fan_parent_rong(self):
        h = hule(Shoupai.from_str('m22s888p34,z222+2,z4444'), 'p5=', param({'zhuangfeng': 1, 'menfeng': 0}))
        assert h == {'hupai': [{'name': '場風 南', 'fanshu': 1}],
                     'fu': 80, 'fanshu': 1, 'damanguan': None, 'defen': 3900,
                     'fenpei': [3900, 0, -3900, 0]}

    def test_80fu_2fan_child_rong(self):
        h = hule(Shoupai.from_str('m22s888p34,z222+2,z4444'), 'p5-', param({'zhuangfeng': 1}))
        assert h == {'hupai': [{'name': '場風 南', 'fanshu': 1},
                               {'name': '自風 南', 'fanshu': 1}],
                     'fu': 80, 'fanshu': 2, 'damanguan': None, 'defen': 5200,
                     'fenpei': [-5200, 5200, 0, 0]}

    def test_80fu_3fan_parent_zimo(self):
        h = hule(Shoupai.from_str('m11p999s123,z222+2,z1111'), None, param({'zhuangfeng': 1, 'menfeng': 0}))
        assert h == {'hupai': [{'name': '場風 南', 'fanshu': 1},
                               {'name': '自風 東', 'fanshu': 1},
                               {'name': '混全帯幺九', 'fanshu': 1}],
                     'fu': 80, 'fanshu': 3, 'damanguan': None, 'defen': 12000,
                     'fenpei': [12000, -4000, -4000, -4000]}

    def test_90fu_1fan_parent_rong(self):
        h = hule(Shoupai.from_str('p88m123s99,s6666,z2222'), 's9=', param({'zhuangfeng': 1, 'menfeng': 0}))
        assert h == {'hupai': [{'name': '場風 南', 'fanshu': 1}],
                     'fu': 90, 'fanshu': 1, 'damanguan': None, 'defen': 4400,
                     'fenpei': [4400, 0, -4400, 0]}

    def test_90fu_2fan_child_rong(self):
        h = hule(Shoupai.from_str('p88m123s99,s6666,z2222'), 's9-', param({'zhuangfeng': 1}))
        assert h == {'hupai': [{'name': '場風 南', 'fanshu': 1},
                               {'name': '自風 南', 'fanshu': 1}],
                     'fu': 90, 'fanshu': 2, 'damanguan': None, 'defen': 5800,
                     'fenpei': [-5800, 5800, 0, 0]}

    def test_90fu_3fan_parent_zimo(self):
        h = hule(Shoupai.from_str('m22s345,z5555,z2222,z666-'), None, param({'zhuangfeng': 1, 'menfeng': 0}))
        assert h == {'hupai': [{'name': '場風 南', 'fanshu': 1},
                               {'name': '翻牌 白', 'fanshu': 1},
                               {'name': '翻牌 發', 'fanshu': 1}],
                     'fu': 90, 'fanshu': 3, 'damanguan': None, 'defen': 12000,
                     'fenpei': [12000, -4000, -4000, -4000]}

    def test_100fu_1fan_parent_rong(self):
        h = hule(Shoupai.from_str('m22p345s67,z2222,s9999'), 's8=', param({'zhuangfeng': 1, 'menfeng': 0}))
        assert h == {'hupai': [{'name': '場風 南', 'fanshu': 1}],
                     'fu': 100, 'fanshu': 1, 'damanguan': None, 'defen': 4800,
                     'fenpei': [4800, 0, -4800, 0]}

    def test_100fu_2fan_child_rong(self):
        h = hule(Shoupai.from_str('m22p345s67,z2222,s9999'), 's8-', param({'zhuangfeng': 1}))
        assert h == {'hupai': [{'name': '場風 南', 'fanshu': 1},
                               {'name': '自風 南', 'fanshu': 1}],
                     'fu': 100, 'fanshu': 2, 'damanguan': None, 'defen': 6400,
                     'fenpei': [-6400, 6400, 0, 0]}

    def test_100fu_3fan_parent_zimo(self):
        h = hule(Shoupai.from_str('z11m999p243,s1111,s9999'), None, param({'zhuangfeng': 1, 'menfeng': 0}))
        assert h == {'hupai': [{'name': '門前清自摸和', 'fanshu': 1},
                               {'name': '三暗刻', 'fanshu': 2}],
                     'fu': 100, 'fanshu': 3, 'damanguan': None, 'defen': 12000,
                     'fenpei': [12000, -4000, -4000, -4000]}

    def test_110fu_1fan_parent_rong(self):
        h = hule(Shoupai.from_str('m234z1177,p1111,s9999'), 'z7=', param({'menfeng': 0}))
        assert h == {'hupai': [{'name': '翻牌 中', 'fanshu': 1}],
                     'fu': 110, 'fanshu': 1, 'damanguan': None, 'defen': 5300,
                     'fenpei': [5300, 0, -5300, 0]}

    def test_110fu_2fan_child_rong(self):
        h = hule(Shoupai.from_str('m234z2277,p1111,z5555'), 'z7-', param({'zhuangfeng': 1}))
        assert h == {'hupai': [{'name': '翻牌 白', 'fanshu': 1},
                               {'name': '翻牌 中', 'fanshu': 1}],
                     'fu': 110, 'fanshu': 2, 'damanguan': None, 'defen': 7100,
                     'fenpei': [-7100, 7100, 0, 0]}

    def test_110fu_3fan_parent_zimo(self):
        h = hule(Shoupai.from_str('m243z11,p1111,s9999,z555+5'), None, param({'zhuangfeng': 1, 'menfeng': 0}))
        assert h == {'hupai': [{'name': '翻牌 白', 'fanshu': 1},
                               {'name': '三槓子', 'fanshu': 2}],
                     'fu': 110, 'fanshu': 3, 'damanguan': None, 'defen': 12000,
                     'fenpei': [12000, -4000, -4000, -4000]}

    def test_5fan_parent_rong(self):
        h = hule(Shoupai.from_str('m22456p456s44556'), 's6=', param({'menfeng': 0}))
        assert h == {'hupai': [{'name': '平和', 'fanshu': 1},
                               {'name': '断幺九', 'fanshu': 1},
                               {'name': '一盃口', 'fanshu': 1},
                               {'name': '三色同順', 'fanshu': 2}],
                     'fu': 30, 'fanshu': 5, 'damanguan': None, 'defen': 12000,
                     'fenpei': [12000, 0, -12000, 0]}

    def test_6fan_child_zimo(self):
        h = hule(Shoupai.from_str('m22456p456s445566'), None, param())
        assert h == {'hupai': [{'name': '門前清自摸和', 'fanshu': 1},
                               {'name': '平和', 'fanshu': 1},
                               {'name': '断幺九', 'fanshu': 1},
                               {'name': '一盃口', 'fanshu': 1},
                               {'name': '三色同順', 'fanshu': 2}],
                     'fu': 20, 'fanshu': 6, 'damanguan': None, 'defen': 12000,
                     'fenpei': [-6000, 12000, -3000, -3000]}

    def test_7fan_parent_rong(self):
        h = hule(Shoupai.from_str('m111z3334,z222=,m999-'), 'z4=', param({'zhuangfeng': 1, 'menfeng': 0}))
        assert h == {'hupai': [{'name': '場風 南', 'fanshu': 1},
                               {'name': '対々和', 'fanshu': 2},
                               {'name': '混老頭', 'fanshu': 2},
                               {'name': '混一色', 'fanshu': 2}],
                     'fu': 50, 'fanshu': 7, 'damanguan': None, 'defen': 18000,
                     'fenpei': [18000, 0, -18000, 0]}

    def test_8fan_child_zimo(self):
        h = hule(Shoupai.from_str('m111z333444,z222=,m999-'), None, param({'zhuangfeng': 1}))
        assert h == {'hupai': [{'name': '場風 南', 'fanshu': 1},
                               {'name': '自風 南', 'fanshu': 1},
                               {'name': '対々和', 'fanshu': 2},
                               {'name': '混老頭', 'fanshu': 2},
                               {'name': '混一色', 'fanshu': 2}],
                     'fu': 50, 'fanshu': 8, 'damanguan': None, 'defen': 16000,
                     'fenpei': [-8000, 16000, -4000, -4000]}

    def test_9fan_parent_rong(self):
        h = hule(Shoupai.from_str('s2223334455567'), 's8=', param({'menfeng': 0}))
        assert h == {'hupai': [{'name': '断幺九', 'fanshu': 1},
                               {'name': '三暗刻', 'fanshu': 2},
                               {'name': '清一色', 'fanshu': 6}],
                     'fu': 50, 'fanshu': 9, 'damanguan': None, 'defen': 24000,
                     'fenpei': [24000, 0, -24000, 0]}

    def test_10fan_child_zimo(self):
        h = hule(Shoupai.from_str('s22233344555678'), None, param())
        assert h == {'hupai': [{'name': '門前清自摸和', 'fanshu': 1},
                               {'name': '断幺九', 'fanshu': 1},
                               {'name': '三暗刻', 'fanshu': 2},
                               {'name': '清一色', 'fanshu': 6}],
                     'fu': 40, 'fanshu': 10, 'damanguan': None, 'defen': 16000,
                     'fenpei': [-8000, 16000, -4000, -4000]}

    def test_11fan_parent_rong(self):
        h = hule(Shoupai.from_str('p2233445566778'), 'p8=', param({'menfeng': 0}))
        assert h == {'hupai': [{'name': '平和', 'fanshu': 1},
                               {'name': '断幺九', 'fanshu': 1},
                               {'name': '二盃口', 'fanshu': 3},
                               {'name': '清一色', 'fanshu': 6}],
                     'fu': 30, 'fanshu': 11, 'damanguan': None, 'defen': 36000,
                     'fenpei': [36000, 0, -36000, 0]}

    def test_12fan_child_zimo(self):
        h = hule(Shoupai.from_str('p22334455667788'), None, param())
        assert h == {'hupai': [{'name': '門前清自摸和', 'fanshu': 1},
                               {'name': '平和', 'fanshu': 1},
                               {'name': '断幺九', 'fanshu': 1},
                               {'name': '二盃口', 'fanshu': 3},
                               {'name': '清一色', 'fanshu': 6}],
                     'fu': 20, 'fanshu': 12, 'damanguan': None, 'defen': 24000,
                     'fenpei': [-12000, 24000, -6000, -6000]}

    def test_13fan_parent_rong(self):
        h = hule(Shoupai.from_str('m1177778888999'), 'm9=', param({'menfeng': 0}))
        assert h == {'hupai': [{'name': '平和', 'fanshu': 1},
                               {'name': '純全帯幺九', 'fanshu': 3},
                               {'name': '二盃口', 'fanshu': 3},
                               {'name': '清一色', 'fanshu': 6}],
                     'fu': 30, 'fanshu': 13, 'damanguan': None, 'defen': 48000,
                     'fenpei': [48000, 0, -48000, 0]}

    def test_damanguan_compound_no_rong(self):
        h = hule(Shoupai.from_str('z77111z444,z222+,z333-'), None, param())
        assert h == {'hupai': [{'name': '大四喜', 'fanshu': '**'},
                               {'name': '字一色', 'fanshu': '*'}],
                     'fu': None, 'fanshu': None, 'damanguan': 3, 'defen': 96000,
                     'fenpei': [-48000, 96000, -24000, -24000]}

    def test_damanguan_baojia_zimo(self):
        h = hule(Shoupai.from_str('m11p456,z555+,z666=,z777-'), None,
                 param({'menfeng': 0, 'lizhibang': 1, 'changbang': 1}))
        assert h == {'hupai': [{'name': '大三元', 'fanshu': '*', 'baojia': '-'}],
                     'fu': None, 'fanshu': None, 'damanguan': 1, 'defen': 48000,
                     'fenpei': [49300, 0, 0, -48300]}

    def test_damanguan_baojia_rong_half(self):
        h = hule(Shoupai.from_str('m11p45,z555+,z666=,z777-'), 'p6=',
                 param({'menfeng': 0, 'lizhibang': 1, 'changbang': 1}))
        assert h == {'hupai': [{'name': '大三元', 'fanshu': '*', 'baojia': '-'}],
                     'fu': None, 'fanshu': None, 'damanguan': 1, 'defen': 48000,
                     'fenpei': [49300, 0, -24300, -24000]}

    def test_damanguan_baojia_rong_all(self):
        h = hule(Shoupai.from_str('m11p45,z555+,z666=,z777-'), 'p6-',
                 param({'menfeng': 0, 'lizhibang': 1, 'changbang': 1}))
        assert h == {'hupai': [{'name': '大三元', 'fanshu': '*', 'baojia': '-'}],
                     'fu': None, 'fanshu': None, 'damanguan': 1, 'defen': 48000,
                     'fenpei': [49300, 0, 0, -48300]}

    def test_double_damanguan_baojia_zimo(self):
        h = hule(Shoupai.from_str('z77,z111-,z2222,z333=3,z444+'), None, param({'lizhibang': 1, 'changbang': 1}))
        assert h == {'hupai': [{'name': '大四喜', 'fanshu': '**', 'baojia': '+'},
                               {'name': '字一色', 'fanshu': '*'}],
                     'fu': None, 'fanshu': None, 'damanguan': 3, 'defen': 96000,
                     'fenpei': [-16100, 97300, -72100, -8100]}

    def test_double_damanguan_baojia_rong_half(self):
        h = hule(Shoupai.from_str('z7,z111-,z2222,z333=3,z444+'), 'z7-', param({'lizhibang': 1, 'changbang': 1}))
        assert h == {'hupai': [{'name': '大四喜', 'fanshu': '**', 'baojia': '+'},
                               {'name': '字一色', 'fanshu': '*'}],
                     'fu': None, 'fanshu': None, 'damanguan': 3, 'defen': 96000,
                     'fenpei': [-64300, 97300, -32000, 0]}

    def test_double_damanguan_baojia_rong_all(self):
        h = hule(Shoupai.from_str('z7,z111-,z2222,z333=3,z444+'), 'z7+', param({'lizhibang': 1, 'changbang': 1}))
        assert h == {'hupai': [{'name': '大四喜', 'fanshu': '**', 'baojia': '+'},
                               {'name': '字一色', 'fanshu': '*'}],
                     'fu': None, 'fanshu': None, 'damanguan': 3, 'defen': 96000,
                     'fenpei': [0, 97300, -96300, 0]}

    def test_compare_qiduizi_or_erbeiko(self):
        h = hule(Shoupai.from_str('m223344p556677s8'), 's8=', param())
        assert h == {'hupai': [{'name': '断幺九', 'fanshu': 1},
                               {'name': '二盃口', 'fanshu': 3}],
                     'fu': 40, 'fanshu': 4, 'damanguan': None, 'defen': 8000,
                     'fenpei': [0, 8000, 0, -8000]}

    def test_compare_two_jiangpai(self):
        h = hule(Shoupai.from_str('m2234455p234s234'), 'm3=', param())
        assert h == {'hupai': [{'name': '断幺九', 'fanshu': 1},
                               {'name': '一盃口', 'fanshu': 1},
                               {'name': '三色同順', 'fanshu': 2}],
                     'fu': 40, 'fanshu': 4, 'damanguan': None, 'defen': 8000,
                     'fenpei': [0, 8000, 0, -8000]}

    def test_compare_shunzi_or_kezi(self):
        h = hule(Shoupai.from_str('m111222333p8999'), 'p7=', param())
        assert h == {'hupai': [{'name': '一盃口', 'fanshu': 1},
                               {'name': '純全帯幺九', 'fanshu': 3}],
                     'fu': 40, 'fanshu': 4, 'damanguan': None, 'defen': 8000,
                     'fenpei': [0, 8000, 0, -8000]}

    def test_compare_kanzhang_or_ryanmenzi(self):
        h = hule(Shoupai.from_str('m12334p567z11z777'), 'm2=', param())
        assert h == {'hupai': [{'name': '翻牌 中', 'fanshu': 1}],
                     'fu': 50, 'fanshu': 1, 'damanguan': None, 'defen': 1600,
                     'fenpei': [0, 1600, 0, -1600]}

    def test_compare_fanshu(self):
        h = hule(Shoupai.from_str('m111222333p7899'), 'p9=', param())
        assert h == {'hupai': [{'name': '平和', 'fanshu': 1},
                               {'name': '一盃口', 'fanshu': 1},
                               {'name': '純全帯幺九', 'fanshu': 3}],
                     'fu': 30, 'fanshu': 5, 'damanguan': None, 'defen': 8000,
                     'fenpei': [0, 8000, 0, -8000]}

    def test_compare_fu(self):
        h = hule(Shoupai.from_str('s1112223335578'), 's9=', param())
        assert h == {'hupai': [{'name': '三暗刻', 'fanshu': 2},
                               {'name': '清一色', 'fanshu': 6}],
                     'fu': 50, 'fanshu': 8, 'damanguan': None, 'defen': 16000,
                     'fenpei': [0, 16000, 0, -16000]}

    def test_compare_damanguan(self):
        h = hule(Shoupai.from_str('m11123457899996'), None, param({'lizhi': 1, 'yifa': True, 'baopai': ['m2'],
                                                                   'fubaopai': ['m5']}))
        assert h == {'hupai': [{'name': '九蓮宝燈', 'fanshu': '*'}],
                     'fu': None, 'fanshu': None, 'damanguan': 1, 'defen': 32000,
                     'fenpei': [-16000, 32000, -8000, -8000]}

    def test_10000patterns(self, shared_datadir):
        with open(shared_datadir / 'hule.json', 'r', encoding='utf-8_sig') as f:
            data = json.load(f)
        for t in data:
            t['in']['param']['rule'] = rule()
            h = hule(Shoupai.from_str(t['in']['shoupai']), t['in'].get('rongpai'), t['in']['param'])
            assert h == t['out']


class TestRule:

    def test_no_fulou_danyaojiu(self):
        h = hule(Shoupai.from_str('m22555p234s78,p777-'),
                 's6=',
                 param({'rule': rule({'fulou_duanyaojiu': False})}))
        assert h.get('hupai') is None

    def test_menqian_danyaojiu(self):
        h = hule(Shoupai.from_str('m22555p234777s78'),
                 's6=',
                 param({'rule': rule({'fulou_duanyaojiu': False})}))
        assert h == {'hupai': [{'name': '断幺九', 'fanshu': 1}],
                     'fu': 40, 'fanshu': 1, 'damanguan': None, 'defen': 1300,
                     'fenpei': [0, 1300, 0, -1300]}

    def test_no_double_goushi_13men(self):
        h = hule(Shoupai.from_str('m19p19s19z1234567'),
                 'm1+',
                 param({'rule': rule({'double_damanguan': False})}))
        assert h == {'hupai': [{'name': '国士無双十三面', 'fanshu': '*'}],
                     'fu': None, 'fanshu': None, 'damanguan': 1, 'defen': 32000,
                     'fenpei': [0, 32000, -32000, 0]}

    def test_no_double_sianke_danqi(self):
        h = hule(Shoupai.from_str('m111p333s777z111m3'),
                 'm3=',
                 param({'rule': rule({'double_damanguan': False})}))
        assert h == {'hupai': [{'name': '四暗刻単騎', 'fanshu': '*'}],
                     'fu': None, 'fanshu': None, 'damanguan': 1, 'defen': 32000,
                     'fenpei': [0, 32000, 0, -32000]}

    def test_no_double_daisixi(self):
        h = hule(Shoupai.from_str('m22z22244,z333+,z111-'),
                 'z4=',
                 param({'rule': rule({'double_damanguan': False})}))
        assert h == {'hupai': [{'name': '大四喜', 'fanshu': '*'}],
                     'fu': None, 'fanshu': None, 'damanguan': 1, 'defen': 32000,
                     'fenpei': [0, 32000, 0, -32000]}

    def test_no_double_pure_jiulian(self):
        h = hule(Shoupai.from_str('m1112345678999'),
                 'm2=',
                 param({'rule': rule({'double_damanguan': False})}))
        assert h == {'hupai': [{'name': '純正九蓮宝燈', 'fanshu': '*'}],
                     'fu': None, 'fanshu': None, 'damanguan': 1, 'defen': 32000,
                     'fenpei': [0, 32000, 0, -32000]}

    def test_no_compound_double_baojia_zimo(self):
        h = hule(Shoupai.from_str('z77,z111-,z2222,z333=3,z444+'),
                 None,
                 param({'lizhibang': 1, 'changbang': 1,
                        'rule': rule({'compound_damanguan': False})}))
        assert h == {'hupai': [{'name': '大四喜', 'fanshu': '**', 'baojia': '+'},
                               {'name': '字一色', 'fanshu': '*'}],
                     'fu': None, 'fanshu': None, 'damanguan': 1, 'defen': 32000,
                     'fenpei': [0, 33300, -32300, 0]}

    def test_no_compound_double_baojia_rong(self):
        h = hule(Shoupai.from_str('z7,z111-,z2222,z333=3,z444+'),
                 'z7-',
                 param({'lizhibang': 1, 'changbang': 1,
                        'rule': rule({'compound_damanguan': False})}))
        assert h == {'hupai': [{'name': '大四喜', 'fanshu': '**', 'baojia': '+'},
                               {'name': '字一色', 'fanshu': '*'}],
                     'fu': None, 'fanshu': None, 'damanguan': 1, 'defen': 32000,
                     'fenpei': [-16300, 33300, -16000, 0]}

    def test_no_baojia_dasanyuan(self):
        h = hule(Shoupai.from_str('m2234,z555-5,z6666,z777+'),
                 'm5=',
                 param({'rule': rule({'damanguan_baojia': False})}))
        assert h == {'hupai': [{'name': '大三元', 'fanshu': '*'}],
                     'fu': None, 'fanshu': None, 'damanguan': 1, 'defen': 32000,
                     'fenpei': [0, 32000, 0, -32000]}

    def test_no_baojia_daisixi(self):
        h = hule(Shoupai.from_str('m2,z222+,z4444,z333+,z111-'),
                 'm2=',
                 param({'rule': rule({'damanguan_baojia': False})}))
        assert h == {'hupai': [{'name': '大四喜', 'fanshu': '**'}],
                     'fu': None, 'fanshu': None, 'damanguan': 2, 'defen': 64000,
                     'fenpei': [0, 64000, 0, -64000]}

    def test_no_countin_damanguan(self):
        h = hule(Shoupai.from_str('p22334455667788'),
                 None,
                 param({'lizhi': 1,
                        'rule': rule({'counting_damanguan': False})}))
        assert h == {'hupai': [{'name': '立直', 'fanshu': 1},
                               {'name': '門前清自摸和', 'fanshu': 1},
                               {'name': '平和', 'fanshu': 1},
                               {'name': '断幺九', 'fanshu': 1},
                               {'name': '二盃口', 'fanshu': 3},
                               {'name': '清一色', 'fanshu': 6}],
                     'fu': 20, 'fanshu': 13, 'damanguan': None, 'defen': 24000,
                     'fenpei': [-12000, 24000, -6000, -6000]}

    def test_ceiled_manguan_30fu_3fan_parent_zimo(self):
        h = hule(Shoupai.from_str('m22z111p445566s789'),
                 None,
                 param({'zhuangfeng': 1, 'menfeng': 0,
                        'rule': rule({'ceiled_manguan': True})}))
        assert h == {'hupai': [{'name': '門前清自摸和', 'fanshu': 1},
                               {'name': '自風 東', 'fanshu': 1},
                               {'name': '一盃口', 'fanshu': 1}],
                     'fu': 30, 'fanshu': 3, 'damanguan': None, 'defen': 6000,
                     'fenpei': [6000, -2000, -2000, -2000]}

    def test_ceiled_manguan_30fu_4fan_child_zimo(self):
        h = hule(Shoupai.from_str('m11z111p123789s789'),
                 None,
                 param({'rule': rule({'ceiled_manguan': True})}))
        assert h == {'hupai': [{'name': '門前清自摸和', 'fanshu': 1},
                               {'name': '場風 東', 'fanshu': 1},
                               {'name': '混全帯幺九', 'fanshu': 2}],
                     'fu': 30, 'fanshu': 4, 'damanguan': None, 'defen': 8000,
                     'fenpei': [-4000, 8000, -2000, -2000]}

    def test_ceiled_manguan_60fu_3fan_parent_zimo(self):
        h = hule(Shoupai.from_str('m11222789,z2222,m444='),
                 None,
                 param({'zhuangfeng': 1, 'menfeng': 0,
                        'rule': rule({'ceiled_manguan': True})}))
        assert h == {'hupai': [{'name': '場風 南', 'fanshu': 1},
                               {'name': '混一色', 'fanshu': 2}],
                     'fu': 60, 'fanshu': 3, 'damanguan': None, 'defen': 12000,
                     'fenpei': [12000, -4000, -4000, -4000]}
