// internal/models/vehicle_model.go
package models

import (
	"gorm.io/gorm"
)

// VehicleType (enum)
type VehicleType string

const (
	VehicleTypeTruck     VehicleType = "TRUCK"
	VehicleTypeImplement VehicleType = "IMPLEMENT"
)

// VehicleStatus (enum)
type VehicleStatus string

const (
	VehicleStatusActive      VehicleStatus = "ACTIVE"
	VehicleStatusInactive    VehicleStatus = "INACTIVE"
	VehicleStatusMaintenance VehicleStatus = "MAINTENANCE"
)

// Vehicle é o nosso modelo GORM para a tabela 'vehicles'
type Vehicle struct {
	gorm.Model // Adiciona ID, CreatedAt, UpdatedAt, DeletedAt

	LicensePlate    string `gorm:"size:20;uniqueIndex:idx_org_license_plate;not null"`
	Brand           string `gorm:"size:50"`
	Model           string `gorm:"size:50"`
	Year            int
	VehicleType     VehicleType   `gorm:"size:20;not null"`
	Status          VehicleStatus `gorm:"size:20;not null;default:'ACTIVE'"`
	CurrentOdometer int           `gorm:"default:0"`
	InitialOdometer int           `gorm:"default:0"`
	PhotoURL        *string       `gorm:"size:512"`

	// Chave estrangeira para a Organização
	OrganizationID uint `gorm:"not null;uniqueIndex:idx_org_license_plate"`

	// (Vamos adicionar os relacionamentos como 'Organization' mais tarde, se necessário)
}
