"""Create an idempotent fictional company for the local OurTeam sandbox."""

from datetime import datetime, timedelta

from ourteam import app
from models import (
    Action,
    Comment,
    Employee,
    EmployeeXP,
    Group,
    GroupComment,
    Status,
    db,
)


PEOPLE = [
    {
        "key": "mira",
        "name": "Mira Chen",
        "title": "Founder & Chief Alignment Officer",
        "department": "Executive",
        "email": "mira@ourteam.local",
        "location": "Floor 14, allegedly",
        "bio": "Mira founded OurTeam after a calendar invite became self-aware. She believes every crisis can be solved with a sharper memo and one fewer meeting.",
        "manager": None,
        "xp": 860,
    },
    {
        "key": "darius",
        "name": "Darius Vale",
        "title": "Chief Operating Optimist",
        "department": "Operations",
        "email": "darius@ourteam.local",
        "location": "Atlanta",
        "bio": "Darius maintains the master spreadsheet and refuses to confirm whether it has macros. Calm in emergencies; creates minor emergencies when bored.",
        "manager": "mira",
        "xp": 615,
    },
    {
        "key": "priya",
        "name": "Priya Nwosu",
        "title": "VP, Products That Might Work",
        "department": "Product",
        "email": "priya@ourteam.local",
        "location": "Brooklyn",
        "bio": "Priya can turn a vague hallway thought into a six-week roadmap before lunch. Keeps a private museum of features that were described as quick wins.",
        "manager": "mira",
        "xp": 740,
    },
    {
        "key": "theo",
        "name": "Theo Martin",
        "title": "Creative Director of Vibes",
        "department": "Creative",
        "email": "theo@ourteam.local",
        "location": "Montreal",
        "bio": "Theo owns eleven black turtlenecks and a label maker. He has never approved the phrase make it pop, though several witnesses claim otherwise.",
        "manager": "priya",
        "xp": 430,
    },
    {
        "key": "june",
        "name": "June Park",
        "title": "Lead, Artificial Coworkers",
        "department": "Applied AI",
        "email": "june@ourteam.local",
        "location": "Seattle",
        "bio": "June teaches machines office etiquette and employees machine etiquette. Her current model has started declining meetings without consulting her.",
        "manager": "priya",
        "xp": 980,
    },
    {
        "key": "rafael",
        "name": "Rafael Ortiz",
        "title": "Director of Community Operations",
        "department": "Operations",
        "email": "rafael@ourteam.local",
        "location": "Miami",
        "bio": "Rafael knows where everything is, who borrowed it, and why the purchase order still says pending. He has a solution, but you may not enjoy it.",
        "manager": "darius",
        "xp": 505,
    },
    {
        "key": "nina",
        "name": "Nina Bell",
        "title": "Workplace Anthropologist",
        "department": "Creative",
        "email": "nina@ourteam.local",
        "location": "London",
        "bio": "Nina studies rituals of modern work: the thumbs-up reaction, the performative calendar block, and the untouched fruit at an offsite breakfast.",
        "manager": "theo",
        "xp": 355,
    },
    {
        "key": "omar",
        "name": "Omar Sayeed",
        "title": "Senior Chaos Coordinator",
        "department": "Operations",
        "email": "omar@ourteam.local",
        "location": "Chicago",
        "bio": "Omar runs tabletop exercises that keep becoming real. He is banned from naming internal projects after weather systems.",
        "manager": "rafael",
        "xp": 290,
    },
]


def seed_demo():
    if Employee.query.first():
        print("OurTeam already has employees; leaving the existing world untouched.")
        return

    now = datetime.utcnow()
    people = {}
    for data in PEOPLE:
        person = Employee(
            name=data["name"],
            title=data["title"],
            company="OurTeam Industries",
            department=data["department"],
            email=data["email"],
            location=data["location"],
            bio=data["bio"],
        )
        people[data["key"]] = person
        db.session.add(person)

    db.session.flush()
    for data in PEOPLE:
        if data["manager"]:
            people[data["key"]].reports_to = people[data["manager"]].id
        db.session.add(EmployeeXP(employee_id=people[data["key"]].id, xp=data["xp"]))

    groups = {
        "launch": Group(groupname="Project Hush-Hush"),
        "culture": Group(groupname="Culture Committee (Unofficial)"),
        "incident": Group(groupname="Incident Response & Snacks"),
    }
    db.session.add_all(groups.values())
    db.session.flush()
    for key in ("priya", "june", "theo", "nina"):
        groups["launch"].members.append(people[key])
    for key in ("mira", "darius", "nina", "omar"):
        groups["culture"].members.append(people[key])
    for key in ("darius", "rafael", "june", "omar"):
        groups["incident"].members.append(people[key])

    def befriend(first, second):
        people[first].friends.append(people[second])
        people[second].friends.append(people[first])

    for pair in (("june", "nina"), ("theo", "priya"), ("omar", "rafael"), ("mira", "darius")):
        befriend(*pair)

    statuses = [
        ("june", "The assistant has started using ‘per my last message.’ This is either progress or a containment failure.", 18),
        ("nina", "Field note: the new quiet room is where people go to take loud calls.", 64),
        ("omar", "If you see a fog machine near Conference B, no you didn’t.", 145),
        ("priya", "Roadmap update: the moon is still in scope, but moved to Q4.", 260),
        ("darius", "Reminder that ‘miscellaneous’ is not a department, cost center, or project strategy.", 390),
        ("mira", "Strong week. Nobody accidentally replied-all to Legal.", 520),
    ]
    for key, content, minutes in statuses:
        db.session.add(Status(employee_id=people[key].id, content=content, timestamp=now - timedelta(minutes=minutes)))

    comments = [
        ("nina", "june", "Could be both. I’m adding it to the field study.", 11),
        ("rafael", "omar", "I signed for the fog machine, so technically I did see it.", 120),
        ("theo", "priya", "Q4 moon has better lighting anyway.", 220),
        ("darius", "mira", "This is how we measure operational excellence now.", 470),
    ]
    for author, recipient, content, minutes in comments:
        db.session.add(Comment(
            author_id=people[author].id,
            employee_id=people[recipient].id,
            content=content,
            timestamp=now - timedelta(minutes=minutes),
        ))

    actions = [
        ("june", "June Park promoted the office assistant from experimental to concerning.", 8),
        ("nina", "Nina Bell documented an emerging lunchroom ritual.", 55),
        ("omar", "Omar Sayeed opened Incident #0042: Atmospheric Conditions.", 138),
        ("priya", "Priya Nwosu moved a celestial deliverable to Q4.", 250),
        ("darius", "Darius Vale renamed three mystery budget lines.", 380),
    ]
    for key, description, minutes in actions:
        db.session.add(Action(
            description=description,
            from_id=people[key].id,
            timestamp=now - timedelta(minutes=minutes),
        ))

    db.session.add(GroupComment(
        group_id=groups["incident"].id,
        author_id=people["omar"].id,
        content="Snacks have been secured. The incident remains dynamic.",
        timestamp=now - timedelta(minutes=95),
    ))
    db.session.commit()
    print(f"Seeded {len(people)} employees, {len(groups)} groups, and one suspicious workplace.")


if __name__ == "__main__":
    with app.app_context():
        seed_demo()
