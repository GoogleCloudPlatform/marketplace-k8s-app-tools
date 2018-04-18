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
	"net/http"

	"fmt"
	"io/ioutil"

	"encoding/json"

	"errors"

	"github.com/GoogleCloudPlatform/marketplace-k8s-app-tools/testrunner/asserts"
	"github.com/GoogleCloudPlatform/marketplace-k8s-app-tools/testrunner/specs"
	"github.com/golang/glog"
)

const metadataUrl = "http://metadata.google.internal/computeMetadata/v1/"
const accessTokenUrl = metadataUrl + "instance/service-accounts/default/token"

type serviceAccountToken struct {
	AccessToken string `json:"access_token"`
	ExpiresIn   int    `json:"expires_in"`
	TokenType   string `json:"token_type"`
}

func RunAction(action *specs.GcpAction) string {
	if msg := validate(action); msg != "" {
		return asserts.MessageWithContext(msg, "Malformed GCP action")
	}

	if action.SetRuntimeConfigVar != nil {
		return runSetRuntimeConfigVar(action.SetRuntimeConfigVar, &http.Client{})
	}

	return ""
}

func validate(action *specs.GcpAction) string {
	return ""
}

func fetchAccessToken(httpClient *http.Client) (string, error) {
	req, err := http.NewRequest(http.MethodGet, accessTokenUrl, nil)
	if err != nil {
		glog.Fatalf("Unexpected failure when constructing access token GET request: %v", err)
	}
	req.Header.Add("Metadata-Flavor", "Google")
	res, err := httpClient.Do(req)
	if err != nil {
		return "", errors.New(fmt.Sprintf("Unable to GET access token: %v", err))
	}
	if res.StatusCode != http.StatusOK {
		return "", errors.New(fmt.Sprintf("Error GETting access token: %v %v", res.StatusCode, res.Status))
	}
	body, err := ioutil.ReadAll(res.Body)
	if err != nil {
		glog.Fatalf("Unexpected failure when reading the body: %v", err)
	}
	token := serviceAccountToken{}
	err = json.Unmarshal(body, &token)
	if err != nil {
		return "", errors.New(fmt.Sprintf("Unable to parse access token: %v", err))
	}
	glog.V(0).Infof("Acquired service account token: %+v", token)
	return token.AccessToken, nil
}
