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
        for path in (
            "/", "/employees", "/employee/1", "/org_tree/1", "/statuses",
            "/recent_actions", "/manage_groups", "/view_group/1", "/leaderboard",
            "/employee/add", "/employee/1/add_image", "/employee/1/add_video",
            "/test_comment", "/test_message", "/files",
        ):
            with self.subTest(path=path):
                self.assertEqual(self.client.get(path).status_code, 200)

    def test_demo_company_is_present(self):
        with app.app_context():
            self.assertEqual(Employee.query.count(), 8)
            self.assertEqual(Employee.query.first().name, "Mira Chen")
            self.assertEqual(Employee.query.first().company, "OurTeam Industries")

    def test_profile_company_carries_into_add_employee(self):
        self.client.get("/employee/1")
        response = self.client.get("/employee/add")
        self.assertIn(b'value="OurTeam Industries"', response.data)
        self.assertIn(b'id="reports_to"', response.data)
        self.assertIn(b'value="1"', response.data)

    def test_directory_can_filter_by_company(self):
        with app.app_context():
            outsider = Employee(
                name="Morgan Elsewhere",
                title="Visiting Executive",
                company="Elsewhere LLC",
                department="Executive",
            )
            db.session.add(outsider)
            db.session.commit()
            outsider_id = outsider.id

        response = self.client.get("/employees?company=Elsewhere%20LLC")
        self.assertIn(b"Morgan Elsewhere", response.data)
        self.assertNotIn(b"Mira Chen", response.data)

        with app.app_context():
            Employee.query.filter_by(id=outsider_id).delete()
            db.session.commit()

    def test_ai_has_an_offline_mode(self):
        self.assertIn("AI is offline", squawk.generate_text("hello"))

    def test_file_directory_cannot_escape_static(self):
        self.assertEqual(self.client.get("/files/../../").status_code, 404)


if __name__ == "__main__":
    unittest.main()
