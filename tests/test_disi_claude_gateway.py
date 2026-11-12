import unittest
from scripts.disi_claude_gateway import validate_request

class ClaudeGatewayTest(unittest.TestCase):
    def event(self,user="ledeghar",repo="ledeghar/MoneyPrinterTurbo",title="[DISI-CLAUDE] Audit repo",action="opened"):
        return {"action":action,"pull_request":{"number":39,"title":title,"user":{"login":user},"head":{"repo":{"full_name":repo}}}}
    def request(self,task="Revisa el sistema de videos y documenta los errores sin editar archivos."):
        return {"schema":"disi-claude-task/1","approved_by":"ledeghar","mode":"READ_ONLY","request_id":"trial-001","task":task,"publish":False,"spend":False}
    def test_valid(self):
        self.assertEqual(validate_request(self.event(),self.request())["number"],39)
    def test_non_owner_blocked(self):
        with self.assertRaisesRegex(ValueError,"owner"):validate_request(self.event(user="outsider"),self.request())
    def test_fork_blocked(self):
        with self.assertRaisesRegex(ValueError,"Fork"):validate_request(self.event(repo="external/fork"),self.request())
    def test_title_required(self):
        with self.assertRaises(ValueError):validate_request(self.event(title="random PR"),self.request())
    def test_action_required(self):
        with self.assertRaises(ValueError):validate_request(self.event(action="edited"),self.request())
    def test_small_prompt_blocked(self):
        with self.assertRaises(ValueError):validate_request(self.event(),self.request(task="hi"))
    def test_large_prompt_blocked(self):
        with self.assertRaises(ValueError):validate_request(self.event(),self.request(task="x"*3000))
    def test_key_detected(self):
        with self.assertRaises(ValueError):validate_request(self.event(),self.request(task="Use this sk-or-secret-token somewhere public."))
    def test_publish_blocked(self):
        r=self.request();r["publish"]=True
        with self.assertRaises(ValueError):validate_request(self.event(),r)
    def test_paid_blocked(self):
        r=self.request();r["spend"]=True
        with self.assertRaises(ValueError):validate_request(self.event(),r)
    def test_approval_required(self):
        r=self.request();r["approved_by"]="someoneelse"
        with self.assertRaises(ValueError):validate_request(self.event(),r)
if __name__=="__main__":unittest.main()
