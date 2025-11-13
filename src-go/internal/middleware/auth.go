// internal/middleware/auth.go
package middleware

import (
	"fmt"
	"log"
	"net/http"
	"strconv" // <-- IMPORTAR STRCONV
	"strings"

	"trucar-go/internal/auth"
	"trucar-go/internal/config"
	"trucar-go/internal/repository"

	"github.com/gin-gonic/gin"
	"github.com/golang-jwt/jwt/v5"
)

func AuthMiddleware() gin.HandlerFunc {
	return func(c *gin.Context) {

		// --- ADICIONE ESTA LINHA ---
		log.Println("[DEBUG-AUTH] O MIDDLEWARE DE AUTENTICAÇÃO FOI EXECUTADO!")
		// ---------------------------

		authHeader := c.GetHeader("Authorization")
		log.Printf("[DEBUG-AUTH] Header recebido: %s", authHeader) // Esta linha já devia lá estar

		if authHeader == "" {
			c.AbortWithStatusJSON(http.StatusUnauthorized, gin.H{"error": "Header de autorização em falta"})
			return
		}
		tokenString := strings.TrimPrefix(authHeader, "Bearer ")
		// ...

		// 1. Validar o Token JWT
		claims := &auth.Claims{} // <-- Usa a nossa nova struct Claims simplificada
		token, err := jwt.ParseWithClaims(tokenString, claims, func(token *jwt.Token) (interface{}, error) {
			if _, ok := token.Method.(*jwt.SigningMethodHMAC); !ok {
				return nil, fmt.Errorf("método de assinatura inesperado: %v", token.Header["alg"])
			}
			return []byte(config.AppConfig.SecretKey), nil
		})

		if err != nil || !token.Valid {
			log.Printf("[DEBUG-AUTH] Erro ao validar o token: %v", err)
			c.AbortWithStatusJSON(http.StatusUnauthorized, gin.H{"error": "Token inválido ou expirado"})
			return
		}

		// --- ALTERAÇÃO PRINCIPAL AQUI ---
		// 2. Extrair o User ID do campo "Subject" (sub)
		userIDStr, err := claims.GetSubject()
		if err != nil {
			c.AbortWithStatusJSON(http.StatusUnauthorized, gin.H{"error": "Claim 'sub' do token inválido"})
			return
		}

		userID, err := strconv.ParseUint(userIDStr, 10, 64)
		if err != nil {
			c.AbortWithStatusJSON(http.StatusUnauthorized, gin.H{"error": "Não foi possível interpretar o ID do utilizador do token"})
			return
		}
		// --- FIM DA ALTERAÇÃO ---

		// 3. O Token é válido! Vamos verificar se o utilizador existe na BD do Go
		user, err := repository.GetUserByID(uint(userID)) // <-- Usar o userID convertido
		if err != nil || user == nil {
			c.AbortWithStatusJSON(http.StatusUnauthorized, gin.H{"error": "Utilizador do token não encontrado"})
			return
		}

		if !user.IsActive {
			c.AbortWithStatusJSON(http.StatusForbidden, gin.H{"error": "Conta inativa"})
			return
		}

		c.Set("currentUser", *user)
		c.Next()
	}
}
