// internal/repository/vehicle_repository.go
package repository

import (
	"trucar-go/internal/db"
	"trucar-go/internal/models"
)

// CreateVehicle cria um novo veículo
func CreateVehicle(vehicle *models.Vehicle) (*models.Vehicle, error) {
	if err := db.DB.Create(vehicle).Error; err != nil {
		return nil, err
	}
	return vehicle, nil
}

// GetVehicleByLicensePlate (dentro de uma organização)
func GetVehicleByLicensePlate(orgID uint, plate string) (*models.Vehicle, error) {
	var vehicle models.Vehicle
	if err := db.DB.Where("organization_id = ? AND license_plate = ?", orgID, plate).First(&vehicle).Error; err != nil {
		return nil, err // Retorna erro (incluindo 'record not found')
	}
	return &vehicle, nil
}

// GetVehiclesByOrganization (para listar todos os veículos do utilizador)
func GetVehiclesByOrganization(orgID uint, skip int, limit int) ([]models.Vehicle, error) {
	var vehicles []models.Vehicle

	if err := db.DB.Where("organization_id = ?", orgID).Offset(skip).Limit(limit).Find(&vehicles).Error; err != nil {
		return nil, err
	}
	return vehicles, nil
}
