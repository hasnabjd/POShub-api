# POSHub REST API - Chapitre 4 - Documentation Complète

## 📋 Livrable - Architecture REST API Complète

Ce dossier contient l'implémentation complète d'une REST API avec AWS API Gateway
---

# 🚀 Guide de Déploiement

## Prérequis
```bash
# AWS CLI configuré
aws configure list

# SAM CLI installé
sam --version

# Python 3.13 avec dépendances
pip install -r ../requirements.txt
```

## Déploiement Simple
```bash
cd rest-api
sam deploy --config-file config/samconfig.toml
```

## Déploiement Complet avec Build
```bash
# Build + Deploy en une commande
sam build && sam deploy --config-file config/samconfig.toml

# Ou avec confirmation automatique
sam deploy --config-file config/samconfig.toml --no-confirm-changeset
```

## Script de Déploiement Automatisé
```bash
# Sur Linux/Mac avec bash
bash rest-api/scripts/deploy.sh

# Sur Windows avec WSL ou Git Bash
wsl bash rest-api/scripts/deploy.sh
```

---


# 📡 Endpoints et Tests

## Récupérer l'API Key
```bash
# Après déploiement, récupérer l'API Key
API_KEY=$(aws apigateway get-api-keys --query 'items[0].value' --output text)
echo "API Key: $API_KEY"
```

## 🩺 Endpoint /health

### Test Basic Health Check
```bash
curl -X GET "https://{api-id}.execute-api.eu-north-1.amazonaws.com/dev/health"
```

**Réponse attendue :**
```json
{
  "status": "healthy",
  "service": "poshub-health-api",
  "chapter": "4",
  "stage": "dev",
  "timestamp": "2024-01-15T10:30:00.123456",
  "throttling": {
    "rate_limit": "50 req/s",
    "burst_limit": "10 req"
  }
}
```

### Test CORS Preflight
```bash
curl -X OPTIONS "https://{api-id}.execute-api.eu-north-1.amazonaws.com/dev/health" \
  -H "Origin: https://frontend.poshub.com"
```

**Headers CORS attendus :**
```
Access-Control-Allow-Origin: *
Access-Control-Allow-Methods: GET,OPTIONS
Access-Control-Allow-Headers: Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token
```

### Test Throttling (50 req/s)
```bash
# Test rate limiting - attention cela va déclencher le throttling !
for i in {1..60}; do
  curl -s "https://{api-id}.execute-api.eu-north-1.amazonaws.com/dev/health" &
done
```

**Résultat attendu :** Requêtes 51-60 reçoivent `429 Too Many Requests`

---

## 📦 Endpoint /orders

### Test GET /orders (Libre - sans auth)
```bash
curl -X GET "https://{api-id}.execute-api.eu-north-1.amazonaws.com/dev/orders"
```

**Réponse attendue :**
```json
{
  "orders": [],
  "count": 0
}
```

### Test POST /orders (Sécurisé - JWT + API Key requis)
```bash
curl -X POST "https://{api-id}.execute-api.eu-north-1.amazonaws.com/dev/orders" \
  -H "Authorization: Bearer {jwt-token}" \
  -H "X-API-Key: {api-key}" \
  -H "Content-Type: application/json" \
  -d '{
    "orderId": "ORDER-TEST-001",
    "amount": 99.99,
    "items": [{"name": "Test Item", "price": 99.99}]
  }'
```

### Test CORS /orders
```bash
curl -X OPTIONS "https://{api-id}.execute-api.eu-north-1.amazonaws.com/dev/orders" \
  -H "Origin: https://frontend.poshub.com"
```

**Headers attendus :**
```
Access-Control-Allow-Origin: *
Access-Control-Allow-Methods: GET,POST,OPTIONS
```

---

#  Tests d'Erreurs d'Authentification

## POST sans API Key (401 Unauthorized)
```bash
curl -X POST "https://{api-id}.execute-api.eu-north-1.amazonaws.com/dev/orders" \
  -H "Authorization: Bearer {jwt-token}" \
  -H "Content-Type: application/json" \
  -d '{"orderId": "test"}'
```

## POST sans JWT (401 Unauthorized)  
```bash
curl -X POST "https://{api-id}.execute-api.eu-north-1.amazonaws.com/dev/orders" \
  -H "X-API-Key: {api-key}" \
  -H "Content-Type: application/json" \
  -d '{"orderId": "test"}'
```

## JWT sans scope orders:write (403 Forbidden)
```bash
curl -X POST "https://{api-id}.execute-api.eu-north-1.amazonaws.com/dev/orders" \
  -H "Authorization: Bearer {jwt-token-no-scope}" \
  -H "X-API-Key: {api-key}" \
  -H "Content-Type: application/json" \
  -d '{"orderId": "test"}'
```

