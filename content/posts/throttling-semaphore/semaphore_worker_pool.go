package main

import "fmt"

func main() {
	maxWorkers := 10
	out := make([]uint64, 32)

	// Creating the semaphore
	sem := NewSemaphore(maxWorkers)

	// Launch the factorial operation using up to maxWorkers goroutines at a time.
	for i := range out {
		// Acquire a semaphore token (or wait for one available)
		sem.Acquire()

		go func(i int) {
			out[i] = factorial(i)

			// Release a semaphore token
			sem.Release()
		}(i)
	}

	// Wait for the workers to finish their job
	sem.TearDown()

	fmt.Println(out)
}

func factorial(n int) uint64 {
	if n > 0 {
		return uint64(n) * factorial(n-1)
	}
	return 1
}
