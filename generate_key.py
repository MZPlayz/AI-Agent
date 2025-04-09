from cryptography.fernet import Fernet

def generate_key():
    key = Fernet.generate_key()
    print("Generated encryption key:")
    print(key.decode())
    print("\nAdd this key to your .env file as ENCRYPTION_KEY=")

if __name__ == '__main__':
    generate_key() 