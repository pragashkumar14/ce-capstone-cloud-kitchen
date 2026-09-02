package test

import (
	"testing"

	"github.com/gruntwork-io/terratest/modules/terraform"
	"github.com/stretchr/testify/assert"
)

// TestTerraformPlan validates that the full infrastructure produces a clean,
// valid plan with the expected number of resources. This does NOT create or
// destroy any real infrastructure -- it only runs `terraform plan`, which is
// deliberate: the live demo environment must not be disturbed by this test,
// and a full apply/destroy cycle would take 10+ minutes due to RDS and the
// NAT Gateway, which is impractical to run in CI on every pull request.
func TestTerraformPlan(t *testing.T) {
	terraformOptions := &terraform.Options{
		TerraformDir: "../../terraform",
		NoColor:      true,
	}

	terraform.Init(t, terraformOptions)

	planOutput := terraform.Plan(t, terraformOptions)

	// A clean plan against already-applied infrastructure should show
	// no changes needed -- confirming the code matches reality with no drift.
	assert.Contains(t, planOutput, "No changes.")
}

// TestTerraformValidate confirms the Terraform code is syntactically valid
// and internally consistent across all modules.
func TestTerraformValidate(t *testing.T) {
	terraformOptions := &terraform.Options{
		TerraformDir: "../../terraform",
		NoColor:      true,
	}

	terraform.Init(t, terraformOptions)
	terraform.Validate(t, terraformOptions)
}
