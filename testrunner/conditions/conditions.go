package conditions // import "github.com/GoogleCloudPlatform/marketplace-k8s-app-tools/testrunner/conditions"

import (
	"github.com/GoogleCloudPlatform/marketplace-k8s-app-tools/testrunner/asserts"
	"github.com/GoogleCloudPlatform/marketplace-k8s-app-tools/testrunner/specs"
)

type TestStatus interface {
	FailuresSoFarCount() int
}

// Evaluate evaluates if a condition is true for the current test status.
// If the condition evaluates to false, the second return contains the reason.
func Evaluate(condition *specs.Condition, testStatus TestStatus) (bool, string) {
	if condition.FailuresSoFar != nil {
		if msg := asserts.DoAssert(testStatus.FailuresSoFarCount(), condition.FailuresSoFar); msg != "" {
			return false, asserts.MessageWithContext(msg, "Count of failures so far")
		}
	}
	return true, ""
}
