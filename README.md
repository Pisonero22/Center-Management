# Center Management

A Django application for running a cultural centre: schedule activities, assign
instructors and rooms, register members and keep track of who is enrolled in what.

It started as my final university project and I have since rewritten it as a
portfolio piece — English codebase, environment-based configuration, an explicit
domain model and a documented setup.

## Features

- CRUD for the four entities of the domain: **activities**, **members**,
  **instructors** and **rooms**.
- **Enrolments** modelled as an explicit join table, so the enrolment date is
  recorded and a member cannot be enrolled twice in the same activity.
- Server-side **filtering**: activities by category and instructor, members by
  the activity they attend.
- **Django admin** configured with list displays, filters, search and an inline
  for the enrolments of an activity.
- A **`seed_demo`** management command that fills the database with a small
  demo dataset in one line.
- **Authentication**: the catalogue is public, but creating, editing, deleting
  and enrolling require a signed-in user.
- **Capacity is enforced**: an activity refuses enrolments once it is full, and
  it cannot offer more places than its main room holds.

## Data model

```mermaid
erDiagram
    INSTRUCTOR ||--o{ ACTIVITY : "teaches"
    INSTRUCTOR ||--o{ ROOM : "manages"
    ROOM ||--o{ ACTIVITY : "hosts as main room"
    ROOM }o--o{ ACTIVITY : "hosts as secondary room"
    MEMBER ||--o{ ENROLLMENT : "signs up"
    ACTIVITY ||--o{ ENROLLMENT : "receives"

    MEMBER {
        string full_name
        string email UK
        string phone
    }
    INSTRUCTOR {
        string full_name
        string specialty
    }
    ROOM {
        string name
        int capacity
        string location
        fk manager "Instructor, nullable"
    }
    ACTIVITY {
        string name
        string category "choices"
        datetime starts_at
        duration duration
        int capacity
    }
    ENROLLMENT {
        fk member
        fk activity
        datetime created_at
    }
```

`Enrollment` is the `through` model of the many-to-many between `Member` and
`Activity`. A `UniqueConstraint` on `(member, activity)` enforces at database
level that the same person cannot take two places in one activity.

## Stack

| Layer      | Choice                                            |
| ---------- | ------------------------------------------------- |
| Language   | Python 3.12                                       |
| Framework  | Django 5.2 (class-based views, ORM, admin)        |
| Database   | SQLite in development                             |
| Frontend   | Django templates with a hand-written stylesheet   |
| Config     | Environment variables loaded from a `.env` file   |

## Getting started

```bash
git clone https://github.com/Pisonero22/center-management.git
cd center-management

python3 -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt

cp .env.example .env               # then edit DJANGO_SECRET_KEY

python manage.py migrate
python manage.py seed_demo         # optional: demo data
python manage.py runserver
```

The site is then available at <http://127.0.0.1:8000/>.

To use the admin at `/admin/`, create a superuser first:

```bash
python manage.py createsuperuser
```

## Configuration

| Variable               | Default                 | Purpose                                    |
| ---------------------- | ----------------------- | ------------------------------------------ |
| `DJANGO_SECRET_KEY`    | insecure development key | Signing key. Required when debug is off.   |
| `DJANGO_DEBUG`         | `true`                  | Debug mode. Set to `false` in production.  |
| `DJANGO_ALLOWED_HOSTS` | `localhost,127.0.0.1`   | Comma-separated list of accepted hosts.    |

No secret is committed to the repository: `settings.py` reads these from the
environment and refuses to start with the development key when debug is off.

## Project layout

```
center-management/
├── config/              # project settings, root URLconf, WSGI/ASGI entry points
├── activities/          # the single application
│   ├── models.py        # Member, Instructor, Room, Activity, Enrollment
│   ├── views.py         # class-based CRUD + the enrolment flow
│   ├── forms.py         # model forms
│   ├── admin.py         # admin configuration
│   ├── urls.py          # application routes
│   ├── management/      # seed_demo command
│   ├── static/css/      # stylesheet
│   └── templates/       # base layout and one folder per entity
├── manage.py
└── requirements.txt
```

## Design notes

- **Class-based views for the CRUD, function views for the enrolment flow.**
  The CRUD is repetitive and generic views remove that boilerplate; enrolling
  someone has actual rules, and a plain function keeps them readable.
- **Destructive actions go through POST.** Removing an enrolment is a form with
  a CSRF token, not a link — a GET request should never change state.
- **The database enforces the invariants it can.** Uniqueness of an enrolment is
  a constraint, not only a check in the view.
- **The last place is a race.** Counting the enrolments and inserting the new
  one happen inside a single transaction with a row lock, so two people
  clicking at the same time cannot both take the last place.
- **Read is public, write is authenticated.** A visitor can browse the
  programme; only signed-in staff change it. Logging out is a POST form, as
  Django requires since 4.1.

## Roadmap

- [ ] Pagination and query optimisation on the list views.
- [ ] Test suite covering the models, the enrolment rules and the views.
- [ ] Docker Compose setup with PostgreSQL and a CI workflow.

## Licence

MIT — see [LICENSE](LICENSE).
