import importlib.util
import unittest
from pathlib import Path

script = Path(__file__).resolve().parents[1] / 'scripts' / 'disi_reels_intake.py'
spec = importlib.util.spec_from_file_location('disi_reels_intake', script)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

class IntakeTests(unittest.TestCase):
    def setUp(self):
        self.brief = {'title': 'Test editorial', 'mode': 'promo', 'style': 'editorial',
                      'hook': 'Gancho', 'context': 'Contexto',
                      'evidence': 'Evidencia', 'cta': 'CTA'}
    def test_plan_is_review_only(self):
        p = mod.plan(self.brief)
        self.assertEqual(p['duration_s'], 12)
        self.assertEqual([s['start_s'] for s in p['scenes']], [0,3,7,10])
        self.assertFalse(p['publication_enabled'])
        self.assertIn('OUTRO_V6_ORIGINAL.mp4', p['original_assets_required'])
    def test_news_without_sources_blocked(self):
        self.brief['mode'] = 'news'
        with self.assertRaises(ValueError): mod.plan(self.brief)
    def test_news_claim_requires_source(self):
        self.brief.update(mode='news', sources=[{'id': 'a', 'title': 'A', 'url': 'https://example.org'}],
                          claims=[{'text': 'hecho', 'source_ids': ['b']}])
        with self.assertRaises(ValueError): mod.plan(self.brief)
        self.brief['claims'][0]['source_ids'] = ['a']
        self.assertEqual(mod.plan(self.brief)['mode'], 'news')
    def test_never_authorize_paid_or_publication(self):
        self.brief['authorize_payment'] = True
        with self.assertRaises(ValueError): mod.plan(self.brief)
        self.brief.pop('authorize_payment')
        self.brief['publish'] = True
        with self.assertRaises(ValueError): mod.plan(self.brief)
    def test_no_fake_presets(self):
        self.brief['style'] = 'fake_32_secret_command'
        with self.assertRaises(ValueError): mod.plan(self.brief)

if __name__ == '__main__':
    unittest.main()
