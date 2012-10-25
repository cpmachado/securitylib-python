"""
.. module:: passwords
    :synopsis: Creation and validation of user passwords.

.. moduleauthor:: Francisco Vieira <francisco.vieira@co.sapo.pt>
"""

from securitylib.utils import randomize, get_random_element
import string
import math
import os
import re

__all__ = ['generate_password', 'validate_password', 'get_password_strength', 'get_entropy_bits']


KEYBOARD_SEQUENCES = [
    "1234567890qwertyuiopasdfghjklzxcvbnm",
    "1qaz2wsx3edc4rfv5tgb6yhn7ujm8ik9ol0p",
    "qazwsxedcrfvtgbyhnujmikolp",
    "0147258369",
    "1470258369",
    "7894561230",
    "abcdefgh",
    "13579",
    "02468",
    "a1b2c3d4e5f6g7h8i9j0",
]

LICENCE_PLATE_REGEX = re.compile(r'([0-9]{2}|[a-zA-Z]{2})[.\-_]([0-9]{2}|[a-zA-Z]{2})[.\-_]([0-9]{2}|[a-zA-Z]{2})')

DICT_WORDS = None


def generate_password(length=12, lower=True, upper=True, digits=True, special=True, ambig=True):
    """
    Generates a password according to the given parameters.
    It is guaranteed that if a type of characters (lower, upper, etc.) is allowed in the password,
    then the generated password will always contain at least one character of that type,
    e.g. if the parameter special is True, then the generated password will have at least a special character.

    :param length: Length of the generated password. Must be at least 8.
    :type length: :class:`int`

    :param lower: Whether the password should contain lower case characters.
    :type lower: :class:`bool`

    :param upper: Whether the password should contain upper case characters.
    :type upper: :class:`bool`

    :param digits: Whether the password should contain digits.
    :type digits: :class:`bool`

    :param special: Whether the password should contain special characters (!\@#$%^&*).
    :type special: :class:`bool`

    :param ambig: Whether the password should contain ambiguous characters (iloILO10).
    :type ambig: :class:`bool`

    :returns: :class:`str` -- The generated password.
    """
    if length < 8:
        raise ValueError('Parameter length must be at least 8.')
    if not any([upper, lower, digits, special]):
        raise ValueError('At least one of upper, lower, digits or special must be True.')
    s_all = ''
    s_lower = 'abcdefghjkmnpqrstuvwxyz'
    s_upper = 'ABCDEFGHJKMNPQRSTUVWXYZ'
    s_digits = '23456789'
    s_special = '!@#$%^&*'
    if ambig:
        s_lower += 'ilo'
        s_upper += 'ILO'
        s_digits += '10'
    password = []
    if lower:
        s_all += s_lower
        password.append(get_random_element(s_lower))
    if upper:
        s_all += s_upper
        password.append(get_random_element(s_upper))
    if digits:
        s_all += s_digits
        password.append(get_random_element(s_digits))
    if special:
        s_all += s_special
        password.append(get_random_element(s_special))
    for _ in xrange(length - len(password)):
        password.append(get_random_element(s_all))
    randomize(password)
    return ''.join(password)


def validate_password(password, min_length=12, min_lower=1, min_upper=1, min_digits=1, min_special=1, min_strength=50):
    """
    Validates a given password against some basic rules.

    :param password: Password to validate.
    :type password: :class:`str`

    :param min_length: Minimum length that the password must have.
    :type min_length: :class:`int`

    :param min_lower: Minimum number of lower case characters that the password must contain.
    :type min_lower: :class:`int`

    :param min_upper: Minimum number of upper case characters that the password must contain.
    :type min_upper: :class:`int`

    :param min_digits: Minimum number of digits that the password must contain.
    :type min_digits: :class:`int`

    :param min_special: Minimum number of special characters (!\@#$%^&*) that the password must contain.
    :type min_special: :class:`int`

    :param min_strength: Minimum strength that the password must have according to function :func:`~securitylib.passwords.get_password_strength`.
    :type min_strength: :class:`bool`

    :returns: :class:`list` -- A list with the name of the parameters whose validations have failed.
                               This means a password is valid only if this function returns an empty list.
    """
    s_lower = set('abcdefghijklmnopqrstuvwxyz')
    s_upper = set('ABCDEFGHIJKLMNOPQRSTUVWXYZ')
    s_digits = set('0123456789')
    s_special = set('!@#$%^&*')

    problems = []
    if len(password) < min_length:
        problems.append('min_length')
    if count_occurrences_in_set(password, s_lower) < min_lower:
        problems.append('min_lower')
    if count_occurrences_in_set(password, s_upper) < min_upper:
        problems.append('min_upper')
    if count_occurrences_in_set(password, s_digits) < min_digits:
        problems.append('min_digits')
    if count_occurrences_in_set(password, s_special) < min_special:
        problems.append('min_special')
    if min_strength and get_password_strength(password) < min_strength:
        problems.append('min_strength')
    return problems


def count_occurrences_in_set(seq, target_set):
    count = 0
    for element in seq:
        if element in target_set:
            count += 1
    return count


