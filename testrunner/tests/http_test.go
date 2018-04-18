// Copyright 2018 Google LLC. All rights reserved.

// Licensed under the Apache License, Version 2.0 (the "License");
// you may not use this file except in compliance with the License.
// You may obtain a copy of the License at

//     http://www.apache.org/licenses/LICENSE-2.0

// Unless required by applicable law or agreed to in writing, software
// distributed under the License is distributed on an "AS IS" BASIS,
// WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
// See the License for the specific language governing permissions and
// limitations under the License.

package tests_test

import (
	"fmt"
	"net/http"
	"net/http/httptest"
	"testing"

	"github.com/GoogleCloudPlatform/marketplace-k8s-app-tools/testrunner/specs"
	"github.com/GoogleCloudPlatform/marketplace-k8s-app-tools/testrunner/tests"
	"github.com/ghodss/yaml"
)

func TestStatusCodeAssert(t *testing.T) {
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.WriteHeader(http.StatusForbidden)
		fmt.Fprintln(w, "Hello World")
	}))
	defer server.Close()
	assertShouldFail(t, server, &specs.HttpTest{
		Url: server.URL,
		Expect: specs.HttpExpect{
			StatusCode: &specs.IntAssert{
				AtLeast:  newInt(http.StatusOK),
				LessThan: newInt(http.StatusBadRequest),
			},
		},
	})
	assertShouldPass(t, server, &specs.HttpTest{
		Url: server.URL,
		Expect: specs.HttpExpect{
			StatusCode: &specs.IntAssert{
				AtLeast: newInt(http.StatusBadRequest),
			},
		},
	})
}

func TestStatusTextAssert(t *testing.T) {
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		fmt.Fprintln(w, "Hello World")
	}))
	defer server.Close()
	assertShouldPass(t, server, &specs.HttpTest{
		Url: server.URL,
		Expect: specs.HttpExpect{
			StatusText: &specs.StringAssert{
				Equals: newString("200 OK"),
			},
		},
	})
	assertShouldFail(t, server, &specs.HttpTest{
		Url: server.URL,
		Expect: specs.HttpExpect{
			StatusText: &specs.StringAssert{
				Contains: newString("Forbidden"),
			},
		},
	})
}

func TestBodyTextAssert(t *testing.T) {
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		fmt.Fprintln(w, "<html><head><title>Hello World</title></head><body>Yay</body></html>")
	}))
	defer server.Close()
	assertShouldPass(t, server, &specs.HttpTest{
		Url: server.URL,
		Expect: specs.HttpExpect{
			BodyText: &specs.TextContentAssert{
				Html: &specs.HtmlAssert{
					Title: &specs.StringAssert{
						Exactly: newString("Hello World"),
					},
				},
			},
		},
	})
	assertShouldFail(t, server, &specs.HttpTest{
		Url: server.URL,
		Expect: specs.HttpExpect{
			BodyText: &specs.TextContentAssert{
				Html: &specs.HtmlAssert{
					Title: &specs.StringAssert{
						Contains: newString("Hi World"),
					},
				},
			},
		},
	})
}

func TestMethodAndHeaders(t *testing.T) {
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		if r.Header.Get("Expected-Header") == "Here" && r.Method == http.MethodPost {
			w.WriteHeader(http.StatusOK)
		} else {
			w.WriteHeader(http.StatusBadRequest)
		}
	}))
	defer server.Close()
	assertShouldPass(t, server, &specs.HttpTest{
		Url:    server.URL,
		Method: newString(http.MethodPost),
		Headers: map[string]string{
			"Expected-Header": "Here",
		},
		Expect: specs.HttpExpect{
			StatusCode: &specs.IntAssert{
				Equals: newInt(http.StatusOK),
			},
		},
	})
	assertShouldFail(t, server, &specs.HttpTest{
		Url: server.URL,
		Headers: map[string]string{
			"Expected-Header": "Here",
		},
		Expect: specs.HttpExpect{
			StatusCode: &specs.IntAssert{
				Equals: newInt(http.StatusOK),
			},
		},
	})
	assertShouldFail(t, server, &specs.HttpTest{
		Url:    server.URL,
		Method: newString(http.MethodPost),
		Expect: specs.HttpExpect{
			StatusCode: &specs.IntAssert{
				Equals: newInt(http.StatusOK),
			},
		},
	})
}

func assertShouldPass(t *testing.T, server *httptest.Server, test *specs.HttpTest) {
	outcome := runTest(t, server, test)
	if len(outcome) > 0 {
		t.Errorf("Expected to pass but was failing: %s", outcome)
	} else {
		t.Logf("Passing OK!")
	}
}

func assertShouldFail(t *testing.T, server *httptest.Server, test *specs.HttpTest) {
	outcome := runTest(t, server, test)
	if len(outcome) == 0 {
		t.Errorf("Expected to fail but was passing")
	} else {
		t.Logf("Failing OK! Test output: %s", outcome)
	}
}

func runTest(t *testing.T, server *httptest.Server, test *specs.HttpTest) string {
	testRule, _ := yaml.Marshal(test)
	t.Logf("---\nTest rule:\n%s", testRule)
	return tests.RunHttpTest(test, server.Client())
}

func newInt(value int) *int {
	return &value
}

func newString(value string) *string {
	return &value
}
