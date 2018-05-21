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

package main

import (
	"flag"
	"fmt"
	"gopkg.in/yaml.v2"
	"net/http"
	"os"
	"path"

	"github.com/GoogleCloudPlatform/marketplace-k8s-app-tools/testrunner/asserts"
	"github.com/GoogleCloudPlatform/marketplace-k8s-app-tools/testrunner/conditions"
	"github.com/GoogleCloudPlatform/marketplace-k8s-app-tools/testrunner/flags"
	"github.com/GoogleCloudPlatform/marketplace-k8s-app-tools/testrunner/gcp"
	"github.com/GoogleCloudPlatform/marketplace-k8s-app-tools/testrunner/specs"
	"github.com/GoogleCloudPlatform/marketplace-k8s-app-tools/testrunner/tests"
	"github.com/golang/glog"
	"io/ioutil"
	"log"
)

const outcomeFailed = "FAILED"
const outcomePassed = "PASSED"
const outcomeSkipped = "SKIPPED"

type testResult struct {
	Name    string
	Message string
	Passed  bool
}

type testStatus struct {
	FailureCount int
}

func (r *testResult) Fail(msg string) {
	r.Passed = false
	r.Message = asserts.MessageWithContext(msg, fmt.Sprintf("%s: HTTP test failed", outcomeFailed))
}

func (r *testResult) Pass() {
	r.Passed = true
	r.Message = outcomePassed
}

func (r *testResult) Skip(msg string) {
	r.Passed = true
	r.Message = asserts.MessageWithContext(msg, fmt.Sprintf("%s: Condition not satisfied", outcomeSkipped))
}

func (t testStatus) FailuresSoFarCount() int {
	return t.FailureCount
}

func GenerateValues(testSpecsValues *string) *map[string]interface{} {
	if testSpecsValues == nil || *testSpecsValues == "" {
		return nil
	}

	valuesFiles, err := ioutil.ReadDir(*testSpecsValues)
	check(err)

	values := make(map[string]interface{})

	for _, valuesFile := range valuesFiles {
		if valuesFile.IsDir() {
			log.Printf("'%v' is a directory. Ignored.\n", valuesFile.Name())
			continue
		}

		var valuesPath = path.Join(*testSpecsValues, valuesFile.Name())
		valuesContent, err := ioutil.ReadFile(valuesPath)
		check(err)

		var parsed interface{}

		err = yaml.Unmarshal(valuesContent, &parsed)
		check(err)

		values[valuesFile.Name()] = parsed
	}

	return &values
}

func main() {
	testSpecs := flags.FlagStringList("test_spec", "Path to a yaml or json file containing the test spec. Can be specified multiple times")
	testSpecsValues := flag.String("test_spec_values", "", "Path to template values for substitution in the test specs")

	flag.Parse()

	if len(*testSpecs) <= 0 {
		glog.Fatal("--test_spec must be specified")
	}

	values := GenerateValues(testSpecsValues)

	status := testStatus{}
	for _, testSpec := range *testSpecs {
		glog.Infof(">>> Running %v", testSpec)
		suite := specs.LoadSuite(testSpec, values)
		if len(suite.Actions) <= 0 {
			glog.Info(" > Nothing to run!")
			continue
		}
		doRunActions(suite, &status)
	}
	if status.FailureCount > 0 {
		glog.Errorf(">>> SUMMARY: %d failed", status.FailureCount)
	} else {
		glog.Infof(">>> SUMMARY: All passed")
	}
	os.Exit(status.FailureCount)
}

// doRunActions executes the actions in the suite and returns a function
// to do a summary report. This report function returns the number of
// test failures, i.e. its returning 0 means all tests are passing.
func doRunActions(suite *specs.Suite, status *testStatus) {
	results := make([]testResult, len(suite.Actions), len(suite.Actions))
	for index, action := range suite.Actions {
		doOneAction(index, &action, status, results)
	}

	for _, r := range results {
		if !r.Passed {
			status.FailureCount++
		}
	}
	if status.FailureCount == 0 {
		glog.Infof(" >> Summary: %s", outcomePassed)
	} else {
		glog.Errorf(" >> Summary: %d %s, %d %s", status.FailureCount, outcomeFailed, len(results)-status.FailureCount, outcomePassed)
	}
	for _, r := range results {
		if r.Passed {
			glog.Infof(" > %s: %s", r.Name, outcomePassed)
		} else {
			glog.Errorf(" > %s: %s", r.Name, outcomeFailed)
		}
	}
}

func doOneAction(index int, action *specs.Action, status *testStatus, results []testResult) {
	result := testResult{}
	if len(action.Name) <= 0 {
		glog.Fatalf("All actions must have names")
	}
	result.Name = fmt.Sprintf("%3d: %s", index, action.Name)
	glog.Infof(" > %s", result.Name)

	recordResult := func(r *testResult) {
		results[index] = *r
		if r.Passed {
			glog.Infof(" %s", r.Message)
		} else {
			glog.Errorf(" %s", r.Message)
		}
	}
	defer recordResult(&result)

	if action.Condition != nil {
		ok, msg := conditions.Evaluate(action.Condition, status)
		if !ok {
			result.Skip(msg)
			return
		}
	}

	if action.HttpTest != nil {
		msg := tests.RunHttpTest(action.HttpTest, &http.Client{})
		if len(msg) > 0 {
			result.Fail(msg)
			return
		}
	} else if action.Gcp != nil {
		msg := gcp.RunAction(action.Gcp)
		if len(msg) > 0 {
			result.Fail(msg)
			return
		}
	}

	result.Pass()
}

func check(err interface{}) {
	if err != nil {
		log.Fatalf("Error: %v", err)
	}
}
