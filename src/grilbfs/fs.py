# This FUSE module implements an encrypted filesystem aimed for
# small-to-moderate sized read-mostly data. The backing store contains two
# files: a GPG-wrapped NaCl encryption key ("key.gpg"), and an single encrypted
# aggregate of all the plaintext ("encrypted.data").

# The module is invoked with two arguments. The first is the mountpoint (an
# empty directory that will be "replaced" by the virtual filesystem). The
# second is the backing directory, which will contain the two files described
# above.

# The body of key.gpg is a 32-byte NaCl "SecretBox" key. The encrypted.data
# file starts with an 8-byte counter (big-endian), a random 24-byte nonce, and
# the remainder is SecretBox-encrypted. The plaintext is a series of records
# concatenated together, each of which is LEN(filename) filename LEN(data)
# data. LEN() is 8-byte big-endian. The filename contains slashes. If
# 'filename' ends in a slash, it represents a directory, and 'data' will be
# empty (and LEN(data) will be 0). This enables empty directories.

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
# counter is incremented, the entire tree is serialized (all files, not just
# the one that was modified), a new random nonce is generated, the entire thing
# is encrypted, the new ciphertext is written to encrypted.data.tmp, and then
# finally the file is atomically renamed into place.


# Extensions:

# --keyid= (base32 string, hash of secretbox key): if provided, the decrypted
# key.gpg contents will be checked against this value, and the filesystem will
# refuse to mount if they do not match. This protects against a corrupted
# backing store, where the attacker creates their own secretbox key, uses your
# GPG public key to wrap it into key.gpg, and puts their own data into
# encrypted.data. This cannot help them learn your old data, but they could
# trick you into writing new data to a key that they control, and they could
# trick you into relying upon (and perhaps executing) data of their choosing.

# --keyidfile=: points to a local file (e.g. ~/.grilbfs-keyid). If this file
# does not already exist, it will be populated with a hash of the secretbox
# key. If it does exist, its contents will be used as if passed to --keyid=. If
# keyidfile points to a trusted local disk, and the backing store is on a
# network drive, then this will protect you against the network drive
# substituting a different key.gpg (and encrypted.data).

# --statefile=: points to a local file (e.g. ~/.grilbfs-state). Each time
# encrypted.data is replaced, the new counter value is written to the state
# file. Upon read, the contents of encrypted.data will be rejected unless
# counter value is equal or higher than the statefile. If --statefile= points
# to a trusted local disk, this protects you against the backing store being
# rewound to an earlier version.

