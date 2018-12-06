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

package specs // import "github.com/GoogleCloudPlatform/marketplace-k8s-app-tools/testrunner/specs"

import (
	"encoding/json"
	"io/ioutil"
	"log"
	"strings"

	"github.com/ghodss/yaml"
)

type Suite struct {
	Actions []Action `json:"actions,omitempty"`
}

type Action struct {
	Name      string     `json:"name,omitempty"`
	Condition *Condition `json:"condition,omitempty"`
	HttpTest  *HttpTest  `json:"httpTest,omitempty"`
	Gcp       *GcpAction `json:"gcp,omitempty"`
	BashTest  *BashTest  `json:"bashTest,omitempty"`
}

type Condition struct {
	FailuresSoFar *IntAssert `json:"failuresSoFar,omitempty"`
}

type HttpTest struct {
	Url     string            `json:"url"`
	Method  *string           `json:"method,omitempty"`
	Headers map[string]string `json:"headers,omitempty"`
	Expect  HttpExpect        `json:"expect"`
}

type GcpAction struct {
	SetRuntimeConfigVar *SetRuntimeConfigVarGcpAction `json:"setRuntimeConfigVar,omitempty"`
}

type BashTest struct {
	Script string     `json:"script"`
	Expect *CliExpect `json:"expect"`
}

type HttpExpect struct {
	StatusCode *IntAssert         `json:"statusCode,omitempty"`
	StatusText *StringAssert      `json:"statusText,omitempty"`
	BodyText   *TextContentAssert `json:"bodyText,omitempty"`
}

type CliExpect struct {
	ExitCode *IntAssert    `json:"exitCode,omitempty"`
	Stdout   *StringAssert `json:"stdout,omitempty"`
	Stderr   *StringAssert `json:"stderr,omitempty"`
}

type SetRuntimeConfigVarGcpAction struct {
	RuntimeConfigSelfLink string `json:"runtimeConfigSelfLink"`
	VariablePath          string `json:"variablePath"`
	Base64Value           string `json:"base64Value"`
}

type TextContentAssert struct {
	Html *HtmlAssert `json:"html,omitempty"`
}

type HtmlAssert struct {
	Title *StringAssert `json:"title,omitempty"`
}

type IntAssert struct {
	Equals      *int `json:"equals,omitempty"`
	AtLeast     *int `json:"atLeast,omitempty"`
	AtMost      *int `json:"atMost,omitempty"`
	LessThan    *int `json:"lessThan,omitempty"`
	GreaterThan *int `json:"greaterThan,omitempty"`
	NotEquals   *int `json:"notEquals,omitempty"`
}

type StringAssert struct {
	Exactly     *string `json:"exactly,omitempty"`
	Equals      *string `json:"equals,omitempty"`
	Contains    *string `json:"contains,omitempty"`
	Matches     *string `json:"matches,omitempty"`
	NotContains *string `json:"notContains,omitempty"`
}

func LoadSuite(path string) *Suite {
	data, err := ioutil.ReadFile(path)
	check(err)

	if strings.HasSuffix(path, ".json") {
		return loadJsonSuite(data)
	} else if strings.HasSuffix(path, ".yaml") || strings.HasSuffix(path, ".yml") {
		return loadYamlSuite(data)
	}
	log.Fatalf("Unrecognized test suite file type: %v", path)
	return &Suite{}
}

func loadJsonSuite(data []byte) *Suite {
	suite := Suite{}
	err := json.Unmarshal(data, &suite)
	check(err)
	return &suite
}

func loadYamlSuite(data []byte) *Suite {
	suite := Suite{}
	err := yaml.Unmarshal(data, &suite)
	check(err)
	return &suite
}

func check(err interface{}) {
	if err != nil {
		log.Fatalf("Error: %v", err)
	}
}
