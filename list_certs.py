#!/usr/bin/env python3
from datetime import datetime, timezone
import sys
from cryptography import x509
from cryptography.hazmat import backends
from cryptography.hazmat.primitives.asymmetric.rsa import RSAPublicKey


def get_pem_certs(filename):
    certs = []
    with open(filename, 'r') as f:
        cert = ''

        for l in f:
            l = l.strip()
            if l == '-----BEGIN CERTIFICATE-----':
                cert = l + '\n'
            elif l == '-----END CERTIFICATE-----':
                cert += l + '\n'
                certs.append(cert.encode('ascii'))
            elif not l:
                continue
            else:
                cert += l + '\n'

    return certs

def print_cert_info(cert):
    # Subject
    print("S: %s" % cert.subject.rfc4514_string())

    # Issuer
    print("I: %s" % cert.issuer.rfc4514_string())

    # SAN
    try:
        SAN = cert.extensions.get_extension_for_oid(x509.ExtensionOID.SUBJECT_ALTERNATIVE_NAME)
        print("SAN:")
        for n in SAN.value:
            if isinstance(n, x509.DNSName):
                print("    DNS:  %s" % n.value)
            elif isinstance(n, x509.IPAddress):
                print("    IP:   %s" % n.value)
            elif isinstance(n, x509.RFC822Name):
                print("    MAIL: %s" % n.value)
            else:
                print("    " + str(n))

    except x509.extensions.ExtensionNotFound:
        pass

    # Validity
    now = datetime.utcnow().replace(tzinfo=timezone.utc)
    t1 = cert.not_valid_before.replace(tzinfo=timezone.utc)
    t2 = cert.not_valid_after.replace(tzinfo=timezone.utc)

    if now < t1:
        info = "not yet valid"
    elif t2 < now:
        info = "expired"
    else:
        info = "valid"

    print("Time: %s - %s (%s)" % (t1, t2, info))

    # Signature hash algorithm
    print("Signature hash algorithm: %s" % cert.signature_hash_algorithm.name)

    # Private key cipher
    pubkey = cert.public_key()
    if isinstance(pubkey, RSAPublicKey):
        cipher = "RSA %s" % pubkey.key_size
    else:
        cipher = str(pubkey)
    print("Key cipher: %s" % cipher)

def main():
    if len(sys.argv) != 2:
        print("Usage: %s <pem file>" % sys.argv[0])
        exit(1)

    for pem in get_pem_certs(sys.argv[1]):
        cert = x509.load_pem_x509_certificate(pem, backend=backends.default_backend())
        print_cert_info(cert)
        print()


if __name__ == '__main__':
    main()
    exit(0)
