import copy
import unittest

import build_history as bh


class AfricaHistoryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.ch = bh.read_json(bh.HISTORY_DIR + '/chapters/nok.json')
        cls.sources = bh.read_json(bh.SOURCES_PATH)
        cls.states, _, _ = bh.load_states()
        cls.emblems = bh.load_emblems()

    def sample(self):
        ch = copy.deepcopy(self.ch)
        ch['area'] = 'africa'
        ch['features'] = [ch['features'][0]]
        f = ch['features'][0]
        f['coordinates'] = [-20.27, 30.93]
        ch['scenes'] = [ch['scenes'][0]]
        sc = ch['scenes'][0]
        sc['show'] = [f['id']]
        sc['dim'] = []
        sc['when'] = {'from': 1400, 'to': 1450, 'label': '1400–1450 CE'}
        sc['camera'] = {'center': [0, 20], 'zoom': 2.6}
        return ch, f, sc

    def problems(self, ch):
        return bh.check([ch], self.sources, self.states, set(), self.emblems)

    def test_africa_area_accepts_southern_site_and_continent_camera(self):
        ch, _, _ = self.sample()
        self.assertEqual(self.problems(ch), [])

    def test_africa_area_does_not_weaken_nigeria_or_accept_london(self):
        ch, f, _ = self.sample()
        ch.pop('area')
        self.assertTrue(any('outside the map area' in p for p in self.problems(ch)))
        ch['area'] = 'africa'
        f['coordinates'] = [51.5, -0.1]
        self.assertTrue(any('outside the map area' in p for p in self.problems(ch)))

    def test_monument_date_must_cover_scene_and_have_source(self):
        ch, f, sc = self.sample()
        f['monument'] = {'type': 'tower', 'from': 1300, 'to': 1450,
                         'note': 'Original schematic of dated enclosure', 'sources': f['sources']}
        self.assertEqual(self.problems(ch), [])
        sc['when']['from'] = 1200
        self.assertTrue(any('monument' in p for p in self.problems(ch)))
        sc['when']['from'] = 1400
        f['monument']['sources'] = []
        self.assertTrue(any('source' in p for p in self.problems(ch)))

    def test_river_requires_mapped_geometry_and_not_rift_dates(self):
        ch, f, sc = self.sample()
        f.update(kind='line', type='river', path=[[9.09,-10.73],[16.4,-3.22],[4.29,6.08]])
        self.assertEqual(self.problems(ch), [])
        f['path'] = [[9.09,-10.73]]
        self.assertTrue(any('path' in p for p in self.problems(ch)))

    def test_unknown_scene_clock_is_rejected(self):
        ch, _, sc = self.sample()
        sc['clock'] = 'yesterday'
        self.assertTrue(any('clock' in p for p in self.problems(ch)))

    def test_architectural_setting_requires_supported_type(self):
        ch, f, sc = self.sample()
        f['monument'] = {'type':'tower','from':1300,'to':1450,'note':'Schematic enclosure',
                         'sources':f['sources'],'setting':'fantasy-castle'}
        self.assertTrue(any('setting' in p for p in self.problems(ch)))


if __name__ == '__main__':
    unittest.main()
