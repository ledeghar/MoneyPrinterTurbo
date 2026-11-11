import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
from disi_public_signals import collect,normalize,FEEDS
class TestDISIPublicSignals(unittest.TestCase):
 def test_offline_no_network(self):
  def blocked(url):raise AssertionError("network accessed")
  r=collect(False,blocked)
  self.assertEqual(r["items"],[])
  self.assertFalse(r["publication_enabled"])
 def test_usgs_provenance(self):
  r=normalize("USGS",{"features":[{"properties":{"title":"TEST","url":"https://earthquake.usgs.gov/a"}}]})
  self.assertEqual(len(r),1)
  self.assertEqual(r[0]["feed"],FEEDS["USGS"])
 def test_nasa_provenance(self):
  r=normalize("NASA_EONET",{"events":[{"title":"TEST","link":"https://eonet.gsfc.nasa.gov/1"}]})
  self.assertEqual(len(r),1)
  self.assertEqual(r[0]["provider"],"NASA EONET")
 def test_failure_is_visible(self):
  def fetch(url):
   if "earthquake" in url:raise ValueError("no internet")
   return {"events":[]}
  r=collect(True,fetch)
  self.assertEqual(len(r["errors"]),1)
  self.assertEqual(r["items"],[])
  self.assertFalse(r["publication_enabled"])
 def test_unknown_rejected(self):
  with self.assertRaises(ValueError):normalize("wrong",{})
if __name__=="__main__":unittest.main()
