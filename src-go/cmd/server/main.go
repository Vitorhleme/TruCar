// cmd/server/main.go
package main

import (
	"fmt"
	"log"

	"trucar-go/internal/api"
	"trucar-go/internal/config"
	"trucar-go/internal/db"     // <-- 1. IMPORTAR O PACOTE DB
	"trucar-go/internal/models" // <-- 2. IMPORTAR OS MODELOS

	"github.com/gin-gonic/gin"
)

func main() {
	// 1. Carregar configuração (lê o .env)
	config.LoadConfig()

	log.Printf("[DEBUG-GO] Chave secreta carregada: '%s'", config.AppConfig.SecretKey)

	// 2. Ligar à Base de Dados
	db.InitDatabase() // <-- 3. CHAMAR O INICIALIZADOR DO DB

	// 3. (Opcional para Dev) Auto-Migrar os modelos
	// Isto cria as tabelas (como o Base.metadata.create_all)
	// Em produção, usaremos um sistema de migração como o Alembic (ex: GORM-Migrate ou Goose)
	err := db.DB.AutoMigrate(&models.User{}, &models.Vehicle{}) // <-- 4. ADICIONAR O MODELO USER À MIGRAÇÃO
	if err != nil {
		log.Fatalf("Falha ao auto-migrar tabelas: %v", err)
	}
	log.Println("Tabelas migradas (AutoMigrate).")

	// 4. Inicializar o Gin (nosso "app = FastAPI()")
	r := gin.Default()

	// 5. Configurar o CORS (Middleware)
	r.Use(func(c *gin.Context) {
		c.Writer.Header().Set("Access-Control-Allow-Origin", "*")
		c.Writer.Header().Set("Access-Control-Allow-Credentials", "true")
		c.Writer.Header().Set("Access-Control-Allow-Headers", "Content-Type, Authorization")
		c.Writer.Header().Set("Access-Control-Allow-Methods", "POST, GET, PUT, DELETE, OPTIONS")

		if c.Request.Method == "OPTIONS" {
			c.AbortWithStatus(204)
			return
		}
		c.Next()
	})

	// 6. Configurar rotas (nosso "app.include_router(api_router)")
	api.SetupRouter(r)

	// 7. Iniciar o servidor (nosso "uvicorn.run(app...)")
	port := config.AppConfig.Port
	if port == "" {
		port = "8000"
	}

	addr := fmt.Sprintf(":%s", port)
	log.Printf("Iniciando servidor na porta %s", addr)

	if err := r.Run(addr); err != nil {
		log.Fatalf("Falha ao iniciar o servidor: %v", err)
	}
}
