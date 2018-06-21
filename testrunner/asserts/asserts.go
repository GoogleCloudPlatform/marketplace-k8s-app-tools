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

package asserts // import "github.com/GoogleCloudPlatform/marketplace-k8s-app-tools/testrunner/asserts"

import (
	"fmt"
	"regexp"
	"strings"

	xmlpath "gopkg.in/xmlpath.v2"

	"bytes"

	"github.com/GoogleCloudPlatform/marketplace-k8s-app-tools/testrunner/specs"
	"golang.org/x/net/html"
)

// MessageWithContext creates a new message that hierarchically puts
// the message within the provided context.
func MessageWithContext(msg string, context string) string {
	return fmt.Sprintf("%v > %v", context, msg)
}

// DoAssert asserts the value against the rule, returning
// an empty string if the assertion succeeds, or the error message.
func DoAssert(value interface{}, rule interface{}) string {
	switch r := rule.(type) {
	case specs.IntAssert:
		return doIntAssert(value.(int), r)
	case *specs.IntAssert:
		return doIntAssert(value.(int), *r)
	case specs.StringAssert:
		return doStringAssert(value.(string), r)
	case *specs.StringAssert:
		return doStringAssert(value.(string), *r)
	case specs.TextContentAssert:
		return doTextContentAssert(value.(string), r)
	case *specs.TextContentAssert:
		return doTextContentAssert(value.(string), *r)
	default:
		panic(fmt.Sprintf("Don't know how to handle rule type, %T", rule))
	}
}

func doIntAssert(value int, rule specs.IntAssert) string {
	if rule.Equals != nil && value != *rule.Equals {
		return fmt.Sprintf("Should have equaled %d, but was %d", *rule.Equals, value)
	}
	if rule.AtLeast != nil && value < *rule.AtLeast {
		return fmt.Sprintf("Should have been at least %d, but was %d", *rule.AtLeast, value)
	}
	if rule.AtMost != nil && value > *rule.AtMost {
		return fmt.Sprintf("Should have been at most %d, but was %d", *rule.AtMost, value)
	}
	if rule.LessThan != nil && value >= *rule.LessThan {
		return fmt.Sprintf("Should have been less than %d, but was %d", *rule.LessThan, value)
	}
	if rule.GreaterThan != nil && value <= *rule.GreaterThan {
		return fmt.Sprintf("Should have been greater than %d, but was %d", *rule.GreaterThan, value)
	}
	if rule.NotEquals != nil && value == *rule.NotEquals {
		return fmt.Sprintf("Should have been different from %d, but was %d", *rule.NotEquals, value)
	}
	return ""
}

func doStringAssert(value string, rule specs.StringAssert) string {
	if rule.Exactly != nil && value != *rule.Exactly {
		return fmt.Sprintf("Should have matched exactly:\n%s\n... but was:\n%s", *rule.Exactly, value)
	}
	if rule.NotContains != nil && strings.Contains(value, *rule.NotContains) {
		return fmt.Sprintf("Should have not contained:\n%s\n... but was:\n%s", *rule.NotContains, value)
	}
	if rule.Equals != nil {
		trimmed := strings.TrimSpace(value)
		if trimmed != *rule.Equals {
			return fmt.Sprintf("Should have been:\n%s\n... but was:\n%s", *rule.Equals, trimmed)
		}
	}
	if rule.Contains != nil && !strings.Contains(value, *rule.Contains) {
		return fmt.Sprintf("Should have contained:\n%s\n... but was:\n%s", *rule.Contains, value)
	}
	if rule.Matches != nil {
		r, err := regexp.Compile(*rule.Matches)
		if err != nil {
			return fmt.Sprintf("Regex failed to compile: %s", *rule.Matches)
		}
		if !r.MatchString(value) {
			return fmt.Sprintf("Should have matched regex:\n%s\n... but was:\n%s", *rule.Matches, value)
		}
	}
	return ""
}

func doTextContentAssert(value string, rule specs.TextContentAssert) string {
	if rule.Html != nil {
		if msg := doHtmlAssert(value, *rule.Html); msg != "" {
			return MessageWithContext(msg, "Html")
		}
	}
	return ""
}

func doHtmlAssert(value string, rule specs.HtmlAssert) string {
	// Use net/html to parse first because it can handle some malformed HTML.
	root, err := html.Parse(strings.NewReader(value))
	if err != nil {
		return "Failed to parse HTML content"
	}

	// Reconstruct well-formed XML for xmlpath library.
	var b bytes.Buffer
	html.Render(&b, root)
	fixedHtml := b.String()
	xmlRoot, err := xmlpath.ParseHTML(strings.NewReader(fixedHtml))
	if err != nil {
		return "Failed to fix and parse HTML to XML"
	}

	if rule.Title != nil {
		title, ok := xmlpath.MustCompile("/html/head/title").String(xmlRoot)
		if !ok {
			return "HTML document contains no title"
		}
		if msg := doStringAssert(title, *rule.Title); msg != "" {
			return MessageWithContext(msg, "Title")
		}
	}
	return ""
}
