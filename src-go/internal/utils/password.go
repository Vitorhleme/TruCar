// internal/utils/password.go
package utils

import (
	"golang.org/x/crypto/bcrypt"
)

// HashPassword usa bcrypt para gerar um hash de uma palavra-passe
func HashPassword(password string) (string, error) {
	// bcrypt.DefaultCost é 10, que é um bom equilíbrio
	bytes, err := bcrypt.GenerateFromPassword([]byte(password), bcrypt.DefaultCost)
	return string(bytes), err
}

// CheckPasswordHash compara uma palavra-passe em texto simples com o seu hash
func CheckPasswordHash(password, hash string) bool {
	err := bcrypt.CompareHashAndPassword([]byte(hash), []byte(password))
	return err == nil // Retorna 'true' se a palavra-passe corresponder
}
