import os
import unittest


os.environ["OPENROUTER_API_KEY"] = ""

from app_factory import create_app
from models import Action, Comment, Employee, EmployeeXP, db
from services import markdown_to_html, nl2br


class IsolatedBehaviorTests(unittest.TestCase):
    """Focused request-level tests for employee CRUD and social behavior."""

    @classmethod
    def setUpClass(cls):
        cls.app = create_app(
            {
                "TESTING": True,
                "WTF_CSRF_ENABLED": False,
                "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
                "DEFAULT_COMPANY": "Test Company",
            }
        )
        cls.app_context = cls.app.app_context()
        cls.app_context.push()
        db.create_all()

    @classmethod
    def tearDownClass(cls):
        db.session.remove()
        cls.app_context.pop()

    def setUp(self):
        db.drop_all()
        db.create_all()
        self.manager = Employee(
            name="Mira Manager",
            title="Director",
            company="Test Company",
            department="Operations",
            email="mira@test.local",
        )
        self.employee = Employee(
            name="Alex Employee",
            title="Engineer",
            company="Test Company",
            department="Product",
            email="alex@test.local",
            reports_to=None,
            bio="Original bio",
            location="Boston",
        )
        db.session.add_all([self.manager, self.employee])
        db.session.commit()
        self.client = self.app.test_client()

    def test_add_employee_persists_employee_and_action(self):
        response = self.client.post(
            "/employee/add",
            data={
                "name": "New Hire",
                "title": "Researcher",
                "company": "Test Company",
                "department": "Research",
                "email": "new@test.local",
                "reports_to": str(self.manager.id),
                "bio": "A useful biography",
                "location": "Denver",
                "submit": "Submit",
            },
        )

        self.assertEqual(response.status_code, 302)
        created = Employee.query.filter_by(email="new@test.local").one()
        self.assertEqual(created.reports_to, self.manager.id)
        self.assertEqual(created.bio, "A useful biography")
        action = Action.query.filter(Action.from_id == created.id).one()
        self.assertIn("New employee added: New Hire", action.description)

    def test_add_employee_rejects_missing_required_fields(self):
        response = self.client.post(
            "/employee/add",
            data={"company": "Test Company", "department": "Research"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertIsNone(Employee.query.filter_by(department="Research").first())
        self.assertIn(b"name: This field is required.", response.data)
        self.assertIn(b"title: This field is required.", response.data)

    def test_edit_employee_updates_fields_and_records_change_actions(self):
        response = self.client.post(
            f"/employee/edit/{self.employee.id}",
            data={
                "name": "Alex Updated",
                "title": "Senior Engineer",
                "company": "New Company",
                "department": "Platform",
                "email": "alex.updated@test.local",
                "reports_to": str(self.manager.id),
                "bio": "Updated bio",
                "location": "Chicago",
                "submit": "Submit",
            },
        )

        self.assertEqual(response.status_code, 302)
        db.session.expire_all()
        updated = db.session.get(Employee, self.employee.id)
        self.assertEqual(updated.name, "Alex Updated")
        self.assertEqual(updated.title, "Senior Engineer")
        self.assertEqual(updated.company, "New Company")
        self.assertEqual(updated.department, "Platform")
        self.assertEqual(updated.reports_to, self.manager.id)
        descriptions = {
            action.description
            for action in Action.query.filter_by(from_id=self.employee.id).all()
        }
        self.assertIn("Title changed from Engineer to Senior Engineer", descriptions)
        self.assertIn("Department changed from Product to Platform", descriptions)
        self.assertIn("Company changed from Test Company to New Company", descriptions)
        self.assertIn("Manager set to Mira Manager", descriptions)
        self.assertIn("Name changed from Alex Employee to Alex Updated", descriptions)
        self.assertIn("Bio changed from Original bio to Updated bio", descriptions)
        self.assertIn("Location changed from Boston to Chicago", descriptions)
        xp = EmployeeXP.query.filter_by(employee_id=self.employee.id).one()
        self.assertEqual(xp.xp, 20)

    def test_add_comment_creates_comment_action_and_awards_xp(self):
        response = self.client.post(
            f"/add_comment/{self.employee.id}",
            data={
                "author_id": str(self.manager.id),
                "content": "Welcome to the team",
            },
        )

        self.assertEqual(response.status_code, 200)
        comment = Comment.query.one()
        self.assertEqual(comment.author_id, self.manager.id)
        self.assertEqual(comment.employee_id, self.employee.id)
        self.assertIn(b"Welcome to the team", response.data)
        action = Action.query.one()
        self.assertIn("New comment by Mira Manager to Alex Employee", action.description)
        self.assertEqual(EmployeeXP.query.filter_by(employee_id=self.manager.id).one().xp, 10)
        self.assertEqual(EmployeeXP.query.filter_by(employee_id=self.employee.id).one().xp, 5)

    def test_multiline_comments_render_line_breaks(self):
        response = self.client.post(
            f"/add_comment/{self.employee.id}",
            data={"author_id": str(self.manager.id), "content": "First line\nSecond line"},
        )

        self.assertIn(b"First line<br>\nSecond line", response.data)

    def test_bio_markdown_preview_is_formatted_and_sanitized(self):
        response = self.client.post(
            "/preview/bio",
            data={"content": "**Bold**\n\n- one\n- two\n\n<script>alert(1)</script> [bad](javascript:alert(1))"},
        )

        self.assertEqual(response.status_code, 200)
        html = response.json["html"]
        self.assertIn("<strong>Bold</strong>", html)
        self.assertIn("<ul>", html)
        self.assertNotIn("<script", html)
        self.assertNotIn("javascript:", html)

    def test_text_renderers_escape_html(self):
        self.assertEqual(str(nl2br('<b>one</b>\ntwo')), '&lt;b&gt;one&lt;/b&gt;<br>\ntwo')
        self.assertNotIn('<img', str(markdown_to_html('<img src=x onerror=alert(1)>')))

    def test_test_comment_post_creates_comment_action_and_awards_xp(self):
        response = self.client.post(
            "/test_comment",
            data={
                "from": str(self.manager.id),
                "to": str(self.employee.id),
                "comment": "Please review the draft",
            },
        )

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.headers["Location"], "/test_comment")
        comment = Comment.query.one()
        self.assertEqual(comment.content, "Please review the draft")
        self.assertIn("New comment by Mira Manager to Alex Employee", Action.query.one().description)
        self.assertEqual(EmployeeXP.query.filter_by(employee_id=self.manager.id).one().xp, 10)
        self.assertEqual(EmployeeXP.query.filter_by(employee_id=self.employee.id).one().xp, 5)

    def test_delete_comment_removes_comment(self):
        comment = Comment(
            content="Temporary comment",
            author_id=self.manager.id,
            employee_id=self.employee.id,
        )
        db.session.add(comment)
        db.session.commit()

        response = self.client.post(f"/delete_comment/{comment.id}")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json, {"success": True})
        self.assertIsNone(db.session.get(Comment, comment.id))


if __name__ == "__main__":
    unittest.main()
