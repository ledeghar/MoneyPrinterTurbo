import importlib.util
import unittest
from datetime import datetime,timedelta,timezone
from unittest.mock import patch

path="scripts/mn_short_weekly_niche.py"
spec=importlib.util.spec_from_file_location("weekly_niche",path)
n=importlib.util.module_from_spec(spec)
spec.loader.exec_module(n)

NOW=datetime(2026,11,11,8,15,tzinfo=timezone.utc)

def v(key,views,creator,age=1):
    return {"id":key,"title":"AI breakthrough and news","views":views,
            "duration_seconds":55,"channel_id":creator,
            "published_at":(NOW-timedelta(days=age)).isoformat()}

class WeeklyNicheTests(unittest.TestCase):
    def test_duration(self):
        self.assertEqual(n.iso_seconds("PT55S"),55)
        self.assertEqual(n.iso_seconds("PT2M30S"),150)
        self.assertEqual(n.iso_seconds("PT3M1S"),181)

    def test_requires_two_separate_million_view_channels(self):
        self.assertEqual(n.rank_niches({"technology":[v("aaa",2300000,"one")]},NOW),[])
        self.assertEqual(n.rank_niches({"technology":[v("aaa",2300000,"one"),
                                                        v("bbb",1800000,"one")]},NOW),[])

    def test_rejects_stale_or_long_video(self):
        old=v("aaa",4000000,"one",age=9)
        long=v("bbb",2200000,"two")
        long["duration_seconds"]=241
        self.assertEqual(n.rank_niches({"technology":[old,long]},NOW),[])

    def test_no_arbitrary_winner_without_data(self):
        self.assertEqual(n.rank_niches({},NOW),[])

    def test_winner_based_on_verified_creator_and_views(self):
        data={"technology::ai news shorts":[v("a11",2000000,"one"),
                                             v("a22",4000000,"two")],
              "gaming::gaming news shorts":[v("b11",1400000,"one"),
                                              v("b22",1100000,"two")]}
        result=n.rank_niches(data,NOW)
        self.assertEqual(result[0]["topic"],"technology::ai news shorts")
        self.assertEqual(result[0]["independent_creators"],2)
        self.assertEqual(result[0]["total_views_7d"],6000000)

    def test_gather_preserves_specific_micro_niche_not_just_category(self):
        def fake_api(endpoint,args,credentials):
            if endpoint=="search":
                return {"items":[{"id":{"videoId":"123456789ab"}},
                                 {"id":{"videoId":"123456789ac"}}]}
            return {"items":[{"id":"123456789ab","snippet":{
                "title":"AI demonstration","channelId":"c1",
                "publishedAt":(NOW-timedelta(days=1)).isoformat()},
                "statistics":{"viewCount":"2000000"},
                "contentDetails":{"duration":"PT35S"}},
                {"id":"123456789ac","snippet":{
                "title":"AI explanation","channelId":"c2",
                "publishedAt":(NOW-timedelta(days=2)).isoformat()},
                "statistics":{"viewCount":"2500000"},
                "contentDetails":{"duration":"PT55S"}}]}
        with patch.object(n,"api",side_effect=fake_api):
            report=n.gather(NOW,({},{}))
        self.assertEqual(report["chosen"]["topic"],"technology")
        self.assertIn("niche_query",report["chosen"])
        self.assertEqual(report["chosen"]["viral_videos"],2)

if __name__=="__main__":
    unittest.main()
