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

package asserts_test

import (
	"testing"

	. "github.com/GoogleCloudPlatform/marketplace-k8s-app-tools/testrunner/asserts"
	"github.com/GoogleCloudPlatform/marketplace-k8s-app-tools/testrunner/specs"
)

func TestStringAssertExactly(t *testing.T) {
	rule := specs.StringAssert{Exactly: newString("to be exact")}
	assertShouldPass(t, "to be exact", rule)
	assertShouldFail(t, "\nto be exact", rule)
	assertShouldFail(t, "to be exact\n", rule)
	assertShouldFail(t, " to be exact", rule)
	assertShouldFail(t, "to be exact ", rule)

	rule = specs.StringAssert{Exactly: newString("")}
	assertShouldPass(t, "", rule)
	assertShouldFail(t, "\n", rule)
	assertShouldFail(t, "a", rule)
}

func TestStringAssertEquals(t *testing.T) {
	rule := specs.StringAssert{Equals: newString("to be equal")}
	assertShouldPass(t, "to be equal", rule)
	assertShouldPass(t, "\nto be equal", rule)
	assertShouldPass(t, "to be equal\n", rule)
	assertShouldPass(t, " to be equal", rule)
	assertShouldPass(t, "to be equal ", rule)
	assertShouldFail(t, "to be different", rule)
	assertShouldFail(t, "to be equal\nbut", rule)

	rule = specs.StringAssert{Equals: newString("")}
	assertShouldPass(t, "", rule)
	assertShouldPass(t, "\n", rule)
	assertShouldFail(t, "a", rule)
}

func TestStringAssertContains(t *testing.T) {
	rule := specs.StringAssert{Contains: newString("more")}
	assertShouldPass(t, "Jane is more fun", rule)
	assertShouldPass(t, "more is less", rule)
	assertShouldPass(t, "less is more", rule)
	assertShouldFail(t, "Jane is fun", rule)
}

func TestStringAssertMatches(t *testing.T) {
	rule := specs.StringAssert{Matches: newString("a[bc]d")}
	assertShouldPass(t, "abd", rule)
	assertShouldPass(t, "123acd456", rule)
	assertShouldFail(t, "ad", rule)
}

func TestStringAssertNotContains(t *testing.T) {
	rule := specs.StringAssert{NotContains: newString("to be excluded")}
	assertShouldFail(t, "to be excluded", rule)
	assertShouldFail(t, "\nto be excluded", rule)
	assertShouldFail(t, "to be excluded\n", rule)
	assertShouldFail(t, " to be excluded", rule)
	assertShouldFail(t, "to be excluded ", rule)

	rule = specs.StringAssert{NotContains: newString("")}
	assertShouldFail(t, "\n", rule)
	assertShouldFail(t, "a", rule)

	rule = specs.StringAssert{NotContains: newString("more")}
	assertShouldFail(t, "Jane is more fun", rule)
	assertShouldFail(t, "more is less", rule)
	assertShouldFail(t, "less is more", rule)
	assertShouldFail(t, "lessmoreless", rule)
	assertShouldPass(t, "Jane is fun", rule)
}

func TestStringAssertMatchesBadRegex(t *testing.T) {
	rule := specs.StringAssert{Matches: newString(`\`)}
	assertShouldFail(t, `\`, rule)
}

func TestIntAssertEquals(t *testing.T) {
	rule := specs.IntAssert{Equals: newInt(10)}
	assertShouldPass(t, 10, rule)
	assertShouldFail(t, 12, rule)
}

func TestIntAssertNotEquals(t *testing.T) {
	rule := specs.IntAssert{NotEquals: newInt(10)}
	assertShouldFail(t, 10, rule)
	assertShouldPass(t, 12, rule)
}

func TestIntAssertAtLeast(t *testing.T) {
	rule := specs.IntAssert{AtLeast: newInt(0)}
	assertShouldPass(t, 10, rule)
	assertShouldPass(t, 0, rule)
	assertShouldFail(t, -1, rule)
}

func TestIntAssertAtMost(t *testing.T) {
	rule := specs.IntAssert{AtMost: newInt(10)}
	assertShouldPass(t, 10, rule)
	assertShouldPass(t, 0, rule)
	assertShouldFail(t, 11, rule)
}

func TestIntAssertLessThan(t *testing.T) {
	rule := specs.IntAssert{LessThan: newInt(0)}
	assertShouldPass(t, -1, rule)
	assertShouldFail(t, 0, rule)
	assertShouldFail(t, 10, rule)
}

func TestIntAssertGreaterThan(t *testing.T) {
	rule := specs.IntAssert{GreaterThan: newInt(10)}
	assertShouldPass(t, 11, rule)
	assertShouldFail(t, 10, rule)
	assertShouldFail(t, 9, rule)
}

func TestHtmlAssertTitle(t *testing.T) {
	rule := specs.TextContentAssert{
		Html: &specs.HtmlAssert{
			Title: &specs.StringAssert{
				Equals: newString("Hello World"),
			},
		},
	}
	assertShouldFail(t, "<html><body><title>Hello World</title></body></html>", rule)
	assertShouldPass(t, "<html><head><title> Hello World </title></head></html>", rule)
	assertShouldFail(t, "<html><head><title>Hi World</title></head></html>", rule)
}

func assertShouldPass(t *testing.T, value interface{}, rule interface{}) {
	outcome := DoAssert(value, rule)
	if len(outcome) > 0 {
		t.Errorf("Expected to pass for value: %v\n...but failed with error: %s", value, outcome)
	}
}

func assertShouldFail(t *testing.T, value interface{}, rule interface{}) {
	outcome := DoAssert(value, rule)
	if len(outcome) == 0 {
		t.Errorf("Expected to fail but was passing for value: %v", value)
	} else {
		t.Logf("DoAssert() output: %s", outcome)
	}
}

func newInt(value int) *int {
	return &value
}

func newString(value string) *string {
	return &value
}
