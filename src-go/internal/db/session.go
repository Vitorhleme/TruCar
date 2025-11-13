// internal/db/session.go
package db

import (
	"log"

	"trucar-go/internal/config" // Importa a nossa config

	"gorm.io/driver/postgres"
	"gorm.io/gorm"
)

// DB é a instância global da base de dados (como o 'engine' ou 'SessionLocal' do SQLAlchemy)
var DB *gorm.DB

// InitDatabase inicializa a ligação com o banco de dados
func InitDatabase() {
	var err error
	dsn := config.AppConfig.DatabaseURL

	if dsn == "" {
		log.Fatal("DATABASE_URL não está definida no .env")
	}

	// Abre a ligação
	DB, err = gorm.Open(postgres.Open(dsn), &gorm.Config{})
	if err != nil {
		log.Fatalf("Falha ao ligar à base de dados: %v", err)
	}

	log.Println("Ligação à base de dados estabelecida com sucesso.")

	// (Opcional) Configurar pool de ligações
	sqlDB, err := DB.DB()
	if err != nil {
		log.Fatalf("Falha ao obter a instância sql.DB: %v", err)
	}

	// Configurações semelhantes ao create_async_engine
	sqlDB.SetMaxIdleConns(10)  // Número de ligações inativas
	sqlDB.SetMaxOpenConns(100) // Número máximo de ligações abertas
}
