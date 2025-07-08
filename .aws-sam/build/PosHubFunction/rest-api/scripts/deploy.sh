#!/bin/bash

# Script de déploiement automatisé pour POSHub REST API - Chapitre 4
# Usage: ./scripts/deploy.sh [--no-confirm] [--stage dev|staging|prod]

set -e

# Couleurs pour l'affichage
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration par défaut
STAGE="dev"
CONFIRM=true
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REST_API_DIR="$(dirname "$SCRIPT_DIR")"
PROJECT_ROOT="$(dirname "$REST_API_DIR")"

echo -e "${BLUE}🚀 POSHub REST API - Script de Déploiement Chapitre 4${NC}"
echo "=================================================="

# Traitement des arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --no-confirm)
            CONFIRM=false
            shift
            ;;
        --stage)
            STAGE="$2"
            shift 2
            ;;
        -h|--help)
            echo "Usage: $0 [--no-confirm] [--stage dev|staging|prod]"
            echo ""
            echo "Options:"
            echo "  --no-confirm    Déployer sans confirmation"
            echo "  --stage STAGE   Stage de déploiement (dev, staging, prod)"
            echo "  -h, --help      Afficher cette aide"
            exit 0
            ;;
        *)
            echo -e "${RED}❌ Option inconnue: $1${NC}"
            exit 1
            ;;
    esac
done

# Validation du stage
if [[ ! "$STAGE" =~ ^(dev|staging|prod)$ ]]; then
    echo -e "${RED}❌ Stage invalide: $STAGE. Utilisez dev, staging ou prod.${NC}"
    exit 1
fi

echo -e "${YELLOW}📋 Configuration:${NC}"
echo "  - Stage: $STAGE"
echo "  - Répertoire: $REST_API_DIR"
echo "  - Confirmation: $CONFIRM"

# Vérifications des prérequis
echo -e "\n${YELLOW}🔍 Vérification des prérequis...${NC}"

# Vérifier AWS CLI
if ! command -v aws &> /dev/null; then
    echo -e "${RED}❌ AWS CLI non trouvé. Installez AWS CLI.${NC}"
    exit 1
fi

# Vérifier SAM CLI
if ! command -v sam &> /dev/null; then
    echo -e "${RED}❌ SAM CLI non trouvé. Installez SAM CLI.${NC}"
    exit 1
fi

# Vérifier les credentials AWS
if ! aws sts get-caller-identity &> /dev/null; then
    echo -e "${RED}❌ Credentials AWS non configurés. Exécutez 'aws configure'.${NC}"
    exit 1
fi

# Vérifier Python 3.13
if ! python3 --version | grep -q "3.13"; then
    echo -e "${YELLOW}⚠️  Python 3.13 recommandé. Version détectée: $(python3 --version)${NC}"
fi

echo -e "${GREEN}✅ Prérequis OK${NC}"

# Se déplacer dans le répertoire REST API
cd "$REST_API_DIR"

# Vérifier les fichiers requis
echo -e "\n${YELLOW}📁 Vérification des fichiers...${NC}"

required_files=(
    "sam-api.yml"
    "config/samconfig.toml"
    "handlers/orders_main.py"
    "handlers/health_main.py"
    "handlers/jwt_authorizer.py"
)

for file in "${required_files[@]}"; do
    if [[ ! -f "$file" ]]; then
        echo -e "${RED}❌ Fichier manquant: $file${NC}"
        exit 1
    fi
done

echo -e "${GREEN}✅ Fichiers requis présents${NC}"

# Vérifier les dépendances Python
echo -e "\n${YELLOW}📦 Vérification des dépendances Python...${NC}"

if [[ -f "$PROJECT_ROOT/requirements.txt" ]]; then
    # Vérifier si PyJWT est présent
    if ! grep -q "PyJWT" "$PROJECT_ROOT/requirements.txt"; then
        echo -e "${YELLOW}⚠️  PyJWT manquant dans requirements.txt. Ajout automatique...${NC}"
        echo "PyJWT>=2.8.0,<3.0.0" >> "$PROJECT_ROOT/requirements.txt"
    fi
    echo -e "${GREEN}✅ Dépendances OK${NC}"
else
    echo -e "${RED}❌ requirements.txt non trouvé dans $PROJECT_ROOT${NC}"
    exit 1
fi

# Affichage de la configuration de déploiement
echo -e "\n${YELLOW}⚙️  Configuration de déploiement:${NC}"
echo "  - Stack Name: poshub-rest-api-chapter4"
echo "  - Region: eu-north-1"
echo "  - Stage: $STAGE"
echo "  - Template: sam-api.yml"

# Confirmation utilisateur
if [[ "$CONFIRM" == true ]]; then
    echo -e "\n${YELLOW}❓ Continuer le déploiement? (y/N)${NC}"
    read -r response
    if [[ ! "$response" =~ ^[Yy]$ ]]; then
        echo -e "${YELLOW}⏹️  Déploiement annulé.${NC}"
        exit 0
    fi
