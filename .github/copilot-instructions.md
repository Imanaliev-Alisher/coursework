# Copilot Instructions for AIS "Class Schedule" System

## Project Overview
This is a Django-based Academic Information System for managing university class schedules, built with Docker and Celery. The system manages buildings, audiences (classrooms), study groups, teachers, students, and subjects with their schedules.

## Architecture & Domain Model

### Core Domain Entities
- **Buildings**: Physical university buildings with address components (`apps/buildings/`)
- **Audiences**: Classrooms within buildings, with types and floor numbers
- **StudyGroups**: Academic groups of students (`apps/groups/`)
- **Users**: Extended Django User model with Teachers/Students profiles (`apps/users/`)
- **Subjects**: Courses with schedules, assigned to audiences and groups (`apps/studies/`)

### Key Relationships
- `Teachers`/`Students` are OneToOne extensions of `User` model
- `Subjects` use ManyToMany for `Schedule`, `Teachers`, and `StudyGroups`
- `Schedule` uses EnumFields for `WeekDays` and `EvenOddBoth` (четные/нечетные недели)
- All models use Russian translations via `gettext_lazy`

## Development Environment

### Docker Stack
```bash
# Start all services (Django, PostgreSQL, Redis, Celery, Nginx)
docker-compose up -d

# Django app runs on port 80 via Nginx
# PostgreSQL on port 5432
# Admin interface uses Jazzmin theme
```

### Key Commands
```bash
# Django management
python manage.py makemigrations
python manage.py migrate
python manage.py createsuperuser
python manage.py collectstatic

# Celery (background tasks)
celery -A config worker -l info
celery -A config beat -l info
```

### Environment Configuration
- Settings in `config/settings.py` use `django-environ`
- Expects `.envs/.django` and `.envs/.postgres` files (not in repo)
- Uses `DJANGO_SECRET_KEY`, `DATABASE_URL`, `REDIS_URL` environment variables

## Project-Specific Patterns

### Custom User Management
- Uses email as primary identifier (not username)
- Custom `UserManager` in `apps/users/managers.py` handles email-based auth
- `AUTH_USER_MODEL = "users.User"` in settings

### Russian Localization
- `LANGUAGE_CODE = 'ru-ru'`, `TIME_ZONE = 'Asia/Bishkek'`
- All model fields use `verbose_name` with Russian translations
- Enum values are in Russian (e.g., `WeekDays.MONDAY = 'Понедельник'`)

### Auto-Generated Fields
- `Buildings.address` auto-constructs from country/region/city/street/house_number
- `Audiences.title` auto-formats as "{auditorium_type} {auditorium_number}"

### Admin Customization
- Uses Jazzmin theme with extensive customization in settings
- Site title: "AIS 'Class Schedule'"
- Admin classes provide list_display, list_filter, search_fields

### Enum Pattern
- Uses `django-enumfields` for constrained choices
- Example: `WeekDays`, `EvenOddBoth` in `apps/studies/enums.py`
- Imported as `EnumField` in models

## Dependencies & Technology Stack

### Key Packages
- **Django 5.2** with PostgreSQL (`psycopg2-binary`)
- **Celery 5.5.2** with Redis broker and `django-celery-beat`
- **django-jazzmin** for admin interface
- **django-crispy-forms** with Bootstrap5
- **django-countries** for country fields
- **django-enumfields** for enum support

### File Structure Convention
```
apps/
  {app_name}/
    models.py      # Domain entities
    admin.py       # Admin interface config
    views.py       # Web views (mostly empty)
    tests.py       # Test cases
    migrations/    # DB schema changes
```

## Integration Points

### Celery Tasks
- Configured with Redis broker (`CELERY_BROKER_URL = REDIS_URL`)
- Database scheduler: `django_celery_beat.schedulers:DatabaseScheduler`
- Task modules auto-discovered from all Django apps

### Static/Media Files
- Static files: `/static/` served by Nginx in production
- Media files: `/media/` for uploaded content
- Uses `django-redis` for caching and sessions

### Database Patterns
- Uses `models.PROTECT` for foreign keys to prevent accidental deletions
- ManyToMany relationships for complex associations (subjects ↔ schedules, teachers, groups)
- Auto-incrementing BigAutoField as default primary key

When working with this codebase:
1. Always use Russian verbose_name for model fields
2. Follow the enum pattern for constrained choices
3. Use PROTECT on ForeignKeys for data integrity
4. Test admin interface changes in Jazzmin theme
5. Consider Celery for async operations
6. Respect the Docker-based development workflow