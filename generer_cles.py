from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization

# Générer la clé privée
private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)

# Sauvegarder la clé privée (format .p8)
with open("rsa_key.p8", "wb") as f:
    f.write(private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption()
    ))

# Sauvegarder la clé publique
public_key = private_key.public_key()
with open("rsa_key.pub", "wb") as f:
    f.write(public_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo
    ))

print("Clés générées avec succès !")