fi

# Validation du template SAM
echo -e "\n${YELLOW}🔍 Validation du template SAM...${NC}"
if sam validate --template-file sam-api.yml; then
    echo -e "${GREEN}✅ Template SAM valide${NC}"
else
    echo -e "${RED}❌ Template SAM invalide${NC}"
    exit 1
fi

# Build
echo -e "\n${YELLOW}🔨 Build du projet SAM...${NC}"
if sam build --config-file config/samconfig.toml; then
    echo -e "${GREEN}✅ Build réussi${NC}"
else
    echo -e "${RED}❌ Échec du build${NC}"
    exit 1
fi

# Déploiement
echo -e "\n${YELLOW}🚀 Déploiement en cours...${NC}"

deploy_cmd="sam deploy --config-file config/samconfig.toml --parameter-overrides Stage=\"$STAGE\""

if [[ "$CONFIRM" == false ]]; then
    deploy_cmd="$deploy_cmd --no-confirm-changeset"
fi

echo "Commande: $deploy_cmd"

if eval $deploy_cmd; then
    echo -e "\n${GREEN}🎉 Déploiement réussi!${NC}"
else
    echo -e "\n${RED}❌ Échec du déploiement${NC}"
    exit 1
fi

# Récupération des outputs
echo -e "\n${YELLOW}📊 Récupération des informations de déploiement...${NC}"

STACK_NAME="poshub-rest-api-chapter4"

# Fonction pour récupérer un output
get_stack_output() {
    aws cloudformation describe-stacks \
        --stack-name "$STACK_NAME" \
        --query "Stacks[0].Outputs[?OutputKey=='$1'].OutputValue" \
        --output text 2>/dev/null || echo "N/A"
}

REST_API_URL=$(get_stack_output "RestApiUrl")
HEALTH_ENDPOINT=$(get_stack_output "HealthEndpoint")
ORDERS_ENDPOINT=$(get_stack_output "OrdersEndpoint")
API_KEY_ID=$(get_stack_output "ApiKeyId")

echo -e "\n${GREEN}🌐 Endpoints déployés:${NC}"
echo "  - API Base URL: $REST_API_URL"
echo "  - Health Check: $HEALTH_ENDPOINT"
echo "  - Orders API: $ORDERS_ENDPOINT"

if [[ "$API_KEY_ID" != "N/A" ]]; then
    echo -e "\n${YELLOW}🔑 Récupération de l'API Key...${NC}"
    API_KEY_VALUE=$(aws apigateway get-api-key --api-key "$API_KEY_ID" --include-value --query 'value' --output text 2>/dev/null || echo "N/A")
    
    if [[ "$API_KEY_VALUE" != "N/A" ]]; then
        echo -e "${GREEN}🔐 API Key: $API_KEY_VALUE${NC}"
    else
        echo -e "${YELLOW}⚠️  Impossible de récupérer la valeur de l'API Key${NC}"
    fi
fi

# Tests de base
echo -e "\n${YELLOW}🧪 Tests de base...${NC}"

if [[ "$HEALTH_ENDPOINT" != "N/A" ]]; then
    echo "Test health check..."
    if curl -s -f "$HEALTH_ENDPOINT" > /dev/null; then
        echo -e "${GREEN}✅ Health check OK${NC}"
    else
        echo -e "${YELLOW}⚠️  Health check en cours d'initialisation...${NC}"
    fi
fi

# Exemples d'utilisation
echo -e "\n${BLUE}📖 Exemples d'utilisation:${NC}"
echo ""
echo "1. Test health check:"
echo "   curl -X GET \"$HEALTH_ENDPOINT\""
echo ""
echo "2. Test GET orders (libre):"
echo "   curl -X GET \"$ORDERS_ENDPOINT\""
echo ""

if [[ "$API_KEY_VALUE" != "N/A" ]]; then
    echo "3. Test POST orders (avec JWT + API Key):"
    echo "   curl -X POST \"$ORDERS_ENDPOINT\" \\"
    echo "     -H \"Authorization: Bearer <YOUR_JWT_TOKEN>\" \\"
    echo "     -H \"X-API-Key: $API_KEY_VALUE\" \\"
    echo "     -H \"Content-Type: application/json\" \\"
    echo "     -d '{\"orderId\": \"test-001\", \"amount\": 99.99}'"
    echo ""
fi

echo "4. Monitoring logs:"
echo "   aws logs tail /aws/lambda/poshub-orders-api-$STAGE --follow"
echo "   aws logs tail /aws/lambda/poshub-health-api-$STAGE --follow"
echo ""

echo "5. Documentation complète:"
echo "   cat rest-api/README.md"
echo "   cat rest-api/examples/orders_calls.md"
echo "   cat rest-api/examples/health_calls.md"

echo -e "\n${GREEN}🎯 Déploiement Chapitre 4 terminé avec succès!${NC}"
echo -e "${BLUE}📚 Consultez rest-api/README.md pour la documentation complète.${NC}" 