def get_password_strength(password):
    """
    Evaluate a password's strength according to some heuristics.

    :param password: Password to evaluate.
    :type password: :class:`str`

    :returns: :class:`int` -- Strength of the password as an int between 0 and 100.
    """
    return min(int(get_entropy_bits(password) * 100 / 52), 100)


class PassVariant:
    def __init__(self, password, entropy=0):
        self.password = password
        self.entropy = entropy

    def __hash__(self):
        return hash(self.password)

    def __eq__(self, other):
        return self.password == other.password

    def __cmp__(self, other):
        return cmp(self.entropy, other.entropy)

    def __repr__(self):
        return '{0} {1}'.format(self.password, self.entropy)


class KeepMinDict(dict):
    def __init__(self, *args, **kwargs):
        super(KeepMinDict, self).__init__(*args, **kwargs)

    def __setitem__(self, key, value):
        if key not in self or value < self[key]:
            super(KeepMinDict, self).__setitem__(key, value)


def load_dict_words():
    global DICT_WORDS
    # If the list of dictionary words is not yet created
    # load the dictionary file and load it into the list.
    if not DICT_WORDS:
        dictionary_dir = os.path.dirname(os.path.abspath(__file__))
        dictionary_path = os.path.join(dictionary_dir, 'dictionary.txt')
        with open(dictionary_path) as f:
            DICT_WORDS = f.read().splitlines()
    return DICT_WORDS


def get_NIST_num_bits(password, repeatcalc=False):
    passlen = len(password)
    result = 0
    if repeatcalc:
        # Variant on NIST rules to reduce long sequences of repeated characters.
        charmult = [1] * 256
        for i in xrange(passlen):
            tempchr = ord(password[i])
            if i >= 19:
                result += charmult[tempchr]
            elif i >= 8:
                result += charmult[tempchr] * 1.5
            elif i >= 1:
                result += charmult[tempchr] * 2
            else:
                result += 4
            # Each time a character appears, it's value is reduced * 0.75, never going below 0.4
            charmult[tempchr] = max(charmult[tempchr] * 0.75, 0.4)
    elif passlen > 20:
        result = 4 + (7 * 2) + (12 * 1.5) + passlen - 20
    elif passlen > 8:
        result = 4 + (7 * 2) + ((passlen - 8) * 1.5)
    elif passlen > 1:
        result = 4 + ((passlen - 1) * 2)
    elif passlen == 1:
        result = 4
    else:
        result = 0
    return result


