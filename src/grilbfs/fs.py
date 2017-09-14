# This FUSE module implements an encrypted filesystem aimed for
# small-to-moderate sized read-mostly data. The backing store contains two
# files: a GPG-wrapped NaCl encryption key ("key.gpg"), and an single encrypted
# aggregate of all the plaintext ("encrypted.data").

# The body of key.gpg is a 32-byte NaCl "SecretBox" key. The encrypted.data
# file starts with a random 24-byte nonce, and the remainder is
# SecretBox-encrypted. The plaintext is a series of records concatenated
# together, each of which is LEN(filename) filename LEN(data) data. LEN() is
# 8-byte big-endian. The filename contains slashes. If 'filename' ends in a
# slash, it represents a directory, and 'data' will be empty (and LEN(data)
# will be 0). This enables empty directories.

# When the filesystem is first mounted, the contents of key.gpg are read into
# memory, and then passed (via a pipe) into a subprocess running GPG. I'm no
# great fan of GPG, but in the environments I care about, GPG is configured to
# automatically ask for a Yubikey and PIN, which is handy. The wrapped
# SecretBox key is read from the pipe and retained in RAM. Do not run this on a
# system that lacks encrypted swap.

# Each time the frontend opens a file, the entire encrypted.data is read,
# decrypted, and parsed. A tree structure is built internally, populated with
# directory objects and the plaintext contents of all files. The frontend is
# then given a filehandle that references one of these objects, and read()
# calls can pull from it.

# If the file is opened in a writable mode, each write() call modifies the
# contents of the in-memory plaintext buffer. When the file is closed, the
# entire tree is serialized (all files, not just the one that was modified), a
# new random nonce is generated, the entire thing is encrypted, the new
# ciphertext is written to encrypted.data.tmp, and then finally the file is
# atomically renamed into place.
