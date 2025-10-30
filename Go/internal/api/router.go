// internal/api/router.go
package api

import (
	"net/http"

	"trucar-go/internal/handlers"
	"trucar-go/internal/middleware" // <-- IMPORTAR O MIDDLEWARE

	"github.com/gin-gonic/gin"
)

// SetupRouter configura todas as rotas da aplicação
func SetupRouter(r *gin.Engine) {

	// Rota raiz
	r.GET("/", func(c *gin.Context) {
		c.JSON(http.StatusOK, gin.H{"status": "Welcome to TruCar Go API!"})
	})

	apiV1 := r.Group("/api/v1")
	{
		// --- Rotas Públicas ---
		// O /login/token já não existe aqui, é tratado pelo Python
		apiV1.POST("/users", handlers.CreateUserHandler) // Criar utilizador é público

		// --- Rotas Protegidas ---
		// Qualquer rota dentro deste grupo vai exigir um token válido
		protected := apiV1.Group("/")
		protected.Use(middleware.AuthMiddleware()) // <-- APLICAR O MIDDLEWARE AQUI
		{
			// /api/v1/users/me
			protected.GET("/users/me", handlers.GetMeHandler)

			// /api/v1/users (GET)
			protected.GET("/users", handlers.GetUsersHandler)

			// --- ADICIONE AS NOVAS ROTAS DE VEÍCULO AQUI ---
			protected.POST("/vehicles", handlers.CreateVehicleHandler)
			protected.GET("/vehicles", handlers.GetVehiclesHandler)
		}
	}
}
