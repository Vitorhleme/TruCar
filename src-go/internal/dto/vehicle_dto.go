// internal/dto/vehicle_dto.go
package dto

import "time"

// CreateVehicleRequest é o DTO para criar um novo veículo (como o VehicleCreate)
type CreateVehicleRequest struct {
	LicensePlate    string `json:"license_plate" binding:"required"`
	Brand           string `json:"brand"`
	Model           string `json:"model"`
	Year            int    `json:"year"`
	VehicleType     string `json:"vehicle_type" binding:"required"` // ex: "TRUCK" ou "IMPLEMENT"
	Status          string `json:"status"`                          // ex: "ACTIVE"
	CurrentOdometer int    `json:"current_odometer"`
	PhotoURL        string `json:"photo_url"`
}

// VehicleResponse é o DTO para retornar dados de um veículo (como o Vehicle)
type VehicleResponse struct {
	ID              uint      `json:"id"`
	LicensePlate    string    `json:"license_plate"`
	Brand           string    `json:"brand"`
	Model           string    `json:"model"`
	Year            int       `json:"year"`
	VehicleType     string    `json:"vehicle_type"`
	Status          string    `json:"status"`
	CurrentOdometer int       `json:"current_odometer"`
	PhotoURL        *string   `json:"photo_url"`
	OrganizationID  uint      `json:"organization_id"`
	CreatedAt       time.Time `json:"created_at"`
}
