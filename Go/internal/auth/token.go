// internal/auth/token.go
package auth

import (
	// (imports continuam iguais)

	"github.com/golang-jwt/jwt/v5"
)

// Claims reflete a estrutura do token gerado pelo Python.
// O Python coloca o ID do utilizador no campo "sub" (Subject).
type Claims struct {
	// Removemos UserID, Email, Role daqui
	jwt.RegisteredClaims
}

// (A função GenerateAccessToken pode ser apagada deste ficheiro,
// pois o Go já não vai gerar tokens, apenas validá-los)
