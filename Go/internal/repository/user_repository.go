// internal/repository/user_repository.go
package repository

import (
	"trucar-go/internal/db"     // A nossa ligação à BD
	"trucar-go/internal/models" // Os nossos modelos GORM

	"gorm.io/gorm"
)

// (Função auxiliar para geração de EmployeeID - como no seu user_model.py)
// NOTA: Em Go, não há um UUID v4 nativo fácil sem libs. Vamos usar um placeholder.
// Em produção, usaríamos uma lib como 'go.uuid' ou 'google/uuid'.
// Por agora, vamos simplificar.
func generateEmployeeID() string {
	// Placeholder simples.
	// TODO: Substituir por uma geração de ID mais robusta
	return "TRC-TEMP-ID"
}

// CreateUser cria um novo utilizador na base de dados
// Equivalente ao seu crud.user.create()
func CreateUser(user *models.User) (*models.User, error) {
	// Definir valores padrão
	user.IsActive = true
	user.EmployeeID = generateEmployeeID() // (Usando o nosso placeholder)

	// db.DB é a nossa instância GORM global do session.go
	if err := db.DB.Create(user).Error; err != nil {
		return nil, err
	}
	return user, nil
}

// GetUsers retorna uma lista de utilizadores com paginação
// Equivalente ao seu crud.user.get_multi()
func GetUsers(skip int, limit int) ([]models.User, error) {
	var users []models.User

	// .Offset(skip).Limit(limit) é o equivalente GORM
	if err := db.DB.Offset(skip).Limit(limit).Find(&users).Error; err != nil {
		return nil, err
	}
	return users, nil
}

// GetUserByEmail encontra um utilizador pelo seu email
// Equivalente ao seu crud.user.get_by_email()
func GetUserByEmail(email string) (*models.User, error) {
	var user models.User

	// .First() procura o primeiro registo. Se não encontrar, retorna gorm.ErrRecordNotFound
	if err := db.DB.Where("email = ?", email).First(&user).Error; err != nil {
		if err == gorm.ErrRecordNotFound {
			return nil, nil // Não é um erro, apenas não encontrou
		}
		return nil, err // Um erro real da BD
	}
	return &user, nil
}

func GetUserByID(id uint) (*models.User, error) {
	var user models.User
	if err := db.DB.First(&user, id).Error; err != nil {
		if err == gorm.ErrRecordNotFound {
			return nil, nil // Não encontrou
		}
		return nil, err // Erro da BD
	}
	return &user, nil
}