def get_entropy_bits(password):
    """
    Evaluate a password's strength according to some heuristics.
    Returns the entropy of the given password in bits.

    E.g. a password with 8 characters, lowercase + digits,
    without dictionary words and without keyboard sequences, will have entropy about 26.
    If it had also uppercase characters the entropy would be about 30.

    :param password: Password to evaluate.
    :type password: :class:`str`

    returns: :class:`int` -- Number of bits of entropy that the password has.
    """
    orig_pass = password

    if not orig_pass:
        return 0

    # Hardcoded parameters
    find_keyboard_sequences = True
    find_dict_words = True
    minwordlen = 3
    minword_accept_len = 6

    # If all the characters in the password are the same return early.
    n_different_characters = len(set(orig_pass))
    if n_different_characters == 1:
        return 6

    orig_pass = handle_license_plates(orig_pass)

    # Tests which types of character the password has.
    upper = False
    lower = False
    digits = False
    other = False
    for char in orig_pass:
        ord_chr = ord(char)
        if ord('A') <= ord_chr <= ord('Z'):
            upper = True
        elif ord('a') <= ord_chr <= ord('z'):
            lower = True
        elif ord('0') <= ord_chr <= ord('9'):
            digits = True
        else:
            other = True

    # Sets the keyspace_multiplier to the sum of the keyspace sizes
    # for each type of character in the password.
    keyspace_multiplier = 0
    if lower:
        keyspace_multiplier += 26
    if upper:
        keyspace_multiplier += 26
    if digits:
        keyspace_multiplier += 10
    if other:
        keyspace_multiplier += 32
    # Converts the keyspace_multiplier to multiply bits of entropy
    # and uses 26 (lowercase keyspace size) as the baseline,
    # i.e. if the password keyspace size is 26, the multiplier will be
    # equal to 1.
    keyspace_multiplier = math.log(keyspace_multiplier) / math.log(26)

    ### Creates many variants of the origial password ###
    # Lowercase variant
    lower_pass = PassVariant(orig_pass.lower())
    # Reversed lowercase variant
    rev_pass = reverse_password(lower_pass)

    passwords_variants = KeepMinDict()
    passwords_variants[lower_pass.password] = lower_pass
    passwords_variants[rev_pass.password] = rev_pass

    # Leet-speak substitutions variants
    leetspeakmap = string.maketrans('@!$1234567890', 'aisizeasgtbgo')
    leetspeak_pass = PassVariant(lower_pass.password.translate(leetspeakmap), 1)
    passwords_variants[leetspeak_pass.password] = leetspeak_pass

    leetspeakmap2 = string.maketrans('@!$1234567890', 'aislzeasgtbgo')
    leetspeak_pass2 = PassVariant(lower_pass.password.translate(leetspeakmap2), 1)
    passwords_variants[leetspeak_pass2.password] = leetspeak_pass2

    if find_keyboard_sequences:
        # Tries to find sequences from keyboard
        # in the variants of the password and removes them.
        for cur_pass in passwords_variants.values():
            tmp_pass = cur_pass.password
            for keyboard_seq in KEYBOARD_SEQUENCES:
                tmp_pass = remove_sequence(tmp_pass, keyboard_seq)
            if cur_pass.password != tmp_pass:
                # Since keyboard sequences were found in the password and removed,
                # we add the new shortened password to the password variants.
                # We don't replace the original (non shortened) variant since it
                # might contain a dictionary word that was hidden by the shortening.
                shortened_pass = PassVariant(tmp_pass, cur_pass.entropy)
                passwords_variants[shortened_pass.password] = shortened_pass

    if find_dict_words:
        # Looks for dictionary words in the password variants.
        dict_words = load_dict_words()
        for cur_pass in passwords_variants.values():
            clean_pass = ''.join(char for char in cur_pass.password if char != '\x00')
            n_alpha_chars = len([char for char in clean_pass if char_is_lower(char)])
            if len(clean_pass) >= minwordlen:
                # Creates a set with all the substrings of the password in it.
                substr_set = get_substrings_set(clean_pass, minwordlen)
                for dict_word in dict_words:
                    # If a dictionary word is found in the substr_set then
                    # it means that word was part of the original password.
                    if dict_word in substr_set and dict_word in clean_pass:
                        if len(dict_word) >= minword_accept_len:
                            break
                        if len(dict_word) * 2 <= n_alpha_chars:
                            continue
                        start_match = clean_pass.index(dict_word)
                        if start_match == 0:
                            break
                        if not char_is_lower(clean_pass[start_match - 1]):
                            break

                else:
                    # If no word is found in the password give it's entropy a bonus.
                    cur_pass.entropy += 6

    for pwd in passwords_variants.values():
        pwd.entropy += get_NIST_num_bits(pwd.password)

    # Find the minimum entropy among all password variants.
    min_entropy = min(pass_variant.entropy for pass_variant in passwords_variants.values())

    # Also consider the entropy of running the get_NIST_num_bits variant
    # for repeated chars against the original password.
    # We add 6 bits to the result simulating that no word was found
    # in the original password. This way, the only way this will result
    # in less entropy than the variants is if there is a great number of
    # repetitions in the original password.
    orig_pass_entropy = get_NIST_num_bits(orig_pass, True) + 6
    if orig_pass_entropy < min_entropy:
        min_entropy = orig_pass_entropy

    return min_entropy * keyspace_multiplier


def handle_license_plates(pwd):
    m = LICENCE_PLATE_REGEX.search(pwd)
    if m:
        filtered_license = ''.join(filter(None, m.groups()))
        count_letters = sum(1 for c in filtered_license if c.islower())
        if count_letters == 2:
            # is valid license plate
            start, end = m.span()
            pwd = pwd[:start] + filtered_license + pwd[end:]
    return pwd


def char_is_lower(char):
    return ord('a') <= ord(char) <= ord('z')


def remove_sequence(string, keyboard_seq):
    """
    Finds the longest common substring between the string and keyboard sequence given
    and if it is big enough (> 2) replaces it in the string with two null bytes
    and repeats the process with the rest of the string.
    Returns the result of remove the keyboard sequences from the string.
    """
    start, lcs = longest_common_substring(string, keyboard_seq)
    if len(lcs) > 2:
        return remove_sequence(string[:start], keyboard_seq) + '\x00\x00' + remove_sequence(string[start + len(lcs):], keyboard_seq)
    else:
        return string


def get_substrings_set(string, min_length):
    """
    Creates a set with all the substring of string that have at least min_length.
    """
    substr_set = set()
    slen = len(string)
    for substr_len in xrange(min_length, slen + 1):
        for substr_start in xrange(slen - substr_len + 1):
            substr_set.add(string[substr_start:substr_start + substr_len])
    return substr_set


def reverse_password(password):
    """
    Creates a PassVariant whose password field is the reverse of the original.
    Also adds 1 to the entropy of the returned PassVariant.
    """
    return PassVariant(reverse_string(password.password), password.entropy + 1)


def reverse_string(string):
    return ''.join(reversed(string))


def longest_common_substring(s1, s2):
    l2 = 1 + len(s2)
    m1 = [0] * l2
    m2 = [0] * l2
    longest, x_longest = 0, 0
    enumerate1 = list(enumerate(s1, 1))
    enumerate2 = list(enumerate(s2, 1))
    for x, s1_char in enumerate1:
        for y, s2_char in enumerate2:
            if s1_char == s2_char:
                m2[y] = m1[y - 1] + 1
                if m2[y] > longest:
                    longest = m2[y]
                    x_longest = x
            else:
                m2[y] = 0
        m1, m2 = m2, m1
    start = x_longest - longest
    return (start, s1[start:x_longest])
