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
	"errors"
	"testing"

	"github.com/GoogleCloudPlatform/marketplace-k8s-app-tools/testrunner/specs"
	"github.com/GoogleCloudPlatform/marketplace-k8s-app-tools/testrunner/tests"
	"github.com/ghodss/yaml"
)

type SimpleSetupExecutor struct{}

func (e *SimpleSetupExecutor) RunTest(test *specs.BashTest) (int, string, string, error) {
	return 0, "FOO", "BAR", nil
}

func TestSimpleSetup(t *testing.T) {
	shouldSuccess(t, &specs.BashTest{
		Expect: &specs.BashExpect{
			StatusCode: &[]specs.IntAssert{
				{Equals: newInt(0)},
			},
			Stdout: &[]specs.StringAssert{
				{Exactly: newString("FOO")},
			},
			Stderr: &[]specs.StringAssert{
				{Exactly: newString("BAR")},
			},
		},
	}, &SimpleSetupExecutor{})
}

type FailingExecutor struct{}

func (e *FailingExecutor) RunTest(test *specs.BashTest) (int, string, string, error) {
	return 0, "FOO", "BAR", errors.New("Error while executing external process")
}

func TestFailingExecutor(t *testing.T) {
	shouldFail(t, &specs.BashTest{
		Expect: &specs.BashExpect{
			StatusCode: &[]specs.IntAssert{
				{Equals: newInt(0)},
			},
			Stdout: &[]specs.StringAssert{
				{Exactly: newString("FOO")},
			},
			Stderr: &[]specs.StringAssert{
				{Exactly: newString("BAR")},
			},
		},
	}, &FailingExecutor{})
}

type StatusCodeExecutor struct{}

func (e *StatusCodeExecutor) RunTest(test *specs.BashTest) (int, string, string, error) {
	return 42, "", "", nil
}

func TestStatusCodeParsing(t *testing.T) {
	shouldSuccess(t, &specs.BashTest{
		Expect: &specs.BashExpect{
			StatusCode: &[]specs.IntAssert{
				{Equals: newInt(42)},
			},
		},
	}, &StatusCodeExecutor{})

	shouldSuccess(t, &specs.BashTest{
		Expect: &specs.BashExpect{
			StatusCode: &[]specs.IntAssert{
				{Equals: newInt(42)},
				{Equals: newInt(42)},
				{NotEquals: newInt(41)},
				{GreaterThan: newInt(41)},
			},
			Stdout: &[]specs.StringAssert{
				{Exactly: newString("")},
			},
			Stderr: &[]specs.StringAssert{
				{Exactly: newString("")},
			},
		},
	}, &StatusCodeExecutor{})

	shouldFail(t, &specs.BashTest{
		Expect: &specs.BashExpect{
			StatusCode: &[]specs.IntAssert{
				{Equals: newInt(0)},
			},
		},
	}, &StatusCodeExecutor{})

	shouldFail(t, &specs.BashTest{
		Expect: &specs.BashExpect{
			StatusCode: &[]specs.IntAssert{
				{LessThan: newInt(40)},
			},
		},
	}, &StatusCodeExecutor{})
}

type StdoutExecutor struct{}

func (e *StdoutExecutor) RunTest(test *specs.BashTest) (int, string, string, error) {
	return 0, "Lorem ipsum dolor sit amet, consectetur adipiscing elit.\nProin nibh augue, suscipit a, scelerisque sed, lacinia in, mi.", "", nil
}

func TestStdoutParsing(t *testing.T) {
	shouldSuccess(t, &specs.BashTest{
		Expect: &specs.BashExpect{
			Stdout: &[]specs.StringAssert{
				{Exactly: newString("Lorem ipsum dolor sit amet, consectetur adipiscing elit.\nProin nibh augue, suscipit a, scelerisque sed, lacinia in, mi.")},
			},
		},
	}, &StdoutExecutor{})

	shouldSuccess(t, &specs.BashTest{
		Expect: &specs.BashExpect{
			StatusCode: &[]specs.IntAssert{
				{Equals: newInt(0)},
			},
			Stdout: &[]specs.StringAssert{
				{Exactly: newString("Lorem ipsum dolor sit amet, consectetur adipiscing elit.\nProin nibh augue, suscipit a, scelerisque sed, lacinia in, mi.")},
				{Contains: newString("consectetur a")},
			},
			Stderr: &[]specs.StringAssert{
				{Exactly: newString("")},
			},
		},
	}, &StdoutExecutor{})

	shouldFail(t, &specs.BashTest{
		Expect: &specs.BashExpect{
			Stdout: &[]specs.StringAssert{
				{Exactly: newString("Proin nibh augue, suscipit a, scelerisque sed, lacinia in, mi.")},
				{Contains: newString("consecteturadipiscingadipiscing")},
			},
		},
	}, &StdoutExecutor{})

	shouldFail(t, &specs.BashTest{
		Expect: &specs.BashExpect{
			Stdout: &[]specs.StringAssert{
				{Exclude: newString("Lorem")},
			},
		},
	}, &StdoutExecutor{})
}

func shouldSuccess(t *testing.T, test *specs.BashTest, executor tests.CommandExecutor) {
	outcome := runBashTest_Test(t, test, executor)
	if len(outcome) > 0 {
		t.Errorf("Expected to pass but was failing: %s", outcome)
	} else {
		t.Logf("Passing OK!")
	}
}

func shouldFail(t *testing.T, test *specs.BashTest, executor tests.CommandExecutor) {
	outcome := runBashTest_Test(t, test, executor)
	if len(outcome) == 0 {
		t.Errorf("Expected to fail but was passing")
	} else {
		t.Logf("Failing OK! Test output: %s", outcome)
	}
}

func runBashTest_Test(t *testing.T, test *specs.BashTest, executor tests.CommandExecutor) string {
	testRule, _ := yaml.Marshal(test)
	t.Logf("---\nTest rule:\n%s", testRule)
	return tests.RunBashTest(test, executor)
}
