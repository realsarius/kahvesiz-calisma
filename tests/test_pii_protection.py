import unittest
import uuid

from app.core.pii_protection import PIIProtector


class PiiProtectionTests(unittest.TestCase):
    def test_placeholder_key_disables_encryption(self):
        protector = PIIProtector(encryption_key="change-me-32-char-min-key", hash_pepper="pepper")
        user_id = uuid.uuid4()
        plain = "Zeynep Yilmaz"

        encrypted = protector.encrypt(plain, user_id, "full_name")
        decrypted = protector.decrypt(encrypted, user_id, "full_name")

        self.assertEqual(encrypted, plain)
        self.assertEqual(decrypted, plain)

    def test_encrypt_decrypt_roundtrip_with_real_key(self):
        protector = PIIProtector(
            encryption_key="prod-like-secret-key-value-123456",
            hash_pepper="pepper-abc",
        )
        user_id = uuid.uuid4()
        plain = "Ayse Kahveci"

        encrypted = protector.encrypt(plain, user_id, "full_name")
        decrypted = protector.decrypt(encrypted, user_id, "full_name")

        self.assertNotEqual(encrypted, plain)
        self.assertEqual(decrypted, plain)

    def test_ciphertext_changes_with_user_context(self):
        protector = PIIProtector(
            encryption_key="prod-like-secret-key-value-123456",
            hash_pepper="pepper-abc",
        )
        plain = "+90 216 555 55 55"

        encrypted_a = protector.encrypt(plain, uuid.uuid4(), "phone")
        encrypted_b = protector.encrypt(plain, uuid.uuid4(), "phone")

        self.assertNotEqual(encrypted_a, encrypted_b)

    def test_wrong_context_cannot_produce_original_text(self):
        protector = PIIProtector(
            encryption_key="prod-like-secret-key-value-123456",
            hash_pepper="pepper-abc",
        )
        user_a = uuid.uuid4()
        user_b = uuid.uuid4()
        plain = "Kadikoy"

        encrypted = protector.encrypt(plain, user_a, "city")
        wrong_decrypted = protector.decrypt(encrypted, user_b, "city")

        self.assertNotEqual(wrong_decrypted, plain)


if __name__ == "__main__":
    unittest.main()

