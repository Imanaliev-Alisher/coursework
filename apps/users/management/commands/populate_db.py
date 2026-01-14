"""
Management command для заполнения базы данных тестовыми данными
Использование: python manage.py populate_db
"""
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.db import transaction
from django.utils import timezone

from apps.buildings.models import Buildings, Audiences, AudiencesTypes
from apps.groups.models import StudyGroups
from apps.studies.models import TimeSlot, Day, SubjectsTypes, Schedule, Subjects
from apps.studies.choices import EvenOddBoth

import random
from datetime import time

User = get_user_model()


class Command(BaseCommand):
    help = 'Заполняет базу данных тестовыми данными'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Очистить существующие данные перед заполнением',
        )

    def handle(self, *args, **options):
        if options['clear']:
            self.stdout.write(self.style.WARNING('Очистка базы данных...'))
            self.clear_database()

        self.stdout.write(self.style.SUCCESS('Начинаем заполнение базы данных...'))

        with transaction.atomic():
            # 1. Создаем администраторов
            managers = self.create_managers()
            self.stdout.write(self.style.SUCCESS(f'✓ Создано {len(managers)} менеджеров'))

            # 2. Создаем преподавателей
            teachers = self.create_teachers()
            self.stdout.write(self.style.SUCCESS(f'✓ Создано {len(teachers)} преподавателей'))

            # 3. Создаем студентов и группы
            groups, students = self.create_groups_and_students()
            self.stdout.write(self.style.SUCCESS(f'✓ Создано {len(groups)} групп с {len(students)} студентами'))

            # 4. Создаем здания и аудитории
            buildings, audiences = self.create_buildings_and_audiences()
            self.stdout.write(self.style.SUCCESS(f'✓ Создано {len(buildings)} зданий с {len(audiences)} аудиториями'))

            # 5. Создаем временные слоты
            time_slots = self.create_time_slots()
            self.stdout.write(self.style.SUCCESS(f'✓ Создано {len(time_slots)} временных слотов'))

            # 6. Создаем дни недели
            days = self.create_days()
            self.stdout.write(self.style.SUCCESS(f'✓ Создано {len(days)} дней недели'))

            # 7. Создаем типы предметов
            subject_types = self.create_subject_types()
            self.stdout.write(self.style.SUCCESS(f'✓ Создано {len(subject_types)} типов предметов'))

            # 8. Создаем расписание
            schedules = self.create_schedules(days, time_slots)
            self.stdout.write(self.style.SUCCESS(f'✓ Создано {len(schedules)} записей расписания'))

            # 9. Создаем предметы
            subjects = self.create_subjects(subject_types, schedules, audiences, teachers, groups)
            self.stdout.write(self.style.SUCCESS(f'✓ Создано {len(subjects)} предметов'))

        self.stdout.write(self.style.SUCCESS('\n🎉 База данных успешно заполнена!'))
        self.print_credentials()

    def clear_database(self):
        """Очистка всех данных"""
        Subjects.objects.all().delete()
        Schedule.objects.all().delete()
        SubjectsTypes.objects.all().delete()
        Day.objects.all().delete()
        TimeSlot.objects.all().delete()
        Audiences.objects.all().delete()
        AudiencesTypes.objects.all().delete()
        Buildings.objects.all().delete()
        StudyGroups.objects.all().delete()
        User.objects.all().delete()
        self.stdout.write(self.style.WARNING('База данных очищена'))

    def create_managers(self):
        """Создает 3 менеджеров (администраторов)"""
        managers_data = [
            {
                'username': 'admin',
                'email': 'admin@university.edu',
                'first_name': 'Главный',
                'last_name': 'Администратор',
                'password': 'admin123',
            },
            {
                'username': 'manager1',
                'email': 'manager1@university.edu',
                'first_name': 'Алексей',
                'last_name': 'Менеджеров',
                'password': 'manager123',
            },
            {
                'username': 'manager2',
                'email': 'manager2@university.edu',
                'first_name': 'Мария',
                'last_name': 'Управляева',
                'password': 'manager123',
            },
        ]

        managers = []
        for data in managers_data:
            password = data.pop('password')
            manager = User.objects.create_user(
                **data,
                role='STAFF',
                is_staff=True,
                is_superuser=True
            )
            manager.set_password(password)
            manager.save()
            managers.append(manager)

        return managers

    def create_teachers(self):
        """Создает 15 преподавателей"""
        departments = [
            'Кафедра программной инженерии',
            'Кафедра информационных систем',
            'Кафедра прикладной математики',
            'Кафедра компьютерных наук',
        ]

        teachers_data = [
            ('ivanov_ii', 'Иван', 'Иванов', '+996555111111', '201А'),
            ('petrova_aa', 'Анна', 'Петрова', '+996555222222', '202Б'),
            ('sidorov_pp', 'Петр', 'Сидоров', '+996555333333', '203В'),
            ('kuznetsov_ss', 'Сергей', 'Кузнецов', '+996555444444', '204Г'),
            ('smirnova_ee', 'Елена', 'Смирнова', '+996555555555', '205А'),
            ('popov_mm', 'Михаил', 'Попов', '+996555666666', '206Б'),
            ('vasileva_oo', 'Ольга', 'Васильева', '+996555777777', '207В'),
            ('fedorov_dd', 'Дмитрий', 'Федоров', '+996555888888', '208Г'),
            ('sokolova_nn', 'Наталья', 'Соколова', '+996555999999', '209А'),
            ('morozov_aa', 'Александр', 'Морозов', '+996555101010', '210Б'),
            ('novikova_tt', 'Татьяна', 'Новикова', '+996555111011', '211В'),
            ('lebedev_vv', 'Виктор', 'Лебедев', '+996555121212', '212Г'),
            ('kozlov_ii', 'Игорь', 'Козлов', '+996555131313', '213А'),
            ('nikolaeva_ll', 'Людмила', 'Николаева', '+996555141414', '214Б'),
            ('orlov_gg', 'Георгий', 'Орлов', '+996555151515', '215В'),
        ]

        teachers = []
        for i, (username, first_name, last_name, phone, office) in enumerate(teachers_data):
            teacher = User.objects.create_user(
                username=username,
                email=f'{username}@university.edu',
                first_name=first_name,
                last_name=last_name,
                role='TEACHER',
                department=departments[i % len(departments)],
                phone=phone,
                office=office
            )
            teacher.set_password('teacher123')
            teacher.save()
            teachers.append(teacher)

        return teachers

    def create_groups_and_students(self):
        """Создает 3 группы по 10 студентов"""
        faculties = [
            'Факультет информационных технологий',
            'Факультет компьютерных наук',
            'Факультет прикладной математики',
        ]

        groups_data = [
            ('ИВТ-21', 'Информационные технологии', faculties[0], 2),
            ('ПИ-31', 'Программная инженерия', faculties[0], 3),
            ('ПМ-11', 'Прикладная математика', faculties[2], 1),
        ]

        first_names = [
            'Александр', 'Дмитрий', 'Максим', 'Иван', 'Артем',
            'Михаил', 'Егор', 'Андрей', 'Никита', 'Даниил',
            'Анастасия', 'Мария', 'Дарья', 'Екатерина', 'Полина',
            'Алина', 'Виктория', 'Ксения', 'София', 'Елизавета'
        ]

        last_names = [
            'Иванов', 'Петров', 'Сидоров', 'Смирнов', 'Козлов',
            'Васильев', 'Соколов', 'Михайлов', 'Новиков', 'Федоров',
            'Морозов', 'Волков', 'Алексеев', 'Лебедев', 'Семенов',
            'Егоров', 'Павлов', 'Захаров', 'Степанов', 'Николаев'
        ]

        groups = []
        all_students = []

        for group_title, description, faculty, course in groups_data:
            # Создаем группу
            group = StudyGroups.objects.create(
                title=group_title,
                description=description,
                faculty=faculty,
                course=course,
                is_active=True
            )
            groups.append(group)

            # Создаем 10 студентов для группы
            group_students = []
            for i in range(1, 11):
                first_name = random.choice(first_names)
                last_name = random.choice(last_names)
                username = f'{last_name.lower()}_{first_name[0].lower()}{i}_{group_title.lower().replace("-", "")}'
                
                student = User.objects.create_user(
                    username=username,
                    email=f'{username}@student.university.edu',
                    first_name=first_name,
                    last_name=last_name,
                    role='STUDENT'
                )
                student.set_password('student123')
                student.save()
                group_students.append(student)
                all_students.append(student)

            # Добавляем студентов в группу
            group.students.set(group_students)

        return groups, all_students

    def create_buildings_and_audiences(self):
        """Создает здания и аудитории"""
        # Создаем типы аудиторий
        audience_types_data = [
            'Лекционная аудитория',
            'Компьютерный класс',
            'Лаборатория',
            'Практическая аудитория'
        ]

        audience_types = []
        for type_name in audience_types_data:
            aud_type, _ = AudiencesTypes.objects.get_or_create(title=type_name)
            audience_types.append(aud_type)

        # Создаем здания
        buildings_data = [
            ('Главный корпус', 'KG', 'Бишкек', 'Чуйский проспект', '265'),
            ('Учебный корпус №2', 'KG', 'Бишкек', 'Фрунзе', '547'),
        ]

        buildings = []
        all_audiences = []

        for title, country, city, street, house in buildings_data:
            building = Buildings.objects.create(
                title=title,
                country=country,
                region='Чуйская область',
                city=city,
                street=street,
                house_number=house
            )
            buildings.append(building)

            # Создаем аудитории для каждого здания
            for floor in range(1, 4):  # 3 этажа
                for room_num in range(1, 6):  # 5 аудиторий на этаже
                    auditorium_number = f'{floor}0{room_num}'
                    audience = Audiences.objects.create(
                        auditorium_number=auditorium_number,
                        floor_number=floor,
                        building=building,
                        auditorium_type=random.choice(audience_types)
                    )
                    all_audiences.append(audience)

        return buildings, all_audiences

    def create_time_slots(self):
        """Создает временные слоты (пары)"""
        time_slots_data = [
            (1, time(8, 0), time(9, 30)),
            (2, time(9, 40), time(11, 10)),
            (3, time(11, 30), time(13, 0)),
            (4, time(13, 30), time(15, 0)),
            (5, time(15, 10), time(16, 40)),
            (6, time(16, 50), time(18, 20)),
        ]

        time_slots = []
        for number, start, end in time_slots_data:
            slot, _ = TimeSlot.objects.get_or_create(
                number=number,
                defaults={'start_time': start, 'end_time': end}
            )
            time_slots.append(slot)

        return time_slots

    def create_days(self):
        """Создает дни недели"""
        days_data = [
            'Понедельник',
            'Вторник',
            'Среда',
            'Четверг',
            'Пятница',
            'Суббота'
        ]

        days = []
        for day_name in days_data:
            day, _ = Day.objects.get_or_create(title=day_name)
            days.append(day)

        return days

    def create_subject_types(self):
        """Создает типы предметов"""
        types_data = [
            'Лекция',
            'Практика',
            'Лабораторная работа',
            'Семинар'
        ]

        subject_types = []
        for type_name in types_data:
            subj_type, _ = SubjectsTypes.objects.get_or_create(title=type_name)
            subject_types.append(subj_type)

        return subject_types

    def create_schedules(self, days, time_slots):
        """Создает записи расписания"""
        schedules = []
        week_types = [EvenOddBoth.EVEN, EvenOddBoth.ODD, EvenOddBoth.BOTH]

        for day in days[:5]:  # Только будние дни
            for slot in time_slots[:4]:  # Первые 4 пары
                for week_type in [EvenOddBoth.BOTH, EvenOddBoth.EVEN, EvenOddBoth.ODD]:
                    schedule, _ = Schedule.objects.get_or_create(
                        week_day=day,
                        time_slot=slot,
                        week_type=week_type
                    )
                    schedules.append(schedule)

        return schedules

    def create_subjects(self, subject_types, schedules, audiences, teachers, groups):
        """Создает 10 предметов"""
        subjects_data = [
            ('Программирование на Python', 'Лекция'),
            ('Программирование на Python', 'Практика'),
            ('Базы данных', 'Лекция'),
            ('Базы данных', 'Лабораторная работа'),
            ('Алгоритмы и структуры данных', 'Лекция'),
            ('Алгоритмы и структуры данных', 'Практика'),
            ('Веб-разработка', 'Лекция'),
            ('Веб-разработка', 'Лабораторная работа'),
            ('Математический анализ', 'Лекция'),
            ('Дискретная математика', 'Семинар'),
        ]

        subjects = []
        lecture_type = next(st for st in subject_types if st.title == 'Лекция')
        practice_type = next(st for st in subject_types if st.title == 'Практика')
        lab_type = next(st for st in subject_types if st.title == 'Лабораторная работа')
        seminar_type = next(st for st in subject_types if st.title == 'Семинар')

        type_map = {
            'Лекция': lecture_type,
            'Практика': practice_type,
            'Лабораторная работа': lab_type,
            'Семинар': seminar_type
        }

        used_schedules = set()

        for title, type_name in subjects_data:
            # Находим доступное расписание
            available_schedules = [s for s in schedules if s.id not in used_schedules]
            selected_schedule = random.choice(available_schedules)
            used_schedules.add(selected_schedule.id)

            subject = Subjects.objects.create(
                title=title,
                audience=random.choice(audiences),
                subject_type=type_map[type_name]
            )

            # Добавляем расписание
            subject.schedule.add(selected_schedule)

            # Добавляем 1-2 преподавателей
            subject_teachers = random.sample(teachers, random.randint(1, 2))
            subject.teachers.set(subject_teachers)

            # Добавляем 1-2 группы
            subject_groups = random.sample(groups, random.randint(1, 2))
            subject.groups.set(subject_groups)

            subjects.append(subject)

        return subjects

    def print_credentials(self):
        """Выводит учетные данные для входа"""
        self.stdout.write(self.style.SUCCESS('\n' + '='*60))
        self.stdout.write(self.style.SUCCESS('УЧЕТНЫЕ ДАННЫЕ ДЛЯ ВХОДА:'))
        self.stdout.write(self.style.SUCCESS('='*60))
        
        self.stdout.write(self.style.WARNING('\n👑 Администраторы:'))
        self.stdout.write('   Username: admin        | Password: admin123')
        self.stdout.write('   Username: manager1     | Password: manager123')
        self.stdout.write('   Username: manager2     | Password: manager123')
        
        self.stdout.write(self.style.WARNING('\n👨‍🏫 Преподаватели:'))
        self.stdout.write('   Username: ivanov_ii    | Password: teacher123')
        self.stdout.write('   Username: petrova_aa   | Password: teacher123')
        self.stdout.write('   (и другие 13 преподавателей с паролем teacher123)')
        
        self.stdout.write(self.style.WARNING('\n👨‍🎓 Студенты:'))
        self.stdout.write('   (30 студентов с паролем student123)')
        self.stdout.write('   Примеры: ivanov_a1_ивт21, petrov_d2_пи31, и т.д.')
        
        self.stdout.write(self.style.SUCCESS('\n' + '='*60))
        self.stdout.write(self.style.SUCCESS('JWT токен: POST /api/auth/token/'))
        self.stdout.write(self.style.SUCCESS('Swagger UI: http://localhost:8000/api/docs/'))
        self.stdout.write(self.style.SUCCESS('='*60 + '\n'))
