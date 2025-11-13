// internal/models/user_model.go
package models

import (
	"time"

	"gorm.io/gorm" // Vamos precisar disto para o gorm.Model
)

// UserRole é o nosso tipo 'enum' (como em Python)
type UserRole string

const (
	RoleClienteAtivo UserRole = "cliente_ativo"
	RoleClienteDemo  UserRole = "cliente_demo"
	RoleDriver       UserRole = "driver"
)

// User é o nosso modelo GORM, equivalente ao models.User do SQLAlchemy
type User struct {
	// gorm.Model adiciona automaticamente: ID (uint), CreatedAt, UpdatedAt, DeletedAt
	gorm.Model

	FullName       string   `gorm:"size:100;index;not null"`
	Email          string   `gorm:"size:100;uniqueIndex;not null"`
	HashedPassword string   `gorm:"size:255;not null"`
	EmployeeID     string   `gorm:"size:50;uniqueIndex;not null"`
	Role           UserRole `gorm:"type:varchar(20);not null"`
	IsActive       bool     `gorm:"default:true;not null"`

	// Campos 'nullable' (opcionais) são ponteiros em Go
	AvatarURL         *string `gorm:"size:512"`
	NotificationEmail *string `gorm:"size:100"`

	NotifyInApp   bool `gorm:"default:true;not null"`
	NotifyByEmail bool `gorm:"default:true;not null"`

	ResetPasswordToken          *string `gorm:"size:255;index"`
	ResetPasswordTokenExpiresAt *time.Time

	OrganizationID uint `gorm:"not null"`

	// --- Relacionamentos ---
	// (Vamos adicionar os relacionamentos aqui à medida que criamos os outros modelos)
	// Exemplo:
	// Organization   Organization `gorm:"foreignKey:OrganizationID"`
}
