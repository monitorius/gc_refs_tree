__all__ = ["get_referrers_tree", "print_referrers"]

import gc
import sys
import inspect


def get_referrers_tree(obj, max_depth):
    """ Returns a tree of obj referrers. Any object is included only once, all duplicates are replaced by ids

        Tree format:
        [ [referrer1, [sub_referrer1_1, sub_referrer1_2, ...]], [referrer2, [sub_referrer2_1, sub_referrer2_2, ...]], ...]
        where referrer1 and referrer2 are direct referrers to obj, and sub_referrs are referrers on them, respectively.
        sub_referrers have the same tree format.
    """
    non_local = {"current_depth": 0}  # emulate nonlocal statment for Python2
    already_seen = []
    exclude = [id(already_seen)]  # for objects created during the work of this function
    exclude.append(id(exclude))

    def get_recursive(obj):
        if non_local["current_depth"] == max_depth:
            return []

        res, new_referrers, seen_referrers = [], [], []
        exclude.extend([id(res), id(new_referrers), id(seen_referrers)])

        for o in gc.get_referrers(obj):
            if inspect.isframe(o):  # TODO: exclude only my frames
                continue

            if id(o) in already_seen:
                seen_referrers.append(o)
            elif id(o) not in exclude:
                new_referrers.append(o)
                already_seen.append(id(o))

        # can't use "for" loop because we need iterator itself to exclude it from referrers
        iterator = iter(new_referrers)
        exclude.append(id(iterator))
        non_local["current_depth"] += 1
        try:
            while True:
                sub_obj = next(iterator)
                res.append((sub_obj, get_recursive(sub_obj)))
        except StopIteration:
            pass
        non_local["current_depth"] -= 1

        # save only ids for already seen objects
        for sub_obj in seen_referrers:
            res.append((id(sub_obj), []))
        return res

    return get_recursive(obj)


def print_referrers(obj, max_depth, print_contents=True, shift_str="\t"):
    """ Prints obj referrers tree. """
    referrers = get_referrers_tree(obj, max_depth)
    non_local = {"shift": 0}  # emulate nonlocal statment for Python2

    def print_hierarchy(referrers):
        current_shift = non_local["shift"] * shift_str
        non_local["shift"] += 1
        for ref, sub_referrers in referrers:
            if isinstance(ref, int):  # it means we've got an id of already seen object
                print("{0}{1} ...".format(current_shift, ref))
            else:
                print("{0}{1} {2}{3}".format(current_shift, id(ref), type(ref), ref if print_contents else ""))

            print_hierarchy(sub_referrers)
        non_local["shift"] -= 1

    print_hierarchy(referrers)


if __name__ == "__main__":
    l = [666, ]
    d = {"d dict": l, "sub list key": ["sub list", l, l], "sub dict key": {"sub dict": l}}
    d1 = {"d dict holder": d}
    t = ("tuple", l)
    del l

    print_referrers(t[1], 3, print_contents=True)
