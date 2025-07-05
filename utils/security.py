"""
Utilitaires de sécurité pour les clés API
"""

import os
import hashlib
from cryptography.fernet import Fernet
import base64

class SecurityManager:
    def __init__(self):
        self.encryption_key = self._get_or_create_key()
        self.cipher = Fernet(self.encryption_key)
    
    def _get_or_create_key(self) -> bytes:
        """Obtenir ou créer une clé de chiffrement"""
        key_file = 'data/.security_key'
        
        if os.path.exists(key_file):
            with open(key_file, 'rb') as f:
                return f.read()
        else:
            # Créer une nouvelle clé
            key = Fernet.generate_key()
            os.makedirs('data', exist_ok=True)
            with open(key_file, 'wb') as f:
                f.write(key)
            return key
    
    def encrypt_api_key(self, api_key: str) -> str:
        """Chiffrer une clé API"""
        encrypted = self.cipher.encrypt(api_key.encode())
        return base64.b64encode(encrypted).decode()
    
    def decrypt_api_key(self, encrypted_key: str) -> str:
        """Déchiffrer une clé API"""
        encrypted_bytes = base64.b64decode(encrypted_key.encode())
        decrypted = self.cipher.decrypt(encrypted_bytes)
        return decrypted.decode()
    
    def hash_api_key(self, api_key: str) -> str:
        """Créer un hash de la clé API pour vérification"""
        return hashlib.sha256(api_key.encode()).hexdigest()[:16]
    
    def validate_api_key_format(self, api_key: str, exchange: str = 'binance') -> bool:
        """Valider le format d'une clé API"""
        if exchange == 'binance':
            # Binance API keys sont généralement 64 caractères
            return len(api_key) == 64 and api_key.isalnum()
        return len(api_key) > 10  # Validation basique