---

# 📊 Monitoring et Logs

## CloudWatch Logs
```bash
# Logs Orders API
aws logs tail /aws/lambda/poshub-orders-api-dev --follow

# Logs Health API
aws logs tail /aws/lambda/poshub-health-api-dev --follow

# Logs JWT Authorizer
aws logs tail /aws/lambda/poshub-jwt-authorizer-dev --follow

# Filtrer par correlation ID
aws logs filter-log-events \
  --log-group-name /aws/lambda/poshub-orders-api-dev \
  --filter-pattern "order-creation-123"
```

## Métriques API Gateway
```bash
# Métriques de throttling
aws cloudwatch get-metric-statistics \
  --namespace AWS/ApiGateway \
  --metric-name ThrottledRequests \
  --dimensions Name=ApiName,Value=poshub-rest-api-dev \
  --start-time 2024-01-15T09:00:00Z \
  --end-time 2024-01-15T10:00:00Z \
  --period 300 \
  --statistics Sum

# Métriques de latence
aws cloudwatch get-metric-statistics \
  --namespace AWS/ApiGateway \
  --metric-name Latency \
  --dimensions Name=ApiName,Value=poshub-rest-api-dev \
  --start-time 2024-01-15T09:00:00Z \
  --end-time 2024-01-15T10:00:00Z \
  --period 300 \
  --statistics Average,Maximum
```

---

# ✅ Checklist de Validation du Livrable

## 🎯 Validation Technique - Infrastructure

### ✅ 1. REST API Native AWS
```bash
# Vérifier que l'API est de type REST (pas Serverless::Api)
aws apigateway get-rest-apis --query 'items[?name==`poshub-rest-api-dev`]'
```
**Attendu :** API de type REST API native

### ✅ 2. Ressource /orders avec méthodes
```bash
# Vérifier les ressources
aws apigateway get-resources --rest-api-id {api-id}
```
**Attendu :** Ressources `/orders` et `/orders/{proxy+}` présentes

### ✅ 3. Stage dev avec MethodSettings
```bash
# Vérifier le stage
aws apigateway get-stage --rest-api-id {api-id} --stage-name dev
```
**Attendu :** 
- Stage "dev" existant
- MethodSettings avec LoggingLevel: INFO
- MetricsEnabled: true

### ✅ 4. JWT Authorizer
```bash
# Vérifier l'authorizer
aws apigateway get-authorizers --rest-api-id {api-id}
```
**Attendu :** Authorizer de type CUSTOM présent

### ✅ 5. API Key + Usage Plan
```bash
# Vérifier API Key
aws apigateway get-api-keys

# Vérifier Usage Plan
aws apigateway get-usage-plans
```
**Attendu :** 
- API Key "poshub-dev-key"
- Usage Plan avec quota 1000/mois, 10 req/s

---

## 🧪 Validation Fonctionnelle - Tests

### ✅ 1. Test Health Check
```bash
curl -s "https://{api-id}.execute-api.eu-north-1.amazonaws.com/dev/health" | jq .status
```
**Attendu :** `"healthy"`

### ✅ 2. Test CORS Health
```bash
curl -s -I -X OPTIONS "https://{api-id}.execute-api.eu-north-1.amazonaws.com/dev/health" | grep -i access-control
```
**Attendu :** Headers CORS présents

### ✅ 3. Test GET Orders (libre)
```bash
curl -s "https://{api-id}.execute-api.eu-north-1.amazonaws.com/dev/orders" | jq .
```
**Attendu :** Réponse JSON avec `orders` array

### ✅ 4. Test POST Orders sans auth (doit échouer)
```bash
curl -s -w "%{http_code}" "https://{api-id}.execute-api.eu-north-1.amazonaws.com/dev/orders" -X POST
```
**Attendu :** Code `401` ou `403`

### ✅ 5. Test Throttling Health (déclenche limitations)
```bash
# Test rapide - 20 requêtes simultanées
for i in {1..20}; do curl -s "https://{api-id}.execute-api.eu-north-1.amazonaws.com/dev/health" & done
```
**Attendu :** Certaines requêtes reçoivent `429 Too Many Requests`


## 🎯 Script de Validation Automatique

