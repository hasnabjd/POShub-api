"""
Utilitaires AWS pour l'intégration avec les services AWS
"""

import os
from typing import Optional

import boto3
from botocore.exceptions import ClientError

from poshub_api.logging_config import get_logger

logger = get_logger(__name__)


class SSMParameterStore:
    """Utilitaire pour interagir avec AWS Systems Manager Parameter Store."""

    def __init__(self):
        """Initialise le client SSM selon l'environnement."""
        self.region = os.getenv("AWS_REGION", "eu-north-1")
        self.ssm_client = None

        try:

            self.ssm_client = boto3.client("ssm", region_name=self.region)
            logger.info(f"SSM client initialisé pour la région: {self.region}")
        except Exception as e:
            logger.warning(f"Impossible d'initialiser le client SSM: {e}")

    def get_parameter(
        self, parameter_name: str, decrypt: bool = True
    ) -> Optional[str]:
        """
        Récupère un paramètre depuis AWS SSM Parameter Store.

        Args:
            parameter_name: Nom du paramètre SSM (ex: /pos/api-key)
            decrypt: Si True, décrypte les SecureString

        Returns:
            La valeur du paramètre ou None si erreur
        """
        if not self.ssm_client:
            logger.error("Client SSM non disponible")
            return None

        try:
            logger.info(f"Récupération du paramètre SSM: {parameter_name}")

            response = self.ssm_client.get_parameter(
                Name=parameter_name, WithDecryption=decrypt
            )

            parameter_value = response["Parameter"]["Value"]

            # ⚠️ ATTENTION: Ne JAMAIS faire cela en production !
            # Ceci est uniquement pour l'exercice de démonstration
            logger.warning(
                f"🔐 DEMO SEULEMENT - Valeur du paramètre "
                f"{parameter_name}: {parameter_value}"
            )
            logger.warning("⚠️ Ne JAMAIS logger des secrets en production !")

            return parameter_value

        except ClientError as e:
            error_code = e.response["Error"]["Code"]
            if error_code == "ParameterNotFound":
                logger.error(f"Paramètre SSM non trouvé: {parameter_name}")
            elif error_code == "AccessDenied":
                logger.error(
                    f"Accès refusé au paramètre SSM: {parameter_name}"
                )
            else:
                logger.error(f"Erreur SSM {error_code}: {e}")
            return None

        except Exception as e:
            logger.error(
                f"Erreur inattendue lors de la récupération du paramètre: {e}"
            )
            return None

    def get_multiple_parameters(
        self, parameter_names: list[str]
    ) -> dict[str, str]:
        """
        Récupère plusieurs paramètres en une seule requête.

        Args:
            parameter_names: Liste des noms de paramètres

        Returns:
            Dictionnaire {nom_paramètre: valeur}
        """
        if not self.ssm_client:
            logger.error("Client SSM non disponible")
            return {}

        try:
            logger.info(
                f"Récupération de {len(parameter_names)} paramètres SSM"
            )

            response = self.ssm_client.get_parameters(
                Names=parameter_names, WithDecryption=True
            )

            # Paramètres trouvés
            parameters = {}
            for param in response["Parameters"]:
                parameters[param["Name"]] = param["Value"]
                # ⚠️ DEMO SEULEMENT
                logger.warning(f"🔐 DEMO - {param['Name']}: {param['Value']}")

            # Paramètres non trouvés
            if response["InvalidParameters"]:
                logger.error(
                    f"Paramètres non trouvés: {response['InvalidParameters']}"
                )

            return parameters

        except Exception as e:
            logger.error(f"Erreur lors de la récupération multiple: {e}")
            return {}


def get_environment_config() -> dict[str, str]:
    """
    Récupère la configuration depuis les variables d'environnement.

    Returns:
        Configuration de l'application
    """
    config = {
        "STAGE": os.getenv("STAGE", "dev"),
        "LOG_LEVEL": os.getenv("LOG_LEVEL", "INFO"),
        "API_KEY_PARAM": os.getenv("API_KEY_PARAM", "/pos/api-key"),
        "AWS_REGION": os.getenv("AWS_REGION", "eu-west-1"),
    }

    logger.info("Configuration environnement chargée:")
    for key, value in config.items():
        if "KEY" in key or "SECRET" in key:
            logger.info(f"  {key}: ***masked***")
        else:
            logger.info(f"  {key}: {value}")

    return config


def initialize_aws_resources() -> dict[str, any]:
    """
    Initialise les ressources AWS nécessaires.

    Returns:
        Dictionnaire contenant les ressources initialisées
    """
    logger.info("Initialisation des ressources AWS...")

    # Configuration environnement
    env_config = get_environment_config()

    # Client SSM
    ssm = SSMParameterStore()

    # Récupération de l'API key depuis SSM
    api_key = None
    api_key_param = env_config["API_KEY_PARAM"]

    if api_key_param:
        api_key = ssm.get_parameter(api_key_param)
        if api_key:
            logger.info("✅ API Key récupérée depuis SSM")
        else:
            logger.warning("⚠️ API Key non disponible")

    resources = {
        "ssm": ssm,
        "config": env_config,
        "api_key": api_key,
    }

    logger.info("✅ Ressources AWS initialisées")
    return resources
