# OurTeam

OurTeam is a deliberately fictional workplace sandbox: part employee directory,
part office social network, and part AI coworker simulator.

## Start locally on Windows

```powershell
.\setup.ps1
.\.venv\Scripts\python.exe ourteam.py
```

Open <http://127.0.0.1:5002>. The setup script creates an isolated Python
environment, installs dependencies, and adds a demo company when the database is
empty. Running it again preserves the current company.

## AI features

The directory, feed, profiles, org chart, and seeded demo all work offline. To
enable generated conversations, copy `.env.example` to `.env` and set
`OPENAI_API_KEY`. `OPENAI_MODEL` controls the model used by the conversation
tools.

## Resetting the sandbox

The local SQLite database lives at `instance/ourteam.db` and is intentionally
ignored by Git. Remove that file manually, then run `python seed_demo.py` to
start a fresh fictional company.
