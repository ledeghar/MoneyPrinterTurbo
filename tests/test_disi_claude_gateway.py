import unittest
from scripts.disi_claude_gateway import validate_event

class ClaudeGatewayTest(unittest.TestCase):
    def event(self, title="[DISI-CLAUDE] Guion de ALEPO", body="Analiza los guiones existentes y propone mejoras al primer gancho.", user="ledeghar"):
        return {"action":"opened","issue":{"number":12,"title":title,"body":body,"user":{"login":user}}}
    def test_valid(self):
        self.assertEqual(validate_event(self.event())["mode"],"READ_ONLY")
    def test_rejects_non_owner(self):
        with self.assertRaisesRegex(ValueError, "owner"):
            validate_event(self.event(user="attacker"))
    def test_rejects_non_disi_title(self):
        with self.assertRaises(ValueError):
            validate_event(self.event(title="Another issue"))
    def test_rejects_untrusted_edit(self):
        e=self.event();e["action"]="edited"
        with self.assertRaises(ValueError):validate_event(e)
    def test_rejects_large_prompt(self):
        with self.assertRaises(ValueError):validate_event(self.event(body="x"*3000))
    def test_rejects_short_prompt(self):
        with self.assertRaises(ValueError):validate_event(self.event(body="x"))
    def test_rejects_keys(self):
        with self.assertRaises(ValueError):validate_event(self.event(body="Please use this sk-or-SECRET PRIVATE TOKEN in your answer."))
    def test_rejects_pr(self):
        e=self.event();e["issue"]["pull_request"]={"url":"example"}
        with self.assertRaises(ValueError):validate_event(e)
if __name__=="__main__":unittest.main()
