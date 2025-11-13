// internal/handlers/vehicle_handlers.go
package handlers

import (
	"net/http"
	"strconv"

	"gorm.io/gorm"

	"trucar-go/internal/dto"
	"trucar-go/internal/models"
	"trucar-go/internal/repository"

	"github.com/gin-gonic/gin"
)

// helperGetCurrentUser (função auxiliar para evitar repetição)
// Ela obtém o utilizador que o nosso middleware de autenticação colocou no contexto.
func helperGetCurrentUser(c *gin.Context) (models.User, bool) {
	_user, exists := c.Get("currentUser")
	if !exists {
		c.JSON(http.StatusUnauthorized, gin.H{"error": "Utilizador não encontrado no contexto"})
		return models.User{}, false
	}
	user, ok := _user.(models.User)
	if !ok {
		c.JSON(http.StatusInternalServerError, gin.H{"error": "Falha ao converter utilizador no contexto"})
		return models.User{}, false
	}
	return user, true
}

// CreateVehicleHandler (POST /vehicles)
func CreateVehicleHandler(c *gin.Context) {
	// 1. Obter o utilizador autenticado
	currentUser, ok := helperGetCurrentUser(c)
	if !ok {
		return // O erro já foi enviado pela função auxiliar
	}

	// 2. Validar o JSON de entrada (o DTO)
	var req dto.CreateVehicleRequest
	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}

	// 3. Verificar se a matrícula já existe *nessa organização*
	_, err := repository.GetVehicleByLicensePlate(currentUser.OrganizationID, req.LicensePlate)
	if err == nil {
		// Encontrou um veículo, o que é um erro (conflito)
		c.JSON(http.StatusConflict, gin.H{"error": "Um veículo com esta matrícula já existe na sua organização"})
		return
	}
	if err != gorm.ErrRecordNotFound {
		// Um erro diferente de "não encontrado" (ex: falha de BD)
		c.JSON(http.StatusInternalServerError, gin.H{"error": "Erro ao verificar a matrícula"})
		return
	}

	// 4. Criar o modelo GORM
	vehicle := models.Vehicle{
		LicensePlate:    req.LicensePlate,
		Brand:           req.Brand,
		Model:           req.Model,
		Year:            req.Year,
		VehicleType:     models.VehicleType(req.VehicleType),
		Status:          models.VehicleStatus(req.Status),
		CurrentOdometer: req.CurrentOdometer,
		InitialOdometer: req.CurrentOdometer,        // Valor inicial é o atual na criação
		OrganizationID:  currentUser.OrganizationID, // Segurança: Força a organização do utilizador
	}
	if req.PhotoURL != "" {
		vehicle.PhotoURL = &req.PhotoURL
	}
	if vehicle.Status == "" {
		vehicle.Status = models.VehicleStatusActive // Default
	}

	// 5. Salvar na base de dados
	createdVehicle, err := repository.CreateVehicle(&vehicle)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": "Falha ao criar o veículo"})
		return
	}

	// 6. Retornar a resposta DTO
	response := dto.VehicleResponse{
		ID:              createdVehicle.ID,
		LicensePlate:    createdVehicle.LicensePlate,
		Brand:           createdVehicle.Brand,
		Model:           createdVehicle.Model,
		Year:            createdVehicle.Year,
		VehicleType:     string(createdVehicle.VehicleType),
		Status:          string(createdVehicle.Status),
		CurrentOdometer: createdVehicle.CurrentOdometer,
		PhotoURL:        createdVehicle.PhotoURL,
		OrganizationID:  createdVehicle.OrganizationID,
		CreatedAt:       createdVehicle.CreatedAt,
	}
	c.JSON(http.StatusCreated, response)
}

// GetVehiclesHandler (GET /vehicles)
func GetVehiclesHandler(c *gin.Context) {
	// 1. Obter o utilizador autenticado
	currentUser, ok := helperGetCurrentUser(c)
	if !ok {
		return
	}

	// 2. Obter paginação
	skipStr := c.DefaultQuery("skip", "0")
	limitStr := c.DefaultQuery("limit", "100")
	skip, _ := strconv.Atoi(skipStr)
	limit, _ := strconv.Atoi(limitStr)

	// 3. Chamar o repositório (com filtro de segurança)
	vehicles, err := repository.GetVehiclesByOrganization(currentUser.OrganizationID, skip, limit)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": "Falha ao buscar veículos"})
		return
	}

	// 4. Converter modelos para DTOs de resposta
	response := make([]dto.VehicleResponse, 0, len(vehicles))
	for _, v := range vehicles {
		response = append(response, dto.VehicleResponse{
			ID:              v.ID,
			LicensePlate:    v.LicensePlate,
			Brand:           v.Brand,
			Model:           v.Model,
			Year:            v.Year,
			VehicleType:     string(v.VehicleType),
			Status:          string(v.Status),
			CurrentOdometer: v.CurrentOdometer,
			PhotoURL:        v.PhotoURL,
			OrganizationID:  v.OrganizationID,
			CreatedAt:       v.CreatedAt,
		})
	}

	c.JSON(http.StatusOK, response)
}
