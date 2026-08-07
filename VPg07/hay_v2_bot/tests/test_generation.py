import unittest
from unittest.mock import patch, MagicMock
from pipelines.generation import generate_response

class TestGeneration(unittest.TestCase):
    @patch("pipelines.generation.OpenAI")
    def test_generate_response(self, mock_openai):
        # Создаём мок ответа
        mock_client = MagicMock()
        mock_completion = MagicMock()
        mock_completion.choices = [MagicMock(message=MagicMock(content="Ответ бота"))]
        mock_client.chat.completions.create.return_value = mock_completion
        mock_openai.return_value = mock_client

        result = generate_response("Как дела?", ["Контекст: всё хорошо"])
        self.assertEqual(result, "Ответ бота")
        mock_client.chat.completions.create.assert_called_once()
        args, kwargs = mock_client.chat.completions.create.call_args
        self.assertEqual(kwargs["model"], "gpt-3.5-turbo-16k")  # из конфига
        self.assertIn("Контекст:", kwargs["messages"][0]["content"])