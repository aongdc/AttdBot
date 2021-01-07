"""
For parsing of users.txt into list or dictionary.
"""

from envs import USERS_TXT


def users(as_dict=True, segmented_list=0):
    """
    Parses _users.txt and returns the users as a list,
    or as a dictionary of users mapped to its index (starting from 1).

    :param as_dict: bool, defaults to True. Whether to return a list or dictionary.
    :param segmented_list: int, defaults to 0. If as_dict=False, determines whether
        to segment the returned list by length as defined by segmented_list. If set
        to 0, a flattened, one-layer non-nested list is returned.
    """
    assert not (as_dict and segmented_list > 0), \
        "Cannot return segmented list if as_dict is set to True!"

    users_lst = dict() if as_dict else []

    with open(USERS_TXT, 'r') as f:
        all_users = f.readlines()
        all_users = [user for user in all_users if user != '\n']
        all_users = [user.strip('\n') for user in all_users]
        if as_dict:
            # returns a dictionary mapping index to user in order listed in users.txt
            for i, user in enumerate(all_users):
                users_lst[user] = i + 1  # first index is 1
        else:
            if segmented_list > 0:
                # returns a nested list segmented by length segmented_list
                all_users = [user.title() for user in all_users]
                users_lst = [all_users[i:i+segmented_list]
                             for i in range(0, len(all_users), segmented_list)]
            else:
                # returns a flattened non-nested list
                for user in all_users:
                    users_lst.append(user)
    f.close()

    return users_lst


if __name__ == '__main__':
    print(users(as_dict=False))
    print(users())