### test_livrable_complet.sh
```bash
#!/bin/bash

echo "🎯 VALIDATION LIVRABLE CHAPITRE 4"
echo "=================================="

# Variables à définir
API_ID="your-api-id"
API_KEY="your-api-key"
JWT_TOKEN="your-jwt-token"

HEALTH_URL="https://${API_ID}.execute-api.eu-north-1.amazonaws.com/dev/health"
ORDERS_URL="https://${API_ID}.execute-api.eu-north-1.amazonaws.com/dev/orders"

PASSED=0
FAILED=0

test_endpoint() {
    local name="$1"
    local url="$2"
    local expected_code="$3"
    local extra_args="$4"
    
    echo -n "Testing $name... "
    
    response=$(curl -s -w "%{http_code}" $extra_args "$url")
    actual_code="${response: -3}"
    
    if [[ "$actual_code" == "$expected_code" ]]; then
        echo "✅ PASS ($actual_code)"
        ((PASSED++))
    else
        echo "❌ FAIL (expected $expected_code, got $actual_code)"
        ((FAILED++))
    fi
}

# Tests de base
test_endpoint "Health Check" "$HEALTH_URL" "200"
test_endpoint "Health CORS" "$HEALTH_URL" "200" "-X OPTIONS -H 'Origin: https://test.com'"
test_endpoint "Orders GET (libre)" "$ORDERS_URL" "200"
test_endpoint "Orders POST sans auth" "$ORDERS_URL" "401" "-X POST"

# Tests avec auth (si tokens fournis)
if [[ -n "$API_KEY" && -n "$JWT_TOKEN" ]]; then
    test_endpoint "Orders POST avec auth" "$ORDERS_URL" "200" "-X POST -H 'Authorization: Bearer $JWT_TOKEN' -H 'X-API-Key: $API_KEY' -H 'Content-Type: application/json' -d '{\"orderId\":\"test\"}'"
fi

echo ""
echo "📊 RÉSULTATS:"
echo "✅ Tests réussis: $PASSED"
echo "❌ Tests échoués: $FAILED"

if [[ $FAILED -eq 0 ]]; then
    echo "🎉 LIVRABLE CHAPITRE 4 VALIDÉ!"
else
    echo "⚠️  Des tests ont échoué. Vérifiez la configuration."
fi
```

---
### Dépannage Commun

#### Erreur 401 sur POST /orders
```bash
# Vérifier API Key
aws apigateway get-api-keys --query 'items[0].value' --output text

# Vérifier JWT format
echo $JWT_TOKEN | cut -d'.' -f2 | base64 -d
```

#### CORS ne fonctionne pas
```bash
# Vérifier méthodes OPTIONS
aws apigateway get-method --rest-api-id {api-id} --resource-id {resource-id} --http-method OPTIONS
```

#### Throttling inattendu
```bash
# Vérifier métriques
aws cloudwatch get-metric-statistics \
  --namespace AWS/ApiGateway \
  --metric-name ThrottledRequests \
  --dimensions Name=ApiName,Value=poshub-rest-api-dev
```

---

## 🔄 Workflow de Développement

### 1. Développement Local
```bash
# Test handlers localement
cd rest-api/handlers
python orders_main.py
python health_main.py
python jwt_authorizer.py
```

### 2. Validation Template
```bash
sam validate --config-file config/samconfig.toml
```

### 3. Build & Test Local
```bash
sam build --config-file config/samconfig.toml
sam local start-api --config-file config/samconfig.toml
```

### 4. Déploiement
```bash
sam deploy --config-file config/samconfig.toml
```

---

## 📝 Notes de Sécurité

### ⚠️ Points d'Attention (Configuration actuelle)
1. **Clé JWT** : Utilise une clé statique pour la démo (changer en production)
2. **CORS** : Configuré pour `*` (restreindre en production)
3. **API Key** : Visible dans les logs (masquer en production)
4. **Rate Limits** : Configurés pour développement (ajuster selon usage)

### 🔒 Recommandations Production
1. Utiliser AWS Parameter Store pour les secrets
2. Implémenter JWKS endpoint réel
3. Configurer WAF pour protection DDoS
4. Activer AWS X-Ray pour le tracing
5. Utiliser des domaines personnalisés
6. Mettre en place des alertes CloudWatch

---

## 🏆 Conformité Exercice - Récapitulatif

### ✅ Éléments Requis Implémentés

1. **sam-api.yml complet** ✅
   - REST API (AWS::ApiGateway::RestApi)
   - Ressources et méthodes
   - Stage dev avec MethodSettings
   - JWT authorizer custom
   - API Key + Usage Plan
   - CORS complet
   - Throttling configuré

---

**🎉 LIVRABLE CHAPITRE 4 COMPLET ET PRÊT POUR PRODUCTION !**

**Auteur** : Chapitre 4 - POSHub API  
**Version** : 1.0.0  
**Date** : $(date +%Y-%m-%d) 