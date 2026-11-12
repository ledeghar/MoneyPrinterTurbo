from pathlib import Path
import unittest
ROOT=Path(__file__).resolve().parents[1]
class ClaudeBookAgents(unittest.TestCase):
    def test_subagent_structure(self):
        agents=list((ROOT/'.claude/agents').glob('disi-*.md'))
        self.assertEqual(len(agents),5)
        for f in agents:
            s=f.read_text(encoding='utf-8')
            self.assertTrue(s.startswith('---\n'),f.name)
            self.assertIn('\nname: ',s)
            self.assertIn('\ndescription: ',s)
            self.assertIn('\ntools: Read, Grep, Glob\n',s)
            self.assertTrue(len(s.split('---',2)[-1].strip())>100)
    def test_skill_and_policy(self):
        s=(ROOT/'.claude/skills/disi-books/SKILL.md').read_text()
        self.assertIn('disi-video-release-auditor',s)
        self.assertIn('disi-book-scriptwriter',s)
        policy=(ROOT/'CLAUDE.md').read_text()
        self.assertIn('10 audio languages',policy)
        self.assertIn('Shorts',policy)
    def test_no_secrets_or_publish_actions(self):
        paths=list((ROOT/'.claude').rglob('*'))
        self.assertTrue(all(not p.name.startswith('.env') for p in paths))
        text='\n'.join(p.read_text(encoding='utf-8') for p in paths if p.is_file())
        self.assertNotIn('ANTHROPIC_API_KEY=',text)
        self.assertIn('Do not publish',text)
if __name__=='__main__': unittest.main()