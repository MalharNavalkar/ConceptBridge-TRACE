import os
import tempfile
import unittest
from pathlib import Path
from fastapi.testclient import TestClient

_TEST_DIR = tempfile.TemporaryDirectory(prefix="cbtrace-test-")
_TEST_DB = Path(_TEST_DIR.name) / "accounts.sqlite3"
_TEST_URL = f"sqlite:///{_TEST_DB}"
os.environ["DATABASE_URL"] = _TEST_URL
os.environ["COOKIE_SECURE"] = "true"

from app.data.curriculum import BY_SLUG, LESSONS, LOCALES, public_question_list, question_bank
from app.data.quiz import QUESTIONS, diagnose, score_answers
from app.services.learning import half_adder
import app.database as database
from app.main import app


class HalfAdderTests(unittest.TestCase):
    def test_all_input_combinations(self):
        self.assertEqual([half_adder(a, b) for a, b in [(0,0),(0,1),(1,0),(1,1)]], [
            {"a":0,"b":0,"sum":0,"carry":0}, {"a":0,"b":1,"sum":1,"carry":0},
            {"a":1,"b":0,"sum":1,"carry":0}, {"a":1,"b":1,"sum":0,"carry":1}])
    def test_rejects_non_binary(self):
        with self.assertRaises(ValueError): half_adder(2, 0)


class CurriculumDataTests(unittest.TestCase):
    def test_nine_complete_localized_lessons_and_quizzes(self):
        self.assertEqual(len(LESSONS), 9)
        self.assertEqual(len(BY_SLUG), 9)
        for lesson in LESSONS:
            with self.subTest(lesson=lesson["slug"]):
                self.assertEqual(set(lesson["modes"]), set(LOCALES))
                self.assertGreaterEqual(len(lesson["quiz"]), 3)
                self.assertTrue(lesson["truth_tables"])
                self.assertTrue(lesson["sources"])
                for locale in LOCALES:
                    mode = lesson["modes"][locale]
                    self.assertTrue(mode["intro"])
                    self.assertGreaterEqual(len(mode["objectives"]), 3)
                    self.assertGreaterEqual(len(mode["sections"]), 2)
                    self.assertGreaterEqual(len(mode["worked_examples"]), 1)
                    self.assertTrue(mode["demo_instructions"])
                    bank = question_bank(lesson["slug"], locale)
                    self.assertEqual(len(bank), 3)
                    for question in bank:
                        self.assertTrue(question["prompt"])
                        self.assertGreaterEqual(len(question["options"]), 3)
                        self.assertTrue(question["correct_why"])
                        self.assertTrue(question["followup"])

    def test_truth_tables_gate_adders_mux_encoder_decoder(self):
        gates = BY_SLUG["logic-gates"]["truth_tables"][0]
        self.assertEqual(gates["rows"], [[0,0,0,0,1,1,0,1],[0,1,0,1,1,0,1,0],[1,0,0,1,1,0,1,0],[1,1,1,1,0,0,0,1]])
        binary = BY_SLUG["binary-numbers"]["truth_tables"][0]["rows"]
        self.assertEqual(binary, [["0000","0","0"],["0101","4+1","5"],["1010","8+2","10"],["1101","8+4+1","13"]])
        boolean = BY_SLUG["boolean-algebra"]["truth_tables"]
        self.assertTrue(all(row[3] == row[4] for row in boolean[0]["rows"]))
        self.assertTrue(all(row[2] == row[3] for row in boolean[1]["rows"]))
        half = BY_SLUG["half-adder"]["truth_tables"][0]["rows"]
        self.assertEqual(half, [[0,0,0,0],[0,1,1,0],[1,0,1,0],[1,1,0,1]])
        full = BY_SLUG["full-adder"]["truth_tables"][0]["rows"]
        for row in full:
            a,b,cin,s,cout = row
            self.assertEqual(s, a ^ b ^ cin)
            self.assertEqual(cout, (a & b) | (a & cin) | (b & cin))
        mux = BY_SLUG["mux-demux"]["truth_tables"]
        self.assertEqual([r[2] for r in mux[0]["rows"]], ["D0","D1","D2","D3"])
        self.assertEqual([r[3] for r in mux[0]["rows"]], [0,1,0,1])
        self.assertEqual([r[2:] for r in mux[1]["rows"]], [[1,0,0,0],[0,1,0,0],[0,0,1,0],[0,0,0,1]])
        enc_tables = BY_SLUG["encoders-decoders"]["truth_tables"]
        enc = enc_tables[0]["rows"]
        self.assertEqual([r[-4:] for r in enc], [[1,0,0,0],[0,1,0,0],[0,0,1,0],[0,0,0,1]])
        self.assertEqual([r[1] for r in enc], ["00","01","10","11"])

    def test_sequential_characteristic_tables(self):
        tables = BY_SLUG["flip-flops"]["truth_tables"]
        self.assertEqual(tables[0]["rows"], [[0,0,"Q (hold)"],[0,1,0],[1,0,1],[1,1,"Invalid"]])
        jk = tables[1]["rows"]
        for q,j,k,next_q in jk:
            expected = q if (j,k)==(0,0) else 0 if (j,k)==(0,1) else 1 if (j,k)==(1,0) else 1-q
            self.assertEqual(next_q, expected)
        dtable = tables[2]["rows"]
        self.assertTrue(all(qnext == d for _,d,qnext in dtable))
        ttable = tables[3]["rows"]
        self.assertTrue(all(qnext == (q ^ t) for q,t,qnext in ttable))
        counter = BY_SLUG["counters-registers"]["truth_tables"][0]["rows"]
        self.assertEqual(len(counter), 16)
        for current, next_state in counter:
            value = int(current, 2)
            self.assertEqual(next_state, format((value + 1) % 16, "04b") if value < 15 else "0000 (wrap)")
        self.assertEqual(counter[0], ["0000","0001"])
        self.assertEqual(counter[7], ["0111","1000"])
        self.assertEqual(counter[-1], ["1111","0000 (wrap)"])

    def test_public_quiz_hides_answer_key_and_each_bank_scores(self):
        for slug in BY_SLUG:
            bank = question_bank(slug, "en")
            safe = public_question_list(slug, "en")
            self.assertTrue(all("correct" not in q and "misconceptions" not in q for q in safe))
            result = score_answers([{"question_id":q["id"],"answer":q["correct"]} for q in bank], questions=bank)
            self.assertEqual((result["score"],result["total"]),(3,3),slug)
            wrong = next(i for i in range(len(bank[0]["options"])) if i != bank[0]["correct"])
            diagnostic = score_answers([{"question_id":bank[0]["id"],"answer":wrong}], questions=bank)["results"][0]
            self.assertFalse(diagnostic["correct"])
            self.assertTrue(diagnostic["category"])
            self.assertTrue(diagnostic["followup"])


