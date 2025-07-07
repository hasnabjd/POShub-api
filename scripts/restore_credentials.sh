#!/bin/bash
# Script pour restaurer les credentials AWS originaux
# Usage: source scripts/restore_credentials.sh

echo "🔄 Restauration des credentials AWS originaux..."

# Vérifier s'il y a des credentials à restaurer
if [ -z "$ORIGINAL_AWS_ACCESS_KEY_ID" ] && [ -z "$ORIGINAL_AWS_SECRET_ACCESS_KEY" ]; then
    echo "⚠️ Aucun credential original trouvé"
    echo "   Les variables d'environnement AWS vont être supprimées"
    
    # Supprimer les variables d'environnement AWS
    unset AWS_ACCESS_KEY_ID
    unset AWS_SECRET_ACCESS_KEY
    unset AWS_SESSION_TOKEN
    unset AWS_DEFAULT_REGION
    unset POSHUB_STAGE
    unset POSHUB_ROLE_ARN
    
    echo "✅ Variables d'environnement AWS supprimées"
else
    # Restaurer les credentials originaux
    export AWS_ACCESS_KEY_ID="$ORIGINAL_AWS_ACCESS_KEY_ID"
    export AWS_SECRET_ACCESS_KEY="$ORIGINAL_AWS_SECRET_ACCESS_KEY"
    export AWS_SESSION_TOKEN="$ORIGINAL_AWS_SESSION_TOKEN"
    export AWS_DEFAULT_REGION="$ORIGINAL_AWS_DEFAULT_REGION"
    
    # Nettoyer les variables de sauvegarde
    unset ORIGINAL_AWS_ACCESS_KEY_ID
    unset ORIGINAL_AWS_SECRET_ACCESS_KEY
    unset ORIGINAL_AWS_SESSION_TOKEN
    unset ORIGINAL_AWS_DEFAULT_REGION
    unset POSHUB_STAGE
    unset POSHUB_ROLE_ARN
    
    echo "✅ Credentials AWS originaux restaurés"
fi

# Vérifier l'identité actuelle
echo "🔍 Identité AWS actuelle:"
aws sts get-caller-identity --output table 2>/dev/null || echo "❌ Aucune identité AWS configurée" 