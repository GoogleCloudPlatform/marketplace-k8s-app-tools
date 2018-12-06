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

package specs_test

import (
	"reflect"
	"testing"

	. "github.com/GoogleCloudPlatform/marketplace-k8s-app-tools/testrunner/specs"
	"github.com/ghodss/yaml"
)

func TestYamlSuite(t *testing.T) {
	actual := LoadSuite("testdata/suite.yaml")
	expected := expectedSuite()
	assertSuitesEqual(t, actual, expected)
}

func TestJsonSuite(t *testing.T) {
	actual := LoadSuite("testdata/suite.json")
	expected := expectedSuite()
	assertSuitesEqual(t, actual, expected)
}

func assertSuitesEqual(t *testing.T, actual *Suite, expected *Suite) {
	// Converting to YAML makes it easier to see diffs.
	actualBytes, _ := yaml.Marshal(actual)
	expectedBytes, _ := yaml.Marshal(expected)
	if !reflect.DeepEqual(actualBytes, expectedBytes) {
		t.Errorf("Loaded suite not matching expected suite. Expected:\n%s\n...actual:\n%s\n", string(expectedBytes), string(actualBytes))
	}
}

func expectedSuite() *Suite {
	return &Suite{
		Actions: []Action{
			{
				Name: "Can load home page",
				HttpTest: &HttpTest{
					Url: "http://{{.Vars.MainVmIp}}:9012",
					Expect: HttpExpect{
						StatusCode: &IntAssert{
							Equals: newInt(200),
						},
						StatusText: &StringAssert{
							Contains: newString("OK"),
						},
						BodyText: &TextContentAssert{
							Html: &HtmlAssert{
								Title: &StringAssert{
									Contains: newString("Hello World!"),
								},
							},
						},
					},
				},
			},
			{
				Name: "Update success variable",
				Gcp: &GcpAction{
					SetRuntimeConfigVar: &SetRuntimeConfigVarGcpAction{
						RuntimeConfigSelfLink: "https://runtimeconfig.googleapis.com/v1beta1/projects/my-project/configs/my-config",
						VariablePath:          "status/success",
						Base64Value:           "c3VjY2Vzcwo=",
					},
				},
			},
			{
				Name: "Can echo to stdout and stderr",
				BashTest: &BashTest{
					Script: "echo \"Text1\"\n>2& echo \"Text2\"",
					Expect: &CliExpect{
						ExitCode: &IntAssert{
							Equals:    newInt(0),
							NotEquals: newInt(1),
						},
						Stdout: &StringAssert{
							Contains:    newString("Text1"),
							NotContains: newString("Foo"),
							Matches:     newString("T.xt1"),
						},
						Stderr: &StringAssert{
							Contains:    newString("Text2"),
							NotContains: newString("Foo"),
							Matches:     newString("T.xt2"),
						},
					},
				},
			},
		},
	}
}

func newInt(value int) *int {
	return &value
}

func newString(value string) *string {
	return &value
}
