NON_MAJOR_FIELD_NAMES = ['capacity', 'limitations', 'number', 'position', 'teacherTitle']


def is_major_change(old_course: dict, new_course: dict):
    if old_course is None or new_course is None:
        return True
    old_course_major_field = {k: v for k, v in old_course.items() if k not in NON_MAJOR_FIELD_NAMES}
    new_course_major_field = {k: v for k, v in new_course.items() if k not in NON_MAJOR_FIELD_NAMES}
    return old_course_major_field != new_course_major_field
