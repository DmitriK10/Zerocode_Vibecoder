import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import unittest
from unittest.mock import patch, MagicMock

class TestAgent(unittest.TestCase):
    """Тесты для агента Haystack."""

    @patch('haystack_agent.OpenAIChatGenerator')
    @patch('haystack_agent.Agent')
    @patch('haystack_agent.ComponentTool')
    @patch('haystack_agent.Secret')
    def test_agent_run(self, mock_secret, mock_component_tool, mock_agent_cls, mock_chat_gen_cls):
        """Проверяет, что агент корректно формирует сообщения и вызывает run с контекстом."""
        print("\n🔍 Тест: работа агента с контекстом")
        mock_secret.from_token.return_value = "mock-secret"

        mock_chat_gen = MagicMock()
        mock_chat_gen_cls.return_value = mock_chat_gen

        mock_agent = MagicMock()
        mock_agent_cls.return_value = mock_agent
        mock_agent.run.return_value = {"last_message": MagicMock(text="Привет!")}

        from haystack_agent import HaystackAgent

        agent = HaystackAgent()
        response = agent.run("Привет", context=["контекст"])

        self.assertEqual(response, "Привет!")
        mock_agent.run.assert_called_once()
        args = mock_agent.run.call_args[1]
        messages = args['messages']
        self.assertEqual(len(messages), 2)
        self.assertEqual(messages[0].text, "контекст")
        self.assertEqual(messages[0]._role, "system")
        self.assertEqual(messages[1].text, "Привет")
        self.assertEqual(messages[1]._role, "user")
        print("✅ Агент корректно обработал контекст и пользовательский запрос")

if __name__ == '__main__':
    unittest.main()