#!/bin/bash
# Script pour assumer le rôle IAM Lambda et exporter les credentials temporaires
# Usage: source scripts/assume_lambda_role.sh dev
# Usage: source scripts/assume_lambda_role.sh prod

set -e

# Configuration par défaut
DEFAULT_STAGE="dev"
DEFAULT_REGION="eu-west-1"
DEFAULT_DURATION="3600"  # 1 heure

# Paramètres
STAGE=${1:-$DEFAULT_STAGE}
REGION=${2:-$DEFAULT_REGION}
DURATION=${3:-$DEFAULT_DURATION}

# Validation du stage
if [[ ! "$STAGE" =~ ^(dev|staging|prod)$ ]]; then
    echo "❌ Stage invalide. Utilisez: dev, staging, ou prod"
    exit 1
fi

# Configuration du rôle
ROLE_NAME="poshub-execution-role-${STAGE}"
SESSION_NAME="poshub-dev-session-$(date +%s)"

echo "🔐 Assumption du rôle IAM pour POSHub API"
echo "   Stage: $STAGE"
echo "   Region: $REGION"
echo "   Role: $ROLE_NAME"
echo "   Duration: ${DURATION}s"

# Obtenir l'Account ID
echo "🔍 Récupération de l'Account ID..."
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text --region $REGION)
if [ -z "$ACCOUNT_ID" ]; then
    echo "❌ Impossible de récupérer l'Account ID"
    exit 1
fi
echo "✅ Account ID: $ACCOUNT_ID"

# Construire l'ARN du rôle
ROLE_ARN="arn:aws:iam::${ACCOUNT_ID}:role/${ROLE_NAME}"
echo "🎯 Role ARN: $ROLE_ARN"

# Vérifier que le rôle existe
echo "🔍 Vérification de l'existence du rôle..."
if ! aws iam get-role --role-name $ROLE_NAME --region $REGION >/dev/null 2>&1; then
    echo "❌ Rôle non trouvé: $ROLE_NAME"
    echo "💡 Créez le rôle avec:"
    echo "   sam deploy --stack-name poshub-${STAGE}"
    echo "   ou"
    echo "   python scripts/deploy_manual.py --stage $STAGE"
    exit 1
fi
echo "✅ Rôle trouvé"

# Assumer le rôle
echo "🔄 Assumption du rôle en cours..."
ASSUME_ROLE_OUTPUT=$(aws sts assume-role \
    --role-arn "$ROLE_ARN" \
    --role-session-name "$SESSION_NAME" \
    --duration-seconds "$DURATION" \
    --region "$REGION" \
    --output json)

if [ $? -ne 0 ]; then
    echo "❌ Échec de l'assumption du rôle"
    echo "💡 Vérifiez que votre utilisateur a les permissions sts:AssumeRole"
    exit 1
fi

# Extraire les credentials
ACCESS_KEY=$(echo $ASSUME_ROLE_OUTPUT | jq -r '.Credentials.AccessKeyId')
SECRET_KEY=$(echo $ASSUME_ROLE_OUTPUT | jq -r '.Credentials.SecretAccessKey')
SESSION_TOKEN=$(echo $ASSUME_ROLE_OUTPUT | jq -r '.Credentials.SessionToken')
EXPIRATION=$(echo $ASSUME_ROLE_OUTPUT | jq -r '.Credentials.Expiration')

# Validation des credentials
if [ "$ACCESS_KEY" = "null" ] || [ "$SECRET_KEY" = "null" ] || [ "$SESSION_TOKEN" = "null" ]; then
    echo "❌ Credentials invalides récupérés"
    exit 1
fi

# Exporter les variables d'environnement
export AWS_ACCESS_KEY_ID="$ACCESS_KEY"
export AWS_SECRET_ACCESS_KEY="$SECRET_KEY"
export AWS_SESSION_TOKEN="$SESSION_TOKEN"
export AWS_DEFAULT_REGION="$REGION"
export POSHUB_STAGE="$STAGE"
export POSHUB_ROLE_ARN="$ROLE_ARN"

# Sauvegarde des credentials originaux (pour restauration)
if [ -n "$ORIGINAL_AWS_ACCESS_KEY_ID" ]; then
    echo "⚠️ Credentials AWS déjà sauvegardés"
else
    export ORIGINAL_AWS_ACCESS_KEY_ID="${AWS_ACCESS_KEY_ID:-}"
    export ORIGINAL_AWS_SECRET_ACCESS_KEY="${AWS_SECRET_ACCESS_KEY:-}"
    export ORIGINAL_AWS_SESSION_TOKEN="${AWS_SESSION_TOKEN:-}"
    export ORIGINAL_AWS_DEFAULT_REGION="${AWS_DEFAULT_REGION:-}"
fi

echo "✅ Rôle assumé avec succès!"
echo "   Access Key: ${ACCESS_KEY:0:10}..."
echo "   Expiration: $EXPIRATION"
echo ""
echo "🚀 Variables d'environnement exportées:"
echo "   AWS_ACCESS_KEY_ID"
echo "   AWS_SECRET_ACCESS_KEY"
echo "   AWS_SESSION_TOKEN"
echo "   AWS_DEFAULT_REGION=$REGION"
echo "   POSHUB_STAGE=$STAGE"
echo "   POSHUB_ROLE_ARN=$ROLE_ARN"
echo ""
echo "💡 Commandes utiles:"
echo "   # Tester l'identité"
echo "   aws sts get-caller-identity"
echo ""
echo "   # Invoquer la Lambda"
echo "   sam local invoke PosHubFunction"
echo ""
echo "   # Déployer"
echo "   sam deploy --stack-name poshub-${STAGE}"
echo ""
echo "   # Restaurer les credentials originaux"
echo "   source scripts/restore_credentials.sh"
echo ""
echo "⏰ Session valide jusqu'à: $EXPIRATION" 