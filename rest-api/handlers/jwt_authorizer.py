"""
JWT Authorizer pour POSHub REST API - Chapitre 4
Lambda Authorizer autonome pour valider les tokens JWT et vérifier les scopes
"""
import json
import jwt
import os
import sys
from typing import Dict, Any

# Ajouter le chemin src au PYTHONPATH pour les imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../src'))

from poshub_api.logging_config import configure_logging, get_logger

# Configure logging
configure_logging()
logger = get_logger(__name__)

# Configuration JWT
JWT_ISSUER = os.getenv("JWT_ISSUER", "https://auth.poshub.internal")
JWT_AUDIENCE = os.getenv("JWT_AUDIENCE", "poshub-api")

# Cache pour les clés publiques JWKS (en production, utiliser Redis/DynamoDB)
JWKS_CACHE = {}

def get_public_key(token_header: Dict[str, Any]) -> str:
    """
    Récupère la clé publique depuis JWKS endpoint.
    En production, ceci devrait être mis en cache.
    """
    try:
        # Pour la démo, on utilise une clé statique
        # En production, récupérer depuis /.well-known/jwks.json
        demo_public_key = """-----BEGIN PUBLIC KEY-----
MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEA4f5wg5l2hKsTeNem/V41
fGnJm6gOdrj8ym3rFkEjWT3z5wYA0LRZ1PdGYnqxlm7T8kNhQZyZ5r7jP4hL1gA
9j9sF1HfE6ooP2D8XpZ0nG8k3fHn2tJ9RrE4i4uU1P0KzHg8W1OGo5P1fBCj8E
-----END PUBLIC KEY-----"""
        return demo_public_key
    except Exception as e:
        logger.error(f"Erreur récupération clé publique: {e}")
        raise Exception("Unauthorized")

def validate_jwt_token(token: str) -> Dict[str, Any]:
    """Valide le token JWT et retourne les claims."""
    try:
        # Décoder le header pour récupérer kid
        header = jwt.get_unverified_header(token)
        
        # Récupérer la clé publique
        public_key = get_public_key(header)
        
        # Décoder et valider le token
        decoded_token = jwt.decode(
            token,
            public_key,
            algorithms=["RS256"],
            issuer=JWT_ISSUER,
            audience=JWT_AUDIENCE,
            options={"verify_exp": True}
        )
        
        logger.info(f"Token JWT valide pour user: {decoded_token.get('sub', 'unknown')}")
        return decoded_token
        
    except jwt.ExpiredSignatureError:
        logger.warning("Token JWT expiré")
        raise Exception("Token expired")
    except jwt.InvalidTokenError as e:
        logger.warning(f"Token JWT invalide: {e}")
        raise Exception("Invalid token")
    except Exception as e:
        logger.error(f"Erreur validation JWT: {e}")
        raise Exception("Unauthorized")

def check_required_scope(decoded_token: Dict[str, Any], required_scope: str) -> bool:
    """Vérifie si le token contient le scope requis."""
    scopes = decoded_token.get("scopes", [])
    if isinstance(scopes, str):
        scopes = scopes.split(" ")
    
    has_scope = required_scope in scopes
    logger.info(f"Vérification scope '{required_scope}': {has_scope}, scopes disponibles: {scopes}")
    return has_scope

def generate_policy(principal_id: str, effect: str, resource: str, context: Dict = None) -> Dict[str, Any]:
    """Génère la policy IAM pour autoriser/refuser l'accès."""
    policy = {
        "principalId": principal_id,
        "policyDocument": {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Action": "execute-api:Invoke",
                    "Effect": effect,
                    "Resource": resource
                }
            ]
        }
    }
    
    if context:
        policy["context"] = context
    
    return policy

def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Lambda Authorizer Function pour valider les tokens JWT - Chapitre 4.
    
    Event structure:
    {
        "type": "REQUEST",
        "authorizationToken": "Bearer <token>",
        "methodArn": "arn:aws:execute-api:..."
    }
    """
    try:
        logger.info("JWT Authorizer invoqué (Chapitre 4)")
        logger.debug(f"Event reçu: {json.dumps(event, default=str)}")
        
        # Extraire le token Authorization
        auth_token = event.get("authorizationToken", "")
        method_arn = event.get("methodArn", "")
        
        if not auth_token:
            logger.warning("Header Authorization manquant")
            raise Exception("Unauthorized")
        
        # Vérifier le format "Bearer <token>"
        if not auth_token.startswith("Bearer "):
            logger.warning("Format Authorization invalide - doit être 'Bearer <token>'")
            raise Exception("Unauthorized")
        
        # Extraire le token
        token = auth_token.replace("Bearer ", "")
        
        # Valider le token JWT
        decoded_token = validate_jwt_token(token)
        
        # Extraire les informations utilisateur
        user_id = decoded_token.get("sub", "unknown")
        username = decoded_token.get("username", "unknown")
        
        # Vérifier le scope requis pour orders:write
        if not check_required_scope(decoded_token, "orders:write"):
            logger.warning(f"Scope 'orders:write' manquant pour user {username}")
            raise Exception("Insufficient scope")
        
        # Générer policy ALLOW avec contexte utilisateur
        policy = generate_policy(
            principal_id=user_id,
            effect="Allow",
            resource=method_arn,
            context={
                "userId": user_id,
                "username": username,
                "scopes": ",".join(decoded_token.get("scopes", []))
            }
        )
        
        logger.info(f"Autorisation accordée pour user {username} sur {method_arn}")
        return policy
        
    except Exception as e:
        logger.error(f"Autorisation refusée: {e}")
        
        # En cas d'erreur, refuser l'accès
        # Note: On pourrait aussi lever une exception, mais retourner DENY est plus propre
        return generate_policy(
            principal_id="unauthorized",
            effect="Deny",
            resource=event.get("methodArn", "*")
        )

# Pour les tests locaux
if __name__ == "__main__":
    # Test event de base
    test_event = {
        "type": "REQUEST",
        "authorizationToken": "Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJSUzI1NiJ9...",
        "methodArn": "arn:aws:execute-api:eu-north-1:123456789:abcd1234/dev/POST/orders"
    }
    
    result = lambda_handler(test_event, None)
    print(json.dumps(result, indent=2)) 