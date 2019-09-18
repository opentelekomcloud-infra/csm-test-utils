package main

import (
	"fmt"
	"log"
	"math"
	"net/http"
	"os"
	"strconv"
	"sync"
)

type client struct {
	baseUrl     string
	historyChan chan string
	store       map[string]int
}

func newClient(baseUrl string) client {
	return client{
		baseUrl:     baseUrl,
		historyChan: make(chan string, 2000),
		store:       make(map[string]int),
	}
}

func (cl client) get(uri string) (*http.Response, error) {
	return http.Get(fmt.Sprintf("http://%s/%s", cl.baseUrl, uri))
}

func (cl client) singleGetRoot(wg *sync.WaitGroup) {
	defer wg.Done()
	response, _ := cl.get("")
	defer func() {
		if recover() != nil {
			fmt.Println("RECOVER")
		}
	}()
	srv := response.Header["Server"][0]
	if srv == "" {
		log.Panic("Missing `Server` header in response")
	}
	cl.historyChan <- srv
}

func (cl client) collectResults() {
	for msg := range cl.historyChan {
		if _, ok := cl.store[msg]; ok {
			cl.store[msg] += 1
		} else {
			cl.store[msg] = 1
		}
	}
}

func (cl client) getRootNTimes(times int) {
	waitGrp := sync.WaitGroup{}
	waitGrp.Add(times)
	go cl.collectResults()
	for i := 0; i < times; i++ {
		go cl.singleGetRoot(&waitGrp)
	}
	waitGrp.Wait()
}

// Check for round-robin lb to balance equally
func (cl client) checkEquallyBalanced() {
	curMin := math.MaxInt32
	curMax := 0
	for k := range cl.store {
		v := cl.store[k]
		if v < curMin {
			curMin = v
		}
		if v > curMax {
			curMax = v
		}
	}

	deviancePrc := (float64(curMax-curMin) / float64(curMin)) * 100

	result := fmt.Sprintf("Deviance is %.2f%% (max: %d, min %d)\n", deviancePrc, curMax, curMin)

	if deviancePrc > 10 {
		err := fmt.Errorf("Nodes are not equally balanced.\n %s", result)
		fmt.Print(err)
		os.Exit(102)
	}
	fmt.Print(result)

}

func (cl client) checkMultiple() {
	if len(cl.store) == 1 {
		fmt.Printf("There is only one node running: %v", cl.store)
		os.Exit(101)
	}
}

func main() {
	cl := newClient(os.Args[1])
	if len(os.Args) == 1 {
		log.Panic("Server address argument is missing")
	}

	var count int
	if len(os.Args) > 2 {
		count, _ = strconv.Atoi(os.Args[2])
	} else {
		count = 100
	}
	cl.getRootNTimes(count)
	cl.checkMultiple()
	cl.checkEquallyBalanced()
}
