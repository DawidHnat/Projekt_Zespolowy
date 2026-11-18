import io
import unittest
from contextlib import redirect_stdout
from unittest.mock import patch
from urllib.error import URLError

import verify_deployment as smoke


class DeploymentTests(unittest.TestCase):
    def run_check(self, responses, sha="abcdef0123456789012345678901234567890123"):
        with (
            patch.object(smoke, "fetch", side_effect=responses) as fetch,
            redirect_stdout(io.StringIO()) as output,
        ):
            result = smoke.main(
                [
                    "--sha",
                    sha,
                    "--status-origin",
                    "http://status.example",
                    "--app-origin",
                    "https://app.example",
                ]
            )
        return result, output.getvalue(), fetch

    def test_exact_release_and_readiness_pass_and_log_seven_characters(self):
        page = '<code data-build-sha="abcdef0">abcdef0</code>'
        result, output, fetch = self.run_check([page, page, '{"status":"ok"}'])
        self.assertEqual(result, 0)
        self.assertIn("PASS deployed SHA abcdef0", output)
        self.assertEqual(
            fetch.call_args_list[-1].args, ("https://app.example/api/health/ready",)
        )

    def test_wrong_http_release_fails_even_when_expected_sha_is_in_comment(self):
        result, _, fetch = self.run_check(
            ['<!-- abcdef0 --><code data-build-sha="0000000">']
        )
        self.assertEqual(result, 1)
        self.assertEqual(fetch.call_count, 1)

    def test_https_application_must_match_http_status(self):
        result, _, _ = self.run_check(
            ['<code data-build-sha="abcdef0">', '<code data-build-sha="0000000">']
        )
        self.assertEqual(result, 1)

    def test_missing_marker_cannot_pass(self):
        self.assertEqual(self.run_check(["abcdef0"])[0], 1)

    def test_conflicting_markers_cannot_pass(self):
        self.assertEqual(
            self.run_check(
                ['<b data-build-sha="abcdef0"><b data-build-sha="0000000">']
            )[0],
            1,
        )

    def test_unavailable_api_fails_and_does_not_log_response_details(self):
        page = '<code data-build-sha="abcdef0">'
        result, output, _ = self.run_check(
            [page, page, URLError("private response details")]
        )
        self.assertEqual(result, 1)
        self.assertNotIn("private response", output)

    def test_timeout_fails(self):
        self.assertEqual(self.run_check([TimeoutError()])[0], 1)

    def test_readiness_requires_the_api_success_response(self):
        page = '<code data-build-sha="abcdef0">'
        for body in (page, '{"status":"unavailable"}', '["ok"]', "{}"):
            with self.subTest(body=body):
                self.assertEqual(self.run_check([page, page, body])[0], 1)

    def test_redirect_to_another_endpoint_cannot_pass(self):
        with patch.object(smoke, "urlopen") as opener:
            response = opener.return_value.__enter__.return_value
            response.status = 200
            response.geturl.return_value = "https://app.example/"
            with self.assertRaises(ValueError):
                smoke.fetch("http://status.example/")

    def test_invalid_sha_does_not_request_network(self):
        result, _, fetch = self.run_check([], sha="not-a-sha")
        self.assertEqual(result, 1)
        fetch.assert_not_called()

    def test_origin_rejects_credentials_and_insecure_application(self):
        with self.assertRaises(ValueError):
            smoke.origin("https://user:password@app.example")
        with self.assertRaises(ValueError):
            smoke.origin("http://app.example", https=True)

    def test_non_200_response_fails(self):
        with patch.object(smoke, "urlopen") as opener:
            opener.return_value.__enter__.return_value.status = 503
            with self.assertRaises(ValueError):
                smoke.fetch("https://app.example/")


if __name__ == "__main__":
    unittest.main()
