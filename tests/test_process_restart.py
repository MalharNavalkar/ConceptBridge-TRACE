import os
import socket
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path
import httpx

ROOT = Path(__file__).resolve().parents[1]

def free_port():
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]

class ProcessRestartTests(unittest.TestCase):
    def test_user_data_survives_fastapi_process_restart(self):
        with tempfile.TemporaryDirectory(prefix="cbtrace-process-") as directory:
            db_path = Path(directory) / "persistent.sqlite3"
            url = f"sqlite:///{db_path}"
            port = free_port()
            base = f"http://127.0.0.1:{port}"
            email = f"restart-{os.urandom(5).hex()}@example.test"
            password = "restart-check-password-123"
            env = os.environ.copy()
            env.update(DATABASE_URL=url, COOKIE_SECURE="false", PYTHONUNBUFFERED="1")
            command = [sys.executable, "-m", "uvicorn", "app.main:app", "--host", "127.0.0.1", "--port", str(port)]
            process = None
            def start():
                p = subprocess.Popen(command, cwd=ROOT, env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                for _ in range(100):
                    if p.poll() is not None:
                        self.fail("FastAPI process exited before the HTTP health check")
                    try:
                        if httpx.get(base + "/api/health", timeout=0.5).status_code == 200:
                            return p
                    except httpx.HTTPError:
                        time.sleep(.1)
                p.terminate(); p.wait(timeout=5)
                self.fail("FastAPI process did not become healthy")
            def stop(p):
                if p and p.poll() is None:
                    p.terminate(); p.wait(timeout=10)
            try:
                process = start()
                with httpx.Client(base_url=base, timeout=10) as client:
                    csrf = client.get("/api/auth/csrf").json()["csrf_token"]
                    registered = client.post("/api/auth/register", json={"email":email,"password":password}, headers={"X-CSRF-Token":csrf})
                    self.assertEqual(registered.status_code, 201, registered.text)
                    csrf = registered.json()["csrf_token"]
                    from app.data.curriculum import question_bank
                    self.assertEqual(client.post("/api/lesson/complete", json={}, headers={"X-CSRF-Token":csrf}).status_code, 200)
                    half_bank = question_bank("half-adder", "en")
                    half_answers = [{"question_id":q["id"],"answer":q["correct"]} for q in half_bank]
                    self.assertEqual(client.post("/api/quiz/attempt", json={"lesson_slug":"half-adder","locale":"en","answers":half_answers}, headers={"X-CSRF-Token":csrf}).status_code, 200)
                    self.assertEqual(client.post("/api/lessons/full-adder/complete", json={}, headers={"X-CSRF-Token":csrf}).status_code, 200)
                    bank = question_bank("full-adder", "en")
                    answers = [{"question_id":q["id"],"answer":q["correct"]} for q in bank]
                    attempt = client.post("/api/quiz/attempt", json={"lesson_slug":"full-adder","locale":"en","answers":answers}, headers={"X-CSRF-Token":csrf})
                    self.assertEqual(attempt.status_code, 200, attempt.text)
                    self.assertEqual((attempt.json()["score"],attempt.json()["total"]),(3,3))
                    project = client.post("/api/projects/from-template", json={}, headers={"X-CSRF-Token":csrf})
                    self.assertEqual(project.status_code, 201, project.text)
                stop(process)
                process = start()
                with httpx.Client(base_url=base, timeout=10) as client:
                    csrf = client.get("/api/auth/csrf").json()["csrf_token"]
                    login = client.post("/api/auth/login", json={"email":email,"password":password}, headers={"X-CSRF-Token":csrf})
                    self.assertEqual(login.status_code, 200, login.text)
                    dashboard = client.get("/api/dashboard").json()
                    self.assertEqual(dashboard["attempt_count"], 2)
                    self.assertEqual(dashboard["lessons_completed"], 2)
                    self.assertEqual(len(dashboard["projects"]), 1)
                    self.assertEqual(dashboard["projects"][0]["progress"], 0)
                    self.assertIn({"slug":"full-adder","title":"Full Adder","opened":True,"completed":True,"attempt_count":1,"best_score":100}, [
                        {"slug":x["slug"],"title":x["title"],"opened":x["opened"],"completed":x["completed"],"attempt_count":x["attempt_count"],"best_score":x["best_score"]}
                        for x in dashboard["lessons"]])
            finally:
                stop(process)

if __name__ == "__main__": unittest.main()
