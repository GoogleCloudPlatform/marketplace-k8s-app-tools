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

package gcp // import "github.com/GoogleCloudPlatform/marketplace-k8s-app-tools/testrunner/gcp"
import (
	"bytes"
	"encoding/json"
	"fmt"
	"net/http"
	"net/url"
	"strings"

	"github.com/GoogleCloudPlatform/marketplace-k8s-app-tools/testrunner/specs"
	"github.com/golang/glog"
)

type VariablePayload struct {
	Name  string `json:"name"`
	Value string `json:"value"`
}

func runSetRuntimeConfigVar(action *specs.SetRuntimeConfigVarGcpAction, httpClient *http.Client) string {
	configUrl, err := url.Parse(action.RuntimeConfigSelfLink)
	if err != nil {
		return fmt.Sprintf("Invalid runtime config self link: %s", action.RuntimeConfigSelfLink)
	}
	configPath := strings.Join(strings.Split(configUrl.Path, "/")[2:], "/")
	payload := VariablePayload{
		Name:  fmt.Sprintf("%s/variables/%s", configPath, action.VariablePath),
		Value: action.Base64Value,
	}
	accessToken, err := fetchAccessToken(httpClient)
	if err != nil {
		return fmt.Sprintf("Unable to fetch access token: %v", err)
	}
	body, err := json.Marshal(payload)
	if err != nil {
		glog.Fatalf("Unexpected failure when constructing payload: %v", err)
	}

	req, err := http.NewRequest(
		http.MethodPost, fmt.Sprintf("%s/variables", configUrl.String()), bytes.NewReader(body))
	if err != nil {
		glog.Fatalf("Unexpected failure when constructing POST request: %v", err)
	}
	req.Header.Add("Authorization", fmt.Sprintf("Bearer %s", accessToken))
	req.Header.Add("Content-Type", "application/json")
	glog.V(1).Infof("About to send request: %+v", req)
	glog.V(1).Infof("Body: %s", body)
	res, err := httpClient.Do(req)
	if err != nil {
		return fmt.Sprintf("POST request error: %v", err)
	}
	if res.StatusCode != http.StatusOK {
		return fmt.Sprintf("POST request status: %v %v", res.StatusCode, res.Status)
	}
	return ""
}
