---
title: "Taming the Flow: Throttling in Golang with Semaphore Magic"
date: 2024-02-27T00:00:00+02:00
tags: ["golang", "throttling", "rate limiting"]

code:
  maxShownLines: 500
---

## Introduction

In today's digital world, APIs serve as the core of modern applications, allowing seamless data exchange and
interaction. However, even the most robust and scalable API servers can succumb to the humongous number of incoming
requests. Picture this scenario: your finely crafted API server, designed to handle thousands of requests per second,
suddenly experiences an unprecedented spike in traffic. Within moments, your server starts to struggle under the weight
of the overwhelming load, its response times slowing to a crawl, and in the worst-case scenario, a complete outage
occurs.

In order to maintain stability and enhance user experience, developers often encounter two essential techniques:
**throttling** and **rate limiting**. Though distinct in their mechanisms, both throttling and rate limiting play
crucial roles. Throttling focuses on controlling the rate at which requests are processed, while rate limiting sets
predefined boundaries on the number of requests a client can make within a given time frame.

While rate limiting is an effective strategy to control the overall request rate and prevent abusive behavior, it falls
short when it comes to handling sudden usage spikes. By leveraging a semaphore-based throttling mechanism, we can
intelligently regulate the flow of incoming requests, mitigating the impact of usage spikes and maintaining a responsive
API.

## Throttling with semaphores
First, let's define what is a **semaphore**. A semaphore is a synchronization construct used in concurrent programming
to control access to a shared resource. It acts as a counter that manages the number of threads or goroutines allowed to
access the resource simultaneously. When a thread or goroutine wants to access the shared resource, it must acquire a
semaphore token. If the token is available, the thread is allowed access; otherwise, it waits until a token becomes
available when another thread releases it.

A simple way to implement a semaphore relies on buffered channel. A buffered channel in Golang is a type of channel that
allows a specific number of elements to be stored in it before blocking the sending operation. There are two ways to
implement semaphores with buffered channels, with opposite setups: either you start with an empty channel and you push
your token in the channel, or you start with a filled channel and you retrieve tokens from it. In this article, we will
explore the latter, because it provides a non-blocking and tentative way to acquire a token.

### Setup and tear down

The following code exposes the `Semaphore` structure, its setup and tear down.

```go
type token struct{}

// Semaphore represents a structure able to limit simultaneous access to a shared resource.
type Semaphore struct {
    c chan token
}

// NewSemaphore creates a new semaphore that allows size simultaneous operations.
func NewSemaphore(size int) *Semaphore {
    s := &Semaphore{
        c: make(chan token, size),
    }

    // Fill the channel with tokens
    for i := 0; i < size; i++ {
        s.c <- token{}
    }

    return s
}

// TearDown tears down a semaphore.
// If there is any ongoing operation, this will wait for them.
func (s *Semaphore) TearDown() {
    for i := 0; i < cap(s.c); i++ {
        <-s.c
    }
}
```

### Blocking Acquire
The `Acquire` method lets the user request for a semaphore token in a blocking way: if all the tokens are currently held
by other goroutines, it will wait for one available. When the operation is finished, the token must be released with the
`Release` method. One possible improvement would be to acquire/release multipe tokens, like proposed in the
[x/sync/semaphore](https://pkg.go.dev/golang.org/x/sync/semaphore) package.

```go
// Acquire acquires a semaphore token, blocking until resources are available.
func (s *Semaphore) Acquire() {
    <-s.c
}

// Release releases a semaphore token.
func (s *Semaphore) Release() {
    s.c <- token{}
}
```

### Non-blocking Acquire
As mentioned before, we chose to used a pre-filled channel. This lets us use `select` on our channel, that allows us to
try to acquire a semaphore token without blocking. On success, similarly to `Acquire`, the token must be released with
the `Release` method.

```go
// TryAcquire tries to acquire a semaphore token, without blocking.
// On success, returns true. On failure, returns false and leaves the semaphore unchanged.
func (s *Semaphore) TryAcquire() bool {
    select {
    case <-s.c:
        return true
    default:
        return false
    }
}
```

## Examples

### Worker pool

The initial scenario we'll explore into is quite common: you're faced with a collection of N tasks that need processing.
Rather than handling them sequentially, you aim to process them concurrently, allowing at most M tasks to run
simultaneously. Also, note that by using this semaphore-based mechanism, we avoid traditional worker pool implementation
with idling goroutines.

{{< code "semaphore_worker_pool.go" "go" >}}


### Best-effort / Degraded mode

The second use-case involves an application that exposes an API for resource-intensive operations. In this particular
situation, if the application experiences a sudden surge in requests, utilizing a worker pool might not be viable. The
requests would start queuing up, potentially leading to a spike in memory consumption that could potentially crash the
application. In this case, the goal is to have the application permit a specific number of concurrent operations and
gracefully decline any additional requests when fully occupied. Additionally, we would prefer to notify the client to
return at a later time (perhaps with an HTTP code `503 Service Unavailable`, for instance).

{{< code "semaphore_best_effort.go" "go" >}}

## Conclusion

In the world of concurrent programming, effective throttling can make the difference between a robust application and
one that struggles under high loads. Through the utilization of semaphores and channels in Go, we've uncovered an
elegant approach to managing task execution. Possible improvements include the acquisition/release of multiple tokens at
the same time, or using a `context.Context` in those operations. By carefully regulating resource access, we prevent
overutilization and maintain steady performance. This not only safeguards our applications from potential crashes but
also positions them to handle surges in traffic with resilience and grace.

Here is a [GitHub Gist](https://gist.github.com/driquet/6d34d5fbb0255ea1f738b90641796b8e) with the semaphore
implementation and the worker pool example.

## See also

* [x/sync/semaphore package](https://pkg.go.dev/golang.org/x/sync/semaphore)
* [Johan Brandhorst: Throttling resource intensive requests](https://jbrandhorst.com/post/go-semaphore/)
* [Jason Lui: Goroutines, wait in line!](https://blog.xendit.engineer/goroutines-wait-in-line-5bae770bb79)
* [gohalt: Golang throttling library](https://github.com/1pkg/gohalt)
