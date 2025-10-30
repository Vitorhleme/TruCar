// internal/config/config.go
package config

import (
	"log"
	"os"

	"github.com/joho/godotenv"
)

// AppConfig armazena a configuração global lida do .env
var AppConfig Config

// Config é a struct que espelha seu .env
type Config struct {
	DatabaseURL string
	SecretKey   string
	Port        string
}

// LoadConfig lê as variáveis do .env e popula a struct AppConfig
func LoadConfig() {
	// Carrega o .env (ignora erro se não existir, útil para produção)
	// O Go procura o .env na pasta onde o executável é chamado (a raiz)
	godotenv.Load()

	AppConfig = Config{
		DatabaseURL: os.Getenv("DATABASE_URL"),
		SecretKey:   os.Getenv("SECRET_KEY"),
		Port:        os.Getenv("PORT"),
	}

	log.Println("Configuração carregada.")
}