class LegacyQuizTests(unittest.TestCase):
    def test_score_and_misconception(self):
        result = score_answers([{"question_id":"q1","answer":0},{"question_id":"q2","answer":2}])
        self.assertEqual((result["score"],result["total"]),(1,2))
        cue = diagnose(next(q for q in QUESTIONS if q["id"]=="q2"),2)
        self.assertEqual(cue["category"],"Confusing XOR with OR")
        self.assertTrue(cue["followup"])
    def test_invalid_question_and_choice(self):
        with self.assertRaises(ValueError): score_answers([{"question_id":"bad","answer":0}])
        with self.assertRaises(ValueError): score_answers([{"question_id":"q1","answer":20}])


class PasswordTests(unittest.TestCase):
    def test_scrypt_hash_and_verification(self):
        from app.services.auth import hash_password, verify_password
        hashed = hash_password("a-long-enough-test-password")
        self.assertNotEqual(hashed, "a-long-enough-test-password")
        self.assertTrue(hashed.startswith("scrypt$"))
        self.assertTrue(verify_password("a-long-enough-test-password", hashed))
        self.assertFalse(verify_password("wrong-password", hashed))


class AccountIsolationTests(unittest.TestCase):
    def test_registration_learning_workflow_isolation_and_reconnect(self):
        base = "https://testserver"
        with TestClient(app, base_url=base) as alice, TestClient(app, base_url=base) as bob:
            self.assertEqual(alice.get("/api/health").json()["status"], "ok")
            self.assertIn("max-age=31536000", alice.get("/").headers.get("strict-transport-security", ""))
            self.assertEqual(alice.get("/api/lessons").status_code,401)
            csrf_a = alice.get("/api/auth/csrf").json()["csrf_token"]
            self.assertEqual(alice.get("/api/auth/me").status_code,401)
            csrf_a = alice.get("/api/auth/csrf").json()["csrf_token"]
            registration = alice.post("/api/auth/register",json={"email":"ALICE@example.test","password":"alice-password-123"},headers={"X-CSRF-Token":csrf_a})
            self.assertEqual(registration.status_code,201,registration.text)
            self.assertNotIn("password", registration.text.lower())
            self.assertEqual(registration.json()["user"]["email"],"alice@example.test")
            cookie = registration.headers.get("set-cookie","").lower()
            self.assertIn("httponly",cookie)
            self.assertIn("secure",cookie)
            token_a = registration.json()["csrf_token"]
            self.assertEqual(alice.get("/api/dashboard").status_code,200)
            self.assertEqual(alice.post("/api/projects",json={"title":"no csrf"}).status_code,403)

            catalog = alice.get("/api/lessons").json()
            self.assertEqual(catalog["lesson_count"],9)
            self.assertEqual(len(catalog["groups"]),3)
            detail = alice.get("/api/lessons/full-adder").json()
            self.assertEqual(detail["modes"]["hi"]["title"],"फुल ऐडर")
            quiz_response = alice.get("/api/quiz?lesson_slug=full-adder&locale=hi").json()
            self.assertEqual(len(quiz_response["questions"]),3)
            self.assertTrue(all("correct" not in q for q in quiz_response["questions"]))
            self.assertEqual(alice.post("/api/lessons/full-adder/open",json={},headers={"X-CSRF-Token":token_a}).status_code,200)
            self.assertEqual(alice.post("/api/lessons/full-adder/complete",json={},headers={"X-CSRF-Token":token_a}).status_code,200)
            course_bank = question_bank("full-adder","hi")
            answers = [{"question_id":q["id"],"answer":q["correct"]} for q in course_bank]
            course_attempt = alice.post("/api/quiz/attempt",json={"lesson_slug":"full-adder","locale":"hi","answers":answers},headers={"X-CSRF-Token":token_a})
            self.assertEqual(course_attempt.status_code,200,course_attempt.text)
            self.assertEqual((course_attempt.json()["score"],course_attempt.json()["total"]),(3,3))
            self.assertEqual(course_attempt.json()["lesson_slug"],"full-adder")

            # Preserve the existing Half Adder completion and assess its course-specific quiz.
            self.assertEqual(alice.post("/api/lesson/complete",json={},headers={"X-CSRF-Token":token_a}).status_code,200)
            half_bank = question_bank("half-adder", "en")
            half_answers = [{"question_id":q["id"],"answer":q["correct"]} for q in half_bank]
            attempt = alice.post("/api/quiz/attempt",json={"lesson_slug":"half-adder","locale":"en","answers":half_answers},headers={"X-CSRF-Token":token_a})
            self.assertEqual(attempt.status_code,200,attempt.text)
            self.assertEqual((attempt.json()["score"],attempt.json()["total"]),(3,3))
            created = alice.post("/api/projects/from-template",json={},headers={"X-CSRF-Token":token_a})
            self.assertEqual(created.status_code,201,created.text)
            project = created.json(); task_id = project["tasks"][0]["id"]
            self.assertEqual((project["total"],project["progress"]),(4,0))

            csrf_b = bob.get("/api/auth/csrf").json()["csrf_token"]
            reg_b = bob.post("/api/auth/register",json={"email":"bob@example.test","password":"bob-password-123"},headers={"X-CSRF-Token":csrf_b})
            self.assertEqual(reg_b.status_code,201,reg_b.text)
            token_b = reg_b.json()["csrf_token"]
            dash_b = bob.get("/api/dashboard").json()
            self.assertEqual(dash_b["attempt_count"],0)
            self.assertEqual(dash_b["lessons_completed"],0)
            self.assertFalse(dash_b["lesson"]["completed"])
            self.assertEqual(dash_b["projects"],[])
            self.assertEqual(bob.get("/api/projects").json(),[])
            self.assertFalse(bob.get("/api/lessons/full-adder").json()["completed"])
            self.assertEqual(bob.post(f"/api/projects/{project['id']}/tasks",json={"title":"intrude"},headers={"X-CSRF-Token":token_b}).status_code,404)
            self.assertEqual(bob.patch(f"/api/tasks/{task_id}",json={"done":True},headers={"X-CSRF-Token":token_b}).status_code,404)

            updated = alice.patch(f"/api/tasks/{task_id}",json={"done":True},headers={"X-CSRF-Token":token_a})
            self.assertEqual(updated.status_code,200,updated.text)
            self.assertEqual(alice.get("/api/projects").json()[0]["progress"],25)
            self.assertEqual(bob.get("/api/dashboard").json()["projects"],[])

            # Recreate the engine as a restart/reconnect simulation; per-user learning and attempts persist.
            database.configure_engine(database.make_engine(_TEST_URL))
            dashboard = alice.get("/api/dashboard").json()
            self.assertEqual(dashboard["attempt_count"],2)
            self.assertEqual(dashboard["lessons_completed"],2)
            self.assertEqual(dashboard["lessons"][4]["slug"],"full-adder")
            self.assertTrue(dashboard["lessons"][4]["completed"])
            self.assertEqual(alice.get("/api/projects").json()[0]["progress"],25)
            with TestClient(app,base_url=base) as restarted:
                csrf = restarted.get("/api/auth/csrf").json()["csrf_token"]
                login = restarted.post("/api/auth/login",json={"email":"alice@example.test","password":"alice-password-123"},headers={"X-CSRF-Token":csrf})
                self.assertEqual(login.status_code,200,login.text)
                self.assertEqual(login.json()["user"]["email"],"alice@example.test")
                self.assertEqual(restarted.get("/api/dashboard").json()["attempt_count"],2)
                self.assertEqual(restarted.post("/api/auth/logout",json={},headers={"X-CSRF-Token":login.json()["csrf_token"]}).status_code,204)
                self.assertEqual(restarted.get("/api/dashboard").status_code,401)


if __name__ == "__main__": unittest.main()
