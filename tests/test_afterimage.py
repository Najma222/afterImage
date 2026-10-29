import unittest
from unittest.mock import patch

import app


class AfterimageApiTests(unittest.TestCase):
    def setUp(self):
        self.client = app.app.test_client()

    def test_empty_input_is_rejected(self):
        response = self.client.post("/api/reconstruct", json={"fragments": [], "tone": "nostalgic"})
        self.assertEqual(response.status_code, 400)
        self.assertFalse(response.get_json()["ok"])

    def test_invalid_tone_is_rejected(self):
        response = self.client.post("/api/reconstruct", json={"fragments": ["rain"], "tone": "triumphant"})
        self.assertEqual(response.status_code, 400)
        self.assertIn("tone", response.get_json()["error"].lower())

    def test_fragment_limits_are_rejected(self):
        too_many = self.client.post("/api/reconstruct", json={"fragments": ["x"] * 16, "tone": "hopeful"})
        too_long = self.client.post("/api/reconstruct", json={"fragments": ["x" * 161], "tone": "hopeful"})
        self.assertEqual(too_many.status_code, 400)
        self.assertEqual(too_long.status_code, 400)

    @patch("app.requests.post")
    def test_valid_payload_returns_model_memory(self, mock_post):
        mock_post.return_value.raise_for_status.return_value = None
        mock_post.return_value.json.return_value = {"message": {"content": "A quiet room remembered the rain."}}
        response = self.client.post("/api/reconstruct", json={"fragments": ["rain", "blue screen"], "tone": "nostalgic"})
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.get_json()["ok"])
        self.assertIn("quiet room", response.get_json()["memory"])

    @patch("app.requests.post", side_effect=app.requests.ConnectionError)
    def test_ollama_unavailable_is_not_faked(self, _mock_post):
        response = self.client.post("/api/reconstruct", json={"fragments": ["rain"], "tone": "eerie"})
        self.assertEqual(response.status_code, 503)
        self.assertFalse(response.get_json()["ok"])
        self.assertIn("unavailable", response.get_json()["error"].lower())

    @patch("app.requests.post")
    def test_timeout_is_reported(self, mock_post):
        mock_post.side_effect = app.requests.Timeout
        response = self.client.post("/api/reconstruct", json={"fragments": ["rain"], "tone": "hopeful"})
        self.assertEqual(response.status_code, 504)
        self.assertIn("long", response.get_json()["error"].lower())


if __name__ == "__main__":
    unittest.main()
