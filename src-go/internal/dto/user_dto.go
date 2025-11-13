// internal/dto/user_dto.go
package dto

import "time"

// CreateUserRequest é o DTO (schema) para criar um novo utilizador
// É o equivalente ao seu schema UserCreate
type CreateUserRequest struct {
	FullName       string `json:"full_name" binding:"required"`
	Email          string `json:"email" binding:"required,email"`
	Password       string `json:"password" binding:"required,min=8"`
	Role           string `json:"role" binding:"required"` // Simplificado para string por agora
	OrganizationID uint   `json:"organization_id" binding:"required"`
}

// UserResponse é o DTO (schema) para retornar dados de um utilizador
// É o equivalente ao seu schema User
type UserResponse struct {
	ID         uint      `json:"id"`
	FullName   string    `json:"full_name"`
	Email      string    `json:"email"`
	EmployeeID string    `json:"employee_id"`
	Role       string    `json:"role"`
	IsActive   bool      `json:"is_active"`
	AvatarURL  *string   `json:"avatar_url"`
	CreatedAt  time.Time `json:"created_at"`
	UpdatedAt  time.Time `json:"updated_at"`
}
