from helpers.data_repo import Term


def term_diff(old_term: Term, new_term: Term) -> (dict, dict):
    if old_term.hash == new_term.hash:
        return []
    old_courses, new_courses = old_term.get_courses(), new_term.get_courses()
    i, j, i_max, j_max = 0, 0, len(old_courses), len(new_courses)
    difference = []
    while i < i_max and j < j_max:
        old, new = old_courses[i], new_courses[j]
        old_key, new_key = (old['courseId'], old['teacherId']), (new['courseId'], new['teacherId'])
        if old_key == new_key:
            if old != new:
                difference.append((old, new))
            i += 1
            j += 1
        elif old_key < new_key:
            difference.append((old, None))
            i += 1
        else:
            difference.append((None, new))
            j += 1
    while i < i_max:
        difference.append((old_courses[i], None))
        i += 1
    while j < j_max:
        difference.append((None, new_courses[j]))
        j += 1
    return difference
