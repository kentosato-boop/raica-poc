import json
import tempfile
import threading
import unittest
import urllib.request
from http.server import ThreadingHTTPServer
from pathlib import Path

import server


class BackendTest(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = Path(self.temp_dir.name) / "raica-test.sqlite3"
        server.init_db(self.db_path)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_seeded_relations_are_consistent(self):
        counts = server.one(
            """SELECT
              (SELECT COUNT(*) FROM candidates) candidates,
              (SELECT COUNT(*) FROM jobs) jobs,
              (SELECT COUNT(*) FROM applications) applications""",
            db_path=self.db_path,
        )
        self.assertEqual(counts, {"candidates": 8, "jobs": 6, "applications": 5})

    def test_matching_recalculates_and_audits(self):
        matches = server.run_matching("job-c-cnc", "test-user", self.db_path)
        self.assertGreaterEqual(len(matches), 1)
        self.assertEqual(matches[0]["candidate_id"], "cand-huy")
        self.assertGreaterEqual(matches[0]["score"], 70)
        audit = server.one("SELECT actor, action FROM audit_logs ORDER BY id DESC LIMIT 1", db_path=self.db_path)
        self.assertEqual(audit, {"actor": "test-user", "action": "matching_run"})


class ApiTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp_dir = tempfile.TemporaryDirectory()
        cls.db_path = Path(cls.temp_dir.name) / "raica-api-test.sqlite3"
        server.init_db(cls.db_path)

        class TestHandler(server.Handler):
            db_path = cls.db_path

            def log_message(self, format, *args):
                pass

        cls.httpd = ThreadingHTTPServer(("127.0.0.1", 0), TestHandler)
        cls.base_url = f"http://127.0.0.1:{cls.httpd.server_port}"
        cls.thread = threading.Thread(target=cls.httpd.serve_forever, daemon=True)
        cls.thread.start()

    @classmethod
    def tearDownClass(cls):
        cls.httpd.shutdown()
        cls.httpd.server_close()
        cls.thread.join(timeout=2)
        cls.temp_dir.cleanup()

    def request(self, path, method="GET", payload=None):
        data = json.dumps(payload).encode() if payload is not None else None
        request = urllib.request.Request(
            self.base_url + path,
            data=data,
            method=method,
            headers={"Content-Type": "application/json"},
        )
        with urllib.request.urlopen(request) as response:
            return response.status, json.load(response)

    def test_dashboard_and_filters(self):
        status, dashboard = self.request("/api/dashboard")
        self.assertEqual(status, 200)
        self.assertEqual(dashboard["stats"]["jobs"], 6)
        _, candidates = self.request("/api/candidates?status=dormant")
        self.assertEqual([candidate["id"] for candidate in candidates], ["cand-dormant-1"])

    def test_match_approval_creates_application_and_audit(self):
        status, updated = self.request(
            "/api/matches/m-mai-a2",
            "PATCH",
            {"recommendation_status": "approved", "actor": "RA test"},
        )
        self.assertEqual(status, 200)
        self.assertEqual(updated["recommendation_status"], "approved")
        application = server.one(
            "SELECT stage FROM applications WHERE candidate_id='cand-mai' AND job_id='job-a-phase2'",
            db_path=self.db_path,
        )
        self.assertEqual(application["stage"], "recommended")

    def test_contact_requires_human_approval_and_completes_queue(self):
        status, result = self.request(
            "/api/contacts",
            "POST",
            {
                "candidate_id": "cand-hoa",
                "channel": "zalo",
                "body": "Follow-up message",
                "approved_by": "CA test",
                "queue_id": "q-ca-hoa",
            },
        )
        self.assertEqual(status, 201)
        self.assertTrue(result["recorded"])
        queue = server.one("SELECT status FROM action_queue WHERE id='q-ca-hoa'", db_path=self.db_path)
        self.assertEqual(queue["status"], "done")


if __name__ == "__main__":
    unittest.main()
