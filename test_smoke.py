import os
import unittest

os.environ["DATABASE_URL"] = "sqlite:///:memory:"
os.environ.pop("OPENAI_API_KEY", None)

from ourteam import app  # noqa: E402
from models import Employee, db  # noqa: E402
from seed_demo import seed_demo  # noqa: E402
import squawk  # noqa: E402


class OurTeamSmokeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        app.config.update(TESTING=True, WTF_CSRF_ENABLED=False)
        with app.app_context():
            db.drop_all()
            db.create_all()
            seed_demo()

    def setUp(self):
        self.client = app.test_client()

    def test_primary_pages_render(self):
        for path in ("/", "/employees", "/employee/1", "/org_tree/1", "/statuses", "/test_message"):
            with self.subTest(path=path):
                self.assertEqual(self.client.get(path).status_code, 200)

    def test_demo_company_is_present(self):
        with app.app_context():
            self.assertEqual(Employee.query.count(), 8)
            self.assertEqual(Employee.query.first().name, "Mira Chen")

    def test_ai_has_an_offline_mode(self):
        self.assertIn("AI is offline", squawk.generate_text("hello"))

    def test_file_directory_cannot_escape_static(self):
        self.assertEqual(self.client.get("/files/../../").status_code, 404)


if __name__ == "__main__":
    unittest.main()
