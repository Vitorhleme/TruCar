// internal/handlers/user_handlers.go
package handlers

import (
	"log"
	"net/http"
	"strconv"

	"trucar-go/internal/dto"
	"trucar-go/internal/models"
	"trucar-go/internal/repository"
	"trucar-go/internal/utils"

	"github.com/gin-gonic/gin"
)

// CreateUserHandler lida com a rota POST /users
func CreateUserHandler(c *gin.Context) {
	var req dto.CreateUserRequest

	// 1. Validar o JSON de entrada
	// c.ShouldBindJSON faz o papel do Pydantic (validação + binding)
	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}

	// 2. Verificar se o email já existe
	existingUser, err := repository.GetUserByEmail(req.Email)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": "Erro ao verificar o email"})
		return
	}
	if existingUser != nil {
		c.JSON(http.StatusConflict, gin.H{"error": "Um utilizador com este email já existe"})
		return
	}

	// 3. Fazer o hash da palavra-passe
	hashedPassword, err := utils.HashPassword(req.Password)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": "Falha ao processar a palavra-passe"})
		return
	}

	// 4. Criar o modelo GORM a partir do DTO
	newUser := models.User{
		FullName:       req.FullName,
		Email:          req.Email,
		HashedPassword: hashedPassword,
		Role:           models.UserRole(req.Role), // Conversão para o nosso tipo 'enum'
		OrganizationID: req.OrganizationID,
	}

	// 5. Chamar o repositório para salvar
	createdUser, err := repository.CreateUser(&newUser)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": "Falha ao criar utilizador"})
		return
	}

	// 6. Criar e retornar a resposta DTO (sem a palavra-passe)
	response := dto.UserResponse{
		ID:         createdUser.ID,
		FullName:   createdUser.FullName,
		Email:      createdUser.Email,
		EmployeeID: createdUser.EmployeeID,
		Role:       string(createdUser.Role),
		IsActive:   createdUser.IsActive,
		AvatarURL:  createdUser.AvatarURL,
		CreatedAt:  createdUser.CreatedAt,
		UpdatedAt:  createdUser.UpdatedAt,
	}

	c.JSON(http.StatusCreated, response)
}

// GetUsersHandler lida com a rota GET /users
func GetUsersHandler(c *gin.Context) {
	// 1. Obter parâmetros de paginação (skip, limit) da query string
	// (como os 'Depends' do FastAPI)
	skipStr := c.DefaultQuery("skip", "0")
	limitStr := c.DefaultQuery("limit", "100")

	skip, err := strconv.Atoi(skipStr)
	if err != nil || skip < 0 {
		skip = 0
	}

	limit, err := strconv.Atoi(limitStr)
	if err != nil || limit <= 0 {
		limit = 100
	}

	// 2. Chamar o repositório
	users, err := repository.GetUsers(skip, limit)
	if err != nil {
		log.Printf("Erro ao buscar utilizadores: %v", err)
		c.JSON(http.StatusInternalServerError, gin.H{"error": "Falha ao buscar utilizadores"})
		return
	}

	// 3. Converter a lista de modelos GORM para uma lista de DTOs de resposta
	response := make([]dto.UserResponse, 0, len(users))
	for _, user := range users {
		response = append(response, dto.UserResponse{
			ID:         user.ID,
			FullName:   user.FullName,
			Email:      user.Email,
			EmployeeID: user.EmployeeID,
			Role:       string(user.Role),
			IsActive:   user.IsActive,
			AvatarURL:  user.AvatarURL,
			CreatedAt:  user.CreatedAt,
			UpdatedAt:  user.UpdatedAt,
		})
	}

	// 4. Retornar a lista
	c.JSON(http.StatusOK, response)
}

func GetMeHandler(c *gin.Context) {
	// 1. Obter o utilizador do contexto (definido pelo middleware)
	_user, exists := c.Get("currentUser")
	if !exists {
		// Isto não deve acontecer se o middleware estiver configurado corretamente
		c.JSON(http.StatusInternalServerError, gin.H{"error": "Erro ao obter o utilizador do contexto"})
		return
	}

	// 2. Fazer a conversão de tipo
	// (Sabemos que é 'models.User' porque o nosso middleware o definiu)
	user := _user.(models.User)

	// 3. Retornar o DTO de resposta
	response := dto.UserResponse{
		ID:         user.ID,
		FullName:   user.FullName,
		Email:      user.Email,
		EmployeeID: user.EmployeeID,
		Role:       string(user.Role),
		IsActive:   user.IsActive,
		AvatarURL:  user.AvatarURL,
		CreatedAt:  user.CreatedAt,
		UpdatedAt:  user.UpdatedAt,
	}

	c.JSON(http.StatusOK, response)
}
