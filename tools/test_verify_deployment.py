import io
import os
import unittest
from contextlib import redirect_stdout
from unittest.mock import patch
from urllib.error import URLError

import verify_deployment as smoke
import verify_sprint3_features as sprint3


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


class Sprint3SmokeTests(unittest.TestCase):
    base_url = "https://app.example"

    def setUp(self):
        self.viewer = {
            "username": "viewer",
            "display_name": "Test viewer",
            "role": "viewer",
            "email": None,
        }

    def test_profile_and_driver_directory_use_the_same_session(self):
        page = {"items": [], "page": 1, "page_size": 1, "total": 0, "summary": {}}
        with (
            patch.object(
                sprint3, "fetch_json", side_effect=[self.viewer, self.viewer, page, {}]
            ) as fetch,
            redirect_stdout(io.StringIO()) as output,
        ):
            sprint3.verify(self.base_url, "viewer", "synthetic")
        calls = [call.args for call in fetch.call_args_list]
        self.assertTrue(all(args[0] is calls[0][0] for args in calls))
        self.assertEqual(
            [args[2] for args in calls],
            [
                "/api/v1/auth/login",
                "/api/v1/auth/profile",
                "/api/v1/drivers/search",
                "/api/v1/auth/logout",
            ],
        )
        self.assertIn("PASS SCRUM-42 + SCRUM-49", output.getvalue())

    def test_incorrect_role_still_ends_the_session(self):
        with (
            patch.object(
                sprint3,
                "fetch_json",
                side_effect=[self.viewer, {**self.viewer, "role": "admin"}, {}],
            ) as fetch,
            self.assertRaises(ValueError),
        ):
            sprint3.verify(self.base_url, "viewer", "synthetic")
        self.assertEqual(fetch.call_args.args[2], "/api/v1/auth/logout")

    def test_missing_credentials_fail_without_network(self):
        with (
            patch.dict(
                os.environ,
                {"DEV_SPRINT3_SMOKE_USERNAME": "", "DEV_SPRINT3_SMOKE_PASSWORD": ""},
            ),
            patch.object(sprint3, "verify") as verify,
            redirect_stdout(io.StringIO()),
        ):
            self.assertEqual(sprint3.main(["--app-origin", self.base_url]), 1)
        verify.assert_not_called()


if __name__ == "__main__":
    unittest.main()
