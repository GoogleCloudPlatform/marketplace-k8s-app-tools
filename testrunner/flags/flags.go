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

package flags // import "github.com/GoogleCloudPlatform/marketplace-k8s-app-tools/testrunner/flags"

import (
	"errors"
	"flag"
	"fmt"
	"strings"
)

type stringMapFlag map[string]string

func (m *stringMapFlag) String() string {
	return fmt.Sprintf("stringMapFlag%v", *m)
}

func (m *stringMapFlag) Set(value string) error {
	split := strings.SplitN(value, "=", 2)
	if len(split) != 2 {
		return errors.New("invalid flag format. Value should be key=value")
	}
	if *m == nil {
		*m = make(map[string]string)
	}
	(*m)[split[0]] = split[1]
	return nil
}

func FlagStringMap(name string, usage string) *map[string]string {
	var f stringMapFlag
	flag.Var(&f, name, usage)
	return (*map[string]string)(&f)
}

type stringListFlags []string

func (l *stringListFlags) String() string {
	return fmt.Sprintf("stringListFlags%v", *l)
}

func (l *stringListFlags) Set(value string) error {
	if len(value) <= 0 {
		return errors.New("empty value is not accepted")
	}
	if *l == nil {
		*l = make([]string, 0, 1)
	}
	*l = append(*l, value)
	return nil
}

func FlagStringList(name string, usage string) *[]string {
	var f stringListFlags
	flag.Var(&f, name, usage)
	return (*[]string)(&f)
}
