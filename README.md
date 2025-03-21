# SAPO Security Lib - Python

The SAPO Security Lib is a library whose purpose is to provide functions/classes
that solve common security related problems, while being easy to use even by
those who are not security experts. This repository contains the Python version
of this library.

Our design principles:

- **Security** — This is an obvious one, but it is important to explain how it
  is enforced.
    - No security primitives were invented, all security sensitive code is based
      on modern security best-practices (e.g. we use PBKDF2 to derive keys from
      passwords, we didn't reinvent the wheel).
    - Very high (near 100%) testing code coverage.
    - Manual code review by security professionals.
- **Security by default** — Using the library with the default parameters should
  provide enough security for most cases (maybe not military grade top security,
  but enough for an application like Gmail, for example). Flexibility was even
  traded in some places for increased security, for example by making it hard
  (i.e., impossible without messing with the lib code) for someone to use a weak
  algorithm instead of the default one.
- **Simple API** — Unfortunately, the acronyms AES, PBKDF2, HMAC, etc. are
  cryptic for many developers, and many others know them but might have
  difficulty knowing when and how to use them. As such, we decided to hide the
  implementation details in the API function names, resulting in names such as
  `generate_encryption_key`, `encrypt`, `prepare_password_for_storage`, etc.
  which most developers are able to understand even if they are not security
  experts.



There are currently 4 modules in this library:

- **crypto** — Cryptographic functions library.
- **advanced_crypto** — Advanced cryptographic functions library.
- **random** — Secure generation of random numbers and strings.
- **passwords** — Creation and validation of user passwords.

Some examples of use cases for each of these modules are given below.

For the full documentation of the library, go [here](http://oss.sapo.pt/securitylib-python/).


## Discussion

Please file any bugs you find in our [issue tracker](https://github.com/sapo/securitylib-python).

## Testing
- tox run

## Building wheel
- python setup.py bdist bdist_wheel

_You should change version in setup.py when upgrading_

## Installation

Upgraded to support from Python 3.5 to 3.13.
There are several ways to install SAPO Security Lib.

### Via PyPI

Just run:
`pip install securitylib`


### Via a tarball release

1. Download the [ZIP file](https://github.com/sapo/securitylib-python/archive/refs/heads/master.zip)
2. Unpack the tarball
3. `python setup.py install`


## Examples:

### Crypto

Generating a key for encryption:

```python
import securitylib

encryption_key = securitylib.crypto.generate_encryption_key()

print(encryption_key)
```

Generating a key for encryption based on a user's password:

```python
import securitylib

password = 'this_is_the_users_password'
salt = securitylib.random.get_random_token()
encryption_key = securitylib.crypto.generate_encryption_key_from_password(password, salt)

print(encryption_key)
```

Encrypting and decrypting data:

```python
import securitylib

data = 'this_is_the_data_we_want_to_encrypt'
encryption_key = securitylib.crypto.generate_encryption_key()
authenticator_key = securitylib.crypto.generate_authenticator_key()
encrypted_data = securitylib.crypto.encrypt(data, encryption_key, authenticator_key)
decrypted_data = securitylib.crypto.decrypt(encrypted_data, encryption_key, authenticator_key)
assert(decrypted_data == data)
```

### Advanced Crypto

Using a stream cipher to encrypt or decrypt a stream:

```python
import securitylib

data_chunks = ['this_is_', 'the_data', '_we', '_want_to_', 'encrypt']

encryption_key = securitylib.crypto.generate_encryption_key()

# Data can be encrypted chunk by chunk
stream_cipher = securitylib.advanced_crypto.StreamCipher(encryption_key)
encrypted_data = ''.join(stream_cipher.encrypt(chunk) for chunk in data_chunks)

# Decryption can also happen chunk by chunk. Here we are decrypting the whole
# stream at once just to check that we get the original data back.
stream_cipher2 = securitylib.advanced_crypto.StreamCipher(encryption_key)
decrypted_data = stream_cipher2.decrypt(encrypted_data)

original_data = ''.join(data_chunks)

assert(decrypted_data == original_data)
```

### Random

Generating random values using a secure source of randomness:

```python
import securitylib

random_bytes = securitylib.random.get_random_bytes(length=16)
random_integer = securitylib.random.get_random_integer(min_result=1000, max_result=9999)
random_string = securitylib.random.get_random_string(length=100, charset='abcdefghijklmnopqrstuvwxyz')
random_GUID = securitylib.random.get_random_GUID()

print(random_bytes, random_integer, random_string, random_GUID)
```

### Passwords

Generating a random password:

```python
import securitylib

password = securitylib.passwords.generate_password(length=12, lower=True, upper=True, digits=True, special=True, ambig=True)

print(password)
```

Getting a password's strength (between 0 and 100):

```python
import securitylib

print(securitylib.passwords.get_password_strength('123456'))
print(securitylib.passwords.get_password_strength('thisismypassword'))
print(securitylib.passwords.get_password_strength('this is my password'))
print(securitylib.passwords.get_password_strength('u6fm08xw@RLs'))
print(securitylib.passwords.get_password_strength('This 1s My P4ssword...'))
```

Validate a user's password against a list of rules:

```python
import securitylib

password = 'this_is_the_users_password'
error_list = securitylib.passwords.validate_password(password, min_length=12, min_lower=1, min_upper=1, min_digits=1, min_special=1, min_strength=50)

print(error_list)
```
