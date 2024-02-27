package main

import (
	"net/http"
	"time"
)

func main() {
	sem := NewSemaphore(10)

	resourceIntensiveOperation := func() {
		time.Sleep(time.Second)
	}

	opHandler := func(w http.ResponseWriter, req *http.Request) {
		// Try to acquire a semaphore token
		ok := sem.TryAcquire()
		if !ok {
			w.WriteHeader(http.StatusServiceUnavailable)
			return
		}

		// Token acquired, do the resource intensive operation and release a token after
		resourceIntensiveOperation()
		sem.Release()
	}

	// Register the endpoint
	http.HandleFunc("/op", opHandler)

	// Run the HTTP server
	http.ListenAndServe(":8080", nil)
}
