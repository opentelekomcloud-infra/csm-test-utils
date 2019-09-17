package main

import (
	"fmt"
	"log"
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
	return client{baseUrl: baseUrl, historyChan: make(chan string), store: make(map[string]int)}
}

func (cl client) get(uri string) (*http.Response, error) {
	return http.Get(fmt.Sprintf("http://%s/%s", cl.baseUrl, uri))
}

func (cl client) singleGetRoot(wg *sync.WaitGroup) {
	defer wg.Done()
	response, _ := cl.get("/")
	srv := response.Header["Server"][0]
	if srv == "" {
		log.Fatal("Missing `Server` header in response")
	}
	cl.historyChan <- srv
}

func (cl client) storeResults() {
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
	for i := 0; i < times; i++ {
		go cl.singleGetRoot(&waitGrp)
	}
	go cl.storeResults()
	waitGrp.Wait()
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
	fmt.Print(cl.store)